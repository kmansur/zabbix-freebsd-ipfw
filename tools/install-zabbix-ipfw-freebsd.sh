#!/bin/sh
# Net Tech IPFW Zabbix Agent installer for FreeBSD
# Usage: sh tools/install-zabbix-ipfw-freebsd.sh --check|--install|--rollback BACKUP_DIR
set -eu
umask 077
MODE=$(printf '%s' "$*" | awk '{print $1}')
[ -n "$MODE" ] || MODE=--check
REPO=/usr/local/src/zabbix-freebsd-ipfw
CONF=/usr/local/etc/zabbix7/zabbix_agentd.conf
AGENT=/usr/local/sbin/zabbix_agentd
DEST=/usr/local/scripts/zabbix
SUDOERS=/usr/local/etc/sudoers.d/zabbix-ipfw
BACKUPS=/var/backups/zabbix-ipfw
FILES='ipfw_collect.sh ipfw_table_discovery.sh ipfw_table_entries.sh ipfw_inventory_collect.py ipfw_duplicate_inventory.py'
DIR=
PARAM=
PY=
BACKUP=
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
ok() { printf 'OK: %s\n' "$*"; }
preflight() {
  [ "$(id -u)" = 0 ] || fail 'Execute como root'
  [ "$(uname -s)" = FreeBSD ] || fail 'Somente FreeBSD'
  [ -x "$AGENT" ] && [ -f "$CONF" ] || fail 'Instale e configure o Zabbix Agent 7'
  [ -x /usr/local/bin/sudo ] && [ -x /sbin/ipfw ] || fail 'sudo ou ipfw indisponivel'
  id zabbix >/dev/null 2>&1 || fail 'Conta zabbix ausente'
  [ -f /usr/local/etc/sudoers ] && [ -d /usr/local/etc/sudoers.d ] || fail 'sudoers.d ausente'
  grep -Eq '^[[:space:]]*[#@]includedir[[:space:]]+/usr/local/etc/sudoers\.d([[:space:]]|$)' /usr/local/etc/sudoers || fail 'Inclua /usr/local/etc/sudoers.d no sudoers principal'
  visudo -cf /usr/local/etc/sudoers >/dev/null 2>&1 || fail 'sudoers principal invalido'
  [ -d "$REPO/scripts" ] && [ -f "$REPO/agent/userparameter_ipfw.conf" ] || fail 'Clone o repositorio em /usr/local/src/zabbix-freebsd-ipfw'
  for name in $FILES; do
    [ -f "$REPO/scripts/$name" ] && [ ! -L "$REPO/scripts/$name" ] || fail "Fonte ausente/insegura: $name"
    [ ! -L "$DEST/$name" ] || fail "Destino symlink: $name"
  done
  [ ! -L "$CONF" ] && [ ! -L "$SUDOERS" ] || fail 'Configuracao symlink nao permitida'
  PY=$(command -v python3 2>/dev/null || true)
  if [ -z "$PY" ]; then
    for candidate in /usr/local/bin/python3.13 /usr/local/bin/python3.12 /usr/local/bin/python3.11; do
      if [ -x "$candidate" ]; then PY=$candidate; break; fi
    done
  fi
  [ -n "$PY" ] && [ -x "$PY" ] || fail 'Instale Python 3'
  "$PY" -c 'import json,ipaddress' || fail 'Bibliotecas Python ausentes'
  DIR=$(awk '/^[[:space:]]*Include[[:space:]]*=/ {x=$0;sub(/^[[:space:]]*Include[[:space:]]*=[[:space:]]*/, "", x);if(x ~ /\/\*\.conf$/){sub(/\/\*\.conf$/, "", x);print x;exit}}' "$CONF")
  [ -n "$DIR" ] || DIR=/usr/local/etc/zabbix7/zabbix_agentd.conf.d
  case "$DIR" in /*) ;; *) fail 'Include relativo nao suportado';; esac
  PARAM=$DIR/userparameter_ipfw.conf
  [ ! -L "$DIR" ] && [ ! -L "$PARAM" ] || fail 'Include/UserParameter symlink'
  ok "Preflight: Python=$PY UserParameters=$PARAM"
}
backup_file() {
  label=$1; path=$2
  if [ -e "$path" ]; then
    [ -f "$path" ] && [ ! -L "$path" ] || fail "Destino inseguro: $path"
    cp -p "$path" "$BACKUP/$label"
    printf '%s present\n' "$label" >> "$BACKUP/manifest"
  else
    printf '%s absent\n' "$label" >> "$BACKUP/manifest"
  fi
}
restore_file() {
  label=$1; path=$2; dir=$3
  state=$(awk -v k="$label" '$1==k {print $2}' "$dir/manifest")
  case "$state" in present) cp -p "$dir/$label" "$path";; absent) rm -f "$path";; *) fail "Backup invalido: $label";; esac
}
rollback() {
  dir=$1
  [ -d "$dir" ] && [ -f "$dir/manifest" ] && [ -f "$dir/paths" ] && [ ! -L "$dir" ] || fail 'Backup ausente'
  original=$(sed -n 's/^CONF=//p' "$dir/paths")
  original_param=$(sed -n 's/^PARAM=//p' "$dir/paths")
  [ "$original" = "$CONF" ] || fail 'Caminho CONF difere do backup'
  case "$original_param" in /usr/local/etc/*/userparameter_ipfw.conf|/usr/local/etc/*/*/userparameter_ipfw.conf) ;; *) fail 'Destino do backup invalido';; esac
  restore_file agent "$CONF" "$dir"
  restore_file userparameter "$original_param" "$dir"
  restore_file sudoers "$SUDOERS" "$dir"
  for name in $FILES; do restore_file "$name" "$DEST/$name" "$dir"; done
  if service zabbix_agentd onestatus >/dev/null 2>&1; then service zabbix_agentd restart >/dev/null 2>&1 || :; fi
  ok "Rollback: $dir"
}
install_all() {
  preflight
  install -d -o root -g wheel -m 0700 "$BACKUPS"
  BACKUP=$(mktemp -d "$BACKUPS/backup.XXXXXXXX")
  printf 'CONF=%s\nPARAM=%s\n' "$CONF" "$PARAM" > "$BACKUP/paths"
  : > "$BACKUP/manifest"
  backup_file agent "$CONF"
  backup_file userparameter "$PARAM"
  backup_file sudoers "$SUDOERS"
  for name in $FILES; do backup_file "$name" "$DEST/$name"; done
  trap 'code=$?; trap - 0; if [ "$code" -ne 0 ]; then printf "Restoring backup after failure\n" >&2; rollback "$BACKUP" || :; fi' 0
  install -d -o root -g wheel -m 0755 "$DEST" "$DIR"
  for name in $FILES; do
    install -o root -g wheel -m 0755 "$REPO/scripts/$name" "$DEST/$name"
    case "$name" in *.sh) sh -n "$DEST/$name" || fail "Erro de sintaxe: $name";; esac
  done
  sed -i '' "1s|^#!/usr/bin/env python3$|#!$PY|" "$DEST/ipfw_inventory_collect.py"
  "$PY" -m py_compile "$DEST/ipfw_inventory_collect.py" "$DEST/ipfw_duplicate_inventory.py" || fail 'Erro Python'
  install -o root -g wheel -m 0644 "$REPO/agent/userparameter_ipfw.conf" "$PARAM"
  grep -Fqx "Include=$DIR/*.conf" "$CONF" || printf '\n# Net Tech IPFW\nInclude=%s/*.conf\n' "$DIR" >> "$CONF"
  cat > "$SUDOERS" <<EOF
