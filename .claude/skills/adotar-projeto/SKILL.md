---
name: adotar-projeto
description: Use quando o harness foi instalado em um projeto que já estava em andamento, com apresentações, documentos, dados ou regras de agente que existiam antes dele. Levanta o que existe sem supor como o projeto foi organizado, encaixa o harness nesse desenho e pergunta ao dono só o que os arquivos não respondem e onde há conflito.
metadata:
  origem: harness-de-entregaveis
---

# Adotar um projeto em andamento

O projeto pode ser um repositório de código, uma pasta só com
apresentações ou um trabalho que segue outras regras. Não suponha nada:
levante, encaixe e pergunte.

1. Não mova, não renomeie e não apague nada do que já existe. A adoção
   só acrescenta registros.
2. Rode `python3 entregaveis/_harness/scripts/preparar.py` e depois
   `python3 entregaveis/_harness/scripts/levantar.py`. Leia a saída.
3. Leia as instruções para agentes que o projeto já tem. Elas continuam
   valendo. Onde uma delas conflita com `_harness/REGRAS.md`, anote o
   conflito para perguntar. Se o projeto já mantém decisões, lições ou
   pendências em outro lugar, deixe-as lá e escreva em `_projeto/` só o
   ponteiro para esse lugar.
4. Abra os candidatos a modelo, guia de marca, escopo, proposta e regra
   de confidencialidade. Registre cada um em `_intake/registro.tsv` com
   `estado: recebido` e o caminho onde ele já está, sem copiar. Preencha
   `_projeto/marca.md` e `regras-de-material.md` a partir deles.
5. Monte o brief com o que os arquivos mostram: cliente, tipo de
   trabalho, decisão esperada, idiomas e entregáveis. Cada inferência é
   uma suposição a confirmar.
6. Para cada entregável que já existe ou está em produção:
   - crie a pasta com `preparar.py --entregavel ID` e ponha no campo
     `origem` o caminho do arquivo atual;
   - em apresentação, rode `levantar.py --titulos ARQUIVO.pptx` e
     reconstrua a storyline com os títulos como estão hoje;
   - preencha o briefing com o que o material deixa ver e marque o
     `estado` no ponto real do trabalho;
   - rode `validar.py ID` e guarde a lista do que o material reprova.
     Não corrija ainda: o dono decide o que vale refazer.
7. Leve ao registro de evidências os números do material que têm fonte.
   Os que não têm formam a lista de lacunas.
8. Pergunte uma vez, com a resposta que você assumiria em cada item:
   - do que é o projeto e que decisão ele precisa provocar (sempre);
   - o que os arquivos não respondem;
   - cada conflito entre o que existe e o harness, com a sua
     recomendação;
   - se as storylines reconstruídas valem como aprovadas ou precisam
     mudar;
   - o que do material existente deve ser refeito pelo método.
9. Ative os pacotes do tipo de trabalho e abra o intake para o que falta,
   como nos passos 5 a 8 de `iniciar-projeto`.
10. Marque `iniciado: sim`, rode `validar.py` e relate com
    `relatar-ao-dono`: o que você encontrou, onde cada coisa foi
    encaixada, os conflitos, o que o material existente reprova e as
    perguntas.
