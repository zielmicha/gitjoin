import pygit2
import os
import tools
import collections
from mysubprocess import check_output

Entry = collections.namedtuple('Entry', 'path name type')
DiffEntry = collections.namedtuple('DiffEntry', 'action path old_mode new_mode')

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

    def diff_with_prev(self, raw=False, file=None):
        if self.parents:
            return self.diff(self.parents[0].hex, raw=raw, file=file) # TODO
        else:
            return None

    def diff(self, id, raw=False, file=None):
        file_args = ['--', file] if file else []
        if raw:
            result = check_output(['git', 'diff', '--raw', id, self.obj.hex] + file_args, cwd=self.repo.path)
            return _parse_raw_diff(result)
        else:
            return check_output(['git', 'diff', id, self.obj.hex] + file_args, cwd=self.repo.path)

@tools.reusable_generator
def _parse_raw_diff(result):
    for line in result.splitlines():
        old_mode, new_mode, old_hex, new_hex, action, path = line.split(None, 5)
        yield DiffEntry(action=action, path=path, old_mode=old_mode.lstrip(':'), new_mode=new_mode)

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
