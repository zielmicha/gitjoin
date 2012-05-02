from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.views import login, logout

import gitjoin.models
from gitjoin import views

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^gitauth', views.gitauth),

    url(r'^accounts/login/$', login, ), #{'template_name': 'login.html'}
    url(r'^accounts/logout/$', logout, ), #{'template_name': 'logout.html'}
    #url(r'^accounts/profile/$', redirect_to, {'url': '/'}),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url('^$', views.home, name='home'),
    url('^org/new$', views.org_new, name='org_new'),
    url('^org/admin/([^/]+)$', views.org_admin, name='org_admin'),
    url('^org/admin/([^/]+)/group/([^/]+)$', views.org_admin_group, name='org_admin_group'),
    url('^org/admin/([^/]+)/groupnew$', views.org_admin_group_new, name='org_admin_group_new'),
    url(r'^repo/new$', views.new_repo, name='new_repo'),
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
    url(r'^([^/]+)/([^/]+)$', views.repo, name='repo'),
    url(r'^([^/]+)/?$', views.user, name='user'),
)
