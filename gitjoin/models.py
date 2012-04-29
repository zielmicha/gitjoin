from django.core import exceptions
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
    
    @staticmethod
    def get_by_name(repofull):
        try:
            alias = RepoAlias.objects.filter(name=repofull).get()
            return alias.repo
        except exceptions.ObjectDoesNotExist as err:
            pass
        
        if '/' not in repofull:
            raise Repo.DoesNotExist('no / in repo name')
        
        holder, reponame = repofull.split('/')
        
        try:
            repo = Repo.objects.filter(name=reponame, holder__name=holder).get()
        except exceptions.ObjectDoesNotExist as err:
            raise Repo.DoesNotExist('no such repository')
        
        return repo
    
    def is_user_authorized(self, user, access='ro'):
        sel_repos = {'ro': user.ro_repos, 'rw': user.rw_repos}[access]
        try:
            ok = sel_repos.filter(id=self.id).get()
        except exceptions.ObjectDoesNotExist as err:
            return False
        
        return True
    
    def check_user_authorized(self, user):
        if not self.is_user_authorized(user):
            raise exceptions.PermissionDenied('not authorized')

class RepoAlias(models.Model):
    repo = models.ForeignKey(Repo)
    name = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = "repository alias"
        verbose_name_plural = "repository aliases"

class PrivilegeOwner(models.Model):
    ro_repos = models.ManyToManyField(Repo, related_name='ro_privilegated')
    rw_repos = models.ManyToManyField(Repo, related_name='rw_privilegated')
    rwplus_repos = models.ManyToManyField(Repo, related_name='rwplus_privilegated')
    
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
    data = models.TextField()
    
    class Meta:
        verbose_name = "SSH key"
        verbose_name_plural = "SSH keys"
    
    def __unicode__(self):
        return u'SSHKey %s, owner: %s' % (self.name, self.owner)

admin.site.register(Repo)
admin.site.register(RepoHolder)
admin.site.register(RepoAlias)
admin.site.register(User)
admin.site.register(PrivilegeOwner)
admin.site.register(SSHKey)