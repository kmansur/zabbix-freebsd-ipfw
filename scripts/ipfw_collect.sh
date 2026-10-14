#!/bin/sh
# FreeBSD IPFW read-only metrics collector.
# Only counts rules with conventional "NNNNN packets bytes action" output.
set -eu
export LC_ALL=C
IPFW=/sbin/ipfw
AWK=/usr/bin/awk

if [ ! -x "$IPFW" ] || [ ! -x "$AWK" ]; then
  printf '%s\n' '{"status":0,"error":"Required executable unavailable"}'
  exit 1
fi

# A failed IPFW command must not be reported as zero rules/packets.
if ! output=$("$IPFW" -a list 2>/dev/null); then
  printf '%s\n' '{"status":0,"error":"IPFW read failed"}'
  exit 1
fi

rules_json=$(printf '%s\n' "$output" | "$AWK" '
function num(x) { return x ~ /^[0-9]+$/ }
{
  if (NF < 4 || !num($1) || !num($2) || !num($3)) next
  action=tolower($4)
  rules++
  if (action == "allow" || action == "accept" || action == "pass") allowed++
  if (action == "deny" || action == "drop") {
    denied++
    deny_packets += $2
    deny_bytes += $3
  }
  if (action == "reject" || action == "reset" || action == "unreach") {
    rejected++
    reject_packets += $2
    reject_bytes += $3
  }
}
END {
  if (rules == 0) {
    print "{\"status\":0,\"error\":\"No parseable IPFW rules\"}"
    exit 0
  }
  printf "{\"status\":1,\"rules_total\":%d,\"rules_allow\":%d,\"rules_deny\":%d,\"rules_reject\":%d,\"deny_packets\":%.0f,\"deny_bytes\":%.0f,\"reject_packets\":%.0f,\"reject_bytes\":%.0f}\n", rules, allowed, denied, rejected, deny_packets, deny_bytes, reject_packets, reject_bytes
}')

# Optional table census: do not replace missing/failed data with zero.
if table_info=$("$IPFW" table all info 2>/dev/null); then
  table_metrics=$(printf '%s\n' "$table_info" | "$AWK" '
    /^--- table\(/ {
      id=$0
      sub(/^--- table\(/, "", id)
      sub(/\).*/, "", id)
      tables++
      next
    }
    /^[[:space:]]*items:[[:space:]]*[0-9]+/ && id != "" {
      if (id == "40") { table40=$2; seen40=1 }
    }
    END {
      printf "\"tables_status\":1,\"tables_total\":%d", tables
      if (seen40) printf ",\"table40_entries\":%d", table40
    }
  ')
else
  table_metrics='"tables_status":0'
fi

# Attach table metrics only to a healthy rules response.
case "$rules_json" in
  *'"status":1'*)
    printf '%s,%s}\n' "${rules_json%?}" "$table_metrics"
    ;;
  *) printf '%s\n' "$rules_json" ;;
esac