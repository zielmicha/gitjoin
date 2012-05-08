import pygit2
import os
import tools
import collections
from mysubprocess import check_output

Entry = collections.namedtuple('Entry', 'path name type last_commit')
DiffEntry = collections.namedtuple('DiffEntry', 'action path old_mode new_mode')

def init(path):
    pygit2.init_repository(path, True)

class Repo(object):
    def __init__(self, path):
        self.path = path
        self.repo = pygit2.Repository(path)

    @staticmethod
    def from_model(model):
        return Repo(os.path.expanduser('~/repos/%d' % model.id))
    
    def list(self, path='', **kwargs):
        return self.get_head().list(path, **kwargs)

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

    def list(self, path, **kwargs):
        return self.get_tree(path).list(**kwargs)
    
    def get_tree(self, path):
        tree = self.obj.tree
        for name in path.split('/'):
            if name:
                tree = self.repo[tree[name].oid]
        return Object(self.repo, path, tree, commit=self)

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
        return [ Commit(self.repo, parent) for parent in self.obj.parents ]

    @tools.reusable_generator
    def list_commits(self):
        for obj in self.repo.walk(self.obj.oid, pygit2.GIT_SORT_TIME):
            yield Commit(self.repo, obj)

    def diff_with_prev(self, raw=False, file=None):
        if self.parents:
            return self.diff(self.obj.parents[0].hex, raw=raw, file=file) # TODO
        else:
            return None

    def diff(self, id, raw=False, file=None):
        file_args = ['--', file] if file else []
        if raw:
            result = check_output(['git', 'diff', '--raw', id, self.obj.hex] + file_args, cwd=self.repo.path)
            return _parse_raw_diff(result)
        else:
            return check_output(['git', 'diff', id, self.obj.hex] + file_args, cwd=self.repo.path)

    @tools.cached(key=lambda self, path: (self.hex, path))
    def get_files_commit_from_dir(self, path):
        d = {}
        path = path.rstrip('/') + '/' if path.rstrip('/') else ''
        for k, v in self.get_files_commit().items():
            if k.startswith(path) and k.count('/') == path.count('/'):
                d[k[len(path):].rstrip('/')] = v
        return d

    @tools.cached(key=lambda self, **k: str(self.hex))
    def get_files_commit(self, _no_check_recur=False):
        # Probably there is a better way to do this, but I don't know how.
        # Caching is necessary to make it O(n), because of merges.
        ' Returns dictionary mapping file path to commit hex when file was last modified '

        # prevent maximum recursion depth exceeded error
        if not _no_check_recur:
            for commit in reversed(self.list_commits()):
                if commit.hex != self.hex:
                    commit.get_files_commit(_no_check_recur=True)

        d = {}

        if len(self.parents) > 1: # merge
            for parent in self.parents:
                d.update(parent.get_files_commit())
        elif len(self.parents) == 1:
            parent = self.parents[0]
            d.update(parent.get_files_commit())

        if len(self.parents) == 1:
            for change in self.diff_with_prev(raw=True):
                if change != 'D':
                    d[change.path] = self.hex
                    for frag_path, frag_name in tools.split_path(change.path):
                        d[frag_path] = self.hex
                else:
                    del d[change.path]

        return d

@tools.reusable_generator
def _parse_raw_diff(result):
    for line in result.splitlines():
        old_mode, new_mode, old_hex, new_hex, action, path = line.split(None, 5)
        yield DiffEntry(action=action, path=path, old_mode=old_mode.lstrip(':'), new_mode=new_mode)

class Object(object):
    def __init__(self, repo, path, obj, commit=None):
        self.repo = repo
        self.path = '/'.join( name for name in path.split('/') if name )
        self.obj = obj
        self.commit = commit

    @tools.reusable_generator
    def list(self, include_commit_info=False):
        if include_commit_info:
            commit_info = self.commit.get_files_commit_from_dir(self.path)
            print commit_info
        else:
            commit_info = {}
        for obj in self.obj:
            value = self.obj[obj.name]
            entry = self.repo[value.oid]
            type = 'dir' if isinstance(entry, pygit2.Tree) else 'file'
            last_commit = commit_info.get(obj.name)
            yield Entry(name=obj.name, path=self.path + (self.path and '/') + obj.name, type=type,
                last_commit=Commit(self.repo, self.repo[last_commit.decode('hex')]) if last_commit else None)

    def is_directory(self):
        return isinstance(self.obj, pygit2.Tree)

    def get_data(self):
        return self.obj.read_raw()

if __name__ == '__main__':
    import pprint
    from gitjoin import git
    repo = git.Repo('repos/4')
    master = repo.get_branch('master')
    msg = master.get_files_commit()
    #print pprint.pformat(msg)[:200], ' etc...'
    #print pprint.pformat(master.get_files_commit_from_dir('webapp'))
