"""Offline wrapper checks in installed Windows PowerShell / pwsh hosts.

Uses real Python/venv processes with fixture build and pip modules, not PyInstaller.
Run: python -m unittest discover -s work -p test_build_windows.py -v
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import venv

ROOT = Path(__file__).resolve().parents[1]
HOSTS = [path for name in ('powershell.exe', 'pwsh.exe')
         if (path := shutil.which(name))] if sys.platform == 'win32' else []
PROBE = '''import json, os, sys
from pathlib import Path
stage = STAGE
if stage == 'pip':
    stage += '-' + sys.argv[1]
with Path('events.jsonl').open('a', encoding='utf-8') as stream:
    stream.write(json.dumps({'stage': stage, 'args': sys.argv[1:],
        'cwd': str(Path.cwd()), 'utf8': os.environ.get('PYTHONUTF8'),
        'cache': os.environ.get('PYINSTALLER_CONFIG_DIR')}) + '\\n')
if os.environ.get('BUILD_TEST_FAIL') == stage:
    sys.exit(23)
ready = Path('dependencies-ready')
if stage == 'dependencies' and not ready.exists():
    sys.exit(10)
if stage == 'pip---version' and os.environ.get('BUILD_TEST_NO_PIP') and not Path('pip-ready').exists():
    sys.exit(1)
if stage == 'ensurepip':
    Path('pip-ready').touch()
if stage == 'pip-check' and Path('pip-conflict').exists():
    sys.exit(1)
if stage == 'pip-install':
    ready.touch()
    Path('pip-conflict').unlink(missing_ok=True)
'''


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


@unittest.skipUnless(HOSTS, 'Requires a Windows PowerShell host')
class WindowsBuildWrapperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sandbox = tempfile.TemporaryDirectory(prefix='.build-shell-test-', dir=ROOT)
        cls.addClassCleanup(cls.sandbox.cleanup)
        cls.base = Path(cls.sandbox.name)
        cls.template = cls.base / 'template-venv'
        venv.EnvBuilder(with_pip=False).create(cls.template)

    def run_case(self, host, *, skip=False, fresh=False, fail='', env_ffmpeg=False,
                 unset_environment=False, zip_output=False, ready=False, auto_python=False,
                 no_pip=False, conflict=False):
        with tempfile.TemporaryDirectory(dir=self.base) as folder:
            caller = Path(folder)
            repo = caller / '项目 [build] with spaces'
            (repo / 'work').mkdir(parents=True)
            script = repo / 'build-windows.ps1'
            shutil.copy2(ROOT / 'build-windows.ps1', script)
            for name, stage in [('work/build_common.py', 'check'),
                                ('work/check_build_dependencies.py', 'dependencies'),
                                ('ensurepip.py', 'ensurepip'),
                                ('work/build_windows.py', 'build'), ('pip.py', 'pip')]:
                (repo / name).write_text(PROBE.replace('STAGE', repr(stage)), encoding='utf-8')
            if ready:
                (repo / 'dependencies-ready').touch()
            if conflict:
                (repo / 'pip-conflict').touch()
            if not fresh:
                shutil.copytree(self.template, repo / '.venv-build-windows')
            ffmpeg = caller / '解码器 [test] with spaces.exe'
            ffmpeg.touch()
            # Resolve the bootstrap executable relative to the caller, outside repo.
            python_path = os.path.relpath(self.template / 'Scripts/python.exe', caller)
            args = '' if auto_python else '-Python ' + ps_quote(python_path)
            if skip:
                args += ' -SkipInstall'
            if zip_output:
                args += ' -Zip'
            if not env_ffmpeg:
                args += ' -FFmpeg ' + ps_quote(ffmpeg.name)
            runner = caller / 'run.ps1'
            runner.write_text('''$ErrorActionPreference = 'Stop'
$oldLocation = (Get-Location).Path
$oldUtf8 = $env:PYTHONUTF8
$oldCache = $env:PYINSTALLER_CONFIG_DIR
$ok = $true
$message = ''
try { & SCRIPT ARGS } catch { $ok = $false; $message = $_.Exception.Message }
$restored = ((Get-Location).Path -eq $oldLocation) -and
    ($env:PYTHONUTF8 -eq $oldUtf8) -and ($env:PYINSTALLER_CONFIG_DIR -eq $oldCache)
@{ok=$ok; restored=$restored; message=$message} | ConvertTo-Json |
    Set-Content -LiteralPath RESULT -Encoding UTF8
'''.replace('SCRIPT', ps_quote(script)).replace('ARGS', args)
                .replace('RESULT', ps_quote(caller / 'result.json')), encoding='utf-8-sig')
            env = os.environ.copy()
            env.update(TEMP=str(caller), TMP=str(caller))
            env['PATH'] = str(self.template / 'Scripts') + os.pathsep + env.get('PATH', '')
            env.update(BUILD_TEST_FAIL=fail, PYTHONUTF8='0',
                       PYINSTALLER_CONFIG_DIR='original-cache')
            env['BUILD_TEST_NO_PIP'] = '1' if no_pip else ''
            if unset_environment:
                env.pop('PYTHONUTF8', None)
                env.pop('PYINSTALLER_CONFIG_DIR', None)
            env.pop('BAILONG_BUILD_FFMPEG', None)
            if env_ffmpeg:
                env['BAILONG_BUILD_FFMPEG'] = ffmpeg.name
            # Only the disposable test process changes policy, never the host/user policy.
            result = subprocess.run([host, '-NoProfile', '-NonInteractive',
                                     '-ExecutionPolicy', 'Bypass', '-File', str(runner)],
                                    cwd=caller, env=env, capture_output=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stderr)
            status = json.loads((caller / 'result.json').read_text(encoding='utf-8-sig'))
            status['stderr'] = result.stderr.decode('utf-8', errors='replace')
            self.assertTrue(status['restored'], status)
            event_path = repo / 'events.jsonl'
            events = [json.loads(line) for line in event_path.read_text(encoding='utf-8').splitlines()] \
                if event_path.exists() else []
            for event in events:
                self.assertEqual(Path(event['cwd']), repo)
                self.assertEqual(event['utf8'], '1')
                self.assertEqual(Path(event['cache']), repo / '.build-windows/pyinstaller-cache')
                if event['stage'] == 'build':
                    expected = ['--ffmpeg', str(ffmpeg)] + (['--zip'] if zip_output else [])
                    self.assertEqual(event['args'], expected)
                if event['stage'] == 'pip-install':
                    self.assertEqual(event['args'], ['install', '-r', 'requirements-build.txt'])
            return status, [event['stage'] for event in events]

    def test_bootstrap_and_install(self):
        for host in HOSTS:
            with self.subTest(host=host):
                status, stages = self.run_case(host, fresh=True)
                self.assertTrue(status['ok'], status)
                self.assertEqual(stages, ['check', 'check', 'dependencies', 'pip---version',
                                          'pip-install', 'dependencies', 'pip-check', 'build'])

    def test_reuse_skip_install_and_environment_ffmpeg(self):
        for host in HOSTS:
            with self.subTest(host=host):
                status, stages = self.run_case(host, skip=True, env_ffmpeg=True,
                                              unset_environment=True, zip_output=True, ready=True)
                self.assertTrue(status['ok'], status)
                self.assertEqual(stages, ['check', 'dependencies', 'pip-check', 'build'])

    def test_failure_stops_pipeline_and_restores_environment(self):
        for host in HOSTS:
            for failure, expected in [
                ('check', ['check']),
                ('pip-install', ['check', 'dependencies', 'pip---version', 'pip-install']),
                ('build', ['check', 'dependencies', 'pip---version', 'pip-install',
                           'dependencies', 'pip-check', 'build'])
            ]:
                with self.subTest(host=host, failure=failure):
                    status, stages = self.run_case(host, fail=failure)
                    self.assertFalse(status['ok'], status)
                    self.assertIn('23', status['message'])
                    self.assertEqual(stages, expected)

    def test_skip_install_requires_existing_environment(self):
        for host in HOSTS:
            with self.subTest(host=host):
                status, stages = self.run_case(host, fresh=True, skip=True)
                self.assertFalse(status['ok'], status)
                self.assertIn('构建环境不存在', status['message'])
                self.assertEqual(stages, [])

    def test_ready_environment_does_not_install(self):
        for host in HOSTS:
            with self.subTest(host=host):
                status, stages = self.run_case(host, ready=True)
                self.assertTrue(status['ok'], status)
                self.assertEqual(stages, ['check', 'dependencies', 'pip-check', 'build'])

    def test_missing_pip_is_bootstrapped_before_installing_dependencies(self):
        for host in HOSTS:
            with self.subTest(host=host):
                status, stages = self.run_case(host, no_pip=True)
                self.assertTrue(status['ok'], status)
                self.assertEqual(stages, ['check', 'dependencies', 'pip---version', 'ensurepip',
                                          'pip-install', 'dependencies', 'pip-check', 'build'])

    def test_conflicts_are_repaired_and_rechecked(self):
        for host in HOSTS:
            with self.subTest(host=host):
                status, stages = self.run_case(host, ready=True, conflict=True)
                self.assertTrue(status['ok'], status)
                self.assertEqual(stages, ['check', 'dependencies', 'pip-check', 'pip---version',
                                          'pip-install', 'dependencies', 'pip-check', 'build'])

    def test_skip_install_does_not_repair_conflicts(self):
        for host in HOSTS:
            with self.subTest(host=host):
                status, stages = self.run_case(host, ready=True, conflict=True, skip=True)
                self.assertFalse(status['ok'], status)
                self.assertEqual(stages, ['check', 'dependencies', 'pip-check'])

    def test_skip_install_reports_missing_dependencies(self):
        for host in HOSTS:
            with self.subTest(host=host):
                status, stages = self.run_case(host, skip=True)
                self.assertFalse(status['ok'], status)
                self.assertIn('构建依赖缺失', status['message'])
                self.assertEqual(stages, ['check', 'dependencies'])

    @unittest.skipUnless(sys.maxsize > 2**32 and (3, 11) <= sys.version_info[:2] <= (3, 13),
                         'Automatic selection needs a supported Python for the fixture')
    def test_automatically_selects_installed_python(self):
        for host in HOSTS:
            with self.subTest(host=host):
                status, stages = self.run_case(host, fresh=True, auto_python=True, ready=True)
                self.assertTrue(status['ok'], status)
                self.assertEqual(stages, ['check', 'check', 'dependencies', 'pip-check', 'build'])


if __name__ == '__main__':
    unittest.main()
