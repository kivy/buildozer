import os
from unittest import mock

import pytest

from buildozer.target import Target, no_config
from tests.targets.utils import (
    patch_buildops_cmd,
    patch_buildops_file_exists,
    patch_logger_error,
)


STANDARD_CMDS = (
    'distclean', 'update', 'debug', 'release', 'deploy', 'run', 'serve',
)

DOMAIN_CASES = [
    ('org.test', 'BUILDOZER_ALLOW_ORG_TEST_DOMAIN'),
    ('org.kivy', 'BUILDOZER_ALLOW_KIVY_ORG_DOMAIN'),
]


def _make_target(standard_cmds=STANDARD_CMDS, **buildozer_attrs):
    m_buildozer = mock.Mock(standard_cmds=standard_cmds, **buildozer_attrs)
    return Target(m_buildozer)


class TestNoConfigDecorator:

    def test_no_config_sets_marker(self):
        @no_config
        def fn():
            pass
        assert getattr(fn, '__no_config')


class TestTargetInit:

    def test_init_defaults(self):
        m_buildozer = mock.Mock()
        target = Target(m_buildozer)
        assert target.buildozer is m_buildozer
        assert target.build_mode == 'debug'
        assert not target.platform_update


class TestTargetNoops:

    def test_check_requirements_is_noop(self):
        assert _make_target().check_requirements() is None

    def test_compile_platform_is_noop(self):
        assert _make_target().compile_platform() is None

    def test_install_platform_is_noop(self):
        assert _make_target().install_platform() is None

    def test_get_available_packages(self):
        assert _make_target().get_available_packages() == ['kivy']


class TestCheckConfigurationTokens:

    def test_no_errors_is_noop(self):
        _make_target().check_configuration_tokens()
        _make_target().check_configuration_tokens(errors=[])

    def test_errors_exit_one(self):
        target = _make_target()
        with patch_logger_error(), \
                mock.patch('builtins.print') as m_print, \
                pytest.raises(SystemExit) as ctx:
            target.check_configuration_tokens(errors=['oops', 'broken'])
        assert ctx.value.code == 1
        printed = [c.args[0] for c in m_print.call_args_list]
        assert 'oops' in printed
        assert 'broken' in printed


class TestGetCustomCommands:

    def test_filters_standard_cmds(self):
        target = _make_target(standard_cmds=STANDARD_CMDS)
        names = {name for name, _doc in target.get_custom_commands()}
        assert names == {'clean'}

    def test_no_standard_cmds_returns_all(self):
        target = _make_target(standard_cmds=())
        names = {name for name, _doc in target.get_custom_commands()}
        assert names == {
            'clean', 'update', 'debug', 'release', 'deploy', 'run', 'serve',
        }


class TestRunCommands:

    def test_empty_args_exits_one(self):
        target = _make_target()
        with patch_logger_error(), pytest.raises(SystemExit) as ctx:
            target.run_commands([])
        assert ctx.value.code == 1
        target.buildozer.usage.assert_called_once_with()

    def test_unknown_command_exits_one(self):
        target = _make_target()
        with patch_logger_error(), pytest.raises(SystemExit) as ctx:
            target.run_commands(['nope'])
        assert ctx.value.code == 1

    def test_flag_without_command_exits_one(self):
        target = _make_target()
        with patch_logger_error(), pytest.raises(SystemExit) as ctx:
            target.run_commands(['--verbose'])
        assert ctx.value.code == 1
        target.buildozer.usage.assert_called_once_with()

    def test_dispatches_to_cmd_method(self):
        target = _make_target()
        with mock.patch.object(target, 'cmd_debug', autospec=True) as m_debug:
            target.run_commands(['debug'])
        m_debug.assert_called_once_with([])

    def test_passes_flags_to_cmd(self):
        target = _make_target()
        with mock.patch.object(target, 'cmd_debug', autospec=True) as m_debug:
            target.run_commands(['debug', '--verbose'])
        m_debug.assert_called_once_with(['--verbose'])

    def test_double_dash_appends_trailing_args(self):
        target = _make_target()
        with mock.patch.object(target, 'cmd_debug', autospec=True) as m_debug:
            target.run_commands(['debug', '--', 'extra1', 'extra2'])
        m_debug.assert_called_once_with(['extra1', 'extra2'])

    def test_runs_config_check_once(self):
        target = _make_target()
        with mock.patch.object(target, 'cmd_debug', autospec=True), \
                mock.patch.object(target, 'cmd_run', autospec=True), \
                mock.patch.object(
                    target, 'check_configuration_tokens') as m_check:
            target.run_commands(['debug', 'run'])
        m_check.assert_called_once_with()

    def test_no_config_method_skips_check(self):
        @no_config
        def cmd_skip(args):
            pass
        target = _make_target()
        target.cmd_skip = cmd_skip
        with mock.patch.object(
                target, 'check_configuration_tokens') as m_check:
            target.run_commands(['skip'])
        m_check.assert_not_called()


