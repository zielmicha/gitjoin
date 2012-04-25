import pygit2
import os
import tools
import collections

Entry = collections.namedtuple('Entry', 'path name')

class Repo(object):
    def __init__(self, path):
        self.repo = pygit2.Repository(path)
    
    @staticmethod
    def from_model(model):
        return Repo(os.path.expanduser('~/repos/%d' % model.id))
    
    def list(self, path=''):
        return self.get_head().list(path)
    
    def get_head(self):
        return Commit(self.repo, self.repo.lookup_reference('HEAD'))

class Commit(object):
    def __init__(self, repo, ref):
        self.repo = repo
        self.obj = self.repo[ref.resolve().oid]
    
    @tools.reusable_generator
    def list(self, path=''):
        tree = self.get_tree(path)
        path = path.rstrip('/')
        for obj in tree:
            value = tree[obj.name]
            entry = self.repo[value.oid]
            yield Entry(name=obj.name, path=path + (path and '/') + obj.name)
    
    def get_tree(self, path):
        tree = self.obj.tree
        for name in path.split('/'):
            if name:
                tree = self.repo[tree[name].oid]
        return tree
