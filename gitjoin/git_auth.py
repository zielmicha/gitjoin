#!/usr/bin/env python
import sys
import os
import shlex
import subprocess

os.environ['DJANGO_SETTINGS_MODULE'] = 'webapp.settings'

from gitjoin import models

import tools

def main():
    auth_obj, = sys.argv[1:]
    command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    cmd, _, arg = command.partition(' ')
    
    if cmd in ('git-upload-pack', 'git-receive-pack'):
        args_split = shlex.split(arg)
        if len(args_split) != 1:
            sys.exit('Unexpected number of arguments: %s' % len(args_split))
        repo = args_split[0]
        invoke_command(auth_obj, cmd, repo)
    else:
        sys.exit('Expected git-upload-pack or git-receive-pack, got %s instead.' % (cmd or 'nothing'))

def invoke_command(auth_obj, cmd, repo):
    try:
        path = get_path(auth_obj, cmd, repo)
    except PermissionDenied as err:
        sys.exit('Cannot access repository %s: %s' % (repo, err.message))
    
    with tools.global_lock(), tools.lock('repo_' + path, shared=cmd == 'git-upload-pack'):
        status = subprocess.call((cmd, path))
    
    sys.exit(status)

def get_path(auth_obj, cmd, repo):
    access = {'git-upload-pack': 'ro', 'git-receive-pack': 'rw'}[cmd]

    ident = gitauth(repo_name=repo, auth=auth_obj, access=access)
    return os.path.expanduser('~/repos/%d' % ident)

def gitauth(repo_name, auth, access):
    auth_type, auth_val = auth.split(':', 1)

    try:
        repo = models.Repo.get_by_name(repo_name)
    except Exception as err:
        raise PermissionDenied(err.message)

    if auth_type == 'user':
        try:
            user = models.User.objects.filter(username=auth_val).get()
        except django.core.exceptions.ObjectDoesNotExist as err:
            raise PermissionDenied('no such user')

        if not repo.is_user_authorized(user, access):
            raise PermissionDenied('access denied for user %s' % user.name)
    elif auth_type == 'repo':
        if int(auth_val) != repo.id:
            raise PermissionDenied('deploy key not valid for repository %s' % repo_name)
    else:
        raise PermissionDenied('internal error')

    return repo.id

class PermissionDenied(Exception): pass

if __name__ == '__main__':
    main()
