# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from django import http
from django.views.generic.list_detail import object_list, object_detail
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
import django.core.exceptions
import webapp.settings
from webapp import settings
from gitjoin import models
from gitjoin import controller
from gitjoin import git
from gitjoin import tools
from gitjoin import live
from gitjoin import hooks
from gitjoin.mysubprocess import check_output
import os

from django.contrib.auth.decorators import login_required as default_login_required
login_required = default_login_required(login_url='/global/accounts/login/')

def home(request):
    return to_template(request, 'home.html', dict(
        users=models.User.objects.all(),
        orgs=models.Organization.objects.all(),
    ))

def user(request, name):
    try:
        holder = models.RepoHolder.get_by_name(name)
    except django.core.exceptions.ObjectDoesNotExist:
        raise http.Http404
    repos = holder.repos.all()
    owners = holder.owners.all() if isinstance(holder, models.Organization) else None
    is_owner = (request.user in owners) if owners else holder == request.user
    groups = holder.group_set.all() if isinstance(holder, models.Organization) else None
    accessible_repos = None if isinstance(holder, models.Organization) else holder.get_accessible_repos()

    return to_template(request, 'user.html', dict(
        repos=repos,
        object=holder,
        owners=owners,
        is_owner=is_owner,
        groups=groups,
        accessible_repos=accessible_repos))

def repo(request, username, name):
    repo = get_repo(request.user, username + '/' + name)
    grepo = git.Repo.from_model(repo)
    return to_template(request, 'repo.html', dict(
            repo=repo,
            branch='master', #repo.default_branch,
            git_list=tools.none_on_error(lambda: grepo.list(include_commit_info=True), errors=[KeyError]),
            path='/',
            readme=grepo.get_readme()))

def repo_tree(request, username, repo_name, branch, path):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    try:
        object = grepo.get_branch(branch).get_tree(path)
    except KeyError:
        raise http.Http404

    if object.is_directory():
        return to_template(request, 'repo_tree.html', dict(
            branch=branch,
            repo=repo,
            path=path,
            git_list=object.list(include_commit_info=True)))
    else:
        return to_template(request, 'repo_blob.html', dict(
            branch=branch,
            repo=repo,
            path=path,
            git_blob=object.get_data()))

@login_required
def repo_admin(request, username, repo_name):
    repo = get_repo(request.user, username + '/' + repo_name)
    error = None

    if request.POST:
        name = request.POST.get('name')
        ro = request.POST.get('ro').split()
        rw = request.POST.get('rw').split()
        rwplus = request.POST.get('rwplus').split()
        public = bool(request.POST.get('public'))
        description = request.POST.get('description')
        try:
            controller.edit_repo(request.user, repo, name,
                                 description=description,
                                 public=public, ro=ro, rw=rw, rwplus=rwplus)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('repo_admin', args=[username, repo.name]))

    return to_template(request, 'repo_admin.html', dict(
        error=error,
        repo=repo,
        has_access=repo.is_user_authorized(request.user, 'rwplus')))

@login_required
def repo_admin_keys(request, username, repo_name):
    repo = get_repo(request.user, username + '/' + repo_name)
    error = None

    return to_template(request, 'repo_admin_keys.html', dict(
        error=error,
        repo=repo,
        ssh_target=username + '/' + repo_name,
        keys=models.SSHKey.objects.filter(target=repo),
        has_access=repo.is_user_authorized(request.user, 'rwplus')))

@login_required
def repo_admin_hooks(request, username, repo_name):
    repo = get_repo(request.user, username + '/' + repo_name)
    error = None

    hook_id = request.GET.get('id')
    hook = None
    if hook_id:
        hook = models.Hook.objects.get(id=int(request.GET.get('id')))
        if hook.repo != repo:
            raise PermissionDenied
        hook_type = hooks.UserHook.get(hook.type_name)

    return to_template(request, 'repo_admin_hooks.html', dict(
        error=error,
        repo=repo,
        hooks=repo.hooks.all(),
        parameters=hook_type.get_parameters(hook) if hook else None,
        hook_type=hook_type if hook else None,
        hook=hook,
        hook_types=hooks.UserHook.get_types(),
        has_access=repo.is_user_authorized(request.user, 'rwplus')))

