# FreeBSD IPFW by Zabbix Agent

Projeto de monitoramento IPFW para Zabbix 7.0; compatibilidade com Zabbix 8.0 ainda precisa de homologação.

**Estado: versão de desenvolvimento, não homologada para produção.**

## Implementado inicialmente

- Coletor somente leitura de regras IPFW e contadores de pacotes/bytes.
- Uma chave `ipfw.raw` com resposta JSON.
- Template de teste com itens dependentes, taxas e triggers básicas.

**Importante:** quantidade de regras `deny` não equivale à quantidade de IPs bloqueados. O coletor inicial não conta endereços de tabelas IPFW.

## Instalação em laboratório

1. Copie `scripts/ipfw_collect.sh` para `/usr/local/libexec/zabbix/ipfw_collect.sh`, como `root:wheel`, permissão 0755.
2. Execute `/usr/local/libexec/zabbix/ipfw_collect.sh` como root e confira o JSON.
3. Instale `agent/userparameter_ipfw.conf` no diretório incluído na configuração do agente.
4. Se necessário, use sudoers limitado **somente** ao script, protegido contra escrita pelo usuário zabbix.
5. Reinicie o agente e teste a chave `ipfw.raw` remotamente.
6. Importe o YAML no Zabbix 7.0 de laboratório.

Não é preciso Agent 2: o UserParameter também funciona no agente clássico.

## Próximas etapas

Validar formatos reais de `ipfw -a list`, `ipfw table all list` e saídas de regras dinâmicas para implementar LLD e contagem de endereços bloqueados com semântica correta.
