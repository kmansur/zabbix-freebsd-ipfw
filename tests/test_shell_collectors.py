"""Portable synthetic tests for IPFW shell LLD and table counters."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "scripts/ipfw_table_discovery.sh"
COUNT = ROOT / "scripts/ipfw_table_entries.sh"


@unittest.skipUnless(shutil.which("sh") and shutil.which("awk"), "requires sh and awk")
class ShellCollectors(unittest.TestCase):
    def execute(self, script, listing, args=()):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            fake = base / "ipfw"
            fake.write_text("#!/bin/sh\nprintf '%s\\n' \"$MOCK_TABLES\"\n")
            fake.chmod(0o755)
            code = script.read_text()
            code = code.replace("IPFW=/sbin/ipfw", f"IPFW={fake}")
            code = code.replace("AWK=/usr/bin/awk", f"AWK={shutil.which('awk')}")
            code = code.replace("/sbin/ipfw table all info", f"{fake} table all info")
            code = code.replace("/usr/bin/awk -v", f"{shutil.which('awk')} -v")
            test_script = base / "run.sh"
            test_script.write_text(code)
            env = {**os.environ, "MOCK_TABLES": listing}
            return subprocess.run(["sh", str(test_script), *args],
                                  capture_output=True, text=True, env=env)

    def test_zero_tables(self):
        result = self.execute(DISCOVERY, "")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), '{"data":[]}')

    def test_duplicate_table_ids_are_rejected(self):
        data = ("--- table(10), set(0) ---\nkindex: type: addr\nitems: 3,\n"
                "--- table(10), set(1) ---\nkindex: type: addr\nitems: 8,\n")
        discovery = self.execute(DISCOVERY, data)
        self.assertEqual(discovery.returncode, 0, discovery.stderr)
        self.assertEqual(len(__import__("json").loads(discovery.stdout)["data"]), 2)
        self.assertNotEqual(self.execute(COUNT, data, ("10",)).returncode, 0)
        self.assertEqual(self.execute(COUNT, data, ("10", "0")).stdout.strip(), "3")
        self.assertEqual(self.execute(COUNT, data, ("10", "1")).stdout.strip(), "8")

    def test_malformed_discovery_does_not_claim_zero_tables(self):
        result = self.execute(DISCOVERY, "unexpected malformed output")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('{"data":[]}', result.stdout)

    def test_incomplete_table_metadata_is_rejected(self):
        result = self.execute(DISCOVERY, "--- table(10), set(0) ---\nitems: 3,")
        self.assertNotEqual(result.returncode, 0)

    def test_distinct_numeric_tables(self):
        import json
        data = ("--- table(10), set(0) ---\nkindex: type: addr\nitems: 3,\n"
                "--- table(11), set(1) ---\nkindex: type: addr\nitems: 8,\n")
        result = self.execute(DISCOVERY, data)
        self.assertEqual(result.returncode, 0, result.stderr)
        tables = json.loads(result.stdout)["data"]
        self.assertEqual(len(tables), 2)
        self.assertEqual(tables[0]["{#TABLE_ID}"], "10")
        self.assertEqual(tables[1]["{#TABLE_SET}"], "1")

    def test_unique_table_entries(self):
        data = "--- table(10), set(0) ---\nkindex: type: addr\nitems: 8,\n"
        result = self.execute(COUNT, data, ("10",))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "8")


if __name__ == "__main__":
    unittest.main()
