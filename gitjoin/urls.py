from django.conf.urls import patterns, include, url
from django.contrib import admin

import gitjoin.models
from gitjoin import views

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^gitauth', views.gitauth),
    
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