class TestCmdDelegations:

    def test_cmd_clean(self):
        target = _make_target()
        target.cmd_clean()
        target.buildozer.clean_platform.assert_called_once_with()

    def test_cmd_update(self):
        target = _make_target()
        target.cmd_update()
        assert target.platform_update
        target.buildozer.prepare_for_build.assert_called_once_with()

    def test_cmd_debug(self):
        target = _make_target()
        target.cmd_debug()
        target.buildozer.prepare_for_build.assert_called_once_with()
        assert target.build_mode == 'debug'
        target.buildozer.build.assert_called_once_with()

    def test_cmd_deploy(self):
        target = _make_target()
        target.cmd_deploy()
        target.buildozer.prepare_for_build.assert_called_once_with()

    def test_cmd_run(self):
        target = _make_target()
        target.cmd_run()
        target.buildozer.prepare_for_build.assert_called_once_with()

    def test_cmd_serve(self):
        target = _make_target()
        target.cmd_serve()
        target.buildozer.cmd_serve.assert_called_once_with()


class TestCmdRelease:

    def _target_with_domain(self, domain):
        target = _make_target()
        target.buildozer.config.get.return_value = domain
        return target

    def test_happy_path(self):
        target = self._target_with_domain('com.example')
        target.cmd_release()
        target.buildozer.prepare_for_build.assert_called_once_with()
        assert target.build_mode == 'release'
        target.buildozer.build.assert_called_once_with()


class TestCheckPackageDomain:

    def _target_with_domain(self, domain):
        target = _make_target()
        target.buildozer.config.get.return_value = domain
        return target

    @pytest.mark.parametrize('domain,env_var', DOMAIN_CASES)
    def test_exits_without_override(self, domain, env_var):
        target = self._target_with_domain(domain)
        with patch_logger_error(), \
                mock.patch.dict(os.environ, {}, clear=True), \
                pytest.raises(SystemExit) as ctx:
            target._check_package_domain(domain, env_var, ['msg'])
        assert ctx.value.code == 1

    @pytest.mark.parametrize('domain,env_var', DOMAIN_CASES)
    def test_passes_with_override(self, domain, env_var):
        target = self._target_with_domain(domain)
        with patch_logger_error(), \
                mock.patch.dict(os.environ, {env_var: '1'}):
            target._check_package_domain(domain, env_var, ['msg'])

    def test_noop_when_domain_differs(self):
        target = self._target_with_domain('com.example')
        with patch_logger_error() as m_error:
            target._check_package_domain(
                'org.test', 'BUILDOZER_ALLOW_ORG_TEST_DOMAIN', ['msg'])
        m_error.assert_not_called()

    def test_body_lines_are_logged(self):
        target = self._target_with_domain('org.test')
        with patch_logger_error() as m_error, \
                mock.patch.dict(os.environ, {}, clear=True), \
                pytest.raises(SystemExit):
            target._check_package_domain(
                'org.test',
                'BUILDOZER_ALLOW_ORG_TEST_DOMAIN',
                ['first line', 'second line'],
            )
        logged = [c.args[0] for c in m_error.call_args_list]
        assert 'first line' in logged
        assert 'second line' in logged


class TestPathOrGitUrl:

    def _target(self, overrides=None):
        overrides = overrides or {}
        target = _make_target(root_dir='/root')

        def fake_get(section, key, fallback=None):
            return overrides.get(key, fallback)

        target.buildozer.config.get.side_effect = fake_get
        return target

    def test_custom_dir_short_circuits(self):
        target = self._target({'python_for_android_dir': 'mycheckout'})
        path, url, branch = target.path_or_git_url('python-for-android')
        assert path == os.path.join('/root', 'mycheckout')
        assert url is None
        assert branch is None

    def test_default_url_and_branch(self):
        target = self._target()
        path, url, branch = target.path_or_git_url('python-for-android')
        assert path is None
        assert branch == 'master'
        assert url == 'https://github.com/kivy/python-for-android.git'

    def test_squash_hyphen_default(self):
        target = self._target()
        target.path_or_git_url('python-for-android')
        keys = [
            call.args[1]
            for call in target.buildozer.config.get.call_args_list
        ]
        assert 'python_for_android_dir' in keys
        assert 'python_for_android_branch' in keys
        assert 'python_for_android_url' in keys

    def test_no_squash_hyphen(self):
        target = self._target()
        target.path_or_git_url('python-for-android', squash_hyphen=False)
        keys = [
            call.args[1]
            for call in target.buildozer.config.get.call_args_list
        ]
        assert 'python-for-android_dir' in keys

    def test_platform_prefix(self):
        target = self._target()
        target.path_or_git_url('p4a', platform='android')
        keys = [
            call.args[1]
            for call in target.buildozer.config.get.call_args_list
        ]
        assert 'android.p4a_dir' in keys
        assert 'android.p4a_branch' in keys
        assert 'android.p4a_url' in keys

    def test_url_overrides_default(self):
        target = self._target({
            'p4a_branch': 'develop',
            'p4a_url': 'https://example.com/fork.git',
        })
        path, url, branch = target.path_or_git_url('p4a')
        assert path is None
        assert branch == 'develop'
        assert url == 'https://example.com/fork.git'


