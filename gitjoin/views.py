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
    user_name = request.GET.get('user')
    repo_name = request.GET.get('repo')
    access = request.GET.get('access')
    
    try:
        user = models.User.objects.filter(username=user_name).get()
    except django.core.exceptions.ObjectDoesNotExist as err:
        return http.HttpResponse('error: no such user')
    
    try:
        repo = get_repo(request.user, repo_name)
    except Exception as err:
        return http.HttpResponse('error: ' + err.message)
    
    if not repo.is_user_authorized(user, access):
        return http.HttpResponse('error: not authorized')
    
    return http.HttpResponse('ok: %d' % repo.id)

def user(request, name):
    user = models.RepoHolder.get_by_name(name)
    repos = user.repos.all()
    return to_template(request, 'user.html', dict(repos=repos, object=user))

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
        repo=repo))

def repo_commits(request, username, repo_name, branch):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    object = grepo.get_branch(branch)
    return to_template(request, 'repo_commits.html', dict(
        branch=branch,
        repo=repo,
        git_commits=object.list_commits()))

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
        holders=[ request.user.name ] + [ org.name for org in request.user.organizations.all() ]
    ))

def ssh_keys(request):
    return to_template(request, 'ssh_keys.html', dict(
        keys=models.SSHKey.objects.filter(owner=request.user)
    ))

def ssh_keys_new(request):
    name = request.POST.get('name')
    data = request.POST.get('data')
    controller.add_ssh_key(request.user, name, data)
    return http.HttpResponseRedirect(reverse('ssh_keys'))

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

def get_repo(user, full_name):
    repo = models.Repo.get_by_name(full_name)
    repo.check_user_authorized(user)
    return repo

def to_template(request, name, args={}):
    args = args.copy()
    args['settings'] = webapp.settings.__dict__
    return direct_to_template(request, name, args)