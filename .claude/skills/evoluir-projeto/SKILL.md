---
name: evoluir-projeto
description: Use quando o projeto muda de natureza e continua sendo o mesmo projeto. Vale quando o consultor diz que a proposta foi vendida, que uma extensão ou um aditivo foi contratado ou que o trabalho passa a ser de outro tipo, e quando um pedido não cabe no tipo, no contrato ou na decisão do brief atual. Abre uma fase nova que herda o contexto e o histórico de tudo o que foi produzido.
metadata:
  origem: harness-de-entregaveis
---

# Evoluir o projeto para uma fase nova

Um projeto começa como proposta, vira o trabalho que foi vendido e muda
outra vez quando uma extensão é vendida. Cada mudança dessas é uma fase
do mesmo projeto. A fase nova herda as decisões, as evidências, o
glossário, a marca, a audiência, as lições, o domínio, os materiais e os
entregáveis das anteriores. O consultor não precisa pedir pelo nome: ele
diz o que aconteceu, e você reconhece a mudança.

## Fase nova ou mudança de escopo

1. É fase nova quando muda ao menos uma destas três coisas:
   - o contrato: algo foi vendido, assinado, renovado ou estendido;
   - o tipo de trabalho: de proposta para assessment, de assessment para
     desenho de processos, de projeto para treinamento;
   - a decisão que o projeto precisa provocar e quem a toma.
2. É mudança de escopo quando o contrato, o tipo de trabalho e a decisão
   são os mesmos, e muda a lista de entregáveis, um prazo ou uma
   audiência. Registre com `registrar-decisao` e não abra fase.
3. Diga ao consultor o que você entendeu, em uma frase, antes de mexer
   em qualquer registro. Se a mensagem serve aos dois casos, pergunte
   uma vez, com a leitura que você recomenda. Abrir uma fase é decisão
   dele.

## Abrir a fase

4. Leia `entregaveis/_projeto/fases.md` e o brief. Rode a simulação e
   mostre a saída ao consultor:

   ```sh
   python3 entregaveis/_harness/scripts/fase.py --nova --tipo "TIPO" --pacotes NOME --origem "o que aconteceu, com as palavras do consultor" --simular
   ```

   Os pacotes estão em `entregaveis/_harness/pacotes/LEIA-ME.md`. Um
   tipo de trabalho sem pacote abre a fase sem `--pacotes`.
5. Com o sim do consultor, rode o mesmo comando sem `--simular`, com
   `--data` quando a mudança foi em outro dia. O script guarda o brief
   da fase encerrada, cria a página de passagem, registra a fase, ativa
   os pacotes e devolve ao modelo as seções do brief que são da fase.

## Passar o contexto adiante

6. Escreva a página de passagem, em
   `entregaveis/_projeto/fases/fase-N/passagem.md`. Leia os entregáveis
   da fase encerrada e liste o que eles prometeram, com a origem de cada
   linha. Em uma proposta vendida, isso é o escopo, os entregáveis, os
   prazos, a equipe, as premissas, o que ficou fora e o resultado
   prometido. O que foi negociado depois vem do consultor: pergunte. O
   que a proposta só sugeriu entra como pergunta, não como compromisso.
7. Dê destino a cada entregável em aberto, com o consultor: termina como
   está, passa para a fase nova (troque o campo `fase` do briefing dele)
   ou é adiado, com `adiar-trabalho`. Os entregues ficam nas pastas
   deles, como história e como fonte. Nenhuma pasta é apagada ou
   renomeada, e o brief guardado não é reescrito.
8. Feche o brief da fase nova a partir da passagem e do brief guardado,
   e pergunte ao consultor só o que os registros não respondem. A lista
   de entregáveis previstos nasce dos compromissos. Faça as perguntas de
   início do pacote novo que a fase anterior ainda não respondeu.
9. Registre com `registrar-decisao` a abertura da fase e cada
   compromisso herdado que vale como decisão, com a origem.
10. Reveja o que muda com o tipo de trabalho:
    - a audiência: quem decidia a compra nem sempre decide no projeto;
    - o domínio, com `calibrar-dominio`: a regra que só valia na fase
      anterior ganha, em `aplica`, os entregáveis dela, e o método do
      trabalho novo entra;
    - os materiais, com `receber-materiais`: o que chegou continua
      valendo, e o pacote novo traz a lista do que pedir;
    - as regras de material e a classificação, que mudam com o contrato.
11. Rode `python3 entregaveis/_harness/scripts/estado.py` e
    `python3 entregaveis/_harness/scripts/validar.py`. A fase só está
    aberta de verdade quando a passagem e o brief não têm trecho por
    escrever.
12. Relate com `relatar-ao-consultor`: a fase que fechou, a que abriu, os
    compromissos herdados, o destino de cada entregável em aberto, o que
    você assumiu e as perguntas que ficaram.
