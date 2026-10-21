# Changelog

## Unreleased

- Fixed installer text/string JSON validation, equivalent Includes and trusted path checks.
- Hardened backup prevalidation and atomic replacement of restored files.
- Fixed healthy-zero inventory responses on malformed input and irrelevant-table failures.
- Added one-cycle table metadata collection with dependent discovery/counters and failure alerts.
- Added explicit discard handling for unavailable dependent metrics and bounded Python command waits.
- Avoided new bytecode cache files; standardized shell line endings.
- Added behavioral regressions and native FreeBSD CI without modifying firewall policy.
- Documented upgrade ordering and operational release gates in docs/release-readiness.md.


- Created a read-only POSIX shell IPFW metrics collector.
- Added a Zabbix agent UserParameter.
- Added initial Zabbix 7.0 development template with dependent metrics and basic triggers.
- Added English and Brazilian Portuguese documentation.

No release or production support claim is made yet.
