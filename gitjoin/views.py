from django import http
import django.core.exceptions
import models

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
    