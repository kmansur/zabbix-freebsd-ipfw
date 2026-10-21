#!/usr/bin/env python3
"""Read-only aggregate IPFW blocked-address inventory for Zabbix.

No raw IP address is emitted. Requires Python 3 and permission to read IPFW.
"""
import json
import subprocess
import sys
import time

sys.dont_write_bytecode = True

from ipfw_duplicate_inventory import summarize


def run(args, timeout=8):
    return subprocess.run(args, check=True, text=True, capture_output=True, timeout=timeout).stdout


def collect():
    started = time.monotonic()
    rules = run(("/sbin/ipfw", "-a", "list"))
    remaining = 8 - (time.monotonic() - started)
    if remaining <= 0:
        raise subprocess.TimeoutExpired("ipfw inventory", 8)
    tables = run(("/sbin/ipfw", "table", "all", "list"), timeout=remaining)
    result = summarize(rules, tables)
    # Avoid exposing partial counts as trustworthy totals.
    if result["status"] != 1:
        return {"status": 0, "error": "Incomplete IPFW inventory; inspect parser support",
                "unsupported_sources": result["unsupported_sources"],
                "missing_referenced_tables": result["missing_referenced_tables"],
                "ambiguous_referenced_tables": result["ambiguous_referenced_tables"]}
    return {"status": 1, **result}


if __name__ == "__main__":
    try:
        print(json.dumps(collect(), separators=(",", ":")))
    except (subprocess.SubprocessError, OSError, UnicodeError) as exc:
        print(json.dumps({"status": 0, "error": type(exc).__name__}))
        sys.exit(0)
