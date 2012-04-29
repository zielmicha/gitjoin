import models
import authorized_keys

class Error(Exception):
    pass

def create_repo(user, name):
    if not name:
        raise Error('empty name')
    try:
        models.Repo.get_by_name(user.name + '/' + name)
    except models.Repo.DoesNotExist:
        pass
    else:
        raise Error('aleardy exists')

    repo = models.Repo(holder=user, name=name)
    repo.save()
    user.rw_repos.add(repo)
    user.rwplus_repos.add(repo)
    user.ro_repos.add(repo)
    user.save()

def edit_repo(repo, name, ro, rw, rwplus):
    def _edit_list(category, new):
        entries = getattr(repo, category + '_privileged')
        if not new:
            raise Error('%s list cannot be empty' % category)
        if repo.holder.name not in new:
            raise Error('Repository holder needs to be in %s list' % category)
        users = []
        for name in new:
            try:
                users.append(models.User.objects.filter(name=name).get())
            except models.User.DoesNotExist:
                raise Error('User %s does not exist' % name)
        entries.clear()
        for user in users:
            entries.add(user)

    if not name:
        raise Error('Name must not be empty')
    if '/' in name:
        raise Error('Name must not contain /')

    repo.name = name
    _edit_list('ro', ro)
    _edit_list('rw', rw)
    _edit_list('rwplus', rwplus)
    repo.save()

def delete_ssh_key(user, id):
    key = models.SSHKey.objects.filter(id=id).get()
    if key.owner == user:
        key.delete()
    else:
        raise Error('Permission denied')

    authorized_keys.create()

def add_ssh_key(user, name, data):
    models.SSHKey(owner=user, name=name, data=data).save()
    authorized_keys.create()