"""Behavioral regressions for data integrity and installer helpers (POSIX host)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from ipfw_duplicate_inventory import summarize


class InventoryIntegrity(unittest.TestCase):
    def test_invalid_rules_never_claim_healthy_zero(self):
        for rules in ('', 'unexpected output', '00100 1 1 allow ip from any to any\nbroken'):
            with self.subTest(rules=rules):
                self.assertEqual(summarize(rules, '')['status'], 0)

    def test_valid_allow_only_is_healthy(self):
        self.assertEqual(summarize('65535 0 0 allow ip from any to any', '')['status'], 1)

    def test_irrelevant_non_address_table_does_not_break_inventory(self):
        result = summarize('00100 1 1 deny ip from 192.0.2.1 to any',
                           '--- table(interfaces), set(0) ---\nem0 0\n')
        self.assertEqual((result['status'], result['host_unique']), (1, 1))

    def test_relevant_invalid_table_still_fails(self):
        self.assertEqual(summarize('00100 1 1 deny ip from table(interfaces) to any',
                                  '--- table(interfaces), set(0) ---\nem0 0')['status'], 0)

    def test_source_ports(self):
        result = summarize('00100 1 1 deny tcp from 192.0.2.1 443 to any', '')
        self.assertEqual((result['status'], result['host_unique']), (1, 1))


@unittest.skipUnless(os.name == 'posix' and shutil.which('sh'), 'POSIX shell required')
class InstallerHelpers(unittest.TestCase):
    def test_shell_syntax(self):
        for script in [ROOT / 'install.sh', *ROOT.glob('scripts/*.sh'), *ROOT.glob('tools/*.sh')]:
            result = subprocess.run(['sh', '-n', str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def execute(self, commands, env=None):
        code = (ROOT / 'install.sh').read_text().rsplit('case "$MODE" in', 1)[0]
        if env and 'TEST_CONFIG_ROOT' in env:
            code = code.replace('/usr/local/etc/zabbix7', env['TEST_CONFIG_ROOT'])
        return subprocess.run(['sh', '-c', code + '\n' + commands], cwd=ROOT,
                              env={**os.environ, **(env or {})}, text=True, capture_output=True)

    def test_agent_formats_and_payload_validation(self):
        for response, key, expected in (
            ('ipfw.raw [t|{"status":1}]', 'ipfw.raw', 0),
            ('ipfw.raw [s|{"status":1}]', 'ipfw.raw', 0),
            ('ipfw.raw [s|{"status":0}]', 'ipfw.raw', 1),
            ('ipfw.raw [s|{invalid}]', 'ipfw.raw', 1),
            ('ipfw.raw [m|ZBX_NOTSUPPORTED]', 'ipfw.raw', 1),
            ('ipfw.tables.discovery [s|{"data":[]}]', 'ipfw.tables.discovery', 0),
            ('ipfw.tables.discovery [s|{"data":1}]', 'ipfw.tables.discovery', 1),
        ):
            with self.subTest(response=response):
                result = self.execute('PY="$TEST_PY"; key="$TEST_KEY"; result="$TEST_RESPONSE"; validate_response',
                                      {'TEST_PY': sys.executable, 'TEST_KEY': key, 'TEST_RESPONSE': response})
                self.assertEqual(result.returncode, expected, result.stderr)

    def test_equivalent_includes(self):
        with tempfile.TemporaryDirectory() as td:
            config = Path(td) / 'agent.conf'
            for text, expected in (('Include=/example/*.conf\n', 0),
                                   ('  Include = /example/*.conf   \n', 0),
                                   ('# Include=/example/*.conf\n', 1),
                                   ('Include=/different/*.conf\n', 1)):
                config.write_text(text)
                result = self.execute('CONF="$TEST_CONF"; DIR=/example; has_include', {'TEST_CONF': str(config)})
                self.assertEqual(result.returncode, expected, result.stderr)

    def test_unsafe_paths_rejected_before_stat(self):
        for path in ('relative', '/usr/local/../etc', '/usr//local', '/usr/./local'):
            result = self.execute('trusted_path "$TEST_PATH"', {'TEST_PATH': path})
            self.assertNotEqual(result.returncode, 0)

    def test_rollback_refuses_outside_backup_root(self):
        result = self.execute('rollback /tmp/untrusted')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Backup fora', result.stderr)

    def test_rollback_prevalidates_all_files_and_restores(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            config_root = base / 'etc'
            config_root.mkdir()
            conf = config_root / 'agent.conf'
            params = config_root / 'agent.d' / 'userparameter_ipfw.conf'
            params.parent.mkdir()
            dest = base / 'scripts'
            dest.mkdir()
            backups = base / 'backups'
            backup = backups / 'backup.fixture'
            backup.mkdir(parents=True)
            sudoers = base / 'sudoers'
            names = ('ipfw_collect.sh', 'ipfw_table_discovery.sh', 'ipfw_table_entries.sh',
                     'ipfw_inventory_collect.py', 'ipfw_duplicate_inventory.py', 'ipfw_tables_collect.py')
            targets = {'agent': conf, 'userparameter': params, 'sudoers': sudoers,
                       **{name: dest / name for name in names}}
            for label, path in targets.items():
                path.write_text('new')
                (backup / label).write_text('old-' + label)
            (backup / 'paths').write_text(f'CONF={conf}\nPARAM={params}\n')
            (backup / 'manifest').write_text(''.join(f'{label} present\n' for label in targets))
            # Exercise rollback mechanics in a sandbox; native trust checks have a separate VM test.
            commands = '''trusted_path() { :; }; visudo() { :; }; offer_restart() { :; }
CONF="$TEST_CONF"; DEST="$TEST_DEST"; BACKUPS="$TEST_BACKUPS"; SUDOERS="$TEST_SUDOERS"
rollback "$TEST_BACKUP"'''
            env = {'TEST_CONFIG_ROOT': str(config_root), 'TEST_CONF': str(conf),
                   'TEST_DEST': str(dest), 'TEST_BACKUPS': str(backups),
                   'TEST_SUDOERS': str(sudoers), 'TEST_BACKUP': str(backup)}
            missing = backup / names[-1]
            missing.unlink()
            result = self.execute(commands, env)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(all(path.read_text() == 'new' for path in targets.values()))
            missing.write_text('old-' + names[-1])
            result = self.execute(commands, env)
            self.assertEqual(result.returncode, 0, result.stderr)
            for label, path in targets.items():
                self.assertEqual(path.read_text(), 'old-' + label)
            # A pre-upgrade backup has no entry for the new sixth component.
            (backup / 'manifest').write_text(''.join(
                f'{label} present\n' for label in targets if label != names[-1]))
            missing.unlink()
            result = self.execute(commands, env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((dest / names[-1]).exists())

    def test_trusted_path_rejects_writable_mode(self):
        # Emulate FreeBSD stat to exercise permission decisions on any POSIX host.
        result = self.execute('stat() { case "$2" in %u) echo 0;; %OLp) echo 777;; esac; }; trusted_path /usr')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Permissao', result.stderr)


if __name__ == '__main__':
    unittest.main()
