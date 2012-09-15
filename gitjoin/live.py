#!/usr/bin/env python
# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from gitjoin import git, tools, models
import sys
import json
import hashlib
import urllib
import os

def githash(data):
    s = hashlib.sha1()
    s.update("blob %u\0" % len(data))
    s.update(data)
    return s.hexdigest()

def main(repo_id, path, user):
    LiveServer(repo_id, path, user).run()

class LiveServer(object):
    def __init__(self, repo_id, path, user):
        self.repo = git.Repo(path)
        self.root = None
        self.storage = create_storage(repo_id, user)

    def run(self):
        while True:
            args, kwargs = json.loads(sys.stdin.readline())
            name = args[0]
            args = args[1:]
            result = self.invoke(name, *args, **kwargs)
            data = json.dumps({'value': result})
            sys.real_stdout.write(data + '\n')
            sys.real_stdout.flush()

    def invoke(self, name, *args, **kwargs):
        method = {
            'has-commit?': self.has_commit,
            'set-new-commits!': self.set_new_commits,
            'set-root!': self.set_root,
            'get-hashes': self.get_hashes,
            'update-file!': self.update_file,
            'reset!': self.reset,
        }[name]
        return method(*args, **kwargs)

    def update_file(self, path, hash, data):
        # not atomic, but who cares
        data = data.decode('base64')
        path = path.encode('utf8')
        self.storage['data_' + path] = data
        self.storage['hash_' + path] = hash

    def has_commit(self, ident):
        try:
            self.repo.get_commit(ident)
        except KeyError:
            return False
        else:
            return True

    def set_new_commits(self, idents):
        pass

    def set_root(self, hex):
        self.root = self.repo.get_commit(hex)

    def get_hashes(self):
        l = []
        for name, obj in self.root.get_tree('/').list_recursive():
            try:
                hex = self.storage['hash_' + name]
            except KeyError:
                hex = obj.hex
            l.append((name, hex))
        return dict(l)

    def get_file_names(self):
        return [ key[5:] for key in self.storage.keys() if key.startswith('data_') ]

    def get_files(self):
        return [ (name, self.get_file(name)) for name in self.get_file_names() ]

    def get_file(self, name):
        return self.storage['data_' + name]

    def reset(self):
        self.storage.clear()

def create_storage(repo_id, user):
    models.LiveData.objects.get_or_create(repo=models.Repo.objects.get(id=repo_id),
                                          user=user)
    path = os.path.expanduser('~/var/live/%d_%d' % (repo_id, user.id))
    if not os.path.isdir(path):
        os.makedirs(path)
    return tools.FSCache(path)
