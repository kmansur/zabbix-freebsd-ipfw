#!/bin/sh
# Net Tech IPFW preflight: safe, read-only checks for classic Agent and Agent 2.
# Usage: sh tools/freebsd-preflight.sh [agent_config_path]
# Never prints IPFW rules or JSON contents.
set -u
export LC_ALL=C
DEFAULT_CLASSIC=/usr/local/etc/zabbix7/zabbix_agentd.conf
DEFAULT_AGENT2=/usr/local/etc/zabbix7/zabbix_agent2.conf
CONF=${1:-}
AGENT=
KIND=
FAIL=0
ok() { printf 'PASS %s\n' "$1"; }
bad() { printf 'FAIL %s\n' "$1"; FAIL=1; }
choose_agent() {
  if [ -n "$CONF" ]; then
    case "$CONF" in
      */zabbix_agent2.conf) AGENT=/usr/local/sbin/zabbix_agent2; KIND=agent2 ;;
      */zabbix_agentd.conf) AGENT=/usr/local/sbin/zabbix_agentd; KIND=classic ;;
      *) bad 'unknown explicit agent configuration path'; return 1 ;;
    esac
  else
    a=no; b=no
    [ -x /usr/local/sbin/zabbix_agentd ] && [ -f "$DEFAULT_CLASSIC" ] && a=yes
    [ -x /usr/local/sbin/zabbix_agent2 ] && [ -f "$DEFAULT_AGENT2" ] && b=yes
    if [ "$a" = yes ] && [ "$b" = yes ]; then
      if service zabbix_agentd onestatus >/dev/null 2>&1 && ! service zabbix_agent2 onestatus >/dev/null 2>&1; then b=no
      elif service zabbix_agent2 onestatus >/dev/null 2>&1 && ! service zabbix_agentd onestatus >/dev/null 2>&1; then a=no
      else bad 'ambiguous agents: pass explicit config path'; return 1
      fi
    fi
    if [ "$a" = yes ]; then CONF=$DEFAULT_CLASSIC; AGENT=/usr/local/sbin/zabbix_agentd; KIND=classic
    elif [ "$b" = yes ]; then CONF=$DEFAULT_AGENT2; AGENT=/usr/local/sbin/zabbix_agent2; KIND=agent2
    else bad 'no supported agent executable and config found'; return 1
    fi
  fi
  [ -f "$CONF" ] && [ -x "$AGENT" ] || { bad 'agent executable or config missing'; return 1; }
  ok "agent selected ($KIND)"
}
agent_key() {
  key=$1
  output=$("$AGENT" -c "$CONF" -t "$key" 2>/dev/null) || { bad "agent test command failed: $key"; return; }
  case "$output" in
    *ZBX_NOTSUPPORTED*|*'Unsupported item key'*|*'Cannot execute'*)
      bad "unsupported agent key: $key"; return ;;
  esac
  case "$key" in
    ipfw.raw|ipfw.inventory.raw|ipfw.tables.discovery)
      if printf '%s\n' "$output" | /usr/bin/grep -Eq '\[t\|\{'; then
        ok "agent key supported: $key"
      else bad "unexpected agent key response: $key"; fi ;;
  esac
}
if choose_agent; then
  SUDOERS=/usr/local/etc/sudoers.d/zabbix-ipfw
  DEST=/usr/local/scripts/zabbix
  if [ -f "$SUDOERS" ] && visudo -cf "$SUDOERS" >/dev/null 2>&1; then ok 'sudoers syntax'; else bad 'sudoers missing or invalid'; fi
  for name in ipfw_collect.sh ipfw_table_discovery.sh ipfw_table_entries.sh ipfw_inventory_collect.py ipfw_duplicate_inventory.py; do
    file="$DEST/$name"
    if [ -f "$file" ] && [ -x "$file" ] && [ ! -L "$file" ] && [ "$(stat -f %Su "$file" 2>/dev/null)" = root ]; then
      ok "root-owned executable: $name"
    else bad "unsafe or missing collector: $name"
    fi
  done
  for key in ipfw.raw ipfw.tables.discovery ipfw.inventory.raw; do agent_key "$key"; done
  PY=$(command -v python3 2>/dev/null || true)
  if [ -n "$PY" ] && [ -x "$DEST/ipfw_inventory_collect.py" ]; then
    root_json=$("$DEST/ipfw_inventory_collect.py" 2>/dev/null) || root_json=
    sudo_json=$(su -m zabbix -c '/usr/local/bin/sudo -n /usr/local/scripts/zabbix/ipfw_inventory_collect.py' 2>/dev/null) || sudo_json=
    if [ -n "$root_json" ] && [ -n "$sudo_json" ] && ROOT_JSON="$root_json" USER_JSON="$sudo_json" "$PY" -c 'import json,os,sys; a=json.loads(os.environ["ROOT_JSON"]); b=json.loads(os.environ["USER_JSON"]); sys.exit(0 if a==b and isinstance(a,dict) and a.get("status")==1 else 1)' >/dev/null 2>&1; then
      ok 'inventory root/sudo equivalent and status=1'
    else bad 'inventory root/sudo mismatch or incomplete status'; fi
  else bad 'Python 3 or inventory collector unavailable'; fi
fi
if [ "$FAIL" -eq 0 ]; then
  printf 'RESULT PASS (local preflight only; template import not checked)\n'
else
  printf 'RESULT FAIL (no network data printed)\n'
fi
exit "$FAIL"
