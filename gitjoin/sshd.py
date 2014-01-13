'''
Optional SSH server based on Twisted Conch if you don't want to use OpenSSH.
'''
from twisted.cred.portal import Portal
from twisted.cred.checkers import FilePasswordDB
from twisted.conch.checkers import SSHPublicKeyDatabase
from twisted.conch.ssh.factory import SSHFactory
from twisted.internet import reactor
from twisted.conch.ssh.keys import Key
from twisted.conch.interfaces import IConchUser
from twisted.conch.avatar import ConchUser
from twisted.conch.ssh.channel import SSHChannel
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.credentials import IUsernamePassword, ISSHPrivateKey
from twisted.cred.error import UnauthorizedLogin, UnhandledCredentials
from twisted.python import components
from twisted.conch.ssh import session
from twisted.cred import portal
from twisted.internet import reactor
from twisted.internet.error import ProcessExitedAlready
from zope.interface import implements, providedBy

import os
import pwd
import sys
import subprocess

from . import tools

class settings: pass
settings = settings()

def nothing():
    pass

class KeyConchUser(ConchUser):
    def __init__(self, avatarId):
        ConchUser.__init__(self)
        self.avatarId = avatarId
        self.channelLookup['session'] = session.SSHSession

class KeySession:
    implements(session.ISession)

    def __init__(self, avatar):
        self.avatar = avatar
        self.proc = None

    def execCommand(self, proto, cmd):
        username, key_id = self.avatar.avatarId
        environ = {}

        # Are we supposed to setuid?
        if settings.username_get:
            uid = settings.username_get(username)

            home = pwd.getpwuid(uid).pw_dir
            environ['PYTHONPATH'] = os.environ['PYTHONPATH']
            environ['HOME'] = home
            environ['PATH'] = os.environ['PATH']

            setuid_args = [uid, settings.gid]
        else:
            environ.update(os.environ)
            home = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')

            setuid_args = []

        environ['SSH_ORIGINAL_COMMAND'] = cmd
        environ['CALLED_WITH_CUSTOM_SSHD'] = '1'

        assert "'" not in key_id # generate by get_ssh_key_fingerprint, so it's safe
        self.proc = reactor.spawnProcess(ProcessExitWorkaroundWrapper(proto),
                                        '/bin/sh', ['sh', '-c', "python -m gitjoin.git_auth '%s'" % key_id], environ, home,
                                        *setuid_args)
        self.avatar.conn.transport.transport.setTcpNoDelay(1)

    def eofReceived(self):
        if self.proc:
            self.proc.closeStdin()

    def closed(self):
        try:
            self.proc.signalProcess('HUP')
        except (OSError, ProcessExitedAlready):
            pass
        self.proc.loseConnection()

class ProcessExitWorkaroundWrapper(object):
    '''
    Process seems to call processExited long before processEnded.
    However SSHSessionProcessProtocol closes channel on processEnded.
    '''
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        return getattr(self._obj, name)

    def processExited(self, reason=None):
        return self.processEnded(reason)

    def childDataReceived(self, a, data):
        return self._obj.childDataReceived(a, data)

components.registerAdapter(KeySession, KeyConchUser, session.ISession)

class KeyRealm(object):
    implements(portal.IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        r = interfaces[0], KeyConchUser(avatarId), nothing
        return r

class KeyChecker(object):
    implements(ICredentialsChecker)

    credentialInterfaces = (ISSHPrivateKey,)

    def requestAvatarId(self, credentials):
        pubkey = tools.reformat_ssh_key('ssh-rsa ' + credentials.blob.encode('base64'))
        id = tools.get_ssh_key_fingerprint(pubkey)
        return (credentials.username, id)

def main(keys_path, username_get=None, gid=None, port=2022):
    settings.username_get = username_get
    settings.gid = gid
    key_path = keys_path + '/id_rsa'

    if not os.path.exists(key_path):
        subprocess.check_call(['ssh-keygen', '-f', key_path,
                               '-t', 'rsa', '-N', ''])

    with open(key_path) as privateBlobFile:
        privateBlob = privateBlobFile.read()
        privateKey = Key.fromString(data=privateBlob)

    with open(key_path + '.pub') as publicBlobFile:
        publicBlob = publicBlobFile.read()
        publicKey = Key.fromString(data=publicBlob)

    factory = SSHFactory()
    factory.privateKeys = {'ssh-rsa': privateKey}
    factory.publicKeys = {'ssh-rsa': publicKey}
    factory.portal = Portal(KeyRealm())
    factory.portal.registerChecker(KeyChecker())

    reactor.listenTCP(port, factory)
    reactor.run()

if __name__ == '__main__':
    main('.')
