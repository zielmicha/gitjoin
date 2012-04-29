import models

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

