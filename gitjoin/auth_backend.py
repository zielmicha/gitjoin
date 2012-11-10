# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from gitjoin.models import User, Group
from webapp.settings import SUPERUSERS
from django.contrib.auth import models as authmodels

import pam
import pwd
import traceback

class VLOBackend(object):

    def authenticate(self, *args, **kwargs):
        try:
            return self._authenticate(*args, **kwargs)
        except Exception as ex:
            # django doesn't show stack traces from auth backend
            traceback.print_exc()
            raise ex

    def _authenticate(self, *args, **kwargs):
        username = self.check_auth(*args, **kwargs)

        if not username:
            return None

        username = username.strip().lower()

        if username.endswith('_admin'):
            # redirect *_admin accounts to normal accounts
            username = username[:-len('_admin')]
            if username not in SUPERUSERS:
                raise Exception('You are not expected to be admin')

        email = username + '@v-lo.krakow.pl'

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User(username=username, email=email, password='')
            user.name = username
            user.set_unusable_password()
            user.save()

        group_name, first_name, last_name = get_name_and_group(username)

        if group_name:
            group_name = group_name.strip().replace(' ', '-').lower()
            group, was_created = Group.objects.get_or_create(name=group_name)

            if group not in user.git_groups.all():
                user.git_groups.add(group)
                user.save()

        if (username in SUPERUSERS) != user.is_superuser or user.is_superuser != user.is_staff:
            user.is_staff = user.is_superuser = (username in SUPERUSERS)
            user.save()

        if (user.first_name, user.last_name) != (first_name, last_name):
            user.first_name = first_name
            user.last_name = last_name
            user.save()

        print 'ok, return', user

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class PAMBackend(VLOBackend):
    def check_auth(self, username, password):
        if pam.authenticate(username, password):
            return username


class DjangoBackend(VLOBackend):
    def check_auth(self, username, password):
        if authmodels.User.objects.get(username=username).check_password(password):
            return username

try:
    from django_cas.backends import _verify as cas_verify
except ImportError:
    pass

class CASBackend(VLOBackend):
    def check_auth(self, ticket, service):
        return cas_verify(ticket, service)

def get_name_and_group(login_name):
    try:
        gecos = pwd.getpwnam(login_name).pw_gecos
    except KeyError:
        return '', '', ''
    name = gecos.split(',')[0].decode('utf8')
    if gecos.count(',') >= 2:
        group = gecos.split(',')[2].decode('utf8')
    else:
        group = None
    if ' ' in name:
        return (group,) + tuple(name.rsplit(' ', 1))
    else:
        return group, name, ''
