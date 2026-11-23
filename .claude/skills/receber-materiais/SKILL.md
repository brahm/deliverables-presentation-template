---
name: receber-materiais
description: Use quando o projeto começa, quando uma página precisa de um dado, modelo ou referência que não existe, quando o consultor entrega um material e quando o estado mostra materiais pendentes. Mantém o registro de intake, gera a lista de pedido de dados para o cliente e leva cada material recebido ao lugar em que ele é usado.
metadata:
  origem: harness-de-entregaveis
---

# Pedir e receber materiais

1. O registro é `entregaveis/_intake/registro.tsv`, com uma linha por
   material e ids `M-001`, `M-002`. Os arquivos ficam em
   `_intake/materiais/`, fora do git. Um material que já está no projeto
   é registrado com o caminho dele, sem cópia.
2. No início do projeto, peça por tipo:
   - `modelo`: os modelos de apresentação, documento e planilha;
   - `marca`: o guia de marca do cliente e o da organização do consultor;
   - `referencia`: duas ou três apresentações que mostram o padrão
     esperado;
   - `escopo`: a proposta, o contrato e o cronograma;
   - `regra`: as regras de confidencialidade e os padrões de projeto;
   - `dados`: os itens da lista de pedido de dados do pacote;
   - `entrevista`: notas e transcrições;
   - `benchmark`: os estudos que o consultor quer citar;
   - `voz`: uma amostra de texto do consultor.
3. A lista de pedido de dados fica em `_intake/pedido-de-dados.md`,
   pronta para o consultor enviar: item, a análise que precisa dele, formato,
   período, responsável no cliente e prazo. Peça só o que alguma análise
   da storyline usa. Quem envia ao cliente é o consultor.
4. Antes de abrir um material, veja em `_projeto/regras-de-material.md`
   se você pode lê-lo. Na dúvida, pergunte.
5. Quando um material chega, marque `recebido` e leve o conteúdo ao
   lugar de uso:
   - modelo e marca vão para `_projeto/marca.md`;
   - números e achados vão para `_projeto/evidencias.tsv`, com fonte e
     data;
   - termos do cliente vão para o glossário;
   - a amostra de voz orienta a skill `humanizar-texto`.
6. Dois materiais que se contradizem, ou uma definição que falta, viram
   uma pergunta na seção de conflitos de `marca.md` e no relatório.
7. Um material que falta e trava uma página fica à vista: a página leva
   "A confirmar (M-nnn)" no lugar do dado, e o item vai para
   `adiar-trabalho`. Nunca preencha a lacuna com um número plausível.
8. No relatório ao consultor, diga o que chegou, o que falta e o que cada
   falta trava.
