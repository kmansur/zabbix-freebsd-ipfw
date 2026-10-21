import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'posix' and shutil.which('sh') and shutil.which('awk'), 'POSIX tools required')
class RuleMetrics(unittest.TestCase):
    def collect(self, rules):
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / 'ipfw'
            fake.write_text('#!/bin/sh\ncase "$1" in -a) printf "%s\\n" "$TEST_RULES";; table) :;; esac\n')
            fake.chmod(0o755)
            script = (ROOT / 'scripts/ipfw_collect.sh').read_text().replace('IPFW=/sbin/ipfw', f'IPFW={fake}')
            script = script.replace('AWK=/usr/bin/awk', 'AWK=' + shutil.which('awk'))
            result = subprocess.run(['sh', '-c', script], env={**os.environ, 'TEST_RULES': rules},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

    def test_categories_partition_total_and_reject_counters(self):
        result = self.collect('00100 1 10 allow ip from any to any\n'
                              '00200 2 20 deny ip from any to any\n'
                              '00300 3 30 reject ip from any to any\n'
                              '00400 4 40 reset tcp from any to any\n'
                              '00500 5 50 unreach host ip from any to any\n'
                              '00600 6 60 count ip from any to any\n'
                              '00700 7 70 skipto 1000 ip from any to any\n')
        self.assertEqual(result['status'], 1)
        self.assertEqual(result['rules_total'], 7)
        self.assertEqual(result['rules_other'], 2)
        self.assertEqual(result['reject_packets'], 12)
        self.assertEqual(result['reject_bytes'], 120)
        self.assertEqual(result['rules_total'], sum(result['rules_' + c] for c in ('allow','deny','reject','other')))

    def test_empty_or_partial_malformed_input_is_not_healthy(self):
        for rules in ('', 'bad output', '00100 0 0 allow ip from any to any\nbad output'):
            self.assertEqual(self.collect(rules)['status'], 0)
