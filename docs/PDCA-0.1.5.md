# PDCA — auditoria técnica v0.1.5 (2026-10-19)

> Avaliação baseada nos arquivos da branch main e nas evidências de testes informadas durante a implantação. **Não equivale a auditoria de produção, importação no Zabbix 8 nem teste completo em FreeBSD.** Nunca anexar logs com endereços ou identificadores privados a issues ou PRs públicos.

## P — Plan: escopo, riscos e critérios

**Objetivo:** garantir instalação/desinstalação reproduzível e segura, integridade das métricas IPFW e funcionamento dos templates 7.0/8.0 antes de anunciar estabilidade.

| Prioridade | Área | Constatação | Ação / aceite |
| --- | --- | --- | --- |
| P0 | Instalador | CI valida sintaxe, mas não exercícios funcionais do fluxo `--install`, `--uninstall` e `--rollback` em FreeBSD | Homologar os três fluxos com snapshot, arquivo preexistente, confirmação SIM/não, falha induzida e comparação byte a byte dos backups |
| P0 | Reinício | Seleção do serviço diferencia Agent clássico/Agent 2, sem evidência de homologação do Agent 2 | Testar agentd e agent2 separadamente, incluindo serviço parado e dois agentes detectáveis |
| P0 | Inventário | Contagem é textual, não cálculo de regras efetivas; interpretações incompletas devolvem `status=0` | Validar dados reais, erros, IPv4/IPv6, tabelas e sets; verificar tratamento de `status=0` no frontend |
| P0 | Template 8 | Arquivo com `zabbix_export.version=8.0`; não há evidência de importação real | Importar em Zabbix 8, conferir schema, Latest data, LLD, gráficos e triggers |
| P1 | Script auxiliar | `tools/freebsd-preflight.sh` usa somente `zabbix_agentd` | Suporte implementado para Agent 2 e rejeição de `ZBX_NOTSUPPORTED` no preflight; aguarda homologação real |
| P1 | Limpeza | `py_compile` gera `__pycache__` e desinstalador mantém cache no diretório compartilhado | Evitar gerar cache na pasta instalada ou oferecer remoção restrita e confirmada de arquivos exclusivos do projeto |
| P1 | Configuração | `Include` pode ser acrescentado em config que já inclui o mesmo diretório com formato diferente; risco de chave duplicada | Testar configs com includes existentes e múltiplos UserParameters; não reescrever configurações compartilhadas sem inspeção |
| P1 | Backup | `--rollback` restaura arquivos, mas não há testes automatizados de falha parcial nem manifest adulterado | Criar testes em jail/VM e validar manifesto, symlinks, diretórios e permissões |
| P1 | Documentação | README em inglês e homologação estavam desatualizados | Atualizar caminhos, estado real, instalação e matriz de aceite |
| P2 | CI | Linux/Python 3.11–3.13 + YAML estático, sem runner FreeBSD nem importação do frontend | Adicionar smoke test FreeBSD e validação por API do Zabbix em ambiente descartável |

## D — Do: evidências e modificações

- Coletores shell/Python, UserParameters, templates e testes sintéticos estão versionados.
- Instalação/desinstalação interativa local e backup foram executados por operador em um host; não é evidência de funcionamento universal.
- O CI anterior aprovou os testes de Python 3.11/3.12/3.13 e sintaxe shell. CI não simula FreeBSD de verdade.
- A reorganização dos templates para `templates/7.0` e `templates/8.0` foi integrada.
- Esta revisão atualiza a documentação e inclui verificações documentais automatizáveis.

## C — Check: matriz de homologação

| Cenário | Estado/evidência atual | Evidência obrigatória para aceite |
| --- | --- | --- |
| Coleta em FreeBSD com agente clássico | Teste funcional básico informado pelo operador | Resultado de `--check`, `--install`, dados Latest data sem dados internos divulgados |
| Agent 2 | Pendente | Instalação, chaves suportadas e reinício confirmado |
| Sem tabelas | Teste básico informado pelo operador | LLD vazio sem erro, status de tabela saudável |
| Com tabelas nomeadas, numéricas e sets | Pendente em FreeBSD real | Contagem correta para todos os protótipos |
| Inventário com regras complexas | Testes sintéticos | Saída real anonimizada e critérios de `status=0` |
| Importação Zabbix 7 | Há relato de itens funcionando | Evidência de importação, protótipos, alertas e gráficos |
| Importação Zabbix 8 | Pendente | Importação sem erro e equivalência operacional verificada |
| Desinstalação/rollback | Desinstalação manual informada pelo operador | Confirmar casos de recusa, backup e restauração integral |
| Segurança e privacidade | Testes de fixtures | Revisão de permissões; não publicar endereços privados |

## A — Act: critérios de encerramento e próximos passos

**Bloqueadores de release estável:** validação de importação e dados no Zabbix 8; Agent 2 em FreeBSD; instalação/rollback em VM limpa; LLD com pelo menos duas tabelas e sets distintos; revisão de sudoers e arquivos de cache.

**Regras operacionais:** não alterar regras IPFW; não usar NOPASSWD: ALL; não remover diretórios compartilhados ou caches de terceiros; não imprimir IPs/hostnames internos em logs de CI; não declarar compatibilidade sem importação real. Manter a versão `0.1.5` como pré-homologação até coleta dessas evidências.

**Ciclo seguinte:** após cumprir os P0, executar checklist novamente, registrar evidências sanitizadas por cenário e só então decidir versão/release. Não publicar release, fazer deploy ou alterar ambientes de produção automaticamente.


### Ciclo de correção do diagnóstico (item 3)

O script `tools/freebsd-preflight.sh` identifica Agent clássico ou Agent 2, aceita argumento de configuração explícito, falha se ambos forem detectados sem escolha inequívoca e não considera `ZBX_NOTSUPPORTED` como sucesso apenas porque o comando terminou com status zero. Verifica também sintaxe do sudoers, propriedade dos scripts e equivalência de inventário root/sudo com `status=1`. **Pendente:** validar em FreeBSD real com ambos os tipos de agente, serviço parado e respostas não suportadas; o CI valida somente sintaxe e contratos estáticos.
