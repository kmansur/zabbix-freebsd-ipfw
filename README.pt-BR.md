# FreeBSD IPFW by Zabbix Agent

Template experimental de monitoramento **somente leitura** do firewall IPFW para Zabbix 7.0 e Zabbix 8.0. Vendor **Net Tech**, versão **0.1.5**. A importação no Zabbix 8 e os testes em FreeBSD real ainda dependem de homologação.

## Escopo

- Métricas de regras e contadores de tráfego via `ipfw.raw`.
- Descoberta LLD de tabelas de endereço (`addr`) por **identificador/nome e set**, incluindo IDs iguais em sets diferentes.
- Contagem de entradas em cada tabela e protótipos de gráficos.
- Inventário agregado de hosts IPv4/IPv6 bloqueados e prefixos CIDR, com valores únicos, ocorrências e duplicatas exatas.
- Alertas de falha ou ausência da coleta.

O inventário **não calcula o conjunto efetivamente bloqueado** levando em conta precedência, interseção de regras, sobreposição CIDR, NAT ou interfaces. Quando a saída do IPFW não pode ser interpretada com segurança, o coletor sinaliza `status=0` em vez de publicar contagens parciais.

## Instalação apenas em laboratório

Os scripts de `scripts/` utilizados pelo agente devem ser instalados em `/usr/local/scripts/zabbix/`, pertencentes a `root:wheel` e com modo 0755, sem permissão de gravação pelo usuário do Zabbix. O arquivo `agent/userparameter_ipfw.conf` deve ser colocado no diretório **efetivamente incluído** pelo agente, sem duplicar chaves existentes.

São necessários os coletores:

- `ipfw_collect.sh`
- `ipfw_table_discovery.sh`
- `ipfw_table_entries.sh`
- `ipfw_inventory_collect.py` e `ipfw_duplicate_inventory.py`

O inventário requer Python 3 acessível via shebang `/usr/bin/env python3` no ambiente de execução do sudo. Se FreeBSD expuser somente o executável versionado (por exemplo, `/usr/local/bin/python3.12`), ajuste o shebang **para o caminho absoluto correto** no host de laboratório antes de conceder acesso no sudoers. Não é obrigatório criar links simbólicos.

Conceda apenas autorização de sudo para os coletores de leitura específicos. O script de contagem aceita um identificador numérico ou nome simples de tabela e, opcionalmente, um set numérico; o script valida os parâmetros antes de invocar o IPFW. Padrões do sudoers são globs, não substituem a validação de argumentos. Consulte `docs/homologation-0.1.5.md` antes de implantar.

Após configurar o agente, confira a sintaxe com os caminhos reais do FreeBSD:

```sh
visudo -cf /usr/local/etc/sudoers.d/zabbix-ipfw
/usr/local/sbin/zabbix_agentd -c /usr/local/etc/zabbix7/zabbix_agentd.conf -t ipfw.raw
/usr/local/sbin/zabbix_agentd -c /usr/local/etc/zabbix7/zabbix_agentd.conf -t ipfw.tables.discovery
/usr/local/sbin/zabbix_agentd -c /usr/local/etc/zabbix7/zabbix_agentd.conf -t 'ipfw.table.set.entries[10,0]'
/usr/local/sbin/zabbix_agentd -c /usr/local/etc/zabbix7/zabbix_agentd.conf -t ipfw.inventory.raw
```

Substitua a chave de tabela pelo identificador/set realmente existente no ambiente de teste. O UserParameter antigo `ipfw.table.entries[*]` continua disponível para compatibilidade, mas um ID sem set será rejeitado quando for ambíguo.

## Template e testes

Importe `templates/7.0/freebsd_ipfw_by_zabbix_agent.yaml` no Zabbix 7 ou `templates/8.0/freebsd_ipfw_by_zabbix_agent.yaml` no Zabbix 8, inicialmente em laboratório. O YAML da versão 8 usa o cabeçalho `version: '8.0'` e requer homologação de importação real no frontend, além dos testes sintéticos. O coletor de tabelas sem nenhuma tabela deve retornar `{"data":[]}` quando a consulta IPFW tiver sucesso; erros da consulta não são convertidos em zero.

Para executar os testes sintéticos em um ambiente de desenvolvimento com Python 3 e PyYAML:

```sh
python3 -m pip install 'PyYAML==6.0.2'
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

O CI executa esses testes com Python 3.11, 3.12 e 3.13, mas não substitui a validação em FreeBSD.

**Estado:** candidato de desenvolvimento, aguardando homologação; não realizar merge nem release antes do aceite. Consulte o roteiro em `docs/homologation-0.1.5.md`.


## Instalador de laboratório para FreeBSD

O arquivo real de instalação está em `install.sh`.
Ele detecta o diretorio raiz do checkout automaticamente e exige que
FreeBSD, IPFW, Zabbix Agent clássico 7, sudo e Python 3 já estejam instalados.
O sudoers principal deve incluir `/usr/local/etc/sudoers.d`.

Execute como root:

```sh
cd /usr/local/src/zabbix-freebsd-ipfw
git switch main
git pull --ff-only origin main
sh install.sh --check
sh install.sh --install
```

A instalação cria backup em `/var/backups/zabbix-ipfw/backup.XXXXXXXX`.
Se necessário, restaure os arquivos usando o caminho **exato** exibido:

```sh
sh install.sh --rollback /var/backups/zabbix-ipfw/backup.XXXXXXXX
```

O instalador não instala pacotes, não muda regras IPFW nem importa o template
automaticamente. Verifique os itens e a descoberta LLD no Zabbix após a instalação.


## Desinstalação interativa

Para remover os componentes **locais** deste template, execute como root:

```sh
sh install.sh --uninstall
```

O desinstalador cria primeiro um backup em `/var/backups/zabbix-ipfw/` e pergunta **individualmente** antes de excluir o arquivo de UserParameters, o arquivo de sudoers, cada um dos cinco coletores e, somente se seguro, o bloco `Include` criado pelo instalador. Apenas a resposta literal `SIM` autoriza cada exclusão; qualquer outra resposta preserva o item. Ao final, pergunta se deve reiniciar o agente.

Não remove Zabbix Agent, Python, sudo, IPFW, repositório nem backups, pois podem ser compartilhados com outras aplicações. Não altera regras de firewall. A desvinculação ou exclusão do template e seus itens no servidor Zabbix deve ser feita separadamente pelo frontend; o script **não acessa a API**.
