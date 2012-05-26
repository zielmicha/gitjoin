# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import tempfile

def get_cmd(cmd, cwd=None, env={}):
    # workaround for http://bugs.python.org/issue13156, can't use subprocess
    # http://stackoverflow.com/questions/967443/python-module-to-shellquote-unshellquote
    import re
    _quote_pos = re.compile('(?=[^-0-9a-zA-Z_./\n])')

    def quote(arg):
        r"""
        >>> quote('\t')
        '\\\t'
        >>> quote('foo bar')
        'foo\\ bar'
        """
        # This is the logic emacs uses
        if arg:
            return _quote_pos.sub('\\\\', arg).replace('\n',"'\n'")
        else:
            return "''"

    assert isinstance(cmd, list)
    command = ' '.join(quote(arg) for arg in cmd)

    for k, v in env.items():
        command = '%s=%s %s' % (quote(k), quote(v), command)

    if cwd:
        command = 'cd %s && %s' % (quote(cwd), command)

    return command

def _popen(cmd, mode):
    #print 'popen', cmd
    return os.popen(cmd, mode)

class CalledProcessError(Exception):
    def __init__(self, message, output=None):
        Exception.__init__(self, message)
        self.output = output

def check_output(cmd, cwd=None, env={}, stdin=None):
    command = get_cmd(cmd, cwd=cwd, env=env)
    if stdin:
        temp = tempfile.NamedTemporaryFile()
        temp.write(stdin)
        temp.flush()
        command = '%s < %s' % (command, quote(temp.name))
    data = _popen(command + '; printf "\\n%s" $?', 'r').read()
    if stdin:
        temp.close()
    result, status = data.rsplit('\n', 1)
    if int(status) != 0:
        raise CalledProcessError('Command exited with non-zero exit status %s' % status, result)
    else:
        return result
