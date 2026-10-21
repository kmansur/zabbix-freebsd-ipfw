[English](release-readiness.md) | Português

# Preparação para release

Para o pacote atual (verificação do agente em execução, Other rules, rejeições e descoberta configurável), siga o [roteiro de atualização e validação final](final-validation.pt-BR.md). A instalação dos arquivos pode terminar com aceite operacional pendente; confira os códigos de saída antes de considerar o serviço validado.

## Escopo e atualização

O projeto monitora totais de regras, tráfego negado agregado, descoberta/contagem de tabelas e inventário textual de hosts/CIDR. Não calcula política efetiva nem descobre regras individuais. Inclui gráficos e o dashboard nativo IPFW com três páginas.

Atualize coletores e UserParameters antes de importar o template. É necessária a chave `ipfw.tables.raw`, o script `ipfw_tables_collect.py` pertencente a root e sua regra sudoers. Execute o instalador, confirme reinício com `YES` e importe atualizando itens, descoberta e protótipos. Exporte separadamente o template do servidor: o instalador local não o restaura.

Uma coleta de metadados a cada cinco minutos alimenta descoberta e contadores dependentes; não há subprocesso por tabela. Chaves antigas permanecem compatíveis. Falhas omitem a descoberta para não anunciar falsamente que todas as tabelas desapareceram.

Configure `Timeout` do agente para pelo menos 10 segundos (15 recomendado nos testes) e alinhe servidor/proxy. A espera dos comandos Python é limitada a oito segundos por coleta, além de parsing e inicialização. Meça conjuntos grandes: timeout não garante desempenho.

## Correções cobertas

- Respostas text/string exigem JSON válido e saudável; Includes equivalentes com espaços são reconhecidos.
- Regras vazias/inválidas falham; regras válidas somente allow permanecem saudáveis.
- Tabelas não utilizadas e que não contêm endereços não invalidam o inventário.
- Fontes literais com um token de porta são aceitas; expressões complexas ainda falham conservadoramente.
- Metadados incompletos/inválidos são rejeitados; a leitura é única por ciclo.
- Totais ausentes são descartados, nunca convertidos em zero; falhas de tabelas têm alertas próprios.
- Instalador/preflight rejeitam symlinks, donos diferentes de root e caminhos graváveis por grupo/outros.
- Rollback valida manifesto, fontes e destinos antes de restaurar, com substituição atômica por arquivo. Não é transação de vários arquivos; falha de I/O pode exigir recuperação pelo operador e é sinalizada como erro.
- Validação e execução Python evitam novo bytecode. Caches antigos em diretório compartilhado são preservados.
- `.gitattributes` fixa finais de linha dos scripts.

## Evidência automatizada e aceite operacional

CI Linux usa Python 3.11–3.13; a VM FreeBSD 14.3 também verifica permissões nativas. Os dados são sintéticos, sem carregar IPFW nem mudar política. A integração Zabbix 7 verifica importação/reimportação via API e páginas do dashboard; não comprova dados reais ou aparência do frontend.

Esses testes não certificam Agent 2 real, equivalência de permissões no IPFW ou recuperação completa de uma instalação. Mantenha a condição de prévia até cumprir a [homologação](homologation-0.1.5.pt-BR.md):

1. Instalação limpa/atualização repetida e equivalência root/sudo.
2. Agente clássico e Agent 2, serviços ativos/parados e seleção ambígua.
3. Dados, gráficos e recuperação dos alertas no Zabbix 7; importação e execução no Zabbix 8.
4. Ausência/presença de tabelas, nomes e sets distintos, IPv4/IPv6 e fontes não suportadas.
5. Remoção confirmada/recusada, backup de arquivos presentes/ausentes e falhas induzidas.
6. Medições de memória e latência em tamanhos representativos.

CI não tem credenciais de produção ou do laboratório do operador. Nunca marque requisitos concluídos só por YAML estático nem publique credenciais ou dados brutos do firewall.
