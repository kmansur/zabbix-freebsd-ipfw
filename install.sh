#!/bin/sh
# Net Tech IPFW Zabbix Agent installer for FreeBSD
# Usage: sh install.sh --check|--install|--uninstall|--rollback BACKUP_DIR
set -eu
umask 077
MODE=${1:---check}
[ -n "$MODE" ] || MODE=--check
case "$0" in
  /*) SCRIPT_PATH=$0 ;;
  *) SCRIPT_PATH=$(pwd)/$0 ;;
esac
REPO=$(cd "$(dirname "$SCRIPT_PATH")" && pwd -P) || exit 1
CONF=
AGENT=
SERVICE=
AGENT_FLAVOR=
resolve_agent() {
  classic_conf=/usr/local/etc/zabbix7/zabbix_agentd.conf
  agent2_conf=/usr/local/etc/zabbix7/zabbix_agent2.conf
  classic_ok=no
  agent2_ok=no
  [ -x /usr/local/sbin/zabbix_agentd ] && [ -f "$classic_conf" ] && classic_ok=yes
  [ -x /usr/local/sbin/zabbix_agent2 ] && [ -f "$agent2_conf" ] && agent2_ok=yes
  if [ "$classic_ok" = yes ] && [ "$agent2_ok" = yes ]; then
    if service zabbix_agentd onestatus >/dev/null 2>&1 && ! service zabbix_agent2 onestatus >/dev/null 2>&1; then
      agent2_ok=no
    elif service zabbix_agent2 onestatus >/dev/null 2>&1 && ! service zabbix_agentd onestatus >/dev/null 2>&1; then
      classic_ok=no
    else
      fail 'Dois agentes encontrados; desative o agente nao utilizado antes de instalar.'
    fi
  fi
  if [ "$classic_ok" = yes ]; then
    AGENT=/usr/local/sbin/zabbix_agentd
    CONF=$classic_conf
    SERVICE=zabbix_agentd
    AGENT_FLAVOR=classic
  elif [ "$agent2_ok" = yes ]; then
    AGENT=/usr/local/sbin/zabbix_agent2
    CONF=$agent2_conf
    SERVICE=zabbix_agent2
    AGENT_FLAVOR=agent2
  else
    fail 'Nenhum Zabbix Agent 7 classico ou Agent 2 instalado com configuracao encontrada.'
  fi
}
confirm_service_restart() {
  printf '\nREINICIAR o servico %s agora? Digite SIM [padrao: nao]: ' "$SERVICE" > /dev/tty
  answer=
  IFS= read -r answer < /dev/tty || fail 'Terminal interativo necessario para confirmar o reinicio.'
  [ "$answer" = SIM ]
}
offer_restart() {
  if service "$SERVICE" onestatus >/dev/null 2>&1; then
    if [ -r /dev/tty ] && [ -w /dev/tty ]; then
      if confirm_service_restart; then
        service "$SERVICE" restart || fail "Falha ao reiniciar $SERVICE"
        ok "Servico reiniciado: $SERVICE"
      else
        printf 'WARN: O servico %s nao foi reiniciado; reinicie manualmente para aplicar as alteracoes.\n' "$SERVICE"
      fi
    else
      printf 'WARN: Sem terminal interativo. Reinicie %s manualmente.\n' "$SERVICE"
    fi
  else
    printf 'WARN: %s esta parado. Nao foi iniciado automaticamente.\n' "$SERVICE"
  fi
}
DEST=/usr/local/scripts/zabbix
SUDOERS=/usr/local/etc/sudoers.d/zabbix-ipfw
BACKUPS=/var/backups/zabbix-ipfw
FILES='ipfw_collect.sh ipfw_table_discovery.sh ipfw_table_entries.sh ipfw_inventory_collect.py ipfw_duplicate_inventory.py ipfw_tables_collect.py'
DIR=
PARAM=
PY=
BACKUP=
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
ok() { printf 'OK: %s\n' "$*"; }
# Validate every existing component, including parent directories, before root writes.
trusted_path() {
  check_path=$1
  case "$check_path" in /*) ;; *) fail 'Caminho deve ser absoluto';; esac
  case "$check_path/" in */../*|*/./*|*'//'*) fail 'Caminho nao normalizado';; esac
  while [ "$check_path" != / ]; do
    [ ! -L "$check_path" ] || fail "Symlink inseguro: $check_path"
    if [ -e "$check_path" ]; then
      [ "$(stat -f %u "$check_path")" = 0 ] || fail "Proprietario inseguro: $check_path"
      mode=$(stat -f %OLp "$check_path")
      [ $((0$mode & 022)) -eq 0 ] || fail "Permissao de escrita insegura: $check_path"
    fi
    check_path=$(dirname "$check_path")
  done
}
has_include() {
  awk -v expected="$DIR/*.conf" '
    /^[[:space:]]*Include[[:space:]]*=/ {
      sub(/^[[:space:]]*Include[[:space:]]*=[[:space:]]*/, "")
      sub(/[[:space:]]*$/, "")
      if ($0 == expected) found=1
    }
    END {exit !found}' "$CONF"
}
validate_response() {
  RESPONSE="$result" "$PY" -c 'import json,os,re,sys
m=re.search(r"\[[ts]\|(.*)\]\s*$",os.environ["RESPONSE"],re.S)
try:
 d=json.loads(m.group(1)) if m else None
 if not isinstance(d,dict): raise ValueError("Expected object")
 if not (isinstance(d.get("data"),list) if sys.argv[1]=="ipfw.tables.discovery" else d.get("status")==1): raise ValueError("Unhealthy response")
except (ValueError,AssertionError): sys.exit(1)' "$key"
}
preflight() {
  [ "$(id -u)" = 0 ] || fail 'Execute como root'
  [ "$(uname -s)" = FreeBSD ] || fail 'Somente FreeBSD'
  resolve_agent
  [ -x "$AGENT" ] && [ -f "$CONF" ] || fail 'Instale e configure o Zabbix Agent'
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
    for candidate in /usr/local/bin/python3.14 /usr/local/bin/python3.13 /usr/local/bin/python3.12 /usr/local/bin/python3.11; do
      if [ -x "$candidate" ]; then PY=$candidate; break; fi
    done
  fi
  [ -n "$PY" ] && [ -x "$PY" ] || fail 'Instale Python 3'
  "$PY" -c 'import json,ipaddress' || fail 'Bibliotecas Python ausentes'
  DIR=$(awk '/^[[:space:]]*Include[[:space:]]*=/ {x=$0;sub(/^[[:space:]]*Include[[:space:]]*=[[:space:]]*/, "", x);if(x ~ /\/\*\.conf$/){sub(/\/\*\.conf$/, "", x);print x;exit}}' "$CONF")
  [ -n "$DIR" ] || DIR=$(dirname "$CONF")/$(basename "$CONF").d
  case "$DIR" in /usr/local/etc/zabbix7/*) ;; *) fail 'Include fora de /usr/local/etc/zabbix7';; esac
  PARAM=$DIR/userparameter_ipfw.conf
  for target in "$CONF" "$PARAM" "$SUDOERS" "$DEST" "$BACKUPS"; do trusted_path "$target"; done
  [ ! -L "$DIR" ] && [ ! -L "$PARAM" ] || fail 'Include/UserParameter symlink'
  ok "Preflight: Agent=$SERVICE Python=$PY UserParameters=$PARAM"
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
backup_state() {
  state=$(awk -v k="$1" '$1==k && NF==2 {print $2}' "$2/manifest")
  # Backups from the five-component installer predate this collector.
  if [ -z "$state" ] && [ "$1" = ipfw_tables_collect.py ] && [ "$(wc -l < "$2/manifest" | tr -d ' ')" = 8 ]; then
    state=absent
  fi
  printf '%s\n' "$state"
}
restore_file() {
  label=$1; path=$2; dir=$3
  state=$(backup_state "$label" "$dir")
  case "$state" in
    present)
      temp=$(mktemp "$path.restore.XXXXXXXX") || fail 'Falha no temporario'
      cp -p "$dir/$label" "$temp" && mv -f "$temp" "$path" || fail "Falha ao restaurar: $label" ;;
    absent) rm -f "$path";;
    *) fail "Backup invalido: $label";;
  esac
}
rollback() {
  dir=$1
  case "$dir" in "$BACKUPS"/backup.*|"$BACKUPS"/uninstall.*) ;; *) fail 'Backup fora do diretorio autorizado';; esac
  trusted_path "$dir"
  [ -d "$dir" ] && [ -f "$dir/manifest" ] && [ -f "$dir/paths" ] && [ ! -L "$dir" ] || fail 'Backup ausente'
  original=$(sed -n 's/^CONF=//p' "$dir/paths")
  original_param=$(sed -n 's/^PARAM=//p' "$dir/paths")
  [ "$original" = "$CONF" ] || fail 'Caminho CONF difere do backup'
  case "$original_param" in /usr/local/etc/zabbix7/*/userparameter_ipfw.conf) ;; *) fail 'Destino do backup invalido';; esac
  # Prevalidate the entire manifest and every source/destination before mutation.
  [ "$(wc -l < "$dir/paths" | tr -d ' ')" = 2 ] || fail 'Paths invalido'
  case "$(wc -l < "$dir/manifest" | tr -d ' ')" in 8|9) ;; *) fail 'Manifesto invalido';; esac
  for label in agent userparameter sudoers $FILES; do
    state=$(backup_state "$label" "$dir")
    case "$state" in
      present) [ -f "$dir/$label" ] || fail "Backup incompleto: $label"; trusted_path "$dir/$label" ;;
      absent) ;;
      *) fail "Manifesto invalido: $label" ;;
    esac
  done
  trusted_path "$dir/paths"; trusted_path "$dir/manifest"
  for target in "$CONF" "$original_param" "$SUDOERS" "$DEST"; do trusted_path "$target"; done
  [ -d "$(dirname "$original_param")" ] && [ -d "$DEST" ] || fail 'Diretorio de restauracao ausente'
  if [ -f "$dir/sudoers" ]; then visudo -cf "$dir/sudoers" >/dev/null 2>&1 || fail 'sudoers do backup invalido'; fi
  restore_file agent "$CONF" "$dir"
  restore_file userparameter "$original_param" "$dir"
  restore_file sudoers "$SUDOERS" "$dir"
  for name in $FILES; do restore_file "$name" "$DEST/$name" "$dir"; done
  visudo -cf /usr/local/etc/sudoers >/dev/null 2>&1 || fail 'sudoers restaurado invalido'
  offer_restart
  ok "Rollback: $dir"
}
install_all() {
  preflight
  install -d -o root -g wheel -m 0700 "$BACKUPS"
  BACKUP=$(mktemp -d "$BACKUPS/backup.XXXXXXXX")
  printf 'CONF=%s\nPARAM=%s\n' "$CONF" "$PARAM" > "$BACKUP/paths"
  : > "$BACKUP/manifest"
  for name in $FILES; do trusted_path "$DEST/$name"; done
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
  for name in ipfw_inventory_collect.py ipfw_tables_collect.py; do
    sed -i '' "1s|^#!/usr/bin/env python3$|#!$PY|" "$DEST/$name"
  done
  "$PY" -c 'import pathlib,sys; [compile(pathlib.Path(p).read_bytes(),p,"exec") for p in sys.argv[1:]]' "$DEST/ipfw_inventory_collect.py" "$DEST/ipfw_duplicate_inventory.py" "$DEST/ipfw_tables_collect.py" || fail 'Erro Python'
  install -o root -g wheel -m 0644 "$REPO/agent/userparameter_ipfw.conf" "$PARAM"
  has_include || printf '\n# Net Tech IPFW\nInclude=%s/*.conf\n' "$DIR" >> "$CONF"
  cat > "$SUDOERS" <<EOF
# Net Tech IPFW read-only collectors
zabbix ALL=(root) NOPASSWD: $DEST/ipfw_collect.sh
zabbix ALL=(root) NOPASSWD: $DEST/ipfw_table_discovery.sh
zabbix ALL=(root) NOPASSWD: $DEST/ipfw_table_entries.sh [a-zA-Z0-9_.-]*
zabbix ALL=(root) NOPASSWD: $DEST/ipfw_table_entries.sh [a-zA-Z0-9_.-]* [0-9]*
zabbix ALL=(root) NOPASSWD: $DEST/ipfw_inventory_collect.py
zabbix ALL=(root) NOPASSWD: $DEST/ipfw_tables_collect.py
EOF
  chown root:wheel "$SUDOERS"
  chmod 0440 "$SUDOERS"
  visudo -cf /usr/local/etc/sudoers >/dev/null 2>&1 || fail 'sudoers invalido'
  for key in ipfw.raw ipfw.tables.discovery ipfw.inventory.raw ipfw.tables.raw; do
    result=$("$AGENT" -c "$CONF" -t "$key" 2>/dev/null) || fail "Teste do agent falhou: $key"
    printf '%s\n' "$result" | grep -q 'ZBX_NOTSUPPORTED' && fail "Chave nao suportada: $key"
    validate_response || fail "JSON valido e saudavel esperado para: $key"
    ok "Chave testada: $key (saida omitida)"
  done
  offer_restart
  trap - 0
  ok "Instalacao concluida. Backup: $BACKUP"
  ok "Rollback: sh $0 --rollback $BACKUP"
}

