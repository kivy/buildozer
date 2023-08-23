'''
Buildozer remote
================

.. warning::

    This is an experimental tool and not widely used. It might not fit for you.

Pack and send the source code to a remote SSH server, bundle buildozer with it,
and start the build on the remote.
You need paramiko to make it work.
'''

__all__ = ["BuildozerRemote"]

from configparser import ConfigParser
from os import makedirs, walk, getcwd
from os.path import join, expanduser, realpath, exists, splitext
import socket
from select import select
import sys
from sys import stdout, stdin, exit
try:
    import termios
    has_termios = True
except ImportError:
    has_termios = False

try:
    import paramiko
except ImportError:
    print('Paramiko missing: pip install paramiko')

from buildozer import Buildozer, __version__
from buildozer.exceptions import BuildozerCommandException, BuildozerException
from buildozer.logger import Logger


class BuildozerRemote(Buildozer):
    def run_command(self, args):
        profile = None

        while args:
            if not args[0].startswith('-'):
                break
            arg = args.pop(0)

            if arg in ('-v', '--verbose'):
                self.logger.log_level = 2

            elif arg in ('-p', '--profile'):
                profile = args.pop(0)

            elif arg in ('-h', '--help'):
                self.usage()
                exit(0)

            elif arg == '--version':
                print('Buildozer (remote) {0}'.format(__version__))
                exit(0)

        self.config.apply_profile(profile)

        if len(args) < 2:
            self.usage()
            return

        remote_name = args[0]
        remote_section = 'remote:{}'.format(remote_name)
        if not self.config.has_section(remote_section):
            self.logger.error('Unknown remote "{}", must be configured first.'.format(
                remote_name))
            return

        self.remote_host = remote_host = self.config.get(
                remote_section, 'host', '')
        self.remote_port = self.config.get(
                remote_section, 'port', '22')
        self.remote_user = remote_user = self.config.get(
                remote_section, 'user', '')
        self.remote_build_dir = remote_build_dir = self.config.get(
                remote_section, 'build_directory', '')
        self.remote_identity = self.config.get(
                remote_section, 'identity', '')
        if not remote_host:
            self.logger.error('Missing "host = " for {}'.format(remote_section))
            return
        if not remote_user:
            self.logger.error('Missing "user = " for {}'.format(remote_section))
            return
        if not remote_build_dir:
            self.logger.error('Missing "build_directory = " for {}'.format(remote_section))
            return

        # fake the target
        self.targetname = 'remote'
        self.check_build_layout()

        # prepare our source code
        self.logger.info('Prepare source code to sync')
        self._copy_application_sources()
        self._ssh_connect()
        try:
            self._ensure_buildozer()
            self._sync_application_sources()
            self._do_remote_commands(args[1:])
            self._ssh_sync(getcwd(), mode='get')
        finally:
            self._ssh_close()

    def _ssh_connect(self):
        self.logger.info('Connecting to {}'.format(self.remote_host))
        self._ssh_client = client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()
        kwargs = {}
        if self.remote_identity:
            kwargs['key_filename'] = expanduser(self.remote_identity)
        client.connect(self.remote_host, username=self.remote_user,
                port=int(self.remote_port), **kwargs)
        self._sftp_client = client.open_sftp()

    def _ssh_close(self):
        self.logger.debug('Closing remote connection')
        self._sftp_client.close()
        self._ssh_client.close()

    def _ensure_buildozer(self):
        s = self._sftp_client
        root_dir = s.normalize('.')
        self.remote_build_dir = join(root_dir, self.remote_build_dir,
                self.package_full_name)
        self.logger.debug('Remote build directory: {}'.format(self.remote_build_dir))
        self._ssh_mkdir(self.remote_build_dir)
        self._ssh_sync(__path__[0])  # noqa: F821 undefined name

    def _sync_application_sources(self):
        self.logger.info('Synchronize application sources')
        self._ssh_sync(self.app_dir)

        # create custom buildozer.spec
        self.logger.info('Create custom buildozer.spec')
        config = ConfigParser()
        config.read('buildozer.spec')
        config.set('app', 'source.dir', 'app')

        fn = join(self.remote_build_dir, 'buildozer.spec')
        fd = self._sftp_client.open(fn, 'wb')
        config.write(fd)
        fd.close()

    def _do_remote_commands(self, args):
        self.logger.info('Execute remote buildozer')
        cmd = (
            'source ~/.profile;'
            'cd {0};'
            'env PYTHONPATH={0}:$PYTHONPATH '
            'python -c "import buildozer, sys;'
            'buildozer.Buildozer().run_command(sys.argv[1:])" {1} {2} 2>&1').format(
            self.remote_build_dir,
            '--verbose' if self.logger.log_level == 2 else '',
            ' '.join(args),
        )
        self._ssh_command(cmd)

    def _ssh_mkdir(self, *args):
        directory = join(*args)
        self.logger.debug('Create remote directory {}'.format(directory))
        try:
            self._sftp_client.mkdir(directory)
        except IOError:
            # already created?
            try:
                self._sftp_client.stat(directory)
            except IOError:
                self.logger.error('Unable to create remote directory {}'.format(directory))
                raise

    def _ssh_sync(self, directory, mode='put'):
        self.logger.debug('Syncing {} directory'.format(directory))
        directory = realpath(expanduser(directory))
        base_strip = directory.rfind('/')
        if mode == 'get':
            local_dir = join(directory, 'bin')
            remote_dir = join(self.remote_build_dir, 'bin')
            if not exists(local_dir):
                makedirs(local_dir)
            for _file in self._sftp_client.listdir(path=remote_dir):
                self._sftp_client.get(join(remote_dir, _file),
                                      join(local_dir, _file))
            return
        for root, dirs, files in walk(directory):
            self._ssh_mkdir(self.remote_build_dir, root[base_strip + 1:])
            for fn in files:
                if splitext(fn)[1] in ('.pyo', '.pyc', '.swp'):
                    continue
                local_file = join(root, fn)
                remote_file = join(self.remote_build_dir, root[base_strip + 1:], fn)
                self.logger.debug('Sync {} -> {}'.format(local_file, remote_file))
                self._sftp_client.put(local_file, remote_file)

    def _ssh_command(self, command):
        self.logger.debug('Execute remote command {}'.format(command))
        transport = self._ssh_client.get_transport()
        channel = transport.open_session()
        try:
            channel.exec_command(command)
            self._interactive_shell(channel)
        finally:
            channel.close()

    def _interactive_shell(self, chan):
        if has_termios:
            self._posix_shell(chan)
        else:
            self._windows_shell(chan)

    def _posix_shell(self, chan):
        oldtty = termios.tcgetattr(stdin)
        try:
            chan.settimeout(0.0)

            while True:
                r, w, e = select([chan, stdin], [], [])
                if chan in r:
                    try:
                        x = chan.recv(128)
                        if len(x) == 0:
                            print('\r\n*** EOF\r\n',)
                            break
                        stdout.write(x)
                        stdout.flush()
                    except socket.timeout:
                        pass
                if stdin in r:
                    x = stdin.read(1)
                    if len(x) == 0:
                        break
                    chan.sendall(x)
        finally:
            termios.tcsetattr(stdin, termios.TCSADRAIN, oldtty)

    # thanks to Mike Looijmans for this code
    def _windows_shell(self, chan):
        import threading

        stdout.write("Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n")

        def writeall(sock):
            while True:
                data = sock.recv(256)
                if not data:
                    stdout.write('\r\n*** EOF ***\r\n\r\n')
                    stdout.flush()
                    break
                stdout.write(data)
                stdout.flush()

        writer = threading.Thread(target=writeall, args=(chan,))
        writer.start()

        try:
            while True:
                d = stdin.read(1)
                if not d:
                    break
                chan.send(d)
        except EOFError:
            # user hit ^Z or F6
            pass


def main():
    try:
        BuildozerRemote().run_command(sys.argv[1:])
    except BuildozerCommandException:
        pass
    except BuildozerException as error:
        Logger().error('%s' % error)


if __name__ == '__main__':
    main()
