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

## Servidores sem tabelas IPFW

O uso de tabelas é **opcional**. O template deve monitorar regras e contadores
mesmo quando nenhuma tabela estiver configurada.

- `ipfw table all info` com execução bem-sucedida e saída vazia: inventário
  vazio; `ipfw.tables.total=0`, `ipfw.tables.status=1` e descoberta
  `{"data":[]}`. Não são criados itens dependentes de tabelas.
- Falha do comando (erro de permissão ou falha de execução): **não** converter
  para zero; indicar falha de coleta das tabelas.
- Uma ou mais tabelas: descobrir todas as tabelas numéricas do tipo `addr`;
  a coleta atual não presume a existência de tabela 40.
- A remoção de uma tabela anteriormente descoberta deve respeitar a retenção
  configurada na descoberta do Zabbix.

É necessário validar em FreeBSD um servidor realmente sem tabelas. Caso
`ipfw table all info` retorne código de erro quando não existem tabelas,
o coletor deverá distinguir explicitamente essa condição dos erros reais
antes de considerarmos o cenário homologado.

## Gráficos (versão experimental)

O YAML contém gráficos de regras por ação, pacotes descartados/s,
bytes descartados/s e quantidade de tabelas. O LLD também inclui
um protótipo de gráfico de entradas para **cada tabela descoberta**.

Em servidores sem tabelas, o LLD retorna `{"data":[]}`: os gráficos
gerais permanecem, mas nenhum gráfico por tabela é criado.

As taxas derivam da variação de contadores e podem mostrar descontinuidades
quando os contadores forem zerados ou regras forem recriadas. A importação
do novo YAML no frontend Zabbix 7 e a compatibilidade com 8 ainda precisam
de homologação. Não realize merge ou release até essa validação.
