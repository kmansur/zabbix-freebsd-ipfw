# FreeBSD IPFW by Zabbix Agent

Projeto de monitoramento IPFW para Zabbix 7.0; compatibilidade com Zabbix 8.0 ainda precisa de homologação.

**Estado: versão de desenvolvimento, não homologada para produção.**

## Implementado inicialmente

- Coletor somente leitura de regras IPFW e contadores de pacotes/bytes.
- Uma chave `ipfw.raw` com resposta JSON.
- Template de teste com itens dependentes, taxas e triggers básicas.

**Importante:** quantidade de regras `deny` não equivale à quantidade de IPs bloqueados. O coletor inicial não conta endereços de tabelas IPFW.

## Instalação em laboratório

1. Copie `scripts/ipfw_collect.sh` para `/usr/local/scripts/zabbix/ipfw_collect.sh`, como `root:wheel`, permissão 0755.
2. Execute `/usr/local/scripts/zabbix/ipfw_collect.sh` como root e confira o JSON.
3. Instale `agent/userparameter_ipfw.conf` no diretório incluído na configuração do agente.
4. Se necessário, use sudoers limitado **somente** ao script, protegido contra escrita pelo usuário zabbix.
5. Reinicie o agente e teste a chave `ipfw.raw` remotamente.
6. Importe o YAML no Zabbix 7.0 de laboratório.

Não é preciso Agent 2: o UserParameter também funciona no agente clássico.

## Próximas etapas

Validar formatos reais de `ipfw -a list`, `ipfw table all list` e saídas de regras dinâmicas para implementar LLD e contagem de endereços bloqueados com semântica correta.

## Descoberta automática de tabelas (branch experimental)

Instale também `ipfw_table_discovery.sh` e `ipfw_table_entries.sh` em
`/usr/local/scripts/zabbix/`, pertencentes a root:wheel, permissão 0755.

O sudoers deve autorizar **somente** os três scripts de leitura do projeto, sem
`NOPASSWD: ALL`. Para `ipfw_table_entries.sh`, permita apenas um identificador
numérico de tabela como argumento, utilizando restrições apropriadas do sudoers.

Após reiniciar o agente, teste:

```sh
/usr/local/sbin/zabbix_agentd -t ipfw.tables.discovery
/usr/local/sbin/zabbix_agentd -t 'ipfw.table.entries[40]'
```

A descoberta atualmente suporta identificadores **numéricos** de tabelas do tipo
`addr`. As contagens incluem entradas de rede e não equivalem automaticamente a
IPs individuais distintos nem a bloqueios efetivos; a ação da regra associada
precisa ser verificada separadamente. Nenhuma operação altera o IPFW.

O YAML desta branch **ainda não foi homologado** por importação no frontend
Zabbix 7.0/8.0. Não substitua a configuração estável de produção sem homologação.
