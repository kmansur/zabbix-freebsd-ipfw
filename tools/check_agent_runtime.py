#!/usr/bin/env python3
"""Read-only passive queries against the running agent; never print payloads.

Exit 0: verified, 1: key/schema/collector failure, 2: unable to verify transport.
Unlike agent -t, zabbix_get queries the daemon that is actually listening.
"""
import argparse
import glob
import json
from pathlib import Path
import shutil
import subprocess
import sys

KEYS = ('ipfw.raw', 'ipfw.inventory.raw', 'ipfw.tables.raw')


def configured_port(path, seen=None):
    seen = set() if seen is None else seen
    path = Path(path).resolve()
    if path in seen:
        raise ValueError('Repeated or recursive configuration include')
    seen.add(path)
    ports = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = (part.strip() for part in line.split('=', 1))
        if key == 'ListenPort':
            ports.append(int(value))
        elif key == 'Include':
            for included in sorted(glob.glob(value)):
                port = configured_port(included, seen)
                if port is not None:
                    ports.append(port)
    if len(ports) > 1 or any(not 1 <= port <= 65535 for port in ports):
        raise ValueError('Ambiguous or invalid ListenPort')
    return ports[0] if ports else None


def healthy(key, payload):
    if not isinstance(payload, dict) or type(payload.get('status')) is not int or payload['status'] != 1:
        return False
    if key == 'ipfw.raw':
        counts = ('rules_total', 'rules_allow', 'rules_deny', 'rules_reject', 'rules_other',
                  'deny_packets', 'deny_bytes', 'reject_packets', 'reject_bytes')
        if not all(type(payload.get(k)) is int and payload[k] >= 0 for k in counts):
            return False
        return payload['rules_total'] == sum(payload[k] for k in counts[1:5])
    if key == 'ipfw.inventory.raw':
        return all(type(payload.get(k)) is int and payload[k] >= 0 for k in
                   ('host_unique', 'host_occurrences', 'host_duplicate_extra',
                    'prefix_unique', 'prefix_occurrences', 'prefix_duplicate_extra'))
    return isinstance(payload.get('data'), list) and isinstance(payload.get('entries'), dict)


def verify(executable, host, port, extra=(), run=None):
    run = subprocess.run if run is None else run
    status = 0
    for key in KEYS:
        try:
            response = run([executable, '-s', host, '-p', str(port), '-k', key, '-t', '10', *extra],
                           capture_output=True, text=True, timeout=12)
            # zabbix_get also prefixes ACL/empty-connection failures with ZBX_NOTSUPPORTED.
            # Classify the transport explanation before treating the prefix as an item error.
            details = (response.stdout + '\n' + response.stderr).lower()
            transport = any(marker in details for marker in (
                'received empty response', 'dropped connection', 'access permissions',
                'connection refused', 'cannot connect', 'cannot establish',
                'connection timed out', 'connection reset', 'tls handshake', 'ssl_connect'))
            unsupported = 'zbx_notsupported' in details or 'unsupported item key' in details
            if transport or (response.returncode and not unsupported):
                print(f'UNVERIFIED {key}: transport, ACL or TLS settings prevented the query')
                if not status:
                    status = 2
                continue
            if unsupported:
                print(f'FAIL running agent rejected {key}; check key registration and collector execution')
                status = 1
                continue
            try:
                valid = healthy(key, json.loads(response.stdout))
            except ValueError:
                valid = False
            if not valid:
                print(f'FAIL running agent returned incomplete, stale-schema or unhealthy data for {key}')
                status = 1
            else:
                print(f'PASS running agent: {key} (payload omitted)')
        except (OSError, subprocess.SubprocessError, UnicodeError):
            print(f'UNVERIFIED {key}: query unavailable or timed out')
            if not status:
                status = 2
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int)
    parser.add_argument('--get', dest='executable')
    for option in ('tls-connect', 'tls-psk-identity', 'tls-psk-file', 'tls-ca-file',
                   'tls-cert-file', 'tls-key-file', 'source-address'):
        parser.add_argument('--' + option)
    args = parser.parse_args(argv)
    executable = args.executable or shutil.which('zabbix_get')
    if not executable:
        for name in ('/usr/local/bin/zabbix_get', '/usr/local/sbin/zabbix_get'):
            if Path(name).is_file():
                executable = name
                break
    if not executable:
        print('UNVERIFIED: install zabbix_get to test the running daemon; agent -t is only a local test')
        return 2
    try:
        port = args.port if args.port is not None else (configured_port(args.config) if args.config else None)
        port = 10050 if port is None else port
        if not 1 <= port <= 65535:
            raise ValueError('Invalid port')
    except (OSError, ValueError, UnicodeError):
        print('UNVERIFIED: cannot resolve agent port; supply --host and --port explicitly')
        return 2
    extra = []
    for option in ('tls-connect', 'tls-psk-identity', 'tls-psk-file', 'tls-ca-file',
                   'tls-cert-file', 'tls-key-file', 'source-address'):
        value = getattr(args, option.replace('-', '_'))
        if value is not None:
            extra.extend(('--' + option, value))
    return verify(executable, args.host, port, extra)


if __name__ == '__main__':
    sys.exit(main())
