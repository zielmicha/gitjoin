import models
import authorized_keys

from django.db import IntegrityError

class Error(Exception):
    pass

def create_repo(user, holder_name, name):
    if not name:
        raise Error('empty name')
    try:
        models.Repo.get_by_name(user.name + '/' + name)
    except models.Repo.DoesNotExist:
        pass
    else:
        raise Error('already exists')

    if holder_name == user.name:
        holder = user
    else:
        holder = models.Organization.objects.filter(name=holder_name, owners=user).get()

    repo = models.Repo(holder=holder, name=name)
    repo.save()
    user.rw_repos.add(repo)
    user.rwplus_repos.add(repo)
    user.ro_repos.add(repo)
    user.save()

def edit_repo(user, repo, name, public, ro, rw, rwplus):
    def _edit_list(category, new):
        entries = getattr(repo, category + '_privileged')
        if not new:
            raise Error('%s list cannot be empty' % category)
        if (user.name not in new) and entries.filter(name=user.name).count() > 0:
            raise Error('You cannot remove yourself from %s list' % category)
        users = []
        for name in new:
            try:
                users.append(models.User.objects.filter(name=name).get())
            except models.User.DoesNotExist:
                raise Error('User %s does not exist' % name)
        entries.clear()
        for new_user in users:
            entries.add(new_user)

    repo.check_user_authorized(user, 'rwplus')

    if not name:
        raise Error('Name must not be empty')
    if '/' in name:
        raise Error('Name must not contain /')

    repo.name = name
    repo.public = public
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

def new_org(user, name):
    try:
        org  = models.Organization(name=name)
        org.save()
        org.owners.add(user)
        org.save()
    except IntegrityError:
        raise Error('organization already exists')