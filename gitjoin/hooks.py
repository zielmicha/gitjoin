# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sys

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

    if action == 'regen':
        regenerate_all_hooks()
    elif action == 'run':
        hook_name = sys.argv[2]
        hook_args = sys.argv[3:]
        git_dir = os.environ['GIT_DIR']
        status = run_hook(git_dir, hook_name, hook_args)
        sys.exit(status)
    else:
        sys.exit('unknown action %r' % action)

def run_hook(path, name, args):
    print path, 'hook', name, ' '.join(args)

    repo = git.Repo(path)

    if name not in supported_hooks:
        return 'unsupported hook %s' % name

    if name == 'update':
        ref, old, new = args
        hook_update(repo, ref, old, new)

def hook_update(repo, ref, old, new):
    if new.count('0') == len(new):
        print 'processing branch deletion... (nothing)'
        return 
    new_commit = repo.get_commit(new)
    print 'counting commits...',
    sys.stdout.flush()
    commits = list(iter_from(old, new_commit))
    print len(commits)
    for i, commit in enumerate(commits):
        commit.get_files_commit(_no_check_recur=True)
        print '\rprocessing commits (%d/%d, %s)...' % (i + 1, len(commits), commit.hex),
        sys.stdout.flush()
    print 'done'

def iter_from(old, new_commit):
    def _i():
        for commit in new_commit.list_commits():
            if commit.hex == old:
                break
            yield commit
    return reversed(list(_i()))


if __name__ == '__main__':
    main()
