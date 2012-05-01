from django import http
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
import django.core.exceptions
import webapp.settings
import models
import controller
import git
import tools

def home(request):
    return to_template(request, 'home.html', dict(
        users=models.User.objects.all(),
        orgs=models.Organization.objects.all(),
    ))

def gitauth(request):
    try:
        auth_type, auth_val = request.GET.get('auth').split(':', 1)
        repo_name = request.GET.get('repo')
        access = request.GET.get('access')

        try:
            repo = models.Repo.get_by_name(repo_name)
        except Exception as err:
            return http.HttpResponse('error: ' + err.message)

        if auth_type == 'user':
            try:
                user = models.User.objects.filter(username=auth_val).get()
            except django.core.exceptions.ObjectDoesNotExist as err:
                return http.HttpResponse('error: no such user')

            if not repo.is_user_authorized(user, access):
                return http.HttpResponse('error: access denied for user %s' % user.name)
        elif auth_type == 'repo':
            if int(auth_val) != repo.id:
                return http.HttpResponse('error: deploy key not valid for repository %s' % repo_name)
        else:
            return http.HttpResponse('error: internal error')

        return http.HttpResponse('ok: %d' % repo.id)
    except Exception as err:
        return http.HttpResponse('error: exception %r' % err)

def user(request, name):
    holder = models.RepoHolder.get_by_name(name)
    repos = holder.repos.all()
    owners = holder.owners.all() if isinstance(holder, models.Organization) else None
    is_owner = (request.user in owners) if owners else holder == request.user
    groups = holder.group_set.all() if isinstance(holder, models.Organization) else None
    return to_template(request, 'user.html', dict(repos=repos, object=holder, owners=owners, is_owner=is_owner, groups=groups))

def repo(request, username, name):
    repo = get_repo(request.user, username + '/' + name)
    grepo = git.Repo.from_model(repo)
    return to_template(request, 'repo.html', dict(
            repo=repo,
            branch='master', #repo.default_branch,
            git_list=tools.none_on_error(grepo.list, errors=[KeyError]),
            path='/',
            readme=grepo.get_readme()))

def repo_tree(request, username, repo_name, branch, path):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    object = grepo.get_branch(branch).get_tree(path)

    if object.is_directory():
        return to_template(request, 'repo_tree.html', dict(
            branch=branch,
            repo=repo,
            path=path,
            git_list=object.list()))
    else:
        return to_template(request, 'repo_blob.html', dict(
            branch=branch,
            repo=repo,
            path=path,
            git_blob=object.get_data()))

def repo_admin(request, username, repo_name):
    repo = get_repo(request.user, username + '/' + repo_name)
    error = None

    if request.POST:
        name = request.POST.get('name')
        ro = request.POST.get('ro').split()
        rw = request.POST.get('rw').split()
        rwplus = request.POST.get('rwplus').split()
        public = bool(request.POST.get('public'))
        try:
            controller.edit_repo(request.user, repo, name, public=public, ro=ro, rw=rw, rwplus=rwplus)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('repo_admin', args=[username, repo.name]))

    return to_template(request, 'repo_admin.html', dict(
        error=error,
        repo=repo,
        has_access=repo.is_user_authorized(request.user, 'rwplus')))

def repo_admin_keys(request, username, repo_name):
    repo = get_repo(request.user, username + '/' + repo_name)
    error = None

    return to_template(request, 'repo_admin_keys.html', dict(
        error=error,
        repo=repo,
        ssh_target=username + '/' + repo_name,
        keys=models.SSHKey.objects.filter(target=repo),
        has_access=repo.is_user_authorized(request.user, 'rwplus')))

def repo_commits(request, username, repo_name, branch):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    object = grepo.get_branch(branch)
    return to_template(request, 'repo_commits.html', dict(
        branch=branch,
        repo=repo,
        git_commits=object.list_commits()))

