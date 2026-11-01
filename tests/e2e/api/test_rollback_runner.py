"""Проверки порядка отката на подставных CLI, без контейнеров и сети."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]


class RollbackRunnerTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.log = self.path / 'commands.jsonl'
        self.report = self.path / 'report.json'
        self.state = self.path / 'state.json'
        self.state.write_text('{}')
        self.env = dict(os.environ, PATH=str(self.path) + os.pathsep + os.environ['PATH'],
                        COMPOSE_PROJECT_NAME='real-city-acceptance-unit',
                        BACKEND_IMAGE='new-backend', FRONTEND_IMAGE='new-frontend',
                        REAL_CITY_PREVIOUS_BACKEND_IMAGE='old-backend',
                        REAL_CITY_PREVIOUS_FRONTEND_IMAGE='old-frontend',
                        SSL_CERT_FILE='fixture.crt', REAL_CITY_API_URL='https://fixture.invalid',
                        FIXTURE_LOG=str(self.log))
        self.cli('docker', '''
import json, os, sys
args = sys.argv[1:]
with open(os.environ['FIXTURE_LOG'], 'a') as out:
    out.write(json.dumps([os.environ['BACKEND_IMAGE'], args]) + '\\n')
if args[:2] == ['image', 'inspect'] and '--format' in args:
    print('same' if os.environ.get('SAME_IMAGES') else args[-1])
if os.environ.get('FAIL_OLD') and os.environ['BACKEND_IMAGE'] == 'old-backend' and 'up' in args:
    sys.exit(1)
''')
        self.cli('curl', 'print("<html></html>")')
        self.cli('python3', f'''
import os, sys
if len(sys.argv) > 1 and sys.argv[1].endswith('storage_outage.py'):
    sys.exit(0)
os.execv({sys.executable!r}, [{sys.executable!r}] + sys.argv[1:])
''')

    def cli(self, name, source):
        path = self.path / name
        path.write_text('#!' + sys.executable + '\n' + source)
        path.chmod(0o700)

    def run_script(self):
        return subprocess.run(['bash', str(ROOT / 'scripts/test-production-rollback.sh'),
                               str(self.state), str(self.report)], env=self.env,
                              capture_output=True, text=True, timeout=10)

    def test_previous_then_current_images_and_report(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        deployments = [(image, args[-3:]) for image, args in calls if 'up' in args]
        self.assertEqual(deployments, [('old-backend', ['--wait', 'backend', 'web']),
                                       ('new-backend', ['--wait', 'backend', 'web'])])
        report = json.loads(self.report.read_text())
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['previous']['backend'], 'old-backend')
        self.assertEqual(report['current']['backend'], 'new-backend')

    def test_retagged_same_release_is_rejected_before_deploy(self):
        self.env['SAME_IMAGES'] = '1'
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('identical', result.stderr)
        self.assertEqual(json.loads(self.report.read_text())['status'], 'failed')
        self.assertNotIn('"up"', self.log.read_text())

    def test_production_project_is_rejected_without_docker(self):
        self.env['COMPOSE_PROJECT_NAME'] = 'real-city-production'
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assertFalse(self.log.exists())

    def test_failed_previous_release_does_not_publish_success(self):
        self.env['FAIL_OLD'] = '1'
        self.report.write_text('{"status":"passed"}')
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assertEqual(json.loads(self.report.read_text())['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
