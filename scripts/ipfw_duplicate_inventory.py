#!/usr/bin/env python3
"""Offline IPFW blocked-host inventory, exact duplicates only.

Reads existing command output from files/stdin. Never modifies firewall state.
Conservative parser: reports incomplete input rather than misleading totals.
"""
import argparse
import ipaddress
import json
import re
from collections import Counter
from pathlib import Path

RULE = re.compile(r"^\s*\d+\s+\d+\s+\d+\s+(deny|drop|reject|reset|unreach)\b(.*)$", re.I)
TABLE_REF = re.compile(r"\btable\((\d+)\)", re.I)
HOST = re.compile(r"\bfrom\s+(\S+)", re.I)
TABLE_HEAD = re.compile(r"^--- table\((\d+)\), set\((\d+)\) ---$")
ENTRY = re.compile(r"^(\S+)\s+\S+(?:\s+.*)?$")

def normalize(token):
    try:
        ip = ipaddress.ip_network(token, strict=False)
    except ValueError:
        return None
    if ip.prefixlen != ip.max_prefixlen:
        return ("prefix", str(ip))
    return ("host", str(ip.network_address))

def summarize(rules, tables):
    refs = set()
    entries = []
    unsupported = 0
    for line in rules.splitlines():
        m = RULE.match(line)
        if not m:
            continue
        rest = m.group(2)
        refs.update(TABLE_REF.findall(rest))
        source = HOST.search(rest)
        if not source:
            unsupported += 1
            continue
        token = source.group(1)
        if token.startswith("table("):
            continue
        if token.lower() in ("any", "me"):
            continue
        parsed = normalize(token)
        if parsed:
            entries.append(parsed)
        else:
            unsupported += 1

    current = None
    seen = set()
    for line in tables.splitlines():
        m = TABLE_HEAD.match(line)
        if m:
            current = m.group(1)
            continue
        if not line.strip():
            continue
        if current not in refs:
            continue
        match = ENTRY.match(line)
        parsed = normalize(match.group(1)) if match else None
        if parsed:
            entries.append(parsed)
            seen.add(current)
        else:
            unsupported += 1

    # If a referenced table is missing from the supplied snapshot, counts
    # cannot be claimed complete.
    headers = set(TABLE_HEAD.findall(tables))
    known_tables = {name for name, _ in headers}
    missing = sorted(refs - known_tables)
    counter = Counter(entries)
    hosts = {value: n for (kind, value), n in counter.items() if kind == "host"}
    prefixes = {value: n for (kind, value), n in counter.items() if kind == "prefix"}
    return {
        "status": 1 if not missing and unsupported == 0 else 0,
        "host_occurrences": sum(hosts.values()),
        "host_unique": len(hosts),
        "host_duplicate_extra": sum(v - 1 for v in hosts.values()),
        "host_duplicated_values": sum(v > 1 for v in hosts.values()),
        "prefix_occurrences": sum(prefixes.values()),
        "prefix_unique": len(prefixes),
        "prefix_duplicate_extra": sum(v - 1 for v in prefixes.values()),
        "referenced_tables": len(refs),
        "missing_referenced_tables": len(missing),
        "unsupported_sources": unsupported,
    }

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rules-file", required=True, type=Path)
    ap.add_argument("--tables-file", required=True, type=Path)
    args = ap.parse_args()
    result = summarize(args.rules_file.read_text(), args.tables_file.read_text())
    print(json.dumps(result, separators=(",", ":")))

if __name__ == "__main__":
    main()
