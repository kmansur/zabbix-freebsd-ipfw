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
5. Importar o YAML em ambiente Zabbix **7** de laboratório com atualização de itens, protótipos e gráficos. Registrar qualquer erro de importação.
6. Verificar `ipfw.inventory.status=1`, `ipfw.inventory.host.unique`, `ipfw.inventory.host.occurrences` e `ipfw.inventory.host.duplicates`. O número de duplicidades é a soma das ocorrências adicionais além da primeira de cada IP.
7. Conferir o gráfico agregado de IPs únicos e duplicados.
8. Verificar LLD e gráficos em dois cenários: com tabelas e sem tabelas. Ausência de tabelas não é erro.
9. Testar, com snapshots sintéticos, regras com IPs repetidos, IPv6, prefixos de rede, fontes inválidas, referências ausentes e o mesmo identificador de tabela em sets diferentes.
10. Validar a importação e o funcionamento em Zabbix **8** separadamente; não inferir compatibilidade apenas a partir do YAML 7.

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
Tabelas nomeadas e múltiplos sets ainda precisam de compatibilidade e evidência reais.

## Rollback

Caso a atualização falhe, restaure o template anterior, remova somente o novo
UserParameter `ipfw.inventory.raw` e reinicie o agente. Remover os dois scripts
Python opcionais não afeta os coletores shell originais.