def repo_commit(request, username, repo_name, commit):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    object = grepo.get_branch(commit)
    return to_template(request, 'commit.html', dict(
        commit=object,
        branch=commit,
        diff=object.diff_with_prev(),
        repo=repo))

def repo_commit_diff(request, username, repo_name, commit):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    object = grepo.get_branch(commit)
    return to_template(request, 'commit_diff.html', dict(
        commit=object,
        branch=commit,
        diff=object.diff_with_prev(),
        repo=repo))

def repo_branches(request, username, repo_name):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    return to_template(request, 'repo_branches.html', dict(
        repo=repo,
        git_branches=grepo.list_branches()))

def new_repo(request):
    error = None
    if request.POST:
        name = request.POST.get('name')
        holder = request.POST.get('holder')
        try:
            controller.create_repo(request.user, holder, name)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('repo', args=[holder, name]))
    return to_template(request, 'new_repo.html', dict(
        error=error,
        req_holder=request.GET.get('holder'),
        holders=[ request.user.name ] + [ org.name for org in request.user.organizations.all() ]
    ))

def ssh_keys(request):
    return to_template(request, 'ssh_keys.html', dict(
        keys=models.SSHKey.objects.filter(owner=request.user),
        ssh_target='user',
    ))

def ssh_keys_new(request, target):
    name = request.POST.get('name')
    data = request.POST.get('data')
    controller.add_ssh_key(request.user, target, name, data)
    if target == 'user':
        return http.HttpResponseRedirect(reverse('ssh_keys'))
    else:
        return http.HttpResponseRedirect(reverse('repo_admin_keys', args=target.split('/', 1)))

def ssh_keys_delete(request):
    id = request.POST.get('id')
    controller.delete_ssh_key(request.user, id)
    return http.HttpResponseRedirect(reverse('ssh_keys'))

def org_new(request):
    error = None
    if request.POST:
        name = request.POST.get('name')
        try:
            controller.new_org(request.user, name)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('user', args=[name]))

    return to_template(request, 'org_new.html', dict(error=error))

def org_admin(request, name):
    holder = models.RepoHolder.get_by_name(name)
    owners = holder.owners.all() if isinstance(holder, models.Organization) else None
    error = None

    if request.POST:
        new_owners = request.POST.get('owners').split()
        try:
            controller.edit_org(request.user, holder, new_owners)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('org_admin', args=[name]))

    return to_template(request, 'org_admin.html', dict(
        object=holder,
        owners=owners,
        error=error,
    ))

def org_admin_group(request, name, group_name):
    if group_name == 'owners':
        return http.HttpResponseRedirect(reverse('org_admin', args=[name]))

    holder = models.RepoHolder.get_by_name(name)
    group = holder.group_set.get(name=group_name)
    error = None

    if request.POST:
        new_members = request.POST.get('members').split()
        new_name = request.POST.get('name')
        try:
            if request.POST.get('delete'):
                controller.delete_group(request.user, group)
            else:
                controller.edit_group(request.user, group, new_name, new_members)
        except controller.Error as err:
            error = err.message
        else:
            if request.POST.get('delete'):
                return http.HttpResponseRedirect(reverse('user', args=[name]))
            else:
                return http.HttpResponseRedirect(reverse('org_admin_group', args=[name, new_name]))

    return to_template(request, 'org_admin_group.html', dict(
        object=holder,
        group=group,
        error=error,
    ))

def org_admin_group_new(request, name):
    holder = models.RepoHolder.get_by_name(name)
    error = None

    if request.POST:
        name = request.POST.get('name')
        try:
            controller.new_group(request.user, holder, name)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('user', args=[holder.name]))

    return to_template(request, 'org_admin_group_new.html', dict(
        object=holder,
        error=error,
    ))

def get_repo(user, full_name):
    repo = models.Repo.get_by_name(full_name)
    repo.check_user_authorized(user)
    return repo

def to_template(request, name, args={}):
    args = args.copy()
    args['settings'] = webapp.settings.__dict__
    return direct_to_template(request, name, args)