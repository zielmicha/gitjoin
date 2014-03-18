# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import tools
import os
import StringIO
import pipes

from gitjoin import models
from webapp import settings

def create():
    out = StringIO.StringIO()
    write_file = True

    try:
        custom = open(os.path.expanduser('~/authorized_keys.custom')).read()
    except IOError:
        print '~/authorized_keys.custom not found - not updating SSH keys'
        write_file = False
        custom = ''

    out.write('# ~/authorized_keys.custom\n')
    out.write(custom)
    out.write('\n# autogenerated\n')

    auth_cmd = 'python -m gitjoin.git_auth'

    for key in models.SSHKey.objects.all():
        keydata = tools.reformat_ssh_key(key.data)
        fingerprint = key.fingerprint
        correct_fingerprint = tools.get_ssh_key_fingerprint(key.data)

        if fingerprint != correct_fingerprint:
            # fill in missing/incorrect data
            fingerprint = key.fingerprint = correct_fingerprint
            key.save()

        out.write(('command="cd %s && source activate_base.inc && %s %s",'
                   'no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty %s\n')
                  % (pipes.quote(settings.APP_ROOT), auth_cmd, fingerprint, keydata))

    if write_file:
        tools.overwrite_file(os.path.expanduser('~/.ssh/authorized_keys'), out.getvalue())

if __name__ == '__main__':
    create()
