#!/bin/sh
# Local read-only preflight for FreeBSD/Zabbix agent. Never prints raw IPFW data.
set -u
AGENT_CONF=${1:-/usr/local/etc/zabbix7/zabbix_agentd.conf}
AGENT=/usr/local/sbin/zabbix_agentd
SUDOERS=/usr/local/etc/sudoers.d/zabbix-ipfw
SCRIPT_DIR=/usr/local/scripts/zabbix
fail=0

ok() { printf 'PASS %s\n' "$1"; }
bad() { printf 'FAIL %s\n' "$1"; fail=1; }

if [ -f "$AGENT_CONF" ] && [ -x "$AGENT" ]; then
    ok "agent executable and config exist"
else
    bad "agent executable/config unavailable"
fi
if [ -f "$SUDOERS" ] && visudo -cf "$SUDOERS" >/dev/null 2>&1; then
    ok "sudoers syntax"
else
    bad "sudoers syntax"
fi

for name in ipfw_collect.sh ipfw_table_discovery.sh ipfw_table_entries.sh ipfw_inventory_collect.py ipfw_duplicate_inventory.py; do
    if [ -f "$SCRIPT_DIR/$name" ] && [ -x "$SCRIPT_DIR/$name" ] && [ "$(stat -f %Su "$SCRIPT_DIR/$name" 2>/dev/null)" = "root" ]; then
        ok "root-owned executable: $name"
    else
        bad "script missing, nonexecutable or not owned by root: $name"
    fi
done

if [ -x "$AGENT" ] && [ -f "$AGENT_CONF" ]; then
    for key in ipfw.raw ipfw.tables.discovery ipfw.inventory.raw; do
        if "$AGENT" -c "$AGENT_CONF" -t "$key" >/dev/null 2>&1; then
            ok "agent invocation: $key"
        else
            bad "agent invocation: $key"
        fi
    done
fi

# Result comparison checks semantic JSON equality only; no private values shown.
if command -v python3 >/dev/null 2>&1 && [ -x "$SCRIPT_DIR/ipfw_inventory_collect.py" ]; then
    if root_data=$("$SCRIPT_DIR/ipfw_inventory_collect.py" 2>/dev/null) &&
       user_data=$(su -m zabbix -c '/usr/local/bin/sudo -n /usr/local/scripts/zabbix/ipfw_inventory_collect.py' 2>/dev/null) &&
       ROOT_JSON="$root_data" USER_JSON="$user_data" python3 -c 'import json,os,sys; a=json.loads(os.environ["ROOT_JSON"]); b=json.loads(os.environ["USER_JSON"]); sys.exit(0 if a == b else 1)' >/dev/null 2>&1; then
        ok "inventory JSON matches root/sudo"
    else
        bad "inventory root/sudo mismatch or interpreter unavailable"
    fi
else
    bad "Python 3/inventory script unavailable"
fi

if [ "$fail" -eq 0 ]; then
    printf 'RESULT PASS (preflight only; not Zabbix import validation)\n'
else
    printf 'RESULT FAIL (check configuration locally; no IPs disclosed)\n'
fi
exit "$fail"
