from collections import namedtuple
from django import template

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