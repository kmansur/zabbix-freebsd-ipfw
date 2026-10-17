#!/bin/sh
# Read-only count for a uniquely identified numeric IPFW table.
set -eu
export LC_ALL=C
[ "$#" -eq 1 ] || exit 2
case "$1" in ''|*[!0-9]*) exit 2 ;; esac
output=$(/sbin/ipfw table all info) || exit 1
printf '%s\n' "$output" | /usr/bin/awk -v wanted="$1" '
/^--- table\(/ {
  id=$0
  sub(/^--- table\(/, "", id)
  sub(/\).*/, "", id)
  selected=(id == wanted)
  if (selected) matches++
}
/^[[:space:]]*items:[[:space:]]*[0-9]+/ && selected {
  value=$2
  sub(/,$/, "", value)
  if (value !~ /^[0-9]+$/) invalid=1
  else { count=value; found++ }
}
END {
  if (matches != 1 || found != 1 || invalid) exit 1
  print count
}
'