#!/bin/sh
# Read-only count for a uniquely identified numeric IPFW table.
set -eu
export LC_ALL=C
[ "$#" -ge 1 ] && [ "$#" -le 2 ] || exit 2
if [ "$#" -eq 2 ]; then
  case "$2" in ''|*[!0-9]*) exit 2 ;; esac
  wanted_set=$2
else
  wanted_set=""
fi
case "$1" in ''|*[!0-9]*) exit 2 ;; esac
output=$(/sbin/ipfw table all info) || exit 1
printf '%s\n' "$output" | /usr/bin/awk -v wanted="$1" -v wanted_set="$wanted_set" '
/^--- table\(/ {
  id=$0
  sub(/^--- table\(/, "", id)
  sub(/\).*/, "", id)
  setid=$0
  sub(/^.*set\(/, "", setid)
  sub(/\).*/, "", setid)
  selected=(id == wanted && (wanted_set == "" || setid == wanted_set))
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