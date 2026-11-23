---
name: redigir-conteudo
description: Use quando o storyboard está pronto e a storyline foi aprovada, para escrever as páginas, o documento ou a especificação da planilha, e sempre que um conteúdo já escrito for alterado.
metadata:
  origem: harness-de-entregaveis
---

# Redigir o conteúdo

1. Escreva no arquivo do tipo de entregável:
   - apresentação: `conteudo.md`. Cada página começa por
     `## N. Título de ação`. A linha seguinte é um comentário com os
     campos: `<!-- tipo: dados; secao: Diagnóstico; fonte: E-003 -->`. O
     que vem depois de `Notas:` são as notas de quem apresenta;
   - documento: `documento.md`, com a evidência citada no texto como
     `[E-003]` ou em uma linha `Fonte:`;
   - planilha: `planilha.md`, com as abas, o dicionário de dados e os
     gráficos, e os dados na pasta `dados/`.
2. O título de cada página é o da storyline aprovada. O corpo prova o
   título e para aí.
3. Respeite os limites do veículo, em
   `entregaveis/_harness/metodo/formatos.md`. O que não cabe vai para as
   notas, para o apêndice ou para a planilha.
4. Preencha o campo `fonte` de toda página que traz número. Uma
   suposição é escrita como suposição na própria página.
5. Em material projetado, escreva as notas: o que quem apresenta diz, a
   transição para a página seguinte e a história que a tela não mostra.
6. Onde falta um dado, escreva "A confirmar (M-nnn)". A checagem reprova
   o material enquanto a marca existir, e é assim que deve ser.
7. Siga `entregaveis/_harness/metodo/texto.md`. Depois de cada gravação,
   o hook devolve os achados daquele arquivo: corrija na hora. Um
   recurso retórico planejado na storyline entra com o campo `recurso`.
8. Não escreva o que `_projeto/regras-de-material.md` proíbe.
9. Escreva primeiro no idioma principal. As outras versões vêm depois da
   revisão, com a skill `preparar-entrega`.
10. Ao terminar, rode `python3 entregaveis/_harness/scripts/validar.py ID`
    e siga para `humanizar-texto` e `revisar-entregavel`.
