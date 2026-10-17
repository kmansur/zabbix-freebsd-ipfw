#!/bin/sh
# Read-only discovery of numeric IPFW address tables.
set -eu
export LC_ALL=C
IPFW=/sbin/ipfw
AWK=/usr/bin/awk
[ -x "$IPFW" ] && [ -x "$AWK" ] || exit 1
output=$("$IPFW" table all info) || exit 1
printf '%s\n' "$output" | "$AWK" '
function emit() {
  if (!active) return
  if (id !~ /^[a-zA-Z0-9_.-]+$/ || setid !~ /^[0-9]+$/ || type !~ /^[a-zA-Z0-9_-]+$/) {
    invalid=1
    return
  }
  if (seen[id SUBSEP setid]++) {invalid=1; return}
  if (n++) data=data ","
  data=data sprintf("{\"{#TABLE_ID}\":\"%s\",\"{#TABLE_SET}\":\"%s\",\"{#TABLE_TYPE}\":\"%s\"}", id, setid, type)
}
BEGIN {active=0; n=0; data=""}
/^--- table\(/ {
  emit()
  active=1
  id=$0; sub(/^--- table\(/, "", id); sub(/\).*/, "", id)
  setid=$0; sub(/^.*set\(/, "", setid); sub(/\).*/, "", setid)
  type=""
  next
}
/^[[:space:]]*kindex:/ {
  if (!active) {invalid=1; next}
  for (i=1; i<=NF; i++) if ($i == "type:" && i < NF) type=$(i+1)
  next
}
NF && !active {invalid=1}
END {
  emit()
  if (invalid) exit 1
  print "{\"data\":[" data "]}"
}
'