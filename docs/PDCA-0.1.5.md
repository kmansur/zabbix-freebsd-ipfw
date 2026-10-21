English | [Português](PDCA-0.1.5.pt-BR.md)

# PDCA — technical audit v0.1.5 (2026-10-19)

Historical assessment based on main and operator-reported deployment evidence. This is not a production audit, a Zabbix 8 import certification or complete FreeBSD acceptance. Never publish private addresses, host identifiers or raw firewall output.

## Plan

Objective: reproducible installation/removal, trustworthy IPFW metrics and verified 7.0/8.0 templates before a stable release.

| Priority | Finding at the audit date | Acceptance action |
|---|---|---|
| P0 | No functional FreeBSD install/uninstall/rollback coverage | Snapshot-based tests, preexisting files, approval/refusal, induced failure and byte-for-byte restore checks |
| P0 | Classic/Agent 2 selection without real Agent 2 acceptance | Test both services separately, stopped services and ambiguous dual-agent installations |
| P0 | Textual inventory is not effective-policy evaluation | Check real IPv4/IPv6, errors, tables/sets and frontend handling of status zero |
| P0 | Zabbix 8 export has no real import evidence | Verify schema, latest data, LLD, graphs and triggers in Zabbix 8 |
| P1 | Auxiliary preflight originally handled only classic agent | Agent 2 support and unsupported-key rejection implemented; real acceptance remains necessary |
| P1 | Python compilation created caches in a shared directory | Avoid new cache files; never delete third-party caches |
| P1 | Equivalent Include formatting could duplicate keys | Normalize Includes and test existing shared configurations |
| P1 | Backups lacked partial-failure/adulterated-manifest tests | Validate manifest, files, symlinks, paths and permissions before restore |
| P1 | Documentation drift | Update paths, capabilities and evidence matrix |
| P2 | CI originally covered Linux/static YAML only | Add native FreeBSD and disposable Zabbix API integration |

## Do and Check

Collectors, UserParameters, versioned templates and synthetic tests were present. An operator reported basic installation/removal and classic-agent collection, including no tables. Those reports do not demonstrate universal compatibility. Agent 2, complex live inventory, Zabbix 8 and complete recovery were pending. Zabbix 7 had a report of working items; prototypes, alerts and graphs still needed evidence at that date.

The later preflight correction added classic/Agent 2 selection, explicit configuration paths, ambiguous-agent failure, unsupported-key rejection, sudoers/script checks and root/sudo inventory equality with status one.

## Act

Stable-release gates: Zabbix 8 runtime/import, Agent 2 on FreeBSD, fresh-install recovery, multiple tables and distinct sets, sudoers review and cache handling. Keep version 0.1.5 as a development preview until evidence is complete. Re-run acceptance after each blocker is closed and record sanitized evidence. Do not deploy, publish a stable release or change production automatically.

Operational constraints: do not modify IPFW policy, grant NOPASSWD: ALL, remove shared directories/caches or publish private data. Do not infer compatibility from a YAML header. Current installer confirmations use `YES`; older audit records refer to the previous Portuguese confirmation.

This file preserves the audit context. Consult [release readiness](release-readiness.md) for subsequent fixes and current release gates and the [acceptance checklist](homologation-0.1.5.md) for procedures. Passing CI does not close all operational requirements.
