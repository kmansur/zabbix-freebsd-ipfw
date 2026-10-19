# Homologação da versão 0.1.5 (sem dados sensíveis)

## Pré-requisitos

- Ambiente de teste FreeBSD com IPFW; usuário `zabbix`.
- Agente Zabbix 7 com include de UserParameters corretamente configurado.
- Python 3 acessível pelo `secure_path` do sudo.
- Permissões `root:wheel`, modo 0755 para scripts e 0440 para sudoers.
- Backup prévio da configuração do agente e do template; nenhum teste altera regras do firewall.

## Procedimento

1. Atualizar a branch `feat/ipfw-table-lld` e instalar os scripts no diretório documentado. Não instalar antes de conferir diferenças locais.
2. Validar o sudoers com `visudo -cf /usr/local/etc/sudoers.d/zabbix-ipfw`.
3. Testar o inventário como root e pelo usuário `zabbix`; os JSONs devem apresentar números equivalentes quando o conjunto de regras não mudou.
4. Confirmar `ipfw.inventory.raw` por meio do `zabbix_agentd -t` usando explicitamente o caminho do arquivo de configuração em uso. Não duplicar UserParameters.
5. Importar `templates/7.0/freebsd_ipfw_by_zabbix_agent.yaml` em Zabbix **7** de laboratório com atualização de itens, protótipos e gráficos. Registrar qualquer erro de importação.
6. Verificar `ipfw.inventory.status=1`, `ipfw.inventory.host.unique`, `ipfw.inventory.host.occurrences` e `ipfw.inventory.host.duplicates`. O número de duplicidades é a soma das ocorrências adicionais além da primeira de cada IP.
7. Conferir o gráfico agregado de IPs únicos e duplicados.
8. Verificar LLD e gráficos em dois cenários: com tabelas e sem tabelas. Ausência de tabelas não é erro.
9. Testar, com snapshots sintéticos, regras com IPs repetidos, IPv6, prefixos de rede, fontes inválidas, referências ausentes e o mesmo identificador de tabela em sets diferentes.
10. Importar `templates/8.0/freebsd_ipfw_by_zabbix_agent.yaml` em Zabbix **8** de laboratório e validar os mesmos itens e gráficos. Não inferir compatibilidade apenas do cabeçalho ou da validação estática.

## Evidências de aceite

- Importação sem erro no frontend.
- Itens suportados e recebendo valores numéricos.
- Comparação root versus sudo idêntica no mesmo cenário.
- Inventário `status=0` quando a interpretação dos dados é incompleta, sem contadores parciais publicados como válidos.
- Ausência de IPs, endereços internos, nomes de máquinas e dumps de regras nos logs, testes e no PR público.
- CI aprovado; demonstração de atualização e de rollback do template.

## Observações

O inventário mede ocorrências textuais de fontes de bloqueio e tabelas referenciadas,
não o conjunto exato de IPs efetivamente bloqueados por toda a semântica do IPFW.
Não tenta inferir sobreposição de prefixos, precedência de regras, NAT, interfaces
ou intersecção de políticas. O parser marca entradas não reconhecidas como incompletas.
Tabelas nomeadas simples e sets distintos têm suporte implementado em LLD e contadores, ainda sem evidência de homologação real. No inventário agregado, referências ambíguas entre sets continuam sinalizadas como incompletas.

## Rollback

Caso a atualização falhe, restaure o template anterior, remova somente o novo
UserParameter `ipfw.inventory.raw` e reinicie o agente. Remover os dois scripts
Python opcionais não afeta os coletores shell originais.

## Descoberta de tabelas por ID e set

A descoberta do template agora utiliza a chave
`ipfw.table.set.entries[{#TABLE_ID},{#TABLE_SET}]`. É necessário instalar o
`UserParameter=ipfw.table.set.entries[*]` da pasta `agent/` e autorizar
a execução do script com **identificador numérico ou nome simples e set numérico** no sudoers, por exemplo:

```sudoers
zabbix ALL=(root) NOPASSWD: /usr/local/scripts/zabbix/ipfw_table_entries.sh [a-zA-Z0-9_.-]* [0-9]*
```

A expressão sudoers acima é um glob, **não** uma validação estrita dos argumentos;
o próprio script valida os dois argumentos e rejeita entradas inválidas.
Mantenha o script `root:wheel`, sem permissão de gravação para `zabbix`.
A chave antiga `ipfw.table.entries[*]` continua disponível para usos
existentes, mas é ambígua quando IDs se repetem em sets distintos.

Os testes sintéticos cobrem chaves qualificadas por set; a compatibilidade
de sintaxes reais de IPFW em FreeBSD ainda requer homologação.

## Tabelas nomeadas

O LLD e o contador aceitam nomes simples de tabelas com caracteres ASCII alfanuméricos, ponto, hífen e sublinhado. Outros identificadores são rejeitados, em vez de interpolados nos comandos. O inventário de endereços bloqueados reconhece referências `table(nome)` com essa mesma restrição; sintaxes complexas continuam sinalizadas como incompletas. Antes da homologação, valide os formatos reais das saídas no FreeBSD de laboratório.\n
## Prefixos CIDR

O template possui itens dependentes para `ipfw.inventory.prefix.unique`,
`ipfw.inventory.prefix.occurrences` e `ipfw.inventory.prefix.duplicates`,
além de gráfico separado de hosts. Prefixos /24 e /32 não são
intercambiáveis: o inventário **não** expande intervalos e não calcula
sobreposição de redes; duplicidade é somente a repetição exata do mesmo
prefixo após normalização.

## Verificação prévia automatizada (somente leitura)

O script `tools/freebsd-preflight.sh` executa verificações locais do
agente, do sudoers, da presença de scripts e da igualdade JSON entre a
execução root/sudo; ele **não imprime** IPs, regras ou saídas brutas.
Depois de revisar o arquivo, execute no FreeBSD de laboratório:

```sh
sh tools/freebsd-preflight.sh /usr/local/etc/zabbix7/zabbix_agentd.conf
```

O `PASS` desse script **não substitui** a importação do template Zabbix,
a avaliação de Latest data, os protótipos e gráficos, nem os testes de
compatibilidade com Zabbix 8. A execução deve ocorrer em uma cópia
revisada e controlada da branch de desenvolvimento, sem redeploy automático.
