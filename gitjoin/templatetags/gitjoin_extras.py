# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from collections import namedtuple
from django import template
from django.utils import safestring
from django.utils.html import conditional_escape

from gitjoin import models

import pretty

register = template.Library()

PathFragment = namedtuple('PathFragment', 'name path')

@register.filter
def split(str, splitter):
    return str.split(splitter)

@register.filter
def splitpath(path):
    fragments = [ name for name in (path or '').split('/') if name ]
    return [ PathFragment(fragments[i], '/'.join(fragments[:i+1])) for i in xrange(len(fragments)) ]

@register.filter
def prettygitident(ident):
    if len(ident) == 40:
        return 'commit %s..%s' % (ident[:5], ident[-5:])
    else:
        return 'branch %s' % ident

@register.filter
def ormaster(ident):
    return ident or 'master'

@register.filter
def usernames(repo, field=None):
    objects = models.PrivilegeOwner.get_privileged(repo, field) if field else repo
    return ' '.join([ obj.get_ident_name() for obj in objects ])

@register.filter
def prettydate(time):
    return pretty.date(time)

@register.filter
def shortcommitmsg(message):
    message = message.split('\n')[0]
    if len(message) > 120:
        message = message[:120]
        message += '...'
    return message

@register.filter
def gitdiff(data):
    return safestring.mark_safe('\n'.join(_gitdiff(data.splitlines())))

#gitdiff.is_safe = True

def _gitdiff(lines):
    for line in lines:
        colors = {'-': 'red', '+' : 'green', '@': 'blue'}
        if line and line[0] in colors:
            color = colors[line[0]]
            yield '<span style="color: %s">%s</span>' % (color, conditional_escape(line))
        else:
            yield conditional_escape(line)
