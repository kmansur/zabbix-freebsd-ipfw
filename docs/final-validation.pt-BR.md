[English](final-validation.md) | Português

# Atualização e validação final

Implementação e testes automatizados são diferentes do aceite operacional. Este roteiro reúne os testes restantes de laboratório. As mensagens de execução continuam em inglês.

## Ordem de atualização

1. Exporte o template do Zabbix e crie um snapshot do laboratório FreeBSD descartável.
2. Atualize o repositório e instale os coletores antes de importar o YAML:

```sh
git switch main
git pull --ff-only origin main
sh install.sh --check
sh install.sh --install
```

Confirme com `YES` somente o reinício do serviço pretendido. Anote o caminho exato do backup. A instalação agora consulta o agente em execução com `zabbix_get`: o teste `agent -t` isoladamente não comprova que o serviço recarregou a configuração.

- Código **0**: arquivos instalados e coleta pelo serviço validada.
- Código **1** após `Files installed`: falha de chave, formato ou coletor no serviço; os arquivos permanecem instalados.
- Código **2** após essa mensagem: não foi possível verificar o serviço (cliente ausente, rede/ACL/TLS ou configuração). Os arquivos permanecem instalados. Erros anteriores da instalação ainda tentam rollback.

Não enfraqueça ACLs do parâmetro Server ou TLS apenas para permitir uma consulta local. Se necessário, instale o pacote correspondente de `zabbix_get` e consulte de uma origem autorizada. A porta não padrão da configuração/includes é detectada. Endereço e TLS podem ser informados explicitamente:

```sh
sh install.sh --verify-runtime
python3 tools/check_agent_runtime.py --host AGENT_ADDRESS --port AGENT_PORT
python3 tools/check_agent_runtime.py --host AGENT_ADDRESS --port AGENT_PORT --tls-connect psk --tls-psk-identity YOUR_IDENTITY --tls-psk-file /secure/path/agent.psk
```

Há opções para certificados e `--source-address`; consulte `--help`. O diagnóstico não registra payloads nem detalhes privados do transporte. A consulta remota valida o endpoint informado, não a identidade do serviço local. Confira se endereço/porta correspondem à interface do host no Zabbix.

3. Importe `templates/7.0/freebsd_ipfw_by_zabbix_agent.yaml`, atualizando itens, descoberta, protótipos, gráficos, dashboards, macros e mapeamentos. Preserve as sobrescritas intencionais das macros do host. A variante Zabbix 8 continua candidata e precisa de validação separada.
4. Abra o dashboard IPFW. As três páginas e o UUID são preservados; Operations agora inclui Other rules e tráfego rejeitado.

## Novas métricas

| Chave | Significado |
|---|---|
| `ipfw.rules.other` | Regras fora das categorias allow/deny/reject, como count/skipto/pipe/etc. |
| `ipfw.reject.packets` | Soma dos contadores de pacotes reject/reset/unreach |
| `ipfw.reject.bytes` | Soma dos contadores de bytes reject/reset/unreach |
| `ipfw.reject.pps` | Variação por segundo do contador agregado de pacotes |
| `ipfw.reject.bytes_per_second` | Variação por segundo do contador agregado de bytes |

Confira `total = allow + deny + reject + other`. É classificação da ação, não análise completa da política. Taxas exigem duas amostras válidas e podem ser interrompidas por resets ou alteração de regras; não representam tráfego único do firewall inteiro. Importar o template sem atualizar os coletores deixa as novas métricas sem dados até a atualização local.

## Macros por host

| Macro | Padrão |
|---|---|
| `{$IPFW.RULES.INTERVAL}` | `1m` |
| `{$IPFW.INVENTORY.INTERVAL}` | `5m` |
| `{$IPFW.TABLES.INTERVAL}` | `5m` |
| `{$IPFW.RULES.NODATA}` | `5m` |
| `{$IPFW.INVENTORY.NODATA}` | `15m` |
| `{$IPFW.TABLES.NODATA}` | `15m` |
| `{$IPFW.TABLE.NAME.MATCHES}` | `.*` |
| `{$IPFW.TABLE.NAME.NOT_MATCHES}` | `^$` |
| `{$IPFW.TABLE.SET.MATCHES}` | `.*` |

Cada janela de ausência de dados deve superar seu intervalo de coleta. Os filtros de nome/ID e set são expressões regulares combinadas com o tipo de tabela addr. Exemplo: incluir `^zbx_test_.*$`, excluir `^zbx_test_ignore$`, set `^0$`. Restaure os padrões após testar. Regex inválida gera erro de descoberta e não altera tabelas do firewall.

Os filtros afetam somente itens/gráficos individuais descobertos. Total de tabelas, metadados brutos e inventário de fontes permanecem sem filtro. Recursos excluídos/perdidos seguem a política de retenção do Zabbix e podem não desaparecer imediatamente.

## Sequência de aceite no laboratório

1. **Base** — registre versões do FreeBSD, agente e servidor, tipo de agente, commit instalado e status dos mestres. Confirme a consulta ao serviço e a igualdade das categorias de regras.
2. **Tabelas e filtros** — compare contagens numéricas/nomeadas com o IPFW. Altere macros de inclusão/exclusão/set, execute o mestre de metadados e confira a descoberta. Sets distintos exigem ambiente isolado; não mude `tables_sets` no firewall existente.
3. **Tráfego rejeitado** — observe duas ou mais amostras e compare os contadores com regras/tráfego autorizados do laboratório. Não crie bloqueios em produção para testar. Confira gráficos e Other rules.
4. **Alertas/recuperação** — somente no host descartável, pare o serviço correto, aguarde além das janelas e confirme os alertas dos mestres. Reinicie o mesmo serviço e confirme novos dados e recuperação. Status verde antigo não comprova coleta atual.
5. **Falha do coletor** — em cópia com snapshot, retire temporariamente a execução de um coletor, confira dados não suportados/não saudáveis e alertas, restaure 0755 e confira recuperação. Diferentes falhas podem aparecer como status ou ausência de dados; não publique payloads.
6. **Rollback** — compare arquivos/permissões com o backup antes e depois de `sh install.sh --rollback EXACT_BACKUP_DIRECTORY`. Teste arquivos presentes/ausentes, aceitação/recusa e rejeição de backup incompleto. Restaure o template do servidor separadamente. Vários arquivos não formam uma transação atômica.
7. **Remoção/reinstalação** — execute `sh install.sh --uninstall`, confira cada `YES`/recusa, preservação de componentes compartilhados e chaves ausentes esperadas. Reinstale, confirme o serviço correto e repita a consulta ao agente em execução.
8. **Compatibilidade** — repita separadamente com agente clássico 7 e Agent 2. Registre aceite Zabbix 7 e importação/execução Zabbix 8 separadamente. Testes Docker Linux não comprovam pacotes nem caminhos de serviço do Agent 2 no FreeBSD.

Registre aprovado/reprovado por cenário, versões e evidências sanitizadas. Não publique endereços privados, nomes de hosts, regras ou credenciais. Até concluir o aceite pendente, o projeto permanece prévia de desenvolvimento.
