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
from webapp import settings

admin.autodiscover()

urlpatterns = patterns('',
    #xurl(r'^global/gitauth', views.gitauth),

    url(r'^global/accounts/login/$', login, ),
    url(r'^global/accounts/logout/$', logout, ),
    url(r'^accounts/profile/$', lambda req: http.HttpResponseRedirect('/')),
#    url(r'global/admin$' if not settings.HAS_CAS else '^$', lambda req: http.HttpResponseRedirect('/global/admin/')),
    url(r'^global/admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^global/admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),

    url('^$', views.home, name='home'),
    url(r'^global/org/new$', views.org_new, name='org_new'),
    url(r'^global/org/admin/([^/]+)$', views.org_admin, name='org_admin'),
    url(r'^global/org/admin/([^/]+)/group/([^/]+)$', views.org_admin_group, name='org_admin_group'),
    url(r'^global/org/admin/([^/]+)/groupnew$', views.org_admin_group_new, name='org_admin_group_new'),
    url(r'^global/repo/new$', views.new_repo, name='new_repo'),
    url(r'^settings/ssh$', views.ssh_keys, name='ssh_keys'),
    url(r'^settings/ssh/new/(.+)$', views.ssh_keys_new, name='ssh_keys_new'),
    url(r'^settings/ssh/delete$', views.ssh_keys_delete, name='ssh_keys_delete'),
    url(r'^settings/ssh/sh/(.*)/add.sh$', views.ssh_keys_new_script, name='ssh_keys_new_script'),
    url(r'^settings/ssh/sh/(.*)/next$', views.ssh_keys_new_script_continue, name='ssh_keys_new_script_continue'),

    url(r'^([^/]+)/([^/]+)/tree/([^/]+)/(.*)$', views.repo_tree, name='repo_tree'),
    url(r'^([^/]+)/([^/]+)/commit/([^/]+)$', views.repo_commit, name='repo_commit'),
    url(r'^([^/]+)/([^/]+)/commit/([^/]+)/diff/(.*)$', views.repo_commit_diff, name='repo_commit_diff'),
    url(r'^([^/]+)/([^/]+)/commits/([^/]+)$', views.repo_commits, name='repo_commits'),
    url(r'^([^/]+)/([^/]+)/branches$', views.repo_branches, name='repo_branches'),
    url(r'^([^/]+)/([^/]+)/admin$', views.repo_admin, name='repo_admin'),
    url(r'^([^/]+)/([^/]+)/admin/keys$', views.repo_admin_keys, name='repo_admin_keys'),
    url(r'^([^/]+)/([^/]+)/admin/hooks$', views.repo_admin_hooks, name='repo_admin_hooks'),
    url(r'^([^/]+)/([^/]+)/admin/hooks/edit$', views.repo_admin_hooks_edit, name='repo_admin_hooks_edit'),
    url(r'^([^/]+)/([^/]+)/admin/hooks/new$', views.repo_admin_hooks_new, name='repo_admin_hooks_new'),
    url(r'^([^/]+)/([^/]+)/live/([^/]+)$', views.live_main, name='live_main'),
    url(r'^([^/]+)/([^/]+).git(|/.*)$', views.repo_git_http, name='repo_git_http'),
    url(r'^([^/]+)/([^/]+)$', views.repo, name='repo'),
    url(r'^([^/]+)/?$', views.user, name='user'),
)