# --uninstall: opt-in confirmation for each project-specific file.
confirm_delete() {
  printf '\nREMOVER %s? Digite SIM [padrao: nao]: ' "$1" > /dev/tty
  answer=
  IFS= read -r answer < /dev/tty || fail 'Terminal interativo necessario'
  [ "$answer" = SIM ]
}
uninstall_all() {
  [ "$(id -u)" = 0 ] || fail 'Execute como root'
  [ "$(uname -s)" = FreeBSD ] || fail 'Somente FreeBSD'
  resolve_agent
  [ -f "$CONF" ] && [ ! -L "$CONF" ] || fail 'Configuracao do agente ausente/insegura'
  [ -r /dev/tty ] && [ -w /dev/tty ] || fail 'Use um terminal interativo'
  DIR=$(awk '/^[[:space:]]*Include[[:space:]]*=/ {x=$0;sub(/^[[:space:]]*Include[[:space:]]*=[[:space:]]*/, "", x);if(x ~ /\/\*\.conf$/){sub(/\/\*\.conf$/, "", x);print x;exit}}' "$CONF")
  [ -n "$DIR" ] || DIR=$(dirname "$CONF")/$(basename "$CONF").d
  case "$DIR" in /usr/local/etc/zabbix7/*) ;; *) fail 'Include fora do escopo seguro';; esac
  PARAM=$DIR/userparameter_ipfw.conf
  for target in "$PARAM" "$SUDOERS"; do [ ! -L "$target" ] || fail "Symlink inseguro: $target"; done
  for target in "$CONF" "$PARAM" "$SUDOERS" "$DEST" "$BACKUPS"; do trusted_path "$target"; done
  for name in $FILES; do [ ! -L "$DEST/$name" ] || fail "Symlink inseguro: $DEST/$name"; done
  [ -d "$BACKUPS" ] || install -d -o root -g wheel -m 0700 "$BACKUPS"
  BACKUP=$(mktemp -d "$BACKUPS/uninstall.XXXXXXXX")
  printf 'CONF=%s\nPARAM=%s\n' "$CONF" "$PARAM" > "$BACKUP/paths"
  : > "$BACKUP/manifest"
  for name in $FILES; do trusted_path "$DEST/$name"; done
  backup_file agent "$CONF"
  backup_file userparameter "$PARAM"
  backup_file sudoers "$SUDOERS"
  for name in $FILES; do backup_file "$name" "$DEST/$name"; done
  ok "Backup antes da remocao: $BACKUP"
  changed=no
  if [ -f "$PARAM" ]; then
    if confirm_delete "$PARAM (UserParameters IPFW)"; then
      rm -f "$PARAM"; changed=yes; ok 'UserParameters removidos'
    else ok 'UserParameters preservados'; fi
  fi
  if [ -f "$SUDOERS" ]; then
    if confirm_delete "$SUDOERS (sudoers IPFW)"; then
      rm -f "$SUDOERS"; changed=yes; ok 'sudoers IPFW removido'
    else ok 'sudoers IPFW preservado'; fi
  fi
  for name in $FILES; do
    target=$DEST/$name
    if [ -f "$target" ]; then
      if confirm_delete "$target (coletor IPFW)"; then
        rm -f "$target"; changed=yes; ok "Removido: $name"
      else ok "Preservado: $name"; fi
    fi
  done
  # Only remove the Include stanza explicitly marked by the installer,
  # and only when no other .conf file in its directory still needs it.
  if grep -Fqx '# Net Tech IPFW' "$CONF" && grep -Fqx "Include=$DIR/*.conf" "$CONF"; then
    shared=no
    for target in "$DIR"/*.conf; do [ -f "$target" ] && shared=yes; done
    if [ "$shared" = no ]; then
      if confirm_delete "bloco Include Net Tech IPFW em $CONF"; then
        temp=$(mktemp "$CONF.ipfw.XXXXXXXX") || fail 'Falha no temporario'
        awk -v include="Include=$DIR/*.conf" '
          $0=="# Net Tech IPFW" {marker=1; next}
          marker && $0==include {marker=0; next}
          marker {print "# Net Tech IPFW"; marker=0}
          {print}
          END {if(marker) print "# Net Tech IPFW"}
        ' "$CONF" > "$temp"
        cat "$temp" > "$CONF"
        rm -f "$temp"
        changed=yes
        ok 'Include exclusivo removido'
      fi
    else
      ok 'Include preservado: existem outros arquivos .conf'
    fi
  fi
  if [ "$changed" = yes ]; then offer_restart; fi
  ok "Desinstalacao local concluida. Backup: $BACKUP"
  printf 'O template vinculado aos hosts no servidor Zabbix deve ser desvinculado no frontend; esta operacao nao usa API remota.\n'
  printf 'Nao foram removidos: Zabbix Agent, IPFW, Python, sudo, repositorio ou backups.\n'
}
case "$MODE" in
  --check) preflight; ok 'Diagnostico concluido; nada alterado';;
  --install) install_all;;
  --uninstall) uninstall_all;;
  --rollback) [ "$#" -eq 2 ] || fail 'Informe o diretorio de backup'; [ "$(id -u)" = 0 ] || fail 'Execute como root'; resolve_agent; rollback "$2";;
  --help) echo 'Usage: sh install.sh --check|--install|--uninstall|--rollback BACKUP_DIR';;
  *) fail 'Modo invalido';;
esac