@login_required
def repo_admin_hooks_new(request, username, repo_name):
    name = request.POST.get('name')
    type = request.POST.get('type')
    repo = get_repo(request.user, username + '/' + repo_name)
    id = controller.add_hook(request.user, repo, name, type)
    return http.HttpResponseRedirect(reverse('repo_admin_hooks', args=[username, repo_name]) + '?id=' + str(id))

@login_required
def repo_admin_hooks_edit(request, username, repo_name):
    name = request.POST.get('name')
    id = int(request.POST.get('id'))
    repo = get_repo(request.user, username + '/' + repo_name)

    if request.POST.get('action') == 'delete':
        controller.delete_hook(request.user, repo, id=id)
        return http.HttpResponseRedirect(reverse('repo_admin_hooks', args=[username, repo_name]))
    else:
        enabled = bool(request.POST.get('enabled'))
        parameters = dict( (k[2:], v) for k, v in request.POST.items() if k.startswith('p_') )

        controller.edit_hook(request.user, repo, name=name, id=id, enabled=enabled, parameters=parameters)
        return http.HttpResponseRedirect(reverse('repo_admin_hooks', args=[username, repo_name]) + '?id=' + str(id))

def repo_commits(request, username, repo_name, branch):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    try:
        object = grepo.get_branch(branch)
    except KeyError:
        raise http.Http404
    return to_template(request, 'repo_commits.html', dict(
        branch=branch,
        repo=repo,
        git_commits=object.list_commits()))

def repo_commit(request, username, repo_name, commit):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    try:
        object = grepo.get_branch(commit)
    except KeyError:
        raise http.Http404
    return to_template(request, 'commit.html', dict(
        commit=object,
        branch=commit,
        diff=object.diff_with_prev(raw=True),
        repo=repo))

def repo_commit_diff(request, username, repo_name, commit, path=None):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    try:
        object = grepo.get_branch(commit)
    except KeyError:
        raise http.Http404
    return to_template(request, 'commit_diff.html', dict(
        commit=object,
        branch=commit,
        diff=object.diff_with_prev(file=path),
        repo=repo))

def repo_branches(request, username, repo_name):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    return to_template(request, 'repo_branches.html', dict(
        repo=repo,
        git_branches=grepo.list_branches()))

def live_main(request, username, repo_name, live_user):
    repo = get_repo(request.user, username + '/' + repo_name)
    l = get_live(repo, live_user)
    return to_template(request, 'live_main.html', dict(
        repo=repo,
        username=live_user,
        files=l.get_files()))

def get_live(repo, username):
    user = models.User.objects.get(name=username)
    return live.LiveServer(repo.id, settings.REPOS_PATH + ('/%d' % repo.id), user)

@csrf_exempt
def repo_git_http(request, username, repo_name, path):
    repo = get_repo(request.user, username + '/' + repo_name)
    grepo = git.Repo.from_model(repo)
    # PATH_INFO=/ GIT_PROJECT_ROOT=~/lemur/ REQUEST_METHOD=GET
    env = {'PATH_INFO': path,
           'GIT_PROJECT_ROOT': grepo.path,
           'REQUEST_METHOD': request.method,
           'GIT_HTTP_EXPORT_ALL': '1'}
    # TODO: QUERY_STRING, REMOTE_USER
    data = check_output([webapp.settings.GIT_CORE_PATH + '/git-http-backend'], env=env)
    header_data, response_data = data.split('\r\n\r\n', 1)
    headers = dict( line.strip().split(':', 1) for line in header_data.splitlines() )
    response = http.HttpResponse(response_data)

    if headers.get('Status'):
        response.status_code = int(headers['Status'].split()[0])
    return response

