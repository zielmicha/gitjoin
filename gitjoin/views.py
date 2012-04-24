from django import http
import django.core.exceptions
import models

def gitauth(request):
    user = request.GET.get('user')
    repofull = request.GET.get('repo')
    
    holder, reponame = repofull.split('/')
    
    try:
        repo = models.Repo.objects.filter(name=reponame, holder__name=holder).get()
    except django.core.exceptions.ObjectDoesNotExist as err:
        return http.HttpResponse('error: no repo')
    
    try:
        user = models.User.objects.filter(username=user).get()
    except django.core.exceptions.ObjectDoesNotExist as err:
        return http.HttpResponse('error: no user')
    
    try:
        ok = user.repos.filter(id=repo.id).get()
    except django.core.exceptions.ObjectDoesNotExist as err:
        return http.HttpResponse('error: not auth')
    
    return http.HttpResponse('ok: %d' % repo.id)
    