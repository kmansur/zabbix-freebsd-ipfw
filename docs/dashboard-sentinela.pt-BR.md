[English](dashboard-sentinela.md) | Português

# Sentinel | IPFW

Dashboard nativo do template, com três páginas e referências relativas ao host. Não precisa de Grafana, serviço web adicional, CSS instalado no frontend ou nova reinstalação dos coletores.

## Direção visual

Cartões grafite, números grandes, ciano para fluxo, violeta para estrutura e âmbar para tráfego negado/repetições. Cartões de saúde usam fundo verde para `OK` e vermelho para `FAILED`, com texto e horário de coleta. O tema escuro do Zabbix é recomendado para a composição; o tema é preferência do usuário e não é modificado pelo template.

O estado OK significa sucesso da coleta, não ausência de incidentes nem garantia da política de segurança. A data/hora exibida deve ser considerada: um valor antigo não comprova coleta atual. As triggers existentes continuam responsáveis pelos alertas.

## Páginas

1. **01 / Operations** — quatro cartões de contexto; destaque para pacotes/s, bytes/s e número de tabelas; quatro gráficos de tráfego, composição e evolução.
2. **02 / Textual inventory** — hosts e prefixos únicos, repetições extras, ocorrências e integridade; gráficos separados para hosts e CIDR. Não representa a política efetiva, não expande prefixos e não deduz sobreposição.
3. **03 / Table atlas** — saúde e quantidade de tabelas; grade de gráficos criados automaticamente pela descoberta, identificados por nome e set, sem IDs fixos de tabelas de teste. Sem tabelas descobertas, a grade pode ficar vazia.

## Como aplicar no Zabbix 7

1. Exporte seu template atual como backup. Se tiver personalizações locais, revise a comparação de importação antes de atualizar.
2. Importe `templates/7.0/freebsd_ipfw_by_zabbix_agent.yaml`. Nas opções avançadas, permita criar/atualizar **dashboards de template**, **mapeamentos de valores** e **gráficos**. Mantenha os itens/regras conforme a atualização normal do template.
3. Abra o host vinculado em **Monitoramento → Hosts → Dashboards** e escolha **Sentinel | IPFW**. O caminho exato pode variar com a tradução do frontend.
4. Confira as três páginas, os horários de coleta e os gráficos das tabelas descobertas. Use uma janela de uma hora para começar.

As chaves e coletores existentes são preservados. A apresentação de status recebe o mapeamento `0 → FAILED`, `1 → OK`; os valores armazenados e as expressões de trigger continuam numéricos.

## Verificação

Os testes estáticos conferem referências a itens/gráficos/protótipos e ausência de sobreposição na grade de 72 colunas. O teste de integração importa e reimporta no Zabbix 7 e verifica a presença de um dashboard com três páginas. Isso não substitui a inspeção visual do frontend do operador. A variante 8.0 continua candidata, sem homologação real.
