# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from gitjoin import models
from gitjoin import authorized_keys
from gitjoin import hooks
from gitjoin import git
import os
import re
import json

from django.db import IntegrityError
from webapp import settings

RESERVED_GLOBAL_NAMES = 'global', 'settings'

class Error(Exception):
    pass

def check_ident(ident):
    if not re.match('^[a-zA-Z0-9_-]+$', ident):
        raise Error('wrong identifier %s' % ident)

def create_repo(user, holder_name, name):
    if not name:
        raise Error('empty name')
    check_ident(name)
    try:
        models.Repo.get_by_name(holder_name + '/' + name)
    except models.Repo.DoesNotExist:
        pass
    else:
        raise Error('already exists')

    if holder_name == user.name:
        holder = user
    else:
        holder = models.Organization.objects.filter(name=holder_name, owners=user).get()

    repo = models.Repo(name=name)
    repo.holder = holder
    repo.save()
    user.rw_repos.add(repo)
    user.rwplus_repos.add(repo)
    user.ro_repos.add(repo)
    user.save()

    init_repo(repo)

def init_repo(repo):
    path = settings.REPOS_PATH + ('/%d' % repo.id)
    git.init(path)
    repo = git.Repo(path)
    hooks.regenerate_hooks(repo)

def edit_repo(user, repo, name, description, public, ro, rw, rwplus):
    def _edit_list(category, new):
        entries = list(models.PrivilegeOwner.get_privileged(repo, category + '_repos'))
        if not new:
            raise Error('%s list cannot be empty' % category)
        if (user.name not in new) and (user in entries):
            raise Error('You cannot remove yourself from %s list' % category)
        users = []
        for name in new:
            try:
                users.append(models.PrivilegeOwner.get_by_name(name))
            except models.PrivilegeOwner.DoesNotExist as err:
                raise Error(err.message)
        entries = getattr(repo, category + '_privileged')
        entries.clear()
        for new_user in users:
            entries.add(new_user)

    def _propagate(to, from_):
        to += from_

    repo.check_user_authorized(user, 'rwplus')

    if not name:
        raise Error('Name must not be empty')
    if '/' in name:
        raise Error('Name must not contain /')

    check_ident(name)
    repo.name = name
    repo.public = public
    repo.description = description

    _propagate(rw, rwplus)
    _propagate(ro, rw)

    _edit_list('ro', ro)
    _edit_list('rw', rw)
    _edit_list('rwplus', rwplus)
    repo.save()

def delete_ssh_key(user, id):
    key = models.SSHKey.objects.filter(id=id).get()
    if key.owner == user or (key.target and key.target.is_user_authorized(user, 'rwplus')):
        key.delete()
    else:
        raise Error('Permission denied')

    authorized_keys.create()

def add_ssh_key(user, target, name, data):
    key = models.SSHKey(name=name, data=data)
    if target == 'user':
        key.owner = user
    else:
        key.target = models.Repo.get_by_name(target)
        key.target.check_user_authorized(user, 'rwplus')
    key.save()
    authorized_keys.create()

def new_org(user, name):
    if not user.is_staff:
        raise Error('Permission denied')
    check_ident(name)
    if name in RESERVED_GLOBAL_NAMES:
        raise Error('%s is a reserved name' % name)
    try:
        org  = models.Organization(name=name)
        org.save()
        org.owners.add(user)
        edit_org(user, org, [user.name])
    except IntegrityError:
        raise Error('organization already exists')

def edit_org(user, org, new_owners):
    org.check_if_owner(user)

    if user.name not in new_owners:
        raise Error('You cannot remove yourself from owners list.')

    users = []
    for new_name in new_owners:
        try:
            users.append(models.User.objects.get(name=new_name))
        except models.User.DoesNotExist:
            raise Error('User named %s does not exist' % new_name)

    owners_group, _created = models.Group.objects.get_or_create(organization=org, name='owners')
    org.owners.clear()
    owners_group.members.clear()
    for user in users:
        owners_group.members.add(user)
        org.owners.add(user)
    org.save()
    owners_group.save()

def edit_group(user, group, name, new_members):
    group.organization.check_if_owner(user)

    existing_members = group.members.all()
    if (user in existing_members) and user.name not in new_members:
        raise Error('You cannot remove yourself from members list.')

    users = []
    for new_name in new_members:
        try:
            users.append(models.User.objects.get(name=new_name))
        except models.User.DoesNotExist:
            raise Error('User named %s does not exist.' % new_name)

    check_ident(name)
    if group.name != name and group.organization.group_set.filter(name=name).count() > 0:
        raise Error('Group named %s already exists.' % name)
    group.name = name
    group.members.clear()
    for user in users:
        group.members.add(user)
    group.save()

def delete_group(user, group):
    group.organization.check_if_owner(user)
    group.delete()

def new_group(user, org, name):
    org.check_if_owner(user)

    check_ident(name)

    group, was_created = models.Group.objects.get_or_create(name=name, organization=org)
    if not was_created:
        raise Error('Group named %s already exists.' % name)
    group.save()

def add_hook(user, repo, name, type_name):
    repo.check_user_authorized(user, 'rwplus')
    hook = models.Hook(repo=repo, name=name, type_name=type_name, parameters='{}')
    hook.save()
    return hook.id

def edit_hook(user, repo, name, id, enabled, parameters):
    repo.check_user_authorized(user, 'rwplus')
    hook = models.Hook.objects.get(id=id)
    if hook.repo != repo:
        raise PermissionDenied
    hook.enabled = enabled
    hook.name = name
    hook.parameters = json.dumps(parameters)
    hook.save()

def delete_hook(user, repo, id):
    repo.check_user_authorized(user, 'rwplus')
    hook = models.Hook.objects.get(id=id)
    if hook.repo != repo:
        raise PermissionDenied
    hook.delete()
