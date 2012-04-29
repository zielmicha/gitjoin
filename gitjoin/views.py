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

def gitauth(request):
    user_name = request.GET.get('user')
    repo_name = request.GET.get('repo')
    access = request.GET.get('access')
    
    try:
        user = models.User.objects.filter(username=user_name).get()
    except django.core.exceptions.ObjectDoesNotExist as err:
        return http.HttpResponse('error: no such user')
    
    try:
        repo = models.Repo.get_by_name(repo_name)
    except Exception as err:
        return http.HttpResponse('error: ' + err.message)
    
    if not repo.is_user_authorized(user, access):
        return http.HttpResponse('error: not authorized')
    
    return http.HttpResponse('ok: %d' % repo.id)

def user(request, name):
    user = models.User.objects.filter(username=name).get()
    repos = models.Repo.objects.filter(holder=user)
    return to_template(request, 'user.html', dict(repos=repos, object=user))

def repo(request, username, name):
    repo = models.Repo.get_by_name(username + '/' + name)
    grepo = git.Repo.from_model(repo)
    return to_template(request, 'repo.html', dict(
            repo=repo,
            branch='master', #repo.default_branch,
            git_list=tools.none_on_error(grepo.list, errors=[KeyError]),
            path='/',
            readme=grepo.get_readme()))

def repo_tree(request, username, repo_name, branch, path):
    repo = models.Repo.get_by_name(username + '/' + repo_name)
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
    repo = models.Repo.get_by_name(username + '/' + repo_name)
    error = None

    if request.POST:
        name = request.POST.get('name')
        ro = request.POST.get('ro').split()
        rw = request.POST.get('rw').split()
        rwplus = request.POST.get('rwplus').split()
        try:
            controller.edit_repo(repo, name, ro, rw, rwplus)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('repo_admin', args=[username, repo.name]))

    return to_template(request, 'repo_admin.html', dict(
        error=error,
        repo=repo))

def repo_commits(request, username, repo_name, branch):
    repo = models.Repo.get_by_name(username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    object = grepo.get_branch(branch)
    return to_template(request, 'repo_commits.html', dict(
        branch=branch,
        repo=repo,
        git_commits=object.list_commits()))

def repo_branches(request, username, repo_name):
    repo = models.Repo.get_by_name(username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    return to_template(request, 'repo_branches.html', dict(
        repo=repo,
        git_branches=grepo.list_branches()))

def new_repo(request):
    error = None
    if request.POST:
        name = request.POST.get('name')
        try:
            controller.create_repo(request.user, name)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('repo', args=[request.user.username, name]))
    return to_template(request, 'new_repo.html', dict(
        error=error
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

def to_template(request, name, args):
    args = args.copy()
    args['settings'] = webapp.settings.__dict__
    return direct_to_template(request, name, args)