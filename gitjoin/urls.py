# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.views import login, logout
from django import http

import gitjoin.models
from gitjoin import views

admin.autodiscover()

urlpatterns = patterns('',
    #xurl(r'^global/gitauth', views.gitauth),

    url(r'^global/accounts/login/$', login, ), #{'template_name': 'login.html'}
    url(r'^global/accounts/logout/$', logout, ), #{'template_name': 'logout.html'}
    #url(r'^accounts/profile/$', redirect_to, {'url': '/'}),
    url(r'global/admin$', lambda req: http.HttpResponseRedirect('/global/admin/')),
    url(r'^global/admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^global/admin/', include(admin.site.urls)),

    url('^$', views.home, name='home'),
    url(r'^global/org/new$', views.org_new, name='org_new'),
    url(r'^global/org/admin/([^/]+)$', views.org_admin, name='org_admin'),
    url(r'^global/org/admin/([^/]+)/group/([^/]+)$', views.org_admin_group, name='org_admin_group'),
    url(r'^global/org/admin/([^/]+)/groupnew$', views.org_admin_group_new, name='org_admin_group_new'),
    url(r'^global/repo/new$', views.new_repo, name='new_repo'),
    url(r'^settings/ssh$', views.ssh_keys, name='ssh_keys'),
    url(r'^settings/ssh/new/(.+)$', views.ssh_keys_new, name='ssh_keys_new'),
    url(r'^settings/ssh/delete$', views.ssh_keys_delete, name='ssh_keys_delete'),

    url(r'^([^/]+)/([^/]+)/tree/([^/]+)/(.*)$', views.repo_tree, name='repo_tree'),
    url(r'^([^/]+)/([^/]+)/commit/([^/]+)$', views.repo_commit, name='repo_commit'),
    url(r'^([^/]+)/([^/]+)/commit/([^/]+)/diff/(.*)$', views.repo_commit_diff, name='repo_commit_diff'),
    url(r'^([^/]+)/([^/]+)/commits/([^/]+)$', views.repo_commits, name='repo_commits'),
    url(r'^([^/]+)/([^/]+)/branches$', views.repo_branches, name='repo_branches'),
    url(r'^([^/]+)/([^/]+)/admin$', views.repo_admin, name='repo_admin'),
    url(r'^([^/]+)/([^/]+)/admin/keys$', views.repo_admin_keys, name='repo_admin_keys'),
    url(r'^([^/]+)/([^/]+).git(|/.*)$', views.repo_git_http, name='repo_git_http'),
    url(r'^([^/]+)/([^/]+)$', views.repo, name='repo'),
    url(r'^([^/]+)/?$', views.user, name='user'),
)
