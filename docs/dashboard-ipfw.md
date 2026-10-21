English | [Português](dashboard-ipfw.pt-BR.md)

# IPFW

Native template dashboard with three pages and host-relative references. No Grafana, additional web service, frontend CSS installation or collector reinstallation is required.

## Visual direction

Graphite cards, large values, cyan for flow, violet for structure and amber for denied traffic/repeated occurrences. Collection health cards use green for `OK` and red for `FAILED`, with text and a collection timestamp. The Zabbix dark theme is recommended; the template does not change the user's theme.

OK means successful collection, not absence of incidents or proof of firewall policy correctness. Check the displayed timestamp: an old value does not prove current collection. Existing triggers remain responsible for alerting.

## Pages

1. **Operations** — four context cards; prominent packets/s, bytes/s and table count; four charts for traffic, rule composition and table-count history.
2. **Textual inventory** — unique hosts/prefixes, extra occurrences and integrity; separate host and CIDR charts. This does not represent effective policy, expand prefixes or calculate overlap.
3. **Table atlas** — table health/count and automatically discovered graphs identified by name and set, without fixed test-table IDs. The grid may be empty when no tables are discovered.

## Apply in Zabbix 7

1. Export the existing template as a backup. Review the import comparison if you have local customizations.
2. Import `templates/7.0/freebsd_ipfw_by_zabbix_agent.yaml`. Allow creation/update of template dashboards, value maps and graphs, along with the normal item/discovery updates.
3. Open **Monitoring → Hosts → Dashboards → IPFW**. Paths may vary with frontend translation.
4. Inspect all pages, collection timestamps and discovered-table graphs, starting with a one-hour window.

The dashboard UUID is preserved when renaming IPFWa to IPFW. Reimport updates the existing dashboard rather than requiring deletion. Stored keys, collector output and numeric trigger expressions are unchanged. Health display mappings are `0 → FAILED`, `1 → OK`.

## Verification

Static tests validate references and non-overlapping positions on the 72-column grid. Integration imports/reimports in Zabbix 7 and checks dashboard identity and three pages. Operator-side visual inspection remains necessary. The 8.0 export remains an unvalidated candidate.