@login_required
def new_repo(request):
    error = None
    if request.POST:
        name = request.POST.get('name')
        holder = request.POST.get('holder')
        try:
            controller.create_repo(request.user, holder, name)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('repo', args=[holder, name]))
    return to_template(request, 'new_repo.html', dict(
        error=error,
        req_holder=request.GET.get('holder'),
        holders=[ request.user.name ] + [ org.name for org in request.user.organizations.all() ]
    ))

@login_required
def ssh_keys(request):
    return to_template(request, 'ssh_keys.html', dict(
        keys=models.SSHKey.objects.filter(owner=request.user),
        ssh_target='user',
    ))

@login_required
def ssh_keys_new(request, target):
    name = request.POST.get('name')
    data = request.POST.get('data')
    controller.add_ssh_key(request.user, target, name, data)
    if target == 'user':
        return http.HttpResponseRedirect(reverse('ssh_keys'))
    else:
        return http.HttpResponseRedirect(reverse('repo_admin_keys', args=target.split('/', 1)))

@login_required
def ssh_keys_delete(request):
    id = request.POST.get('id')
    controller.delete_ssh_key(request.user, id)
    return http.HttpResponseRedirect(reverse('ssh_keys'))

def ssh_keys_new_script(request, ssh_target):
    data = open(webapp.settings.APP_ROOT + '/gitjoin/add.sh').read()
    data = data.replace('__URL__', webapp.settings.URL + reverse('ssh_keys_new_script_continue', args=[ssh_target]))
    return http.HttpResponse(data, content_type='text/plain')

@login_required
def ssh_keys_new_script_continue(request, ssh_target):
    return to_template(request, 'ssh_keys_new_script_continue.html', dict(
            ssh_target=ssh_target,
            data=request.GET['key']))

@login_required
def org_new(request):
    error = None
    if request.POST:
        name = request.POST.get('name')
        try:
            controller.new_org(request.user, name)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('user', args=[name]))

    return to_template(request, 'org_new.html', dict(error=error))

@login_required
def org_admin(request, name):
    holder = models.RepoHolder.get_by_name(name)
    owners = holder.owners.all() if isinstance(holder, models.Organization) else None
    error = None

    if request.POST:
        new_owners = request.POST.get('owners').split()
        try:
            controller.edit_org(request.user, holder, new_owners)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('org_admin', args=[name]))

    return to_template(request, 'org_admin.html', dict(
        object=holder,
        owners=owners,
        error=error,
    ))

@login_required
def org_admin_group(request, name, group_name):
    if group_name == 'owners':
        return http.HttpResponseRedirect(reverse('org_admin', args=[name]))

    holder = models.RepoHolder.get_by_name(name)
    group = holder.group_set.get(name=group_name)
    error = None

    if request.POST:
        new_members = request.POST.get('members').split()
        new_name = request.POST.get('name')
        try:
            if request.POST.get('delete'):
                controller.delete_group(request.user, group)
            else:
                controller.edit_group(request.user, group, new_name, new_members)
        except controller.Error as err:
            error = err.message
        else:
            if request.POST.get('delete'):
                return http.HttpResponseRedirect(reverse('user', args=[name]))
            else:
                return http.HttpResponseRedirect(reverse('org_admin_group', args=[name, new_name]))

    return to_template(request, 'org_admin_group.html', dict(
        object=holder,
        group=group,
        error=error,
    ))

@login_required
def org_admin_group_new(request, name):
    holder = models.RepoHolder.get_by_name(name)
    error = None

    if request.POST:
        name = request.POST.get('name')
        try:
            controller.new_group(request.user, holder, name)
        except controller.Error as err:
            error = err.message
        else:
            return http.HttpResponseRedirect(reverse('user', args=[holder.name]))

    return to_template(request, 'org_admin_group_new.html', dict(
        object=holder,
        error=error,
    ))

def get_repo(user, full_name):
    try:
        repo = models.Repo.get_by_name(full_name)
    except models.Repo.DoesNotExist:
        raise http.Http404
    repo.check_user_authorized(user)
    return repo

def to_template(request, name, args={}):
    args = args.copy()
    args['settings'] = webapp.settings.__dict__
    return direct_to_template(request, name, args)
