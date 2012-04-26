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

    url(r'^([^/]+)/([^/]+)/tree/([^/]+)/(.*)$', views.repo_tree, name='repo_tree'),
    url(r'^([^/]+)/([^/]+)/admin$', views.repo_admin, name='repo_admin'),
    url(r'^([^/]+)/([^/]+)$', views.repo, name='repo'),
    url(r'^([^/]+)/?$', views.user, name='user'),
)