class TestInstallOrUpdateRepo:

    def _target(self):
        target = _make_target(
            platform_dir='/platform',
            root_dir='/root',
            environ={'PATH': '/bin'},
        )
        return target

    def _patch_path_or_git_url(self, target, return_value):
        return mock.patch.object(
            target, 'path_or_git_url', return_value=return_value)

    def test_new_install_with_custom_dir(self):
        target = self._target()
        with self._patch_path_or_git_url(target, ('/custom', None, None)), \
                patch_buildops_file_exists() as m_exists, \
                mock.patch('buildozer.buildops.mkdir') as m_mkdir, \
                mock.patch(
                    'buildozer.buildops.file_copytree') as m_copytree, \
                patch_buildops_cmd() as m_cmd:
            m_exists.return_value = False
            install_dir = target.install_or_update_repo('p4a')
        assert install_dir == os.path.join('/platform', 'p4a')
        m_mkdir.assert_called_once_with(install_dir)
        m_copytree.assert_called_once_with('/custom', install_dir)
        m_cmd.assert_not_called()

    def test_new_install_without_custom_dir_clones(self):
        target = self._target()
        with self._patch_path_or_git_url(
                target,
                (None, 'https://example.com/p4a.git', 'main')), \
                patch_buildops_file_exists() as m_exists, \
                mock.patch('buildozer.buildops.mkdir') as m_mkdir, \
                mock.patch(
                    'buildozer.buildops.file_copytree') as m_copytree, \
                patch_buildops_cmd() as m_cmd:
            m_exists.return_value = False
            target.install_or_update_repo('p4a')
        m_mkdir.assert_not_called()
        m_copytree.assert_not_called()
        m_cmd.assert_called_once_with(
            ['git', 'clone', '--branch', 'main',
             'https://example.com/p4a.git'],
            cwd='/platform',
            env={'PATH': '/bin'},
        )

    def test_existing_install_without_update_is_noop(self):
        target = self._target()
        target.platform_update = False
        with self._patch_path_or_git_url(
                target,
                (None, 'https://example.com/p4a.git', 'main')), \
                patch_buildops_file_exists() as m_exists, \
                mock.patch('buildozer.buildops.mkdir') as m_mkdir, \
                mock.patch(
                    'buildozer.buildops.file_copytree') as m_copytree, \
                patch_buildops_cmd() as m_cmd:
            m_exists.return_value = True
            target.install_or_update_repo('p4a')
        m_mkdir.assert_not_called()
        m_copytree.assert_not_called()
        m_cmd.assert_not_called()

    def test_existing_install_update_with_custom_dir_copies(self):
        target = self._target()
        target.platform_update = True
        with self._patch_path_or_git_url(target, ('/custom', None, None)), \
                patch_buildops_file_exists() as m_exists, \
                mock.patch(
                    'buildozer.buildops.file_copytree') as m_copytree, \
                patch_buildops_cmd() as m_cmd:
            m_exists.return_value = True
            target.install_or_update_repo('p4a')
        install_dir = os.path.join('/platform', 'p4a')
        m_copytree.assert_called_once_with('/custom', install_dir)
        m_cmd.assert_not_called()

    def test_existing_install_update_without_custom_dir_pulls(self):
        target = self._target()
        target.platform_update = True
        with self._patch_path_or_git_url(
                target,
                (None, 'https://example.com/p4a.git', 'main')), \
                patch_buildops_file_exists() as m_exists, \
                mock.patch(
                    'buildozer.buildops.file_copytree') as m_copytree, \
                patch_buildops_cmd() as m_cmd:
            m_exists.return_value = True
            target.install_or_update_repo('p4a')
        install_dir = os.path.join('/platform', 'p4a')
        m_copytree.assert_not_called()
        assert m_cmd.call_count == 2
        m_cmd.assert_any_call(
            ['git', 'clean', '-dxf'],
            cwd=install_dir,
            env={'PATH': '/bin'},
        )
        m_cmd.assert_any_call(
            ['git', 'pull', 'origin', 'main'],
            cwd=install_dir,
            env={'PATH': '/bin'},
        )
