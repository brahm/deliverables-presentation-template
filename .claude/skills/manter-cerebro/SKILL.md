---
name: manter-cerebro
description: Use quando um registro, uma ata, um material ou um entregável do projeto muda, quando o estado, a lista do dia ou um hook diz que há itens a absorver, antes de escrever um briefing, uma storyline, um status ou uma resposta sobre o que o projeto sabe, e quando o consultor pergunta onde está uma informação. Busca nas notas e nos registros, leva o que o projeto aprendeu às notas do segundo cérebro com a fonte de cada afirmação e mantém o índice e o registro de atualizações.
metadata:
  origem: harness-de-entregaveis
---

# Manter o segundo cérebro

O segundo cérebro guarda o que o projeto aprendeu, em notas de Markdown
dentro de `entregaveis/_cerebro/`. O método está em
`entregaveis/_harness/metodo/segundo-cerebro.md`, e o comando é
`python3 entregaveis/_harness/scripts/cerebro.py`. O consultor nunca
precisa pedir: a atualização faz parte de cada ação do projeto.

## Antes de escrever ou responder

1. Busque com `cerebro.py --buscar TERMOS`. A busca traz as notas e as
   linhas dos registros. Para um id, use `cerebro.py --id E-008`.
2. Abra a nota que a busca trouxe e leia a seção "Em resumo". Use o que
   ela diz com a fonte que ela cita. O dado sai do registro, e a nota
   diz o que ele significa.
3. Se a busca não traz nada, diga ao consultor que o projeto não
   registrou aquilo e pergunte. Não preencha a falta com suposição.

## Depois de cada ação do projeto

4. Rode `cerebro.py --pendentes`. A lista traz o que foi registrado e
   nenhuma nota guarda, e o que mudou depois de absorvido.
5. Para cada item, decida se ele ensina algo. Ensina quando muda o que
   se sabe sobre o cliente, as pessoas, as plataformas, os processos, o
   método ou um entregável. Uma decisão operacional, um ajuste de forma
   e uma linha repetida não ensinam: saia com
   `cerebro.py --absorver ITENS --nada "motivo"`.
6. Ache a nota do assunto com `--buscar`. Atualize a que existe. Crie
   outra só quando nenhuma serve, com `cerebro.py --nova PASTA "Título"`.

   | Pasta | O que entra |
   | --- | --- |
   | `1-projetos` | O que tem prazo e fim: entregável em andamento, frente de trabalho |
   | `2-areas` | O que é acompanhado sempre: cliente, pessoas, plataformas, processos, contrato |
   | `3-recursos` | O que serve de consulta: método, conceito, referência, resumo de material |
   | `4-arquivo` | O que deixou de estar ativo |

7. Escreva na nota o que o item ensina, uma afirmação por linha, com o
   id entre parênteses. Não copie a linha do registro: diga o que ela
   significa e a que se liga. Uma suposição é escrita como suposição.
8. Refaça a seção "Em resumo" quando o que importa mudou. Ela tem até
   cinco linhas. Ligue a nota às vizinhas na seção "Ligações".
9. Registre com `cerebro.py --absorver ITENS --nota CAMINHO`. O comando
   recusa a nota que não cita o item, data a nota, escreve a linha no
   registro de atualizações e refaz o índice.

## O que não entra

10. Tarefa, mudança de data, cobrança, aviso, versão, linha de base e
    horas ficam só nos registros. O histórico das decisões também: a
    nota cita o id da decisão e diz o que ela muda.
11. Nome de outro cliente, credencial e dado que
    `entregaveis/_projeto/regras-de-material.md` proíbe não entram em
    nota. O segundo cérebro segue as mesmas regras dos registros e só
    vive em git local ou em repositório privado.
12. Nada de `entregaveis/_cerebro/` volta ao template, nem como lição
    proposta.

## Manutenção

13. Quando um entregável é entregue ou uma frente termina, leve a nota
    ao arquivo com `cerebro.py --mover NOTA 4-arquivo`.
14. No fechamento do dia, rode `cerebro.py --conferir` e trate os
    avisos: ligação quebrada, id que não existe, nota sem fonte, nota
    órfã e item fora das notas.
15. Em um projeto adotado, comece pelas notas de área: o cliente, as
    pessoas e o que é avaliado. Absorva o resto por assunto, nos dias
    seguintes, e diga ao consultor quanto falta.

## Relatório

Diga em uma frase o que entrou no segundo cérebro e em que nota. Diga
também o que ficou por absorver e por quê.
