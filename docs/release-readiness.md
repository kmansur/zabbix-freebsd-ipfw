# Release readiness

## Scope and upgrade

This project monitors rule totals, aggregate deny traffic, address-table discovery and counters, and textual blocked-source host/CIDR inventory. It does not compute effective policy. Per-rule discovery and a Zabbix dashboard are outside the current implementation; the YAML provides graphs.

Upgrade collectors and UserParameters **before** importing the updated template. The updated template requires `ipfw.tables.raw` and its root-owned `ipfw_tables_collect.py` sudo rule. Re-run the installer and confirm service restart, then import with update of existing items, discovery rules and prototypes enabled. Back up the server-side template separately: the host installer does not restore server configuration.

Table discovery and entry counts now depend on a single metadata item polled every five minutes. No per-table subprocess is required by the updated template. Legacy discovery/count keys remain available for compatibility. A failed metadata response omits discovery data, so transient errors do not falsely announce that all tables disappeared.

Set the supported agent's `Timeout` to at least 10 seconds (15 recommended for testing), and align the server/proxy timeout with the agent. Python collectors cap command waits at eight seconds per collection, with additional time needed for parsing and process startup. Measure large rulesets before production; timeouts are not a guarantee of throughput.

## Corrections covered by regression tests

- Installer accepts text/string agent responses and requires valid healthy JSON.
- Equivalent Include declarations with whitespace are recognized.
- Empty/malformed rule output fails inventory validation; valid allow-only output succeeds.
- Unreferenced non-address tables do not invalidate address inventory.
- Literal source addresses followed by one port token are supported. Complex source expressions remain conservative failures.
- Table metadata rejects malformed/incomplete records and is read once regardless of discovered table count.
- Missing dependent totals are discarded rather than replaced by zero; table failures have dedicated alerts.
- Installer and preflight reject symlinks and non-root/group-writable/world-writable path components.
- Rollback validates all manifest entries, source files and destinations before restoration, with atomic replacement per file. Multi-file restoration is not a filesystem transaction: I/O failure during application can still require operator recovery. It stops with an error instead of announcing success.
- Installation syntax-checks Python without creating bytecode; runtime collectors disable bytecode writes. Existing caches from old installations are left untouched because this is a shared directory.
- Shell line endings are fixed through `.gitattributes`.

## Automated evidence versus operational acceptance

Linux CI runs the regression suite on Python 3.11–3.13. The separate FreeBSD 14.3 VM job runs the same suite plus native permissions checks. These jobs use synthetic data, do not load IPFW, and do not change firewall policy.

Passing those jobs does **not** certify real Agent 2 service operation, template import, permission equivalence against live IPFW, or recovery on an actual installation. The existing [homologation checklist](homologation-0.1.5.md) remains the operational release gate. Preserve the development-preview designation until the following evidence is available:

1. Fresh install and repeated upgrade on FreeBSD, with root/sudo results equivalent.
2. Classic agent and Agent 2 separately, stopped/active services and ambiguous installation selection.
3. Zabbix 7.0 and 8.0 import/update, supported items, dependent discovery, graphs and alert recovery.
4. Tables absent/present, named tables and repeated names across sets, IPv4/IPv6 and unsupported sources.
5. Removal with confirmation/refusal and rollback of preexisting/absent files, including induced failures.
6. Runtime latency and memory measurements on representative rule/table sizes.

No production environment or live Zabbix frontend is available to the repository CI by default. Do not mark these items complete based on static YAML tests. Credentials and raw firewall data must never be committed.
