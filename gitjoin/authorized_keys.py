# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import tools
import os
import StringIO

from gitjoin import models

def create():
    out = StringIO.StringIO()

    custom = open(os.path.expanduser('~/authorized_keys.custom')).read()
    out.write('# ~/authorized_keys.custom\n')
    out.write(custom)
    out.write('\n# autogenerated\n')

    auth_cmd = 'python -m gitjoin.git_auth'

    for key in models.SSHKey.objects.all():
        keydata = tools.reformat_ssh_key(key.data)
        fingerprint = key.fingerprint

        if not fingerprint:
            # fill in missing data
            fingerprint = key.fingerprint = tools.get_ssh_key_fingerprint(key.data)
            key.save()

        out.write('command="%s %s",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty %s\n' % (auth_cmd, fingerprint, keydata))

    tools.overwrite_file(os.path.expanduser('~/.ssh/authorized_keys'), out.getvalue())

if __name__ == '__main__':
    create()
