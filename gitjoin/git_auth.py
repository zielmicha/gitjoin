#!/usr/bin/env python
# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import sys

sys.real_stdout = sys.stdout
sys.stdout = sys.stderr # but do not redirect native stdout

import os
import shlex
import subprocess

os.environ['DJANGO_SETTINGS_MODULE'] = 'webapp.settings'

from gitjoin import models, live
from webapp import settings

import tools

def main():
    auth_obj, = sys.argv[1:]
    command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    cmd, _, arg = command.partition(' ')

    if cmd in ('git-upload-pack', 'git-receive-pack', 'gitjoin-live'):
        args_split = shlex.split(arg)
        if len(args_split) != 1:
            sys.exit('Unexpected number of arguments: %s' % len(args_split))
        invoke_command(auth_obj, cmd, args_split)
    else:
        sys.exit('Expected git-upload-pack or git-receive-pack, got %s instead.' % (cmd or 'nothing'))

def invoke_command(auth_obj, cmd, args):
    repo_name = args[0]
    try:
        repo_id, permission, user = get_repo_and_permission_and_user(auth_obj, cmd, repo_name)
    except PermissionDenied as err:
        sys.exit('Cannot access repository %s: %s' % (repo_name, err.message))

    path = settings.REPOS_PATH + ('/%d' % repo_id)
    if cmd == 'gitjoin-live':
        live.main(repo_id, path, user)
    else:
        os.environ['GIT_PERMISSION'] = permission
        status = subprocess.call((cmd, path))
        sys.exit(status)

def get_repo_and_permission_and_user(auth_obj, cmd, repo):
    access = {'git-upload-pack': 'ro', 'git-receive-pack': 'rw', 'gitjoin-live': 'rw'}[cmd]

    ident, permission, user = gitauth(repo_name=repo, auth=auth_obj, access=access)
    return ident, permission, user

def gitauth(repo_name, auth, access):
    try:
        repo = models.Repo.get_by_name(repo_name)
    except Exception as err:
        raise PermissionDenied(err.message)

    permission = None
    errors = []
    user = None
    for key in models.SSHKey.objects.filter(fingerprint=auth):
        if key.owner:
            user = key.owner
            if not repo.is_user_authorized(user, access):
                errors.append('access denied for user %s' % user.name)
            else:
                if access == 'rw' and repo.is_user_authorized(user, 'rwplus'):
                    permission = 'rwplus'
                else:
                    permission = access
        elif key.target:
            if key.target == repo:
                permission = 'rw'
            else:
                errors.append('deploy key valid for repository %s' % key.target.get_full_name())

    if not permission:
        if errors:
            raise PermissionDenied(', '.join(errors))
        else:
            if os.environ.get('CALLED_WITH_CUSTOM_SSHD'):
                raise PermissionDenied('key you authorized with is not authorized for any repos'
                                       + ' (id: %s)' % auth)
            else:
                raise PermissionDenied(
                    'no keys found (looks like .authorized_keys is out of sync with DB)')

    return repo.id, permission, user

class PermissionDenied(Exception): pass

if __name__ == '__main__':
    main()
