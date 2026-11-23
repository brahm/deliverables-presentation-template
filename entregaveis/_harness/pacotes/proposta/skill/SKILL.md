---
name: pacote-proposta
description: Use quando o trabalho é uma proposta comercial, uma resposta a concorrência, a apresentação oral de uma proposta ou um pedido de investimento, ao iniciar o projeto, ao abrir um entregável, antes da storyline, da redação, da revisão e do envio, e quando o estado ou a lista do dia mostram uma informação que o consultor ainda não forneceu ou um controle pendente. Pede ao consultor o objetivo, o ponto de vista, a abordagem, as tarefas, o cronograma, a equipe recomendada e o preço, e mantém só os controles de uma proposta.
metadata:
  origem: harness-de-entregaveis
---

# Proposta

O conteúdo do pacote está em `entregaveis/_harness/pacotes/proposta/`.
Uma proposta não é um projeto: a governança é menor do que a do nível
enxuto, e o trabalho do agente é obter do consultor as informações de
que a proposta é feita. O método, o contexto e o conteúdo são do
consultor e ficam no domínio, com `calibrar-dominio`. As skills do fluxo
continuam valendo.

1. No início, faça ao consultor as perguntas da seção "O que perguntar
   ao consultor no início" de `PACOTE.md`, junto com as de
   `iniciar-projeto`.
2. Rode `python3 entregaveis/_harness/scripts/governanca.py --sugerir`.
   Com o sim do consultor, grave `--nivel proposta`. Não proponha status,
   linha de base, ritos nem aceite para uma proposta.
3. Mostre as informações com `governanca.py --insumos` e peça todas de
   uma vez, com a pergunta de cada uma. O consultor responde na ordem
   que preferir, em texto, em arquivo ou em conversa.
4. Para cada informação condicional, pergunte uma vez se ela vale. Sim:
   `--insumo CODIGO --pendente`. Não:
   `--insumo CODIGO --nao-se-aplica --motivo MOTIVO`.
5. Quando uma informação chega, guarde-a onde a tabela "Informações que
   o consultor fornece" diz e grave
   `--insumo CODIGO --recebido --onde ONDE --quem NOME`. Arquivo recebido
   entra pelo intake e fica fora do git. Método e modelo da casa entram
   pelo domínio e nunca voltam ao template.
6. Não escreva no lugar do consultor. Sem o objetivo, o ponto de vista e
   a abordagem não há storyline. Sem as tarefas, o cronograma e a
   equipe, a página correspondente fica com a lacuna à vista. O preço
   nunca é estimado pelo agente.
7. Se o consultor mudar uma informação já recebida, grave de novo e
   registre a mudança com `registrar-decisao`.
8. Antes do envio, confira os controles com `governanca.py --controles`.
   Um controle fecha com `--controle CODIGO --cumprido --evidencia ID
   --quem NOME`, e a confirmação vem do consultor.
9. Rode `validar.py --so confidencialidade` na revisão, com os nomes de
   outros clientes em `_projeto/confidencial.tsv`.
10. Quem envia a proposta é o consultor. Prepare o texto de envio com
    `preparar-entrega` e pare.
11. Não escreva método, roteiro de seções ou argumento a partir deste
    pacote. Leia a seção "O que este pacote não traz" e peça ao
    consultor o que faltar.
12. Quando o consultor disser que a proposta foi vendida, aplique
    `evoluir-projeto`. A fase nova escolhe o nível de governança de
    novo, e os controles do pacote do trabalho passam a valer.
