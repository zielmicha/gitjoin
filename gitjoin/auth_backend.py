from django.contrib.auth.models import Group
from gitjoin.models import User
from webapp.settings import SUPERUSERS

import pam
import pwd

class VLOBackend(object):
    
    def authenticate(self, *args, **kwargs):
        username = self.check_auth(*args, **kwargs)
        
        if not username:
            return None
        
        username = username.strip().lower()
        
        print username
        
        if username.endswith('_admin'):
            # redirect *_admin accounts to normal accounts
            username = username[:-len('_admin')]
            if username not in SUPERUSERS:
                raise Exception('You are not expected to be admin')
        
        email = username + '@v-lo.krakow.pl'
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User(username=username, email=email, password='')
            user.name = username
            user.set_unusable_password()
            user.save()
        
        group_name, first_name, last_name = get_name_and_group(username)
        
        if group_name:
            group, was_created = Group.objects.get_or_create(name=group_name)
        
            if group not in user.groups.all():
                user.groups.add(group)
                user.save()
        
        if (username in SUPERUSERS) != user.is_superuser or user.is_superuser != user.is_staff:
            user.is_staff = user.is_superuser = (username in SUPERUSERS)
            user.save()
        
        if (user.first_name, user.last_name) != (first_name, last_name):
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        
        print 'ok, return', user
        
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class PAMBackend(VLOBackend):
    def check_auth(self, username, password):
        if pam.authenticate(username, password):
            return username

from django_cas.backends import _verify as cas_verify

class CASBackend(VLOBackend):
    def check_auth(self, ticket, service):
        return cas_verify(ticket, service)

def get_name_and_group(login_name):
    gecos = pwd.getpwnam(login_name).pw_gecos
    name = gecos.split(',')[0].decode('utf8')
    if gecos.count(',') >= 2:
        group = gecos.split(',')[2].decode('utf8')
    else:
        group = None
    if ' ' in name:
        return (group,) + tuple(name.rsplit(' ', 1))
    else:
        return group, name, ''