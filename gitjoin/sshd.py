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
from zope.interface import implements, providedBy

import os
import pwd

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

    def execCommand(self, proto, cmd):
        username, key_id = self.avatar.avatarId
        uid = settings.username_get(username)
        environ = {}
        home = pwd.getpwuid(uid).pw_dir
        environ['SSH_ORIGINAL_COMMAND'] = cmd
        environ['PYTHONPATH'] = os.environ['PYTHONPATH']
        environ['HOME'] = home
        environ['PATH'] = os.environ['PATH']
        assert "'" not in key_id # generate by get_ssh_key_fingerprint, so it's safe
        self.pty = reactor.spawnProcess(proto,
                                        '/bin/sh', ['sh', '-c', "python -m gitjoin.git_auth '%s'" % key_id], environ, home,
                                        uid, settings.gid)
        self.avatar.conn.transport.transport.setTcpNoDelay(1)

    def closed(self):
        pass

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

def main(keys_path, username_get, gid, port=2022):
    settings.username_get = username_get
    settings.gid = gid

    with open(keys_path + '/id_rsa') as privateBlobFile:
        privateBlob = privateBlobFile.read()
        privateKey = Key.fromString(data=privateBlob)

    with open(keys_path + '/id_rsa.pub') as publicBlobFile:
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
    main('.', lambda name: 1002, 100)
