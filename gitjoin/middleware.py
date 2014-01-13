from gitjoin import models

class AuthReplaceUserMiddleware(object):
    def process_request(self, request):
        django_user = request.user
        if not django_user.is_anonymous():
            request.user = models.User.get_for_django_user(django_user)
