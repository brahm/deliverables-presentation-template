---
name: construir-storyline
description: Use quando o briefing de um entregável está completo, antes de qualquer página, e quando o consultor pede para mudar a história de um material. Monta a abertura, o resumo executivo e a sequência de títulos de ação, e leva a sequência ao consultor para aprovação.
metadata:
  origem: harness-de-entregaveis
---

# Construir a storyline

O método está em `entregaveis/_harness/metodo/metodo.md`, seção 3. O
arquivo é `storyline.md`, na pasta do entregável.

1. Releia o briefing. Junte o que já existe: o registro de evidências,
   os materiais recebidos e o esqueleto de storyline do pacote ativo.
2. Escreva a abertura: situação, complicação, pergunta e resposta. A
   resposta é a grande ideia.
3. Escolha de dois a quatro argumentos que sustentam a resposta. Eles
   não se sobrepõem e, juntos, cobrem a pergunta.
4. Escreva a sequência como títulos de ação: frases com verbo que dizem
   a mensagem de cada página. Alterne o que é e o que poderia ser.
   Termine no ganho para a audiência e em uma página do tipo `pedido`.
   Material com mais de dez páginas abre com uma página do tipo `resumo`.
5. Faça o teste dos títulos: leia só a coluna de títulos, em ordem. Ela
   precisa contar a história e levar ao pedido.
6. Corte. Cada página sustenta a grande ideia. O que é verdadeiro e não
   sustenta vai para o apêndice ou sai.
7. Preencha "Recursos planejados": o momento que a audiência vai
   lembrar, a metáfora e a frase a repetir. Sem plano, eles não entram.
8. Na coluna Evidência, ponha o id do registro ou "falta". Cada "falta"
   vira um pedido com `receber-materiais`.
9. Confira o tamanho: o conteúdo ocupa cerca de 60% do tempo disponível.
10. Escreva o resumo executivo, com a conclusão primeiro.
11. Rode `python3 entregaveis/_harness/scripts/validar.py ID --so storyline,texto`.
12. Leve ao consultor a grande ideia, a sequência de títulos e a lista do que
    falta de evidência, e peça a aprovação. Depois do sim, registre em
    `storyline.md` `aprovada: sim`, a data e as palavras dele, e mude o
    `estado` do briefing para `storyboard`. Nunca marque a aprovação por
    conta própria.

Em planilha, a sequência lista as abas e a pergunta que cada uma
responde. Em treinamento, lista os módulos e o objetivo de cada um.
