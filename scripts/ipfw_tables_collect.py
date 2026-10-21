#!/usr/bin/env python3
"""Collect table metadata once per polling cycle; never emit table contents."""
import json
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HEADER = re.compile(r'^--- table\(([a-zA-Z0-9_.-]+)\), set\((\d+)\) ---$')


def parse(text):
    tables = []
    current = None
    seen = set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('--- table('):
            match = HEADER.fullmatch(line)
            if not match or match.groups() in seen:
                raise ValueError('Invalid table header')
            seen.add(match.groups())
            current = {'id': match[1], 'set': match[2]}
            tables.append(current)
        elif current is None:
            raise ValueError('Missing table header')
        elif line.startswith('kindex:'):
            match = re.search(r'\btype:\s*([a-zA-Z0-9_-]+)\b', line)
            if not match or 'type' in current:
                raise ValueError('Invalid table type')
            current['type'] = match[1]
        elif line.startswith('items:'):
            match = re.match(r'items:\s*([0-9]+)(?:,|\s|$)', line)
            if not match or 'count' in current:
                raise ValueError('Invalid item count')
            current['count'] = int(match[1])
    if any('type' not in t or 'count' not in t for t in tables):
        raise ValueError('Incomplete table metadata')
    return {'status': 1, 'data': [
        {'{#TABLE_ID}': t['id'], '{#TABLE_SET}': t['set'], '{#TABLE_TYPE}': t['type']}
        for t in tables], 'entries': {t['set'] + ':' + t['id']: t['count'] for t in tables}}


def collect():
    result = subprocess.run(('/sbin/ipfw', 'table', 'all', 'info'),
                            check=True, text=True, capture_output=True, timeout=8)
    return parse(result.stdout)


if __name__ == '__main__':
    try:
        print(json.dumps(collect(), separators=(',', ':')))
    except (subprocess.SubprocessError, OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({'status': 0, 'error': type(exc).__name__}))
