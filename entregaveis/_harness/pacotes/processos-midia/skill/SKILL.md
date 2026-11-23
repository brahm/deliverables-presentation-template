---
name: pacote-processos-midia
description: Use em projeto de definição ou redesenho de processos de mídia digital, ao iniciar o projeto, ao abrir um entregável, antes da storyline, da revisão e do envio, e quando a lista do dia ou o estado mostram um controle do tipo de projeto pendente ou a confirmar. Traz só os controles de governança deste tipo de projeto, sem método e sem etapas de trabalho.
metadata:
  origem: harness-de-entregaveis
---

# Definição de processos de mídia digital

O conteúdo do pacote está em
`entregaveis/_harness/pacotes/processos-midia/`. Ele traz a governança
deste tipo de projeto. O método, as etapas e o que é do cliente vêm do
consultor durante o projeto e ficam no domínio, com `calibrar-dominio`.
As skills do fluxo continuam valendo.

1. No início do projeto, faça ao consultor as perguntas da seção "O que
   perguntar ao consultor no início" de `PACOTE.md`, junto com as de
   `iniciar-projeto`.
2. Mostre os controles com
   `python3 entregaveis/_harness/scripts/governanca.py --controles` e
   leve a lista ao consultor, com a tabela de "Controles de governança".
3. Para cada controle a confirmar, pergunte uma vez se ele vale neste
   projeto. Sim: `--controle CODIGO --pendente`. Não:
   `--controle CODIGO --nao-se-aplica --motivo MOTIVO`.
4. Antes da storyline, da revisão e do envio, confira os controles que
   valem antes daquela etapa. O que falta vira pedido ao cliente ou
   pergunta ao consultor, e não é contornado.
5. Um controle só fecha com a evidência e com quem confirmou:
   `--controle CODIGO --cumprido --evidencia ID --quem NOME`. A
   confirmação vem do consultor ou do cliente, nunca do agente.
6. Registre papéis e prazos de resposta em `_projeto/papeis.tsv`, as
   aprovações em `_projeto/decisoes.md` e as conversas em
   `_projeto/reunioes.tsv`. A evidência do controle cita esses ids.
7. Não escreva método, etapa de trabalho ou roteiro a partir deste
   pacote. Leia a seção "O que este pacote não traz" e peça ao consultor
   o que faltar.
