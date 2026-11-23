---
name: pacote-proposta
description: Use quando o entregável é uma proposta comercial, uma resposta a concorrência, a apresentação oral de uma proposta, um escopo de trabalho ou um pedido de investimento, ao levantar as informações com o dono, ao montar o briefing e a storyline, ao citar casos e valores e ao revisar o material.
metadata:
  origem: harness-de-entregaveis
---

# Proposta

O conteúdo do pacote está em `entregaveis/_harness/pacotes/proposta/`.
Esta skill diz que parte abrir em cada momento. As skills do fluxo
continuam valendo, e a seção 7 de `metodo/metodo.md` dá o argumento.

1. No início, faça ao dono as perguntas da seção "O que perguntar ao
   dono no início" de `PACOTE.md`. Sem decisor identificado, diga ao
   dono que a proposta ainda não tem leitor e pergunte como descobrir.
2. No intake, parta de `pedido-de-dados.tsv`. Quase tudo vem do dono.
   Ponha em `_projeto/confidencial.tsv` os nomes de outros clientes que
   não podem aparecer.
3. Quando há pedido formal de proposta, monte a matriz de requisitos
   antes de qualquer storyline. Ela é uma planilha e vira o roteiro.
4. No briefing, a audiência é o mapa de decisores: uma linha por
   pessoa, com a dor, o critério e a objeção.
5. Na storyline, parta do esqueleto em "Esqueletos de storyline".
   Escolha dois ou três temas e registre a prova de cada um na seção
   de recursos planejados da storyline.
6. Cada afirmação usa a fonte que a tabela "Evidência que cada
   afirmação pede" aceita. Um caso só entra com a autorização do dono
   registrada em `decisoes.md`, e o resultado dele nunca é arredondado
   nem completado.
7. O valor, o prazo e os termos são do dono. Monte a estrutura das
   opções e a conta, deixe os números que faltam como lacuna visível e
   peça cada um.
8. O que está fora do escopo aparece escrito. A proposta e o escopo de
   trabalho usam as mesmas palavras.
9. Na revisão, leia a proposta no papel de cada decisor do mapa e passe
   pela lista de "Armadilhas". Rode
   `validar.py --so confidencialidade`.
10. Quem envia a proposta é o dono. Prepare o texto de envio com
    `preparar-entrega` e pare.
