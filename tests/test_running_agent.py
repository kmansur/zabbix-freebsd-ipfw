import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_agent_runtime import configured_port, healthy, verify


class RunningAgentTests(unittest.TestCase):
    def test_live_queries_use_bounded_get_and_no_raw_payload_logging(self):
        data = {'status': 1, 'rules_total': 7, 'rules_allow': 1, 'rules_deny': 2,
                'rules_reject': 3, 'rules_other': 1, 'deny_packets': 0, 'deny_bytes': 0,
                'reject_packets': 0, 'reject_bytes': 0}
        inventory = {'status': 1, 'host_unique': 0, 'host_occurrences': 0, 'host_duplicate_extra': 0,
                     'prefix_unique': 0, 'prefix_occurrences': 0, 'prefix_duplicate_extra': 0}
        run = Mock(side_effect=[subprocess.CompletedProcess([], 0, json.dumps(d), '') for d in
                               (data, inventory, {'status': 1, 'data': [], 'entries': {}})])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(verify('/fixture/zabbix_get', '127.0.0.1', 10051, run=run), 0)
        self.assertEqual(run.call_count, 3)
        for call in run.call_args_list:
            self.assertIn('10051', call.args[0])
            self.assertEqual(call.kwargs['timeout'], 12)
        self.assertNotIn('rules_total', output.getvalue())

    def test_missing_key_and_invalid_payload_fail(self):
        for response in ('ZBX_NOTSUPPORTED: Unsupported item key.', '{}', '{"status":0}', 'not-json'):
            run = Mock(return_value=subprocess.CompletedProcess([], 0, response, ''))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verify('get', '127.0.0.1', 10050, run=run), 1)

    def test_transport_failure_is_not_success(self):
        for run in (Mock(side_effect=subprocess.TimeoutExpired('get', 12)),
                    Mock(return_value=subprocess.CompletedProcess([], 1, '', 'private connection detail'))):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verify('get', '127.0.0.1', 10050, run=run), 2)

    def test_acl_response_with_unsupported_prefix_is_unverified(self):
        message = ('ZBX_NOTSUPPORTED: Received empty response from Zabbix Agent at [192.0.2.10]. '
                   'Assuming that agent dropped connection because of access permissions.')
        for code in (0, 1):
            for stdout, stderr in ((message, ''), ('', message)):
                run = Mock(return_value=subprocess.CompletedProcess([], code, stdout, stderr))
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(verify('get', '127.0.0.1', 10050, run=run), 2)
                self.assertIn('UNVERIFIED', output.getvalue())
                self.assertNotIn('FAIL', output.getvalue())
                self.assertNotIn('192.0.2.10', output.getvalue())

    def test_old_raw_schema_and_wrong_totals_are_rejected(self):
        self.assertFalse(healthy('ipfw.raw', {'status': 1, 'rules_total': 0}))
        self.assertFalse(healthy('ipfw.raw', {'status': True}))

    def test_port_include_default_and_recursion(self):
        with tempfile.TemporaryDirectory() as td:
            config = Path(td) / 'agent.conf'
            config.write_text('# ListenPort=9999\n')
            self.assertIsNone(configured_port(config))
            included = Path(td) / 'extra.conf'
            included.write_text('ListenPort = 10055\n')
            config.write_text(f'Include={included}\n')
            self.assertEqual(configured_port(config), 10055)
            included.write_text(f'Include={config}\n')
            with self.assertRaises(ValueError):
                configured_port(config)


if __name__ == '__main__':
    unittest.main()
