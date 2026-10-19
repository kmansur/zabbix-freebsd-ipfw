"""Static contracts for FreeBSD preflight diagnostics (native runtime tests still required)."""
from pathlib import Path
import unittest

SCRIPT = (Path(__file__).resolve().parents[1] / "tools/freebsd-preflight.sh").read_text(encoding="utf-8")


class PreflightContractTests(unittest.TestCase):
    def test_agent_variants_and_ambiguity(self):
        for name in ("zabbix_agentd", "zabbix_agent2", "ambiguous agents", "explicit config path"):
            self.assertIn(name, SCRIPT)

    def test_rejects_unsupported_and_unexpected_outputs(self):
        for text in ("ZBX_NOTSUPPORTED", "unsupported agent key", "unexpected agent key response"):
            self.assertIn(text, SCRIPT)
        self.assertIn("agent test command failed", SCRIPT)

    def test_does_not_log_network_outputs(self):
        self.assertIn("ROOT_JSON=", SCRIPT)
        self.assertIn("USER_JSON=", SCRIPT)
        self.assertIn("status", SCRIPT)
        self.assertNotIn('printf "%s\\n" "$root_json"', SCRIPT)

    def test_agent_output_regex_accepts_real_types(self):
        import re
        import subprocess
        pattern = r"\[[ts]\|\{"
        self.assertIn(pattern, SCRIPT)
        for example in ('ipfw.raw [t|{"status":1}]', 'ipfw.raw [s|{"status":1}]'):
            self.assertIsNotNone(re.search(pattern, example))
            proc = subprocess.run(["grep", "-E", pattern], input=example,
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
        self.assertIsNone(re.search(pattern, "ipfw.raw [m|ZBX_NOTSUPPORTED]"))

    def test_complete_local_diagnostics(self):
        self.assertIn("ipfw.tables.discovery", SCRIPT)
        self.assertIn("ipfw.inventory.raw", SCRIPT)
        self.assertIn("inventory root/sudo", SCRIPT)


if __name__ == "__main__":
    unittest.main()
