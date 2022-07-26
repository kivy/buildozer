from sys import exit
import os
from os.path import join


def no_config(f):
    f.__no_config = True
    return f


class Target:
    def __init__(self, buildozer):
        self.buildozer = buildozer
        self.build_mode = 'debug'
        self.artifact_format = 'apk'
        self.platform_update = False

    def check_requirements(self):
        pass

    def check_configuration_tokens(self, errors=None):
        if errors:
            self.buildozer.info('Check target configuration tokens')
            self.buildozer.error(
                '{0} error(s) found in the buildozer.spec'.format(
                len(errors)))
            for error in errors:
                print(error)
            exit(1)

    def compile_platform(self):
        pass

    def install_platform(self):
        pass

    def get_custom_commands(self):
        result = []
        for x in dir(self):
            if not x.startswith('cmd_'):
                continue
            if x[4:] in self.buildozer.standard_cmds:
                continue
            result.append((x[4:], getattr(self, x).__doc__))
        return result

    def get_available_packages(self):
        return ['kivy']

    def run_commands(self, args):
        if not args:
            self.buildozer.error('Missing target command')
            self.buildozer.usage()
            exit(1)

        result = []
        last_command = []
        while args:
            arg = args.pop(0)
            if arg == '--':
                if last_command:
                    last_command += args
                    break
            elif not arg.startswith('--'):
                if last_command:
                    result.append(last_command)
                    last_command = []
                last_command.append(arg)
            else:
                if not last_command:
                    self.buildozer.error('Argument passed without a command')
                    self.buildozer.usage()
                    exit(1)
                last_command.append(arg)
        if last_command:
            result.append(last_command)

        config_check = False

        for item in result:
            command, args = item[0], item[1:]
            if not hasattr(self, 'cmd_{0}'.format(command)):
                self.buildozer.error('Unknown command {0}'.format(command))
                exit(1)

            func = getattr(self, 'cmd_{0}'.format(command))

            need_config_check = not hasattr(func, '__no_config')
            if need_config_check and not config_check:
                config_check = True
                self.check_configuration_tokens()

            func(args)

    def cmd_clean(self, *args):
        self.buildozer.clean_platform()

    def cmd_update(self, *args):
        self.platform_update = True
        self.buildozer.prepare_for_build()

    def cmd_debug(self, *args):
        self.buildozer.prepare_for_build()
        self.build_mode = 'debug'
        self.artifact_format = self.buildozer.config.getdefault('app', 'android.debug_artifact', 'apk')
        self.buildozer.build()

    def cmd_release(self, *args):
        error = self.buildozer.error
        self.buildozer.prepare_for_build()
        if self.buildozer.config.get("app", "package.domain") == "org.test":
            error("")
            error("ERROR: Trying to release a package that starts with org.test")
            error("")
            error("The package.domain org.test is, as the name intented, a test.")
            error("Once you published an application with org.test,")
            error("you cannot change it, it will be part of the identifier")
            error("for Google Play / App Store / etc.")
            error("")
            error("So change package.domain to anything else.")
            error("")
            error("If you messed up before, set the environment variable to force the build:")
            error("export BUILDOZER_ALLOW_ORG_TEST_DOMAIN=1")
            error("")
            if "BUILDOZER_ALLOW_ORG_TEST_DOMAIN" not in os.environ:
                exit(1)

        if self.buildozer.config.get("app", "package.domain") == "org.kivy":
            error("")
            error("ERROR: Trying to release a package that starts with org.kivy")
            error("")
            error("The package.domain org.kivy is reserved for the Kivy official")
            error("applications. Please use your own domain.")
            error("")
            error("If you are a Kivy developer, add an export in your shell")
            error("export BUILDOZER_ALLOW_KIVY_ORG_DOMAIN=1")
            error("")
            if "BUILDOZER_ALLOW_KIVY_ORG_DOMAIN" not in os.environ:
                exit(1)

        self.build_mode = 'release'
        self.artifact_format = self.buildozer.config.getdefault('app', 'android.release_artifact', 'aab')
        self.buildozer.build()

    def cmd_deploy(self, *args):
        self.buildozer.prepare_for_build()

    def cmd_run(self, *args):
        self.buildozer.prepare_for_build()

    def cmd_serve(self, *args):
        self.buildozer.cmd_serve()

    def path_or_git_url(self, repo, owner='kivy', branch='master',
                        url_format='https://github.com/{owner}/{repo}.git',
                        platform=None,
                        squash_hyphen=True):
        """Get source location for a git checkout

        This method will check the `buildozer.spec` for the keys:
            {repo}_dir
            {repo}_url
            {repo}_branch

        and use them to determine the source location for a git checkout.

        If a `platform` is specified, {platform}.{repo} will be used
        as the base for the buildozer key

        `{repo}_dir` specifies a custom checkout location
        (relative to `buildozer.root_dir`). If present, `path` will be
        set to this value and `url`, `branch` will be set to None,
        None. Otherwise, `{repo}_url` and `{repo}_branch` will be
        examined.

        If no keys are present, the kwargs will be used to create
        a sensible default URL and branch.

        :Parameters:
            `repo`: str (required)
                name of repository to fetch. Used both for buildozer
                keys ({platform}.{repo}_dir|_url|_branch) and in building
                default git URL
            `branch`: str (default 'master')
                Specific branch to retrieve if none specified in
                buildozer.spec.
            `owner`: str
                owner of repo.
            `platform`: str or None
                platform prefix to use when retrieving `buildozer.spec`
                keys. If specified, key names will be {platform}.{repo}
                instead of just {repo}
            `squash_hyphen`: boolean
                if True, change '-' to '_' when looking for
                keys in buildozer.spec. This lets us keep backwards
                compatibility with old buildozer.spec files
            `url_format`: format string
                Used to construct default git URL.
                can use {repo} {owner} and {branch} if needed.

        :Returns:
            A Tuple (path, url, branch) where
                `path`
                    Path to a custom git checkout. If specified,
                    both `url` and `branch` will be None
                `url`
                    URL of git repository from where code should be
                    checked-out
                `branch`
                    branch name (or tag) that should be used for the
                    check-out.

        """
        if squash_hyphen:
            key = repo.replace('-', '_')
        else:
            key = repo
        if platform:
            key = "{}.{}".format(platform, key)
        config = self.buildozer.config
        path = config.getdefault('app', '{}_dir'.format(key), None)

        if path is not None:
            path = join(self.buildozer.root_dir, path)
            url = None
            branch = None
        else:
            branch = config.getdefault('app', '{}_branch'.format(key), branch)
            default_url = url_format.format(owner=owner, repo=repo, branch=branch)
            url = config.getdefault('app', '{}_url'.format(key), default_url)
        return path, url, branch

    def install_or_update_repo(self, repo, **kwargs):
        """Install or update a git repository into the platform directory.

        This will clone the contents of a git repository to
        `buildozer.platform_dir`. The location of this repo can be
        specified via URL and branch name, or via a custom (local)
        directory name.

        :Parameters:
            **kwargs:
                Any valid arguments for :meth:`path_or_git_url`

        :Returns:
            fully qualified path to updated git repo
        """
        cmd = self.buildozer.cmd
        install_dir = join(self.buildozer.platform_dir, repo)
        custom_dir, clone_url, clone_branch = self.path_or_git_url(repo, **kwargs)
        if not self.buildozer.file_exists(install_dir):
            if custom_dir:
                cmd(["mkdir", "-p", install_dir])
                cmd(["cp", "-a", f"{custom_dir}/*", f"{install_dir}/"])
            else:
                cmd(["git", "clone", "--branch", clone_branch, clone_url], cwd=self.buildozer.platform_dir)
        elif self.platform_update:
            if custom_dir:
                cmd(["cp", "-a", f"{custom_dir}/*", f"{install_dir}/"])
            else:
                cmd(["git", "clean", "-dxf"], cwd=install_dir)
                cmd(["git", "pull", "origin", clone_branch], cwd=install_dir)
        return install_dir
