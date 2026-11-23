---
name: usar-outro-ambiente
description: Use quando o consultor quer levar o trabalho para o Claude desktop, o ChatGPT desktop ou o Microsoft Copilot, e quando ele traz de lá o registro do projeto ou um material produzido. Monta o pacote de instruções e de conhecimento do projeto e traz de volta o que foi feito fora, sem perder o que já estava registrado.
metadata:
  origem: harness-de-entregaveis
---

# Usar o harness em outro ambiente

O guia de cada ambiente está em
`entregaveis/_harness/ambientes/LEIA-ME.md`. Fora do Claude Code não há
trava nem checagem automática: diga isso ao consultor uma vez.

## Levar

1. Pergunte para que ambiente o trabalho vai e o que ele quer fazer lá.
2. Confira `entregaveis/_projeto/regras-de-material.md`. Levar o brief,
   as decisões, as evidências e o domínio para outro ambiente é material
   saindo do projeto: quem decide é o consultor. Se as regras não dizem
   se aquele ambiente é permitido, pergunte e registre a resposta com
   `registrar-decisao`.
3. Com o sim dele, rode
   `python3 entregaveis/_harness/scripts/empacotar.py --projeto`. O
   pacote sai em `entregaveis/_ambiente/`, que fica fora do git. Sem o
   sim, ou em um projeto que não foi iniciado, indique os arquivos
   prontos de `entregaveis/_harness/ambientes/`, que não levam nada do
   projeto.
4. Diga ao consultor o que fazer, pelo passo a passo do ambiente dele:
   onde colar `instrucoes.txt`, que arquivos enviar e o limite de
   arquivos do plano. Se o limite não comporta todos, a ordem é
   `5-projeto.txt`, `1-procedimentos.txt`, `2-metodo-e-texto.txt`, o
   pacote da fase atual, `4-modelos.txt` e `3-formatos-e-visual.txt`.
5. Lembre o que ele precisa trazer de volta: o registro do projeto
   atualizado e os materiais produzidos.

## Trazer de volta

6. Leia o registro que o consultor trouxe e compare com os arquivos de
   `entregaveis/_projeto/`. Leve cada parte nova ao arquivo certo, pela
   skill do assunto: decisões com `registrar-decisao`, materiais com
   `receber-materiais`, lições com `registrar-licao`, itens adiados com
   `adiar-trabalho`. Nunca troque um registro inteiro pelo que veio de
   fora, e nunca apague uma linha.
7. O que contradiz um registro daqui vira pergunta ao consultor, com as
   duas versões lado a lado.
8. Um material produzido fora entra na pasta do entregável dele e passa
   pelas checagens daqui: rode
   `python3 entregaveis/_harness/scripts/validar.py` e aplique
   `revisar-entregavel` antes de tratá-lo como pronto. Página escrita
   fora sem storyline aprovada volta à storyline.
9. Relate com `relatar-ao-consultor`: o que entrou, o que as checagens
   acusaram e o que ficou em conflito.
