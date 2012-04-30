from django.core import exceptions
from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User as DjangoUser
from django.db.models import Q
from itertools import chain

class RepoHolder(models.Model):
    name = models.CharField(max_length=50, unique=True)

    @classmethod
    def get_by_name(self, name):
        try:
            return User.objects.filter(name=name).get()
        except User.DoesNotExist:
            return Organization.objects.filter(name=name).get()

    class Meta:
        verbose_name = "repository holder"
        verbose_name_plural = "repository holders"
        abstract = True

    def __unicode__(self):
        return self.name

class Repo(models.Model):
    holding_user = models.ForeignKey('User', related_name='repos', null=True, blank=True)
    holding_org = models.ForeignKey('Organization', related_name='repos', null=True, blank=True)

    @property
    def holder(self):
        return self.holding_user or self.holding_org

    @holder.setter
    def holder(self, val):
        self.holding_org = self.holding_user = None
        if isinstance(val, User):
            self.holding_user = val
        else:
            self.holding_org = val

    name = models.CharField(max_length=50)
    public = models.BooleanField()

    class Meta:
        verbose_name = "repository"
        verbose_name_plural = "repositories"

    def get_full_name(self):
        return self.holder.name + '/' + self.name

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
            repo = Repo.objects.filter(name=reponame).filter(Q(holding_user__name=holder) | Q(holding_org__name=holder)).get()
        except exceptions.ObjectDoesNotExist as err:
            raise Repo.DoesNotExist('no such repository')
        
        return repo
    
    def is_user_authorized(self, user, access='ro'):
        if self.public and access == 'ro':
            return True

        if self.holder == user:
            return True

        if not isinstance(user, User):
            return False

        # 1. verify if user is authorized
        sel_repos = {'ro': user.ro_repos, 'rw': user.rw_repos, 'rwplus': user.rwplus_repos}[access]
        try:
            ok = sel_repos.filter(id=self.id).get()
        except exceptions.ObjectDoesNotExist as err:
            # 2. verify if user's group is authorized
            priv_groups  = user.git_groups.filter(** {access + '_repos': self})
            try:
                ok = priv_groups.get()
            except exceptions.ObjectDoesNotExist as err:
                return False
            else:
                return True
        
        return True
    
    def check_user_authorized(self, user, access='ro'):
        if not self.is_user_authorized(user, access):
            raise exceptions.PermissionDenied('access denied for user %s' % user.name)

    def __unicode__(self):
        return u'Repo: %s/%s' % (self.holder.name, self.name)

class RepoAlias(models.Model):
    repo = models.ForeignKey(Repo)
    name = models.CharField(max_length=50, unique=True)
    
    class Meta:
        verbose_name = "repository alias"
        verbose_name_plural = "repository aliases"

class PrivilegeOwner(models.Model):
    ro_repos = models.ManyToManyField(Repo, related_name='ro_privileged', blank=True)
    rw_repos = models.ManyToManyField(Repo, related_name='rw_privileged', blank=True)
    rwplus_repos = models.ManyToManyField(Repo, related_name='rwplus_privileged', blank=True)

    @classmethod
    def get_by_name(cls, name):
        if name.startswith('@'):
            name = name[1:]
            try:
                return Group.get_by_name(name)
            except Group.DoesNotExist:
                raise PrivilegeOwner.DoesNotExist('Group named %s does not exist.' % name)
        else:
            try:
                return User.objects.filter(name=name).get()
            except User.DoesNotExist:
                raise PrivilegeOwner.DoesNotExist('User named %s does not exist.' % name)

    @classmethod
    def get_privileged(cls, repo, field):
        return chain(*[ type.objects.filter(**{field: repo}) for type in [User, Group] ] )

    class Meta:
        verbose_name = "privilige owner"
        verbose_name_plural = "privilege owners"

class User(PrivilegeOwner, RepoHolder, DjangoUser):
    def get_ident_name(self):
        return self.name

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

class Group(PrivilegeOwner):
    name = models.CharField(max_length=50)
    members = models.ManyToManyField(User, related_name='git_groups', blank=True)
    organization = models.ForeignKey('Organization', blank=True, null=True)

    def get_ident_name(self):
        if self.organization:
            return '@' + self.organization.name + '/' + self.name
        else:
            return '@' + self.name

    @classmethod
    def get_by_name(cls, name):
        if '/' in name:
            org_name, name = name.split('/', 1)
            org = Organization.objects.filter(name=org_name).get()
        else:
            org = None
        return Group.objects.filter(organization=org, name=name).get()

    def __unicode__(self):
        return u'Group: %s' % self.get_ident_name()[1:]

class Organization(RepoHolder):
    owners = models.ManyToManyField(User, related_name='organizations')

    def check_if_owner(self, user):
        try:
            self.owners.get(id=user.id)
        except User.DoesNotExist:
            raise exceptions.PermissionDenied

class SSHKey(models.Model):
    owner = models.ForeignKey(User, blank=True, null=True)
    target = models.ForeignKey(Repo, blank=True, null=True)
    data = models.TextField()
    name = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = "SSH key"
        verbose_name_plural = "SSH keys"
    
    def __unicode__(self):
        return u'SSHKey %s, owner: %s' % (self.name, self.owner)

admin.site.register(Repo)
admin.site.register(RepoAlias)
admin.site.register(User)
admin.site.register(PrivilegeOwner)
admin.site.register(SSHKey)
admin.site.register(Organization)
admin.site.register(Group)