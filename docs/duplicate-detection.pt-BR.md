[English](duplicate-detection.md) | Português

# Inventário agregado de fontes duplicadas

Conte hosts IPv4 /32 e IPv6 /128 normalizados separadamente de prefixos CIDR. Publique apenas agregados: nunca crie um item por IP nem envie endereços brutos. Não são avaliados sobreposição de redes, política efetiva, precedência, NAT ou interfaces.

## Métricas implementadas

- `ipfw.inventory.host.unique`, `ipfw.inventory.host.occurrences`, `ipfw.inventory.host.duplicates`.
- `ipfw.inventory.prefix.unique`, `ipfw.inventory.prefix.occurrences`, `ipfw.inventory.prefix.duplicates`.
- `ipfw.inventory.status`: um somente quando as fontes necessárias forem interpretadas integralmente.

Duplicidades são ocorrências extras além da primeira de cada valor normalizado. O conteúdo de cada tabela referenciada e identificada sem ambiguidade entra uma vez; tabelas sem relação não são contadas. Referências ausentes/ambíguas e sintaxes relevantes não suportadas geram status zero, sem totais parciais publicados pelo coletor. Regras válidas sem fontes elegíveis podem gerar zero saudável; saída de regras vazia ou inválida não pode.

## Coleta e validação

O inventário é consultado a cada cinco minutos, com memória local, sem banco persistente de IPs e com espera dos comandos limitada. Lista vazia de tabelas é válida. Os testes cobrem ausência de tabelas, múltiplas referências, duplicidades entre fontes, IPv4/IPv6, CIDR, nomes/sets, referências que não bloqueiam, saída inválida e falhas de comandos.

O inventário e os itens estão implementados. Fontes complexas reais e escala ainda exigem homologação; duplicidade exata não equivale a sobreposição de redes nem a tráfego único. Veja [homologação](homologation-0.1.5.pt-BR.md).