# Net Tech IPFW read-only collectors
zabbix ALL=(root) NOPASSWD: $DEST/ipfw_collect.sh
zabbix ALL=(root) NOPASSWD: $DEST/ipfw_table_discovery.sh
zabbix ALL=(root) NOPASSWD: $DEST/ipfw_table_entries.sh [a-zA-Z0-9_.-]*
zabbix ALL=(root) NOPASSWD: $DEST/ipfw_table_entries.sh [a-zA-Z0-9_.-]* [0-9]*
zabbix ALL=(root) NOPASSWD: $DEST/ipfw_inventory_collect.py
EOF
  chown root:wheel "$SUDOERS"
  chmod 0440 "$SUDOERS"
  visudo -cf /usr/local/etc/sudoers >/dev/null 2>&1 || fail 'sudoers invalido'
  for key in ipfw.raw ipfw.tables.discovery ipfw.inventory.raw; do
    result=$("$AGENT" -c "$CONF" -t "$key" 2>/dev/null) || fail "Teste do agent falhou: $key"
    printf '%s\n' "$result" | grep -q 'ZBX_NOTSUPPORTED' && fail "Chave nao suportada: $key"
    printf '%s\n' "$result" | grep -Eq '\[t\|\{' || fail "JSON esperado para: $key"
    ok "Chave testada: $key (saida omitida)"
  done
  if service zabbix_agentd onestatus >/dev/null 2>&1; then
    service zabbix_agentd restart >/dev/null || fail 'Falha reiniciando agente'
  else
    printf 'WARN: Agente nao estava em execucao; nao iniciado automaticamente\n'
  fi
  trap - 0
  ok "Instalacao concluida. Backup: $BACKUP"
  ok "Rollback: sh $0 --rollback $BACKUP"
}
case "$MODE" in
  --check) preflight; ok 'Diagnostico concluido; nada alterado';;
  --install) install_all;;
  --rollback) [ "$#" -eq 2 ] || fail 'Informe o diretorio de backup'; [ "$(id -u)" = 0 ] || fail 'Execute como root'; rollback "$2";;
  --help) echo 'Usage: sh tools/install-zabbix-ipfw-freebsd.sh --check|--install|--rollback BACKUP_DIR';;
  *) fail 'Modo invalido';;
esac
