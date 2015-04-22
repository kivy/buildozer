'''
iOS target, based on kivy-ios project. (not working yet.)
'''

import sys
if sys.platform != 'darwin':
    raise NotImplementedError('Windows platform not yet working for Android')

import plistlib
from buildozer import BuildozerCommandException
from buildozer.target import Target, no_config
from os.path import join, basename, expanduser, realpath
from getpass import getpass

PHP_TEMPLATE = '''
<?php
// credits goes to http://jeffreysambells.com/2010/06/22/ios-wireless-app-distribution

$ipas = glob('*.ipa');
$provisioningProfiles = glob('*.mobileprovision');
$plists = glob('*.plist');

$sr = stristr( $_SERVER['SCRIPT_URI'], '.php' ) === false ? 
    $_SERVER['SCRIPT_URI'] : dirname($_SERVER['SCRIPT_URI']) . '/';
$provisioningProfile = $sr . $provisioningProfiles[0];
$ipa = $sr . $ipas[0];
$itmsUrl = urlencode( $sr . 'index.php?plist=' . str_replace( '.plist', '', $plists[0] ) );


if ($_GET['plist']) {
    $plist = file_get_contents( dirname(__FILE__) 
        . DIRECTORY_SEPARATOR 
        . preg_replace( '/![A-Za-z0-9-_]/i', '', $_GET['plist']) . '.plist' );
    $plist = str_replace('_URL_', $ipa, $plist);
    header('content-type: application/xml');
    echo $plist;
    die();
}


?><!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
        "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<title>Install {appname}</title>
<style type="text/css">
li { padding: 1em; }
</style>

</head>
<body>
<ul>
    <li><a href="<? echo $provisioningProfile; ?>">Install Team Provisioning File</a></li>
    <li><a href="itms-services://?action=download-manifest&url=<? echo $itmsUrl; ?>">
         Install Application</a></li>
</ul>
</body>
</html>
'''

