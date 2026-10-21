[English](CHANGELOG.md) | Português

# Histórico de alterações

## Não lançado

- Adicionados Other rules, contadores/taxas/graficos de rejeicao, macros por host, verificacao do agente em execucao e roteiro final bilingue.
- Adicionados testes de servicos reais classico/Agent 2 para chave ausente, arquivo atualizado sem recarga e recuperacao apos reinicio.


- Interface e mensagens de execução em inglês; documentação em inglês e português. Confirmação do instalador alterada para `YES`; UUIDs e chaves preservados.
- Dashboard nativo IPFW com páginas de operação, inventário textual e atlas de tabelas, status legíveis e cores consistentes.
- Corrigidos JSON text/string do agente, Includes equivalentes e validação dos caminhos confiáveis.
- Reforçados validação dos backups e substituição atômica de cada arquivo restaurado.
- Corrigidos sucesso falso do inventário e falha causada por tabelas não referenciadas.
- Coleta única de metadados de tabelas, descoberta/contadores dependentes e alertas de falha.
- Descarte de métricas dependentes indisponíveis e limite de espera dos comandos Python.
- Evitada criação de novo bytecode; finais de linha dos scripts padronizados.
- Regressões comportamentais, CI FreeBSD nativo sem alteração de política e integração de importação Zabbix 7.
- Documentada ordem de atualização e critérios de release.
- Criados coletores somente leitura, UserParameters e template inicial Zabbix 7 com métricas dependentes, alertas, gráficos e documentação bilíngue.

Ainda não há release estável nem declaração de suporte universal a produção.
