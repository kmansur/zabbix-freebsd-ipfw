English | [Português](homologation-0.1.5.pt-BR.md)

# Version 0.1.5 acceptance checklist

## Prerequisites

- Disposable FreeBSD/IPFW laboratory and a `zabbix` account.
- Zabbix 7 classic agent or Agent 2 with the effective UserParameter Include; validate each implementation separately.
- Python 3 available through the installed absolute shebang; scripts owned by root:wheel with mode 0755 and sudoers mode 0440.
- Backups of agent configuration and the server-side template. These checks must not change firewall policy.

## Procedure

1. Review main and run `sh install.sh --check`, then `sh install.sh --install`. Record the exact backup path without publishing private identifiers. Confirm restart with `YES` when appropriate.
2. Run `visudo -cf /usr/local/etc/sudoers.d/zabbix-ipfw` and validate the main sudoers include.
3. Compare root and zabbix/sudo inventory JSON when the ruleset is unchanged.
4. Test `ipfw.inventory.raw` with the installed agent and its actual configuration. Avoid duplicate UserParameters.
5. Import `templates/7.0/freebsd_ipfw_by_zabbix_agent.yaml` into a Zabbix 7 laboratory, enabling item/prototype/graph/dashboard/value-map updates.
6. Verify inventory status, unique hosts, occurrences and extra duplicates. Duplicates mean occurrences beyond the first of each normalized value.
7. Check host and CIDR graphs and all three Sentinel dashboard pages.
8. Check discovery and graphs with tables and without tables. No tables is a valid healthy condition.
9. Use synthetic snapshots for repeated IPs, IPv6, CIDR, invalid sources, missing tables and repeated table names across sets.
10. Import `templates/8.0/freebsd_ipfw_by_zabbix_agent.yaml` into Zabbix 8 and repeat runtime checks. Static validation or a version header does not prove compatibility.

## Acceptance evidence

Successful import, supported numeric items, equivalent root/sudo values, status zero on incomplete inventory without partial trusted totals, CI success and proven update/restore behavior. Do not publish private addresses, hostnames, topology or raw dumps in logs or PRs.

Inventory counts textual sources and referenced tables, not effective blocked IPs. It does not evaluate NAT, ordering, interface conditions, prefix overlap or policy intersections. Exact /24 and /32 prefixes are different and are never expanded. Ambiguous inventory table references across sets remain incomplete.

## Tables and legacy keys

Current templates use `ipfw.tables.raw` as master for dependent LLD and `ipfw.table.set.entries[{#TABLE_ID},{#TABLE_SET}]` counters. Install `ipfw_tables_collect.py` and its sudo rule before template upgrade. Legacy `ipfw.table.entries[*]` and set-qualified collector keys remain available. A table ID without set is ambiguous when repeated across sets.

Simple named tables accept ASCII alphanumeric characters, dot, hyphen and underscore; malformed names and complex unsupported sources fail conservatively. Sudoers argument globs do not replace validation inside the root-owned script. Example legacy authorization:

```sudoers
zabbix ALL=(root) NOPASSWD: /usr/local/scripts/zabbix/ipfw_table_entries.sh [a-zA-Z0-9_.-]* [0-9]*
```

Do not change `net.inet.ip.fw.tables_sets` on an existing firewall just to run acceptance: test distinct sets in an isolated configuration.

## Recovery and preflight

Use `sh install.sh --rollback EXACT_BACKUP_PATH` to restore local files, and `sh install.sh --uninstall` for individual removal confirmations (`YES`). Shared components remain. Server-side template unlinking/restoration is separate. Confirm file contents, permissions and the correct service (`zabbix_agentd` or `zabbix_agent2`) after changes; multi-file recovery is not a filesystem transaction.

```sh
sh tools/freebsd-preflight.sh /usr/local/etc/zabbix7/zabbix_agentd.conf
```

Preflight checks local agent, sudoers, scripts and root/sudo JSON equivalence without printing raw firewall data. PASS does not replace frontend import, latest-data, prototypes, graphs, alert recovery or Zabbix 8 validation. See [PDCA](PDCA-0.1.5.md) and [release readiness](release-readiness.md). Pending scenarios remain pending until real evidence exists.
