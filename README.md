# FreeBSD IPFW by Zabbix Agent

Read-only FreeBSD IPFW firewall monitoring with Zabbix 7.0 and a separate Zabbix 8.0 template candidate. Maintainer/vendor: **Net Tech**, template version **0.1.5**.

> **Status: pre-release / awaiting complete FreeBSD and Zabbix 8 validation.** Synthetic CI checks are not a substitute for real Agent 2, template import and rollback tests. See [PDCA technical review](docs/PDCA-0.1.5.md).

## Features

- Rule totals and packet/byte counters from `/sbin/ipfw -a list`.
- Read-only low-level discovery of IPFW address tables by name/number **and set**, with entry counters and graph prototypes.
- Aggregate inventory of exact blocked-host and CIDR-prefix occurrences, unique values and duplicates. Missing or ambiguous sources yield `status=0` rather than partial totals.
- Dependent items, triggers and graphs for Zabbix monitoring.

**Interpretation limit:** inventory is based on textual deny/drop/reject sources and referenced tables; it does not derive the effective firewall policy, ordering, NAT or overlapping subnets. Packet sums are not necessarily unique traffic totals.

## Directory layout

| Path | Purpose |
| --- | --- |
| `install.sh` | Interactive FreeBSD installer/check/uninstall/rollback |
| `scripts/` | Five read-only collectors and parser |
| `agent/userparameter_ipfw.conf` | Agent UserParameters |
| `templates/7.0/freebsd_ipfw_by_zabbix_agent.yaml` | Zabbix 7.0 export |
| `templates/8.0/freebsd_ipfw_by_zabbix_agent.yaml` | Zabbix 8.0 export **pending live import validation** |
| `tools/freebsd-preflight.sh` | Optional legacy runtime checks (classic Agent only at present) |
| `docs/homologation-0.1.5.md` | Acceptance criteria and safe testing |
| `docs/PDCA-0.1.5.md` | Technical review and action plan |

## Installation (FreeBSD test VM or jail)

Install prerequisite packages yourself: a compatible FreeBSD Zabbix Agent (classic or Agent 2), `sudo`, `python3`, and `git`. Ensure the IPFW interface is available and the sudoers main configuration includes `/usr/local/etc/sudoers.d`. Review host-specific service paths.

```sh
git clone https://github.com/kmansur/zabbix-freebsd-ipfw.git
cd zabbix-freebsd-ipfw
sh install.sh --check
sh install.sh --install
```

Run as root. The installer detects the checkout directory, validates prerequisites, creates a backup under `/var/backups/zabbix-ipfw/`, installs five root-owned collectors, configures UserParameters and command-specific sudo rules and asks before restarting the active Zabbix service. Do not grant `NOPASSWD: ALL`.

It does **not** install OS packages, change IPFW rules, or import a Zabbix Server template. See [Portuguese installation guide](README.pt-BR.md).

To remove installed local files, use `sh install.sh --uninstall`: confirmation **SIM** is required for every file. Backups and shared services are retained. For rollback use `sh install.sh --rollback /var/backups/zabbix-ipfw/backup.YOUR_ID` with the actual backup path.

## Template import

Import the appropriate YAML in a test frontend, link to a test host and review item support, LLD, graphs and triggers. Zabbix 8 import is **not yet verified on a real frontend**. Zabbix Server template removal/unlinking is manual and is not performed by the local installer.

## Testing, security and contributions

CI runs shell syntax checks and synthetic Python/YAML tests, not FreeBSD integration. Do not publish real internal addresses, firewall output, hostnames, topology, customer identifiers or logs containing them. Use RFC 5737/RFC 3849 test addresses only.

For operational acceptance, follow [homologation checklist](docs/homologation-0.1.5.md). Project license: MIT.
