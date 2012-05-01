import pygit2
import os
import tools
import collections
import subprocess

Entry = collections.namedtuple('Entry', 'path name type')

class Repo(object):
    def __init__(self, path):
        if not os.path.exists(path):
            pygit2.init_repository(path, True)
        self.path = path
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

    def get_ref(self, name):
        obj = self.repo.lookup_reference(name)
        return Commit(self.repo, obj.resolve())

    def get_commit(self, ident):
        try:
            ident = ident.decode('hex')
        except (ValueError, TypeError) as err:
            raise KeyError(err)
        return Commit(self.repo, self.repo[ident])

    def get_branch(self, name):
        try:
            return self.get_commit(name)
        except KeyError:
            return self.get_ref('refs/heads/' + name)

    def get_head(self):
        return self.get_ref('HEAD')

    def list_branches(self):
        return os.listdir(os.path.join(self.path, 'refs', 'heads'))

class Commit(object):
    def __init__(self, repo, ref):
        self.repo = repo
        self.obj = self.repo[ref.oid]

    def list(self, path):
        return self.get_tree(path).list()
    
    def get_tree(self, path):
        tree = self.obj.tree
        for name in path.split('/'):
            if name:
                tree = self.repo[tree[name].oid]
        return Object(self.repo, path, tree)

    @property
    def message(self):
        return self.obj.message

    @property
    def author(self):
        return self.obj.author

    @property
    def commiter(self):
        return self.obj.commiter

    @property
    def hex(self):
        return self.obj.hex

    @property
    def parents(self):
        return self.obj.parents

    @tools.reusable_generator
    def list_commits(self):
        for obj in self.repo.walk(self.obj.oid, pygit2.GIT_SORT_TIME):
            yield Commit(self.repo, obj)

    def diff_with_prev(self):
        if self.parents:
            return self.diff(self.parents[0].hex) # TODO
        else:
            return None

    def diff(self, id):
        return subprocess.check_output(['git', 'diff', self.obj.hex, id], cwd=self.repo.path)

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
