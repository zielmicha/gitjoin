# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sys
import itertools

import models
import git

supported_hooks = ['update', 'post-receive']

hook_script = '''#!/bin/bash
export GIT_DIR=$(realpath $GIT_DIR)
export DJANGO_SETTINGS_MODULE=webapp.settings
cd
python -m gitjoin.hooks run %s $*
'''

def regenerate_all_hooks():
    for repo in models.Repo.objects.all():
        print repo.get_full_name()
        repo = git.Repo.from_model(repo)
        regenerate_hooks(repo)

def regenerate_hooks(repo):
    for name in supported_hooks:
        repo.set_hook(name, hook_script % name)

def main():
    if len(sys.argv) < 2:
        sys.exit('missing action')

    action = sys.argv[1]
    permission = os.environ.get('GIT_PERMISSION', '')

    if action == 'regen':
        regenerate_all_hooks()
    elif action == 'run':
        hook_name = sys.argv[2]
        hook_args = sys.argv[3:]
        git_dir = os.environ['GIT_DIR']
        status = run_hook(git_dir, permission, hook_name, hook_args)
        sys.exit(status)
    else:
        sys.exit('unknown action %r' % action)

def run_hook(path, permission, name, args):
    repo = git.Repo(path)

    if name not in supported_hooks:
        return 'unsupported hook %s' % name

    if name == 'update':
        ref, old, new = args
        hook_update(repo, permission, ref, old, new)

def hook_update(repo, permission, ref, old, new):
    print 'counting commits...',
    sys.stdout.flush()
    to_add, to_remove = get_commit_changes(repo, old, new)
    print 'new', len(to_add),
    if to_remove:
        print 'remove', len(to_remove)
    else:
        print

    if to_remove and permission != 'rwplus':
        sys.exit('You are not permitted to rewind this repository.')

    for i, hex in enumerate(to_add):
        commit = repo.get_commit(hex)
        commit.get_files_commit(_no_check_recur=True)
        print '\rprocessing new commits (%d/%d, %s)...' % (i + 1, len(to_add), commit.hex),
        sys.stdout.flush()

    print 'done'

def get_commit_changes(repo, old, new):
    zeros = '0000000000000000000000000000000000000000'
    old_commit_list = repo.get_commit(old).list_commits() if old != zeros else []
    new_commit_list = repo.get_commit(new).list_commits() if new != zeros else []
    iterated_from_new = set()
    iterated_from_old = set()

    common_ancestor = None

    for commit_from_new, commit_from_old in itertools.izip_longest(new_commit_list, old_commit_list, fillvalue=None):
        if commit_from_new:
            commit_from_new = commit_from_new.hex
            iterated_from_new.add(commit_from_new)

        if commit_from_old:
            commit_from_old = commit_from_old.hex
            iterated_from_old.add(commit_from_old)

        if commit_from_new in iterated_from_old:
            common_ancestor = commit_from_new
            break

        if commit_from_old in iterated_from_new:
            common_ancestor = commit_from_old
            break

    to_add = []
    to_remove = []

    for commit in old_commit_list:
        if commit.hex == common_ancestor:
            break
        to_remove.append(commit.hex)

    for commit in new_commit_list:
        if commit.hex == common_ancestor:
            break
        to_add.append(commit.hex)

    return to_add, to_remove

if __name__ == '__main__':
    main()
