# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from gitjoin.models import User, Group
from webapp.settings import CAS_SERVER_URL
from django.contrib.auth import models as authmodels

import django_cas.views

def _service_url(request, redirect_to=None):
    protocol = ('http://', 'https://')[request.is_secure()]
    host = request.get_host()
    service = protocol + host + request.path
    return service

django_cas.views._service_url = _service_url

import pam
import pwd
import traceback
import urllib
import json

class AtomshareCASBackend(object):
    def authenticate(self, *args, **kwargs):
        try:
            return self._authenticate(*args, **kwargs)
        except Exception as ex:
            # django doesn't show stack traces from auth backend
            traceback.print_exc()
            raise

    def _authenticate(self, ticket, service):
        data = validate(ticket, service)
        username = data['user_name']
        attr = data['attributes']
        email = attr['mail']
        superuser = attr['is_admin'] == 'True'
        first_name = attr['first_name']

        last_name = attr['last_name']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User(username=username)
            user.name = username
            user.set_unusable_password()
            user.save()

        if (user.first_name, user.last_name, user.email) != (first_name, last_name, email):
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

        if superuser != user.is_superuser:
            user.is_staff = user.is_superuser = superuser
            user.save()

        print 'ok, return', user

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    keep_django_details = False

def validate(ticket, service):
    args = urllib.urlencode({'ticket': ticket, 'service': service, 'format': 'json'})
    url = CAS_SERVER_URL + 'serviceValidate?' + args
    print url
    stream = urllib.urlopen(url)
    if stream.getcode() != 200:
        raise Exception('request failed with %d' % stream.getcode())
    return json.load(stream)
