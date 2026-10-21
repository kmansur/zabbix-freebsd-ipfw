#!/usr/bin/env python3
"""Disposable Docker test: prove a changed file is not a reloaded daemon.

Uses synthetic JSON and no IPFW access. Intended for CI only.
"""
import argparse
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from check_agent_runtime import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--binary', required=True)
    args = parser.parse_args()
    executable = shutil.which('zabbix_get')
    if not executable:
        raise RuntimeError('zabbix_get is required for the CI service test')
    raw = {'status': 1, 'rules_total': 7, 'rules_allow': 1, 'rules_deny': 2,
           'rules_reject': 3, 'rules_other': 1, 'deny_packets': 20, 'deny_bytes': 200,
           'reject_packets': 30, 'reject_bytes': 300}
    inventory = {'status': 1, 'host_unique': 0, 'host_occurrences': 0, 'host_duplicate_extra': 0,
                 'prefix_unique': 0, 'prefix_occurrences': 0, 'prefix_duplicate_extra': 0}
    tables = {'status': 1, 'data': [], 'entries': {}}

    def parameter(key, value):
        return f"UserParameter={key},printf '%s\\n' '{json.dumps(value, separators=(',', ':'))}'\n"

    name = 'ipfw-runtime-ci'
    with tempfile.TemporaryDirectory() as td:
        config = Path(td) / 'agent.conf'
        base = ('LogType=console\nPidFile=/tmp/ipfw-ci.pid\nHostname=ipfw-ci\n'
                'Server=0.0.0.0/0\nListenPort=10050\nTimeout=10\n')
        base += parameter('ipfw.raw', raw) + parameter('ipfw.inventory.raw', inventory)
        config.write_text(base)
        config.chmod(0o644)
        try:
            subprocess.run(['docker', 'run', '-d', '--name', name,
                            '-p', '127.0.0.1:10050:10050', '-v', f'{config}:/tmp/ipfw-ci.conf:ro',
                            '--entrypoint', args.binary, args.image, '-f', '-c', '/tmp/ipfw-ci.conf'], check=True)
            def check():
                with contextlib.redirect_stdout(io.StringIO()):
                    return verify(executable, '127.0.0.1', 10050)
            for _ in range(30):
                code = check()
                if code != 2:
                    break
                time.sleep(1)
            if code != 1:
                raise RuntimeError('Missing key was not detected in the running agent')
            config.write_text(base + parameter('ipfw.tables.raw', tables))
            if check() != 1:
                raise RuntimeError('A file change must not be mistaken for a daemon reload')
            subprocess.run(['docker', 'restart', name], check=True)
            for _ in range(30):
                if check() == 0:
                    break
                time.sleep(1)
            else:
                raise RuntimeError('Restart did not make the new key available')
            print('PASS: missing key detected; file-only update still fails; restart restores live collection')
        finally:
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True)


if __name__ == '__main__':
    main()
