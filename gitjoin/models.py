from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User as DjangoUser

class RepoHolder(models.Model):
    name = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = "repository holder"
        verbose_name_plural = "repository holders"
    
    def __unicode__(self):
        return self.name

class Repo(models.Model):
    holder = models.ForeignKey(RepoHolder)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "repository"
        verbose_name_plural = "repositories"

class PrivilegeOwner(models.Model):
    repos = models.ManyToManyField(Repo, related_name='privilegated')
    
    class Meta:
        verbose_name = "privilige owner"
        verbose_name_plural = "privilege owners"

class User(PrivilegeOwner, RepoHolder, DjangoUser):
    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

class SSHKey(PrivilegeOwner):
    owner = models.ForeignKey(User)
    name = models.CharField(max_length=50)
    data = models.CharField(max_length=150)
    
    class Meta:
        verbose_name = "ssh key"
        verbose_name_plural = "ssh keys"

admin.site.register(Repo)
admin.site.register(RepoHolder)
admin.site.register(User)
admin.site.register(PrivilegeOwner)