#!/bin/sh
# Read-only discovery of numerical IPFW tables and their declared types.
set -eu
export LC_ALL=C
IPFW=/sbin/ipfw
AWK=/usr/bin/awk

[ -x "$IPFW" ] && [ -x "$AWK" ] || exit 1
# Successful empty output means zero tables. A failed command is NOT zero tables.
output=$("$IPFW" table all info) || exit 1

printf '%s\n' "$output" | "$AWK" '
function emit() {
  if (id ~ /^[0-9]+$/ && setid ~ /^[0-9]+$/ && type ~ /^[a-zA-Z0-9_-]+$/) {
    if (seen[id]++) ambiguous=1
    if (n++) data=data ","
    data=data sprintf("{\"{#TABLE_ID}\":\"%s\",\"{#TABLE_SET}\":\"%s\",\"{#TABLE_TYPE}\":\"%s\"}", id, setid, type)
  }
}
BEGIN {id=""; setid=""; type=""; data=""}
/^--- table\(/ {
  emit()
  id=$0; sub(/^--- table\(/, "", id); sub(/\).*/, "", id)
  setid=$0; sub(/^.*set\(/, "", setid); sub(/\).*/, "", setid)
  type=""
}
/^[[:space:]]*kindex:/ {
  for (i=1; i<=NF; i++) if ($i == "type:" && i < NF) type=$(i+1)
}
END {emit(); if (ambiguous) exit 1; print "{\"data\":[" data "]}"}
'