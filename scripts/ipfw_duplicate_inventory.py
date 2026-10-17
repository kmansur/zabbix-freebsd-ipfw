#!/usr/bin/env python3
"""Conservative read-only IPFW blocked-address inventory.

Only aggregated host/prefix counts leave this module. The parser supports
numeric source tables with explicit headers and literal source IP/CIDR rules.
Unknown rule/source/table syntax fails closed (status=0).
"""
import argparse
import ipaddress
import json
import re
from collections import Counter
from pathlib import Path

RULE = re.compile(r"^\s*\d+\s+\d+\s+\d+\s+(deny|drop|reject|reset|unreach)\b(.*)$", re.I)
SOURCE = re.compile(r"\bfrom\s+(\S+)\s+to\s+", re.I)
TABLE_REF = re.compile(r"^table\((\d+)\)$", re.I)
TABLE_HEAD = re.compile(r"^--- table\((\d+)\), set\((\d+)\) ---$")
HOST_OR_PREFIX = re.compile(r"^([^\s]+)(?:\s+.*)?$")
SKIP_SOURCE = frozenset({"any", "me"})
# Option keywords which may occur between action and protocol; the actual
# FROM clause is parsed separately, after the action has been identified.


def normalize(token):
    try:
        network = ipaddress.ip_network(token, strict=False)
    except ValueError:
        return None
    if network.prefixlen == network.max_prefixlen:
        return ("host", str(network.network_address))
    return ("prefix", str(network))


def summarize(rules, tables):
    references = set()
    entries = []
    unsupported = 0

    for line in rules.splitlines():
        match = RULE.match(line)
        if not match:
            continue
        source = SOURCE.search(match.group(2))
        if source is None:
            unsupported += 1
            continue
        token = source.group(1)
        table_ref = TABLE_REF.fullmatch(token)
        if table_ref:
            references.add(table_ref.group(1))
        elif token.lower() in SKIP_SOURCE:
            continue
        else:
            value = normalize(token)
            if value is None:
                unsupported += 1
            else:
                entries.append(value)

    headers = set()
    current = None
    parsed_tables = {}
    for line in tables.splitlines():
        stripped = line.strip()
        header = TABLE_HEAD.fullmatch(stripped)
        if stripped.startswith("--- table(") and header is None:
            unsupported += 1
            current = None
            continue
        if header:
            current = header.groups()
            headers.add(current)
            parsed_tables.setdefault(current, [])
            continue
        if not stripped:
            continue
        if current is None:
            # A nonempty, non-header table listing cannot safely be decoded.
            unsupported += 1
            continue
        token = stripped.split()[0]
        value = normalize(token)
        if value is None:
            unsupported += 1
        else:
            parsed_tables[current].append(value)

    known_ids = {ident for ident, _ in headers}
    missing = references - known_ids
    ambiguous = {ident for ident in references
                 if sum(ident == x for x, _ in headers) > 1}
    for (ident, _set), values in parsed_tables.items():
        if ident in references:
            entries.extend(values)

    counts = Counter(entries)
    host = {v: n for (kind, v), n in counts.items() if kind == "host"}
    prefix = {v: n for (kind, v), n in counts.items() if kind == "prefix"}
    return {
        "status": int(not (missing or ambiguous or unsupported)),
        "host_occurrences": sum(host.values()),
        "host_unique": len(host),
        "host_duplicate_extra": sum(n - 1 for n in host.values()),
        "host_duplicated_values": sum(n > 1 for n in host.values()),
        "prefix_occurrences": sum(prefix.values()),
        "prefix_unique": len(prefix),
        "prefix_duplicate_extra": sum(n - 1 for n in prefix.values()),
        "referenced_tables": len(references),
        "missing_referenced_tables": len(missing),
        "ambiguous_referenced_tables": len(ambiguous),
        "unsupported_sources": unsupported,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rules-file", required=True, type=Path)
    parser.add_argument("--tables-file", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.rules_file.read_text(), args.tables_file.read_text()),
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
