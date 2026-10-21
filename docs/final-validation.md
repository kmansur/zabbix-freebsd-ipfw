English | [Português](final-validation.pt-BR.md)

# Upgrade and final validation

Implementation and automated checks are separate from operator acceptance. This is the single runbook for the remaining laboratory checks. Runtime messages remain English.

## Upgrade order

1. Export your Zabbix template and snapshot the disposable FreeBSD laboratory.
2. Update the checkout and install collectors before importing the YAML:

```sh
git switch main
git pull --ff-only origin main
sh install.sh --check
sh install.sh --install
```

Confirm a restart only for the intended service with `YES`. Record the exact backup directory. Installation now performs a passive query against the running agent using `zabbix_get`, rather than assuming that `agent -t` proves a service reload.

- Exit **0**: installed files and live collection verified.
- Exit **1** after the `Files installed` message: live key/schema/collector verification failed; files remain installed.
- Exit **2** after that message: live collection could not be verified (missing `zabbix_get`, network/ACL/TLS or configuration). Files remain installed. Earlier installation errors still attempt rollback.

Do not weaken Server ACLs or TLS merely to make loopback checks pass. Install the matching `zabbix_get` package if absent, then query from an authorized origin. A non-default port in the agent configuration/includes is detected. Non-loopback endpoints and TLS can be supplied explicitly:

```sh
sh install.sh --verify-runtime
python3 tools/check_agent_runtime.py --host AGENT_ADDRESS --port AGENT_PORT
python3 tools/check_agent_runtime.py --host AGENT_ADDRESS --port AGENT_PORT --tls-connect psk --tls-psk-identity YOUR_IDENTITY --tls-psk-file /secure/path/agent.psk
```

The checker also supports certificate options and `--source-address`; see `--help`. It does not log payloads or transport details. A checker run against a remote endpoint verifies that endpoint, not the local service identity. Verify the host/port correspond to the interface configured in Zabbix.

3. Import `templates/7.0/freebsd_ipfw_by_zabbix_agent.yaml`, updating items, discovery rules, prototypes, graphs, dashboards, macros and value maps. Preserve any intentional host-level macro overrides. Zabbix 8 remains a separate candidate; do not import the 7.0 file as proof of 8.0 support.
4. Open the IPFW dashboard. The three pages and existing UUID are preserved. Operations now includes Other rules and rejected traffic.

## New metrics

| Key | Meaning |
|---|---|
| `ipfw.rules.other` | Rules outside allow/deny/reject categories, including count/skipto/pipe/etc. |
| `ipfw.reject.packets` | Sum of reject/reset/unreach packet counters |
| `ipfw.reject.bytes` | Sum of reject/reset/unreach byte counters |
| `ipfw.reject.pps` | Change per second of the aggregate packet counter |
| `ipfw.reject.bytes_per_second` | Change per second of the aggregate byte counter |

Check `total = allow + deny + reject + other`. These are rule-action classifications, not a full semantic policy analysis. Counter rates need two valid samples and may be interrupted by resets or rule changes; they do not represent unique traffic through the whole firewall. Updating the template without updating collectors leaves new metrics without data until collectors are upgraded.

## Host-level macros

| Macro | Default |
|---|---|
| `{$IPFW.RULES.INTERVAL}` | `1m` |
| `{$IPFW.INVENTORY.INTERVAL}` | `5m` |
| `{$IPFW.TABLES.INTERVAL}` | `5m` |
| `{$IPFW.RULES.NODATA}` | `5m` |
| `{$IPFW.INVENTORY.NODATA}` | `15m` |
| `{$IPFW.TABLES.NODATA}` | `15m` |
| `{$IPFW.TABLE.NAME.MATCHES}` | `.*` |
| `{$IPFW.TABLE.NAME.NOT_MATCHES}` | `^$` |
| `{$IPFW.TABLE.SET.MATCHES}` | `.*` |

Each no-data window must be greater than its corresponding polling interval. Name/ID and set filters are regular expressions combined with the address-table type filter. For example, include `^zbx_test_.*$`, exclude `^zbx_test_ignore$`, set `^0$`. Restore defaults after testing. Invalid regex values cause discovery errors; they do not change firewall tables.

Filters affect discovered per-table items/graphs only. Total-table count, raw metadata and blocked-source inventory remain unfiltered. Existing excluded/lost items follow Zabbix's configured lost-resource policy; they need not disappear immediately.

## Laboratory acceptance sequence

1. **Baseline** — record FreeBSD, agent and server versions; agent flavor; installed commit; master/health item status. Confirm live verification and rule-category equality.
2. **Tables and filters** — compare numerical/named-table entry counts with IPFW output. Change include/exclude/set macros, execute the metadata master and inspect discovery. Distinct sets require a separate isolated configuration; do not change `tables_sets` on the existing firewall.
3. **Rejected traffic** — observe two or more collection samples. Compare counters with authorized laboratory rules and traffic; do not add blocking rules to a production firewall for this test. Confirm reject graphs and Other rules.
4. **Alerts/recovery** — on the disposable host only, stop the actual agent service, wait beyond the configured no-data windows and confirm rule/inventory/table alerts. Restart the same service; confirm fresh data and recovered alerts. Do not infer success from old green status values.
5. **Collector failure** — in a snapshot-backed copy, temporarily remove execute permission from a collector, verify unsupported/unhealthy data and alert behavior, then restore mode 0755 and confirm recovery. Do not publish raw payloads. Different failure modes can surface as collector-status or no-data problems.
6. **Rollback** — compare backed-up files/permissions before and after `sh install.sh --rollback EXACT_BACKUP_DIRECTORY`. Test preexisting and absent files, refusal/acceptance and incomplete backup rejection. Unlink/restore server-side templates separately. Multi-file restore is not a filesystem transaction.
7. **Removal/reinstall** — `sh install.sh --uninstall`, verify individual `YES`/refusal behavior, preserved shared components and expected missing keys; reinstall, confirm the right service restart and re-run live verification.
8. **Compatibility** — repeat on classic Agent 7 and Agent 2 separately. Record Zabbix 7 live acceptance and Zabbix 8 import/runtime results separately. The Linux Docker service tests do not prove FreeBSD Agent 2 packaging or service paths.

Record pass/fail per scenario, environment versions and sanitized evidence. Do not publish private addresses, hostnames, rules or credentials. Until pending acceptance is completed, this remains a development preview rather than a universal production certification.
