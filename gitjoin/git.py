import pygit2
import os
import tools
import collections

Entry = collections.namedtuple('Entry', 'path name type')

class Repo(object):
    def __init__(self, path):
        if not os.path.exists(path):
            pygit2.init_repository(path, True)
        self.repo = pygit2.Repository(path)
    
    @staticmethod
    def from_model(model):
        return Repo(os.path.expanduser('~/repos/%d' % model.id))
    
    def list(self, path=''):
        return self.get_head().list(path)

    def get_readme(self):
        try:
            return self.get_head().get_tree('README').get_data()
        except KeyError:
            return ''

    def get_ref(self, path):
        return Commit(self.repo, self.repo.lookup_reference(path))

    def get_branch(self, name):
        return self.get_ref('refs/heads/' + name)

    def get_head(self):
        return self.get_ref('HEAD')

class Commit(object):
    def __init__(self, repo, ref):
        self.repo = repo
        self.obj = self.repo[ref.resolve().oid]

    def list(self, path):
        return self.get_tree(path).list()
    
    def get_tree(self, path):
        tree = self.obj.tree
        for name in path.split('/'):
            if name:
                tree = self.repo[tree[name].oid]
        return Object(self.repo, path, tree)

class Object(object):
    def __init__(self, repo, path, obj):
        self.repo = repo
        self.path = '/'.join( name for name in path.split('/') if name )
        self.obj = obj

    @tools.reusable_generator
    def list(self):
        for obj in self.obj:
            value = self.obj[obj.name]
            entry = self.repo[value.oid]
            type = 'dir' if isinstance(entry, pygit2.Tree) else 'file'
            yield Entry(name=obj.name, path=self.path + (self.path and '/') + obj.name, type=type)

    def is_directory(self):
        return isinstance(self.obj, pygit2.Tree)

    def get_data(self):
        return self.obj.read_raw()