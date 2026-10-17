# IPFW duplicate-address detection — design and acceptance criteria

## Purpose

The community template must not assume that each blocked address appears only once.
Duplicate detection is aggregate-only: **never create one Zabbix item per IP**.

## Supported classes

1. Exact host duplicates: repeated /32 IPv4 or /128 IPv6 in deny rules, tables, or both.
2. Exact prefix duplicates: repeated normalized CIDR networks.
3. Network overlap (e.g. an address inside /24): separate metric; not equivalent to exact duplication.
4. Rule actions and referenced tables must be verified before counting entries as blocked.
5. Named/numeric tables and sets need unique identity; table identifiers are not hard-coded.

## Proposed metrics

- `ipfw.blocked.entries.total`: total eligible entries (may include duplicates).
- `ipfw.blocked.entries.unique`: distinct normalized entries.
- `ipfw.blocked.entries.duplicates`: extra occurrences beyond one for each normalized entry.
- `ipfw.blocked.entries.duplicated`: number of distinct entries occurring more than once.
- `ipfw.blocked.prefixes.total`: distinct CIDR prefixes.
- `ipfw.blocked.inventory.status`: 1 only for complete successful collection.

No individual addresses should be sent to Zabbix; report counts only.

## Collection policy

- Inventory snapshot: every 5 minutes or configurable, not every minute.
- Use local bounded memory and avoid persistent IP address databases.
- Separate incomplete/unsupported rule syntax from a true result of zero.
- Handle an empty table inventory `{\"data\":[]}` as a normal state.
- Separate exact duplicates from CIDR overlaps; not all CIDR addresses are individual hosts.
- Only report verified unique counts when all relevant sources and table references have been parsed successfully.

## Required fixtures before integration

- No tables (generic FreeBSD test fixture).
- One address table plus individual deny rules (generic FreeBSD test fixture).
- Multiple tables 10/20/30/40, with duplicates across tables.
- Duplicate addresses between rules and tables.
- IPv4 /32 and IPv6 /128, plus prefixes.
- Multiple sets, named tables, non-deny references.
- Malformed output and command failures.

**Status:** design approved in principle; implementation, tests, and Zabbix items are pending. Do not claim unique counts from existing collectors yet.
