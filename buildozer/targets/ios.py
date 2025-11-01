'''
iOS target, based on kivy-ios project
'''


from getpass import getpass
from os.path import join, basename, expanduser, realpath
import plistlib
import sys

import buildozer.buildops as buildops
from buildozer.exceptions import BuildozerCommandException
from buildozer.target import Target, no_config


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
    targetname = "ios"

    def __init__(self, buildozer):
        super().__init__(buildozer)
        executable = sys.executable or 'python'
        self._toolchain_cmd = [executable, "toolchain.py"]
        self._xcodebuild_cmd = ["xcodebuild"]
        # set via install_platform()
        self.ios_dir = None
        self.ios_deploy_dir = None

    def check_requirements(self):
        if sys.platform != "darwin":
            raise NotImplementedError("Only macOS is supported for iOS target")

        buildops.checkbin('Xcode xcodebuild', 'xcodebuild')
        buildops.checkbin('Xcode xcode-select', 'xcode-select')
        buildops.checkbin('Git git', 'git')
        buildops.checkbin('Cython cython', 'cython')
        buildops.checkbin('pkg-config', 'pkg-config')
        buildops.checkbin('autoconf', 'autoconf')
        buildops.checkbin('automake', 'automake')
        buildops.checkbin('libtool', 'libtool')

        self.logger.debug('Check availability of a iPhone SDK')
        sdk_list = buildops.cmd(
            ['xcodebuild', '-showsdks'],
            get_stdout=True,
            env=self.buildozer.environ).stdout
        iphoneos_lines = [
            line
            for line in sdk_list.split("\n")
            if "iphoneos" in line]
        if not iphoneos_lines:
            sdk = None
        else:
            last_iphoneos_line = iphoneos_lines[-1]
            sdk = last_iphoneos_line.split()[1]  # Second column

        if not sdk:
            raise Exception(
                'No iPhone SDK found. Please install at least one iOS SDK.')
        else:
            self.logger.debug(' -> found %r' % sdk)

        self.logger.debug('Check Xcode path')
        xcode = buildops.cmd(
            ["xcode-select", "-print-path"],
            get_stdout=True,
            env=self.buildozer.environ).stdout
        if not xcode:
            raise Exception('Unable to get xcode path')
        self.logger.debug(' -> found {0}'.format(xcode))

    def install_platform(self):
        """
        Clones `kivy/kivy-ios` and `phonegap/ios-deploy` then sets `ios_dir`
        and `ios_deploy_dir` accordingly.
        """
        self.ios_dir = self.install_or_update_repo('kivy-ios', platform='ios')
        self.ios_deploy_dir = self.install_or_update_repo('ios-deploy',
                                                          platform='ios',
                                                          branch='1.7.0',
                                                          owner='phonegap')

    def toolchain(self, cmd, **kwargs):
        kwargs.setdefault('cwd', self.ios_dir)
        return buildops.cmd(
            [*self._toolchain_cmd, *cmd],
            env=self.buildozer.environ,
            **kwargs)

    def xcodebuild(self, *args, **kwargs):
        filtered_args = [arg for arg in args if arg is not None]
        return buildops.cmd(
            [*self._xcodebuild_cmd, *filtered_args],
            env=self.buildozer.environ,
            **kwargs)

    @property
    def code_signing_allowed(self):
        allowed = self.buildozer.config.getboolean("app", "ios.codesign.allowed")
        allowed = "YES" if allowed else "NO"
        return f"CODE_SIGNING_ALLOWED={allowed}"

    @property
    def code_signing_development_team(self):
        team = self.buildozer.config.getdefault("app", f"ios.codesign.development_team.{self.build_mode}", None)
        return f"DEVELOPMENT_TEAM={team}" if team else None

    def get_available_packages(self):
        available_modules = self.toolchain(["recipes", "--compact"], get_stdout=True)[0]
        return available_modules.splitlines()[0].split()

    def load_plist_from_file(self, plist_rfn):
        with open(plist_rfn, 'rb') as f:
            return plistlib.load(f)

    def dump_plist_to_file(self, plist, plist_rfn):
        with open(plist_rfn, 'wb') as f:
            plistlib.dump(plist, f)

    def compile_platform(self):
        # for ios, the compilation depends really on the app requirements.
        # compile the distribution only if the requirements changed.
        last_requirements = self.buildozer.state.get('ios.requirements', '')
        app_requirements = self.buildozer.config.getlist('app', 'requirements',
                '')

        # we need to extract the requirements that kivy-ios knows about
        available_modules = self.get_available_packages()
        onlyname = lambda x: x.split('==')[0]  # noqa: E731 do not assign a lambda expression, use a def
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
            self.logger.info('Using custom source dirs:\n    {}'.format(
                '\n    '.join(['{} = {}'.format(k, v)
                               for k, v in source_dirs.items()])))

        if not need_compile:
            self.logger.info('Distribution already compiled, pass.')
            return

        self.toolchain(["build", *ios_requirements])

        if not buildops.file_exists(
                join(self.ios_deploy_dir, 'ios-deploy')):
            self.xcodebuild(cwd=self.ios_deploy_dir)

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

        ios_frameworks = self.buildozer.config.getlist('app', 'ios.frameworks', '')
        frameworks_cmd = []
        for framework in ios_frameworks:
            frameworks_cmd.append(f"--add-framework={framework}")

        self.app_project_dir = join(self.ios_dir, '{0}-ios'.format(app_name.lower()))
        if not buildops.file_exists(self.app_project_dir):
            cmd = ["create", *frameworks_cmd, app_name, self.buildozer.app_dir]
        else:
            cmd = ["update", *frameworks_cmd, f"{app_name}-ios"]
        self.toolchain(cmd)

        # fix the plist
        plist_fn = '{}-Info.plist'.format(app_name.lower())
        plist_rfn = join(self.app_project_dir, plist_fn)
        version = self.buildozer.get_version()
        self.logger.info('Update Plist {}'.format(plist_fn))
        plist = self.load_plist_from_file(plist_rfn)
        plist['CFBundleIdentifier'] = self._get_package()
        plist['CFBundleShortVersionString'] = version
        plist['CFBundleVersion'] = '{}.{}'.format(version,
                self.buildozer.build_id)

        # add icons
        self._create_icons()

        # Generate OTA distribution manifest if `app_url`, `display_image_url` and `full_size_image_url` are defined.
        app_url = self.buildozer.config.getdefault("app", "ios.manifest.app_url", None)
        display_image_url = self.buildozer.config.getdefault("app", "ios.manifest.display_image_url", None)
        full_size_image_url = self.buildozer.config.getdefault("app", "ios.manifest.full_size_image_url", None)

        if any((app_url, display_image_url, full_size_image_url)):

            if not all((app_url, display_image_url, full_size_image_url)):
                self.logger.error("Options ios.manifest.app_url, ios.manifest.display_image_url"
                                     " and ios.manifest.full_size_image_url should be defined all together")
                return

            plist['manifest'] = {
                'appURL': app_url,
                'displayImageURL': display_image_url,
                'fullSizeImageURL': full_size_image_url,
            }
        # Permissions and their Justification Descriptions
        local_network_usage_description = self.buildozer.config.getdefault(
            "app", "ios.local_network_usage_description", None)
        media_usage_description = self.buildozer.config.getdefault(
            "app", "ios.media_usage_description", None)
        camera_usage_description = self.buildozer.config.getdefault(
            "app", "ios.camera_usage_description", None)
        viewcontroller_based_statusbar_appearance = self.buildozer.config.getdefault(
            "app", "ios.viewcontroller_based_statusbar_appearance", None)

        # types
        custom_ext_types = self.buildozer.config.getdefault("app", "ios.app_extensions", None)

        if media_usage_description:
            plist['NSAppleMusicUsageDescription'] = media_usage_description
        if local_network_usage_description:
            plist['NSLocalNetworkUsageDescription'] = local_network_usage_description
        if camera_usage_description:
            plist['NSCameraUsageDescription'] = camera_usage_description
        if viewcontroller_based_statusbar_appearance:
            plist['UIViewControllerBasedStatusBarAppearance'] = viewcontroller_based_statusbar_appearance
        if custom_ext_types:
            import ast
            custom_ext_types = ast.literal_eval(custom_ext_types)
            plist["UTExportedTypeDeclarations"] = []
            plist["CFBundleDocumentTypes"] = []
            for ext in custom_ext_types:
                plist["UTExportedTypeDeclarations"].append({
                    'UTTypeConformsTo': ext[1],
                    'UTTypeIdentifier': ext[2],
                    'UTTypeDescription': ext[3],
                    'UTTypeIconFile': ext[4],
                    'UTTypeReferenceURL': ext[5],
                    'UTTypeTagSpecification': {'public.filename-extension': ext[0]}, })
                plist["CFBundleDocumentTypes"].append({
                    "CFBundleTypeName": ext[3],
                    "CFBundleTypeIconFile": ext[4],
                    "CFBundleTypeRole": "Editor",
                    "LSHandlerRank": "Owner",
                    "LSItemContentTypes": [ext[2]], })
            plist["LSSupportsOpeningDocumentsInPlace"] = "NO"
            plist["UISupportsDocumentBrowser"] = "NO"

        # ok, write the modified plist.
        self.dump_plist_to_file(plist, plist_rfn)

        mode = self.build_mode.capitalize()
        self.xcodebuild(
            "-configuration",
            mode,
            '-allowProvisioningUpdates',
            'ENABLE_BITCODE=NO',
            self.code_signing_allowed,
            self.code_signing_development_team,
            'clean',
            'build',
            cwd=self.app_project_dir)
        ios_app_dir = '{app_lower}-ios/build/{mode}-iphoneos/{app_lower}.app'.format(
                app_lower=app_name.lower(), mode=mode)
        self.buildozer.state['ios:latestappdir'] = ios_app_dir

        intermediate_dir = join(self.ios_dir, '{}-{}.intermediates'.format(app_name, version))
        xcarchive = join(intermediate_dir, '{}-{}.xcarchive'.format(
            app_name, version))
        ipa_name = '{}-{}.ipa'.format(app_name, version)
        ipa_tmp = join(intermediate_dir, ipa_name)
        ipa = join(self.buildozer.bin_dir, ipa_name)
        build_dir = join(self.ios_dir, '{}-ios'.format(app_name.lower()))

        buildops.rmdir(intermediate_dir)

        self.logger.info('Creating archive...')
        self.xcodebuild(
            '-alltargets',
            '-configuration',
            mode,
            '-scheme',
            app_name.lower(),
            '-archivePath',
            xcarchive,
            '-destination',
            'generic/platform=iOS',
            'archive',
            'ENABLE_BITCODE=NO',
            self.code_signing_allowed,
            self.code_signing_development_team,
            cwd=build_dir)

        key = 'ios.codesign.{}'.format(self.build_mode)
        ioscodesign = self.buildozer.config.getdefault('app', key, '')
        if not ioscodesign:
            self.logger.error('Cannot create the IPA package without'
                ' signature. You must fill the "{}" token.'.format(key))
            return
        elif ioscodesign[0] not in ('"', "'"):
            ioscodesign = '"{}"'.format(ioscodesign)

        self.logger.info('Creating IPA...')
        self.xcodebuild(
            '-exportArchive',
            f'-archivePath "{xcarchive}"',
            f'-exportOptionsPlist "{plist_rfn}"',
            f'-exportPath "{ipa_tmp}"',
            f'CODE_SIGN_IDENTITY={ioscodesign}',
            'ENABLE_BITCODE=NO',
            cwd=build_dir)

        self.logger.info('Moving IPA to bin...')
        buildops.rename(ipa_tmp, ipa)

        self.logger.info('iOS packaging done!')
        self.logger.info('IPA {0} available in the bin directory'.format(
            basename(ipa)))
        self.buildozer.state['ios:latestipa'] = ipa
        self.buildozer.state['ios:latestmode'] = self.build_mode

    def cmd_deploy(self, *args):
        super().cmd_deploy(*args)
        self._run_ios_deploy(lldb=False)

    def cmd_run(self, *args):
        super().cmd_run(*args)
        self._run_ios_deploy(lldb=True)

    def cmd_xcode(self, *args):
        '''Open the xcode project.
        '''
        app_name = self.buildozer.namify(self.buildozer.config.get('app',
            'package.name'))
        app_name = app_name.lower()

        ios_dir = join(self.buildozer.platform_dir, 'kivy-ios')
        buildops.cmd(
            ["open", f"{app_name}.xcodeproj"],
            cwd=join(ios_dir, f"{app_name}-ios"),
            env=self.buildozer.environ
        )

    def _run_ios_deploy(self, lldb=False):
        state = self.buildozer.state
        if 'ios:latestappdir' not in state:
            self.logger.error(
                'App not built yet. Run "debug" or "release" first.')
            return
        ios_app_dir = state.get('ios:latestappdir')

        if lldb:
            debug_mode = '-d'
            self.logger.info('Deploy and start the application')
        else:
            debug_mode = ''
            self.logger.info('Deploy the application')

        buildops.cmd(
            [join(self.ios_deploy_dir, "ios-deploy"), debug_mode, "-b", ios_app_dir],
            cwd=self.ios_dir,
            show_output=True,
            env=self.buildozer.environ)

    def _create_icons(self):
        icon = self.buildozer.config.getdefault('app', 'icon.filename', '')
        if not icon:
            return
        icon_fn = join(self.buildozer.app_dir, icon)
        if not buildops.file_exists(icon_fn):
            self.logger.error('Icon {} does not exists'.format(icon_fn))
            return

        self.toolchain(["icon", self.app_project_dir, icon_fn])

    def check_configuration_tokens(self):
        errors = []
        config = self.buildozer.config
        if not config.getboolean('app', 'ios.codesign.allowed'):
            return
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
        super().check_configuration_tokens(errors)

    @no_config
    def cmd_list_identities(self, *args):
        '''List the available identities to use for signing.
        '''
        identities = self._get_available_identities()
        print('Available identities:')
        for x in identities:
            print('  - {}'.format(x))

    def _get_available_identities(self):
        output = buildops.cmd(
            ["security", "find-identity", "-v", "-p", "codesigning"],
            get_stdout=True,
            env=self.buildozer.environ
        ).stdout

        lines = output.splitlines()[:-1]
        lines = [u'"{}"'.format(x.split('"')[1]) for x in lines]
        return lines

    def _unlock_keychain(self):
        password_file = join(self.buildozer.buildozer_dir, '.ioscodesign')
        password = None
        if buildops.file_exists(password_file):
            with open(password_file) as fd:
                password = fd.read()

        if not password:
            # no password available, try to unlock anyway...
            error = buildops.cmd(
                ["security", "unlock-keychain", "-u"],
                break_on_error=False,
                quiet=True,  # Log doesn't need secure info
                env=self.buildozer.environ).return_code
            if not error:
                return
        else:
            # password available, try to unlock
            error = buildops.cmd(
                ["security", "unlock-keychain", "-p", password],
                break_on_error=False,
                quiet=True,  # Log doesn't need secure info
                env=self.buildozer.environ
            ).return_code
            if not error:
                return

        # we need the password to unlock.
        correct = False
        attempt = 3
        while attempt:
            attempt -= 1
            password = getpass('Password to unlock the default keychain:')
            error = buildops.cmd(
                ["security", "unlock-keychain", "-p", password],
                quiet=True,  # Log doesn't need secure info
                break_on_error=False,
                env=self.buildozer.environ
            ).return_code
            if not error:
                correct = True
                break
            self.logger.error('Invalid keychain password')

        if not correct:
            self.logger.error('Unable to unlock the keychain, exiting.')
            raise BuildozerCommandException()

        # maybe user want to save it for further reuse?
        print(
            'The keychain password can be saved in the build directory\n'
            'As soon as the build directory will be cleaned, '
            'the password will be erased.')

        save = None
        while save is None:
            q = input('Do you want to save the password (Y/n): ')
            if q in ('', 'Y'):
                save = True
            elif q == 'n':
                save = False
            else:
                print('Invalid answer!')

        if save:
            with open(password_file, 'wb') as fd:
                fd.write(password.encode())


def get_target(buildozer):
    return TargetIos(buildozer)
