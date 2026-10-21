English | [Português](duplicate-detection.pt-BR.md)

# Aggregate duplicate-source inventory

Count exact normalized IPv4 /32 and IPv6 /128 hosts separately from CIDR prefixes. Report aggregates only; never create a Zabbix item per IP or send raw addresses. Prefix overlap, effective policy, ordering, NAT and interfaces are not evaluated.

## Implemented metrics

- `ipfw.inventory.host.unique`, `ipfw.inventory.host.occurrences`, `ipfw.inventory.host.duplicates`.
- `ipfw.inventory.prefix.unique`, `ipfw.inventory.prefix.occurrences`, `ipfw.inventory.prefix.duplicates`.
- `ipfw.inventory.status`: one only when required sources are fully interpreted.

Duplicates are extra occurrences beyond the first exact normalized value. Referenced table contents are included once per uniquely identified table; unrelated tables are not counted. Missing/ambiguous references or unsupported relevant syntax return status zero and the collector omits partial totals. A valid ruleset without eligible sources can yield healthy zero; malformed/empty rule output cannot.

## Collection and validation

Inventory is polled every five minutes. Memory is local, no persistent IP database is created, and command waits are bounded. An empty table list is valid. Tests cover no tables, multiple referenced tables, cross-source duplicates, IPv4/IPv6, CIDR, names/sets, non-deny references, malformed output and command failures.

Aggregate inventory and template items are implemented. Real complex-source/scale acceptance remains necessary; do not interpret exact duplicates as subnet overlap or unique traffic totals. See [acceptance](homologation-0.1.5.md).