class TargetIos(Target):

    def check_requirements(self):
        checkbin = self.buildozer.checkbin
        cmd = self.buildozer.cmd

        checkbin('Xcode xcodebuild', 'xcodebuild')
        checkbin('Xcode xcode-select', 'xcode-select')
        checkbin('Git git', 'git')
        checkbin('Cython cython', 'cython')
        checkbin('pkg-config', 'pkg-config')
        checkbin('autoconf', 'autoconf')
        checkbin('automake', 'automake')
        checkbin('libtool', 'libtool')

        self.buildozer.debug('Check availability of a iPhone SDK')
        sdk = cmd('xcodebuild -showsdks | fgrep "iphoneos" |'
                'tail -n 1 | awk \'{print $2}\'',
                get_stdout=True)[0]
        if not sdk:
            raise Exception(
                'No iPhone SDK found. Please install at least one iOS SDK.')
        else:
            self.buildozer.debug(' -> found %r' % sdk)

        self.buildozer.debug('Check Xcode path')
        xcode = cmd('xcode-select -print-path', get_stdout=True)[0]
        if not xcode:
            raise Exception('Unable to get xcode path')
        self.buildozer.debug(' -> found {0}'.format(xcode))

    def install_platform(self):
        cmd = self.buildozer.cmd
        self.ios_dir = ios_dir = join(self.buildozer.platform_dir, 'kivy-ios')
        if not self.buildozer.file_exists(ios_dir):
            cmd('git clone https://github.com/kivy/kivy-ios',
                    cwd=self.buildozer.platform_dir)
        elif self.platform_update:
            cmd('git clean -dxf', cwd=ios_dir)
            cmd('git pull origin master', cwd=ios_dir)

        self.ios_deploy_dir = ios_deploy_dir = join(self.buildozer.platform_dir,
                'ios-deploy')
        if not self.buildozer.file_exists(ios_deploy_dir):
            cmd('git clone https://github.com/phonegap/ios-deploy',
                    cwd=self.buildozer.platform_dir)

    def get_available_packages(self):
        available_modules = self.buildozer.cmd(
                './toolchain.py recipes --compact',
                cwd=self.ios_dir, get_stdout=True)[0]
        return available_modules.splitlines()[0].split()

    def compile_platform(self):
        # for ios, the compilation depends really on the app requirements.
        # compile the distribution only if the requirements changed.
        last_requirements = self.buildozer.state.get('ios.requirements', '')
        app_requirements = self.buildozer.config.getlist('app', 'requirements',
                '')

        # we need to extract the requirements that kivy-ios knows about
        available_modules = self.get_available_packages()
        onlyname = lambda x: x.split('==')[0]
        ios_requirements = [x for x in app_requirements if onlyname(x) in
                            available_modules]

        need_compile = 0
        if last_requirements != ios_requirements:
            need_compile = 1

        # len('requirements.source.') == 20, so use name[20:]
        source_dirs = {'{}_DIR'.format(name[20:].upper()):
                            realpath(expanduser(value))
                       for name, value in self.buildozer.config.items('app')
                       if name.startswith('requirements.source.')}
        if source_dirs:
            need_compile = 1
            self.buildozer.environ.update(source_dirs)
            self.buildozer.info('Using custom source dirs:\n    {}'.format(
                '\n    '.join(['{} = {}'.format(k, v)
                               for k, v in source_dirs.items()])))

        if not need_compile:
            self.buildozer.info('Distribution already compiled, pass.')
            return

        modules_str = ' '.join(ios_requirements)
        self.buildozer.cmd('./toolchain.py build {}'.format(modules_str),
                           cwd=self.ios_dir)

        if not self.buildozer.file_exists(self.ios_deploy_dir, 'ios-deploy'):
            self.buildozer.cmd('make ios-deploy', cwd=self.ios_deploy_dir)

        self.buildozer.state['ios.requirements'] = ios_requirements
        self.buildozer.state.sync()

    def _get_package(self):
        config = self.buildozer.config
        package_domain = config.getdefault('app', 'package.domain', '')
        package = config.get('app', 'package.name')
        if package_domain:
            package = package_domain + '.' + package
        return package.lower()

    def build_package(self):
        self._unlock_keychain()

        # create the project
        app_name = self.buildozer.namify(self.buildozer.config.get('app',
            'package.name'))

        self.app_project_dir = join(self.ios_dir, '{0}-ios'.format(app_name.lower()))
        if not self.buildozer.file_exists(self.app_project_dir):
            self.buildozer.cmd('./toolchain.py create {0} {1}'.format(
                app_name, self.buildozer.app_dir),
                cwd=self.ios_dir)
        else:
            self.buildozer.cmd('./toolchain.py update {0}-ios'.format(
                app_name),
                cwd=self.ios_dir)

        # fix the plist
        plist_fn = '{}-Info.plist'.format(app_name.lower())
        plist_rfn = join(self.app_project_dir, plist_fn)
        version = self.buildozer.get_version()
        self.buildozer.info('Update Plist {}'.format(plist_fn))
        plist = plistlib.readPlist(plist_rfn)
        plist['CFBundleIdentifier'] = self._get_package()
        plist['CFBundleShortVersionString'] = version
        plist['CFBundleVersion'] = '{}.{}'.format(version,
                self.buildozer.build_id)

        # add icon
        icon = self._get_icon()
        if icon:
            plist['CFBundleIconFiles'] = [icon]
            plist['CFBundleIcons'] = {'CFBundlePrimaryIcon': {
                'UIPrerenderedIcon': False, 'CFBundleIconFiles': [icon]}}

        # ok, write the modified plist.
        plistlib.writePlist(plist, plist_rfn)

        mode = 'Debug' if self.build_mode == 'debug' else 'Release'
        self.buildozer.cmd('xcodebuild -configuration {} clean build'.format(mode),
                cwd=self.app_project_dir)
        ios_app_dir = '{app_lower}-ios/build/{mode}-iphoneos/{app_lower}.app'.format(
                app_lower=app_name.lower(), mode=mode)
        self.buildozer.state['ios:latestappdir'] = ios_app_dir

        key = 'ios.codesign.{}'.format(self.build_mode)
        ioscodesign = self.buildozer.config.getdefault('app', key, '')
        if not ioscodesign:
            self.buildozer.error('Cannot create the IPA package without'
                ' signature. You must fill the "{}" token.'.format(key))
            return
        elif ioscodesign[0] not in ('"', "'"):
            ioscodesign = '"{}"'.format(ioscodesign)

        ipa = join(self.buildozer.bin_dir, '{}-{}.ipa'.format(
            app_name, version))
        self.buildozer.cmd((
            '/usr/bin/xcrun '
            '-sdk iphoneos PackageApplication {ios_app_dir} '
            '-o {ipa} --sign {ioscodesign} --embed '
            '{ios_app_dir}/embedded.mobileprovision').format(
                ioscodesign=ioscodesign, ios_app_dir=ios_app_dir,
                mode=mode, ipa=ipa),
                cwd=self.ios_dir)

        self.buildozer.info('iOS packaging done!')
        self.buildozer.info('IPA {0} available in the bin directory'.format(
            basename(ipa)))
        self.buildozer.state['ios:latestipa'] = ipa
        self.buildozer.state['ios:latestmode'] = self.build_mode

        self._create_index()

    def cmd_deploy(self, *args):
        super(TargetIos, self).cmd_deploy(*args)
        self._run_ios_deploy(lldb=False)

    def cmd_run(self, *args):
        super(TargetIos, self).cmd_run(*args)
        self._run_ios_deploy(lldb=True)

    def cmd_xcode(self, *args):
        '''Open the xcode project.
        '''
        app_name = self.buildozer.namify(self.buildozer.config.get('app',
            'package.name'))
        app_name = app_name.lower()

        ios_dir = ios_dir = join(self.buildozer.platform_dir, 'kivy-ios')
        self.buildozer.cmd('open {}.xcodeproj'.format(
            app_name), cwd=join(ios_dir, '{}-ios'.format(app_name)))

    def _run_ios_deploy(self, lldb=False):
        state = self.buildozer.state
        if 'ios:latestappdir' not in state:
            self.buildozer.error(
                'App not built yet. Run "debug" or "release" first.')
            return
        ios_app_dir = state.get('ios:latestappdir')

        if lldb:
            debug_mode = '-d'
            self.buildozer.info('Deploy and start the application')
        else:
            debug_mode = ''
            self.buildozer.info('Deploy the application')

        self.buildozer.cmd('{iosdeploy} {debug_mode} -b {app_dir}'.format(
            iosdeploy=join(self.ios_deploy_dir, 'ios-deploy'),
            debug_mode=debug_mode, app_dir=ios_app_dir),
            cwd=self.ios_dir, show_output=True)

    def _get_icon(self):
        # check the icon size, must be 72x72 or 144x144
        icon = self.buildozer.config.getdefault('app', 'icon.filename', '')
        if not icon:
            return
        icon_fn = join(self.buildozer.app_dir, icon)
        if not self.buildozer.file_exists(icon_fn):
            self.buildozer.error('Icon {} does not exists'.format(icon_fn))
            return
        output = self.buildozer.cmd('file {}'.format(icon),
                cwd=self.buildozer.app_dir, get_stdout=True)[0]
        if not output:
            self.buildozer.error('Unable to read icon {}'.format(icon_fn))
            return
        # output is something like: 
        # "data/cancel.png: PNG image data, 50 x 50, 8-bit/color RGBA,
        # non-interlaced"
        info = output.splitlines()[0].split(',')
        fmt = info[0].split(':')[-1].strip()
        if fmt != 'PNG image data':
            self.buildozer.error('Only PNG icon are accepted, {} invalid'.format(icon_fn))
            return
        size = [int(x.strip()) for x in info[1].split('x')]
        if size != [72, 72] and size != [144, 144]:
            # icon cannot be used like that, it need a resize.
            self.buildozer.error('Invalid PNG size, must be 72x72 or 144x144. Resampling.')
            nearest_size = 144
            if size[0] < 144:
                nearest_size = 72

            icon_basename = 'icon-{}.png'.format(nearest_size)
            self.buildozer.file_copy(icon_fn, join(self.app_project_dir,
                icon_basename))
            self.buildozer.cmd('sips -z {0} {0} {1}'.format(nearest_size,
                icon_basename), cwd=self.app_project_dir)
        else:
            # icon ok, use it as it.
            icon_basename = 'icon-{}.png'.format(size[0])
            self.buildozer.file_copy(icon_fn, join(self.app_project_dir,
                icon_basename))

        icon_fn = join(self.app_project_dir, icon_basename)
        return icon_fn

    def _create_index(self):
        # TODO
        pass

    def check_configuration_tokens(self):
        errors = []
        config = self.buildozer.config
        identity_debug = config.getdefault('app', 'ios.codesign.debug', '')
        identity_release = config.getdefault('app', 'ios.codesign.release',
                identity_debug)
        available_identities = self._get_available_identities()

        if not identity_debug:
            errors.append('[app] "ios.codesign.debug" key missing, '
                    'you must give a certificate name to use.')
        elif identity_debug not in available_identities:
            errors.append('[app] identity {} not found. '
                    'Check with list_identities'.format(identity_debug))

        if not identity_release:
            errors.append('[app] "ios.codesign.release" key missing, '
                    'you must give a certificate name to use.')
        elif identity_release not in available_identities:
            errors.append('[app] identity "{}" not found. '
                    'Check with list_identities'.format(identity_release))

        super(TargetIos, self).check_configuration_tokens(errors)

    @no_config
    def cmd_list_identities(self, *args):
        '''List the available identities to use for signing.
        '''
        identities = self._get_available_identities()
        print('Available identities:')
        for x in identities:
            print('  - {}'.format(x))

    def _get_available_identities(self):
        output = self.buildozer.cmd('security find-identity -v -p codesigning',
                get_stdout=True)[0]

        lines = output.splitlines()[:-1]
        lines = [u'"{}"'.format(x.split('"')[1]) for x in lines]
        return lines

    def _unlock_keychain(self):
        password_file = join(self.buildozer.buildozer_dir, '.ioscodesign')
        password = None
        if self.buildozer.file_exists(password_file):
            with open(password_file) as fd:
                password = fd.read()

        if not password:
            # no password available, try to unlock anyway...
            error = self.buildozer.cmd('security unlock-keychain -u',
                    break_on_error=False)[2]
            if not error:
                return
        else:
            # password available, try to unlock
            error = self.buildozer.cmd('security unlock-keychain -p {}'.format(
                password), break_on_error=False, sensible=True)[2]
            if not error:
                return

        # we need the password to unlock.
        correct = False
        attempt = 3
        while attempt:
            attempt -= 1
            password = getpass('Password to unlock the default keychain:')
            error = self.buildozer.cmd('security unlock-keychain -p "{}"'.format(
                password), break_on_error=False, sensible=True)[2]
            if not error:
                correct = True
                break
            self.error('Invalid keychain password')

        if not correct:
            self.error('Unable to unlock the keychain, exiting.')
            raise BuildozerCommandException()

        # maybe user want to save it for further reuse?
        print(
            'The keychain password can be saved in the build directory\n'
            'As soon as the build directory will be cleaned, '
            'the password will be erased.')

        save = None
        while save is None:
            q = raw_input('Do you want to save the password (Y/n): ')
            if q in ('', 'Y'):
                save = True
            elif q == 'n':
                save = False
            else:
                print('Invalid answer!')

        if save:
            with open(password_file, 'wb') as fd:
                fd.write(password)

def get_target(buildozer):
    return TargetIos(buildozer)
