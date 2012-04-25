from django import http
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.simple import direct_to_template
import django.core.exceptions
import models
import git

def gitauth(request):
    user_name = request.GET.get('user')
    repo_name = request.GET.get('repo')
    
    try:
        user = models.User.objects.filter(username=user_name).get()
    except django.core.exceptions.ObjectDoesNotExist as err:
        return http.HttpResponse('error: no such user')
    
    try:
        repo = models.Repo.get_by_name(repo_name)
    except Exception as err:
        return http.HttpResponse('error: ' + err.message)
    
    if not repo.is_user_authorized(user):
        return http.HttpResponse('error: not authorized')
    
    return http.HttpResponse('ok: %d' % repo.id)

def user(request, name):
    user = models.User.objects.filter(username=name).get()
    repos = models.Repo.objects.filter(holder=user)
    return direct_to_template(request, 'user.html', dict(repos=repos, object=user))

def repo(request, username, name):
    repo = models.Repo.get_by_name(username + '/' + name)
    grepo = git.Repo.from_model(repo)
    return direct_to_template(request, 'repo.html', dict(
            repo=repo,
            git_list=grepo.list(),
            readme='README should be here!'))


    
