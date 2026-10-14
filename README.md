# FreeBSD IPFW by Zabbix Agent

FreeBSD IPFW firewall monitoring for Zabbix 7.0, with Zabbix 8.0 compatibility targeted for validation.

> **Status: development preview.** Do not deploy to production without checking permissions, IPFW output and item values.

## Scope of the first implementation

- Read-only collector of IPFW rule counts and packet/byte counters.
- One Zabbix agent UserParameter returning JSON.
- Dependent items, rates and basic triggers.
- Explicit collector failure reporting; **a blocked IP address count is not inferred from deny rules**.

IP addresses in IPFW tables, rule-level LLD, advanced dashboards and verified Zabbix 8.0 export are planned, **not implemented** in this preview.

## Install (test host only)

1. Copy `scripts/ipfw_collect.sh` to `/usr/local/scripts/zabbix/ipfw_collect.sh` owned by root, mode 0755.
2. Verify `/sbin/ipfw -a list` output and test the collector as root.
3. Place `agent/userparameter_ipfw.conf` under the agent's included configuration directory.
4. Provide **command-specific** privilege escalation for the Zabbix agent account if necessary; never use `NOPASSWD: ALL`.
5. Restart the installed Zabbix agent; verify `zabbix_get -s <host> -k ipfw.raw` before import.
6. Import `templates/zabbix-7.0/freebsd_ipfw_by_zabbix_agent.yaml` to a Zabbix 7.0 test server.

The collector uses POSIX shell and awk; no Python dependency. It **never** executes IPFW changes or resets counters. Keep scripts owned by root and not writable by the Zabbix agent.

## Limitations

The parser expects conventional `ipfw -a list` lines: rule number, packet count, byte count and action. It does not enumerate blocked source IPs. Dynamic state, rule sets and tables require further testing. Summing packet counters across rules is *not* a reliable global drop ratio or unique packet count when accounting/reinjection/other rule behavior is involved.

## Contributing

See [README.pt-BR.md](README.pt-BR.md). MIT license applies to repository content.
