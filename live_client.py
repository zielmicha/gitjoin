#!/usr/bin/python2.7
# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import subprocess
import argparse
import pygit2
import json
import os
import hashlib
import tempfile

# default
DEFAULT_ADDRESS = 'gitdev@localhost'
MAX_SIZE = 5 * 1024 * 1024
VERBOSE = False

# this is going to be replaced with generated variables
#__PLACE_FOR_AUTOGEN__#

def main():
    parser = argparse.ArgumentParser(description='Gitjoin\'s live git client')
    parser.add_argument('path',
                        help='repository path')
    parser.add_argument('name',
                        help='remote repository name')
    parser.add_argument('--address', dest='address',
                        default=DEFAULT_ADDRESS,
                        help='connect to this SSH address (default: %(default)s)')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_const', const=True,
                        default=False)
    parser.add_argument('--reset', dest='reset', action='store_const', const=True, default=False,
                        help='instead of running daemon, reset all live data for this repo')

    args = parser.parse_args()
    global VERBOSE
    VERBOSE = args.verbose
    prog = Program(args.address, args.name, args.path)

    try:
        if args.reset:
            prog.reset()
        else:
            prog.run()
    finally:
            prog.conn.kill()

class Program(object):

    def __init__(self, address, remote_name, path):
        self.repo = pygit2.Repository(path)
        self.conn = Connection(address, remote_name)
        self.path = path
        self.uploaded_hashes = {}

    def reset(self):
        self.conn.call('reset!')
        print 'Ok.'

    def run(self):
        head = self.repo[self.repo.lookup_reference('HEAD').resolve().oid]
        common_commit, new_commits = self.find_common_commit(head)
        self.conn.call('set-new-commits!', [ (commit.hex, commit.message) for commit in new_commits ])
        self.conn.call('set-root!', common_commit.hex)
        self.uploaded_hashes = self.conn.call('get-hashes')
        common_commit = self.repo[common_commit.oid]
        self.root_tree = common_commit.tree
        self.add_watched_files(head.tree)

    def add_watched_files(self, tree, path=''):
        for entry in tree:
            name = entry.name
            obj = self.repo[tree[name].oid]
            new_path = (path + '/' + name) if path else name
            if isinstance(obj, pygit2.Tree):
                self.add_watched_files(obj, new_path)
            else:
                self.add_watched_file(new_path)

    def add_watched_file(self, path):
        self.check_file(path)

    def check_file(self, path):
        real_path = os.path.join(self.path, path)
        if os.path.getsize(real_path) <= MAX_SIZE:
            data = open(real_path).read()
            my_hex = githash(data)
            if my_hex != self.uploaded_hashes.get(path):
                self.update_file(path, my_hex)

    def update_file(self, path, hex):
        if VERBOSE:
            print 'update file', path, '(to %s, from %s)' % (hex, self.uploaded_hashes.get(path))

        real_path = os.path.join(self.path, path)
        data = self.compute_diff(path, open(real_path).read()).encode('base64')
        self.conn.call('update-file!', path, hex, data)
        self.uploaded_hashes[path] = hex

    def compute_diff(self, path, data):
        try:
            old = self.get_object(path).read_raw()
        except KeyError:
            old = ''
        return diff(data, old)

    def get_object(self, path):
        tree = self.root_tree
        for name in path.split('/'):
            tree = self.repo[tree[name].oid]
        return tree

    def find_common_commit(self, head):
        MAX_SEARCH = 100
        queue = [head]
        new_commits = []
        searched = 0
        while queue:
            commit = queue.pop()
            searched += 1
            if searched >= MAX_SEARCH:
                break

            if self.conn.call('has-commit?', commit.hex):
                return commit, new_commits

            new_commits.append(commit)

            queue += commit.parents

        raise Exception('searched %d commits up, no common found' % searched)

class Connection(object):
    def __init__(self, address, remote_name):
        self.proc = subprocess.Popen(['ssh', address, 'gitjoin-live', remote_name],
                                     stdout=subprocess.PIPE, stdin=subprocess.PIPE, close_fds=True)
        self.output, self.input = (self.proc.stdin, self.proc.stdout)

    def call(self, *args, **kwargs):
        if VERBOSE and args[0] != 'update-file!':
            print repr(args)[1:-1], repr(kwargs)[1:-1]
        data = json.dumps([args, kwargs])
        assert '\n' not in data
        self.output.write(data + '\n')
        self.output.flush()
        result = json.loads(self.input.readline())
        if result.get('error'):
            raise RemoteError(result['error'])
        else:
            return result['value']

    def kill(self):
        os.kill(self.proc.pid, 9)

def githash(data):
    s = hashlib.sha1()
    s.update("blob %u\0" % len(data))
    s.update(data)
    return s.hexdigest()

def diff(a, b):
    def make_tmp(data):
        f = tempfile.NamedTemporaryFile()
        f.write(data)
        f.flush()
        return f
    af = make_tmp(a)
    bf = make_tmp(b)
    try:
        return get_output(['diff', '-u', bf.name, af.name])
    finally:
        af.close()
        bf.close()

def get_output(*args, **kwargs):
    try:
        return subprocess.check_output(*args, **kwargs)
    except subprocess.CalledProcessError as err:
        return err.output

class RemoteError(Exception):
    pass

if __name__ == '__main__':
    main()
