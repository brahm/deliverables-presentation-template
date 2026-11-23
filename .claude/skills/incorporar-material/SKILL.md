---
name: incorporar-material
description: Use quando aparece um arquivo na pasta de entrada, quando o consultor cria ou altera à mão uma apresentação, um documento ou uma planilha fora do fluxo e quando o resumo do dia lista um arquivo sem classificar. Classifica o arquivo, leva ao lugar certo sem pedir que o consultor refaça nada e confere se ele contradiz os registros.
metadata:
  origem: harness-de-entregaveis
---

# Incorporar um material

A pasta de entrada é `entregaveis/_intake/entrada/`, fora do git. O
consultor larga ali o que chegou ou o que fez, e você leva cada arquivo
ao lugar dele. Nada fica na entrada.

1. Antes de abrir, veja em `_projeto/regras-de-material.md` se você
   pode ler o arquivo.
2. Classifique. Pergunte uma vez só quando não der para inferir.

| O arquivo é | Para onde vai | O que fazer |
| --- | --- | --- |
| Ata ou transcrição | `entregaveis/_atas/` | Siga `processar-ata` |
| Material do cliente | `_intake/materiais/` | Marque `recebido` no intake e siga `receber-materiais` |
| Entregável feito à mão | A pasta do entregável | Adote, como no passo 3 |
| Nota solta ou mensagem salva | `_intake/materiais/` | Extraia o que ela traz, como no passo 4 |

3. Entregável feito à mão, como um deck montado fora do fluxo:
   - se o entregável ainda não existe, crie a pasta com
     `python3 entregaveis/_harness/scripts/preparar.py --entregavel ID`
     e ponha o caminho do arquivo no campo `origem` do briefing;
   - registre a etapa em que ele está, sem voltar o trabalho ao começo;
   - preencha o briefing e a storyline a partir do que o arquivo diz, e
     leve ao consultor o que não der para tirar dele;
   - não reescreva o arquivo. Ele fica como está.
4. Extraia decisões, compromissos e números. As decisões seguem
   `registrar-decisao`. Os compromissos entram em `_projeto/acoes.tsv`.
   Os números entram em `_projeto/evidencias.tsv` com confiança `baixa`,
   a confirmar, e o arquivo como fonte.
5. Confira o conteúdo contra o glossário, as decisões vigentes e as
   evidências. Aponte cada contradição ao consultor, com os dois lados.
6. Quando o consultor edita à mão um arquivo que o harness gerou, a
   versão dele passa a valer. Não gere por cima. Leve a mudança à fonte
   em Markdown, ou pergunte se a fonte deixa de ser usada, e registre a
   resposta com `registrar-decisao`.
7. Diga no resumo do dia o que entrou, para onde foi e o que contradiz
   os registros.
