"""Native FreeBSD permission checks; no firewall access or service changes."""
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == 'FreeBSD' and os.geteuid() == 0,
                     'requires root in disposable FreeBSD VM')
class NativePermissions(unittest.TestCase):
    def test_permissions_and_symlinks(self):
        code = (ROOT / 'install.sh').read_text().rsplit('case "$MODE" in', 1)[0]
        with tempfile.TemporaryDirectory(dir='/root') as td:
            target = Path(td) / 'collector'
            target.write_text('fixture')
            def check(path):
                return subprocess.run(['sh', '-c', code + '\ntrusted_path "$TEST_PATH"'],
                                      env={**os.environ, 'TEST_PATH': str(path)}, capture_output=True)
            target.chmod(0o755)
            self.assertEqual(check(target).returncode, 0)
            target.chmod(0o775)
            self.assertNotEqual(check(target).returncode, 0)
            target.chmod(0o755)
            link = Path(td) / 'link'
            link.symlink_to(target)
            self.assertNotEqual(check(link).returncode, 0)
            Path(td).chmod(0o777)
            self.assertNotEqual(check(target).returncode, 0)
