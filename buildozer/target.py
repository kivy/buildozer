from sys import exit

class Target(object):

    def __init__(self, buildozer):
        super(Target, self).__init__()
        self.buildozer = buildozer
        self.build_mode = 'debug'
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
                print error
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
        for arg in args:
            if not arg.startswith('--'):
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

        for item in result:
            command, args = item[0], item[1:]
            if not hasattr(self, 'cmd_{0}'.format(command)):
                self.buildozer.error('Unknow command {0}'.format(command))
                exit(1)
            getattr(self, 'cmd_{0}'.format(command))(args)

    def cmd_clean(self, *args):
        self.buildozer.clean_platform()

    def cmd_update(self, *args):
        self.platform_update = True
        self.buildozer.prepare_for_build()

    def cmd_debug(self, *args):
        self.buildozer.prepare_for_build()
        self.build_mode = 'debug'
        self.buildozer.build()

    def cmd_release(self, *args):
        self.buildozer.prepare_for_build()
        self.build_mode = 'release'
        self.buildozer.build()

    def cmd_deploy(self, *args):
        self.buildozer.prepare_for_build()

    def cmd_run(self, *args):
        self.buildozer.prepare_for_build()

