#!/bin/sh
# Read-only entry count for a single numeric IPFW table.
set -eu
export LC_ALL=C
IPFW=/sbin/ipfw
AWK=/usr/bin/awk

[ "$#" -eq 1 ] || exit 2
case "$1" in
  ''|*[!0-9]*) exit 2 ;;
esac
[ -x "$IPFW" ] && [ -x "$AWK" ] || exit 1
table_id=$1
output=$("$IPFW" table all info) || exit 1

printf '%s\n' "$output" | "$AWK" -v wanted="$table_id" '
/^--- table\(/ {
  id=$0
  sub(/^--- table\(/, "", id)
  sub(/\).*/, "", id)
  selected=(id == wanted)
}
/^[[:space:]]*items:[[:space:]]*[0-9]+/ && selected {
  print $2
  found=1
  exit
}
END {if (!found) exit 1}
'