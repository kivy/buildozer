from sys import exit

class Target(object):

    def __init__(self, buildozer):
        super(Target, self).__init__()
        self.buildozer = buildozer
        self.build_mode = 'debug'
        self.platform_update = False

    def check_requirements(self):
        pass

    def compile_platform(self):
        pass

    def run_commands(self, args):
        if not args:
            print 'ERROR: missing target command'
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
                    print 'ERROR: argument passed without a command'
                    self.buildozer.usage()
                    exit(1)
                last_command.append(arg)
        if last_command:
            result.append(last_command)

        for item in result:
            command, args = item[0], item[1:]
            if not hasattr(self, 'cmd_{0}'.format(command)):
                print 'Unknown command {0}'.format(command)
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

