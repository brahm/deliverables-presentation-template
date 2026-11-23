---
name: desenhar-visual
description: Use quando uma página mostra dados, uma relação entre itens ou uma imagem, e ao gerar o arquivo final de um entregável (pptx, docx, pdf ou xlsx). Escolhe o gráfico pela pergunta e o diagrama pela relação, aplica o modelo do projeto e confere o resultado renderizado.
metadata:
  origem: harness-de-entregaveis
---

# Desenhar o visual e gerar o arquivo

As práticas estão em `entregaveis/_harness/metodo/visual.md` e os
formatos em `metodo/formatos.md`.

1. Para cada página, decida o que a audiência deve lembrar. É isso que
   recebe o destaque.
2. Dados. Escolha o gráfico pela pergunta que ele responde. Destaque o
   que o título diz e deixe o resto em cinza. O título é o achado. A
   página traz a fonte e a data. Sem 3D e sem eixo que distorce.
3. Itens que se relacionam viram um diagrama, escolhido pela relação:
   rede, segmento, junção, fluxo ou pilha.
4. Imagens. Use só as que vieram nos materiais do projeto ou que o dono
   confirmou que pode usar. Fuja da primeira ideia.
5. Marca. Aplique o modelo, as fontes e as cores de
   `_projeto/marca.md`. Use os layouts do modelo em vez de desenhar por
   cima deles. Sem modelo registrado, peça um e use um desenho neutro
   até ele chegar.
6. Gere o arquivo final a partir da fonte em Markdown com
   `python3 entregaveis/_harness/scripts/gerar.py ID --imagens`. Ele
   usa o modelo registrado, grava em `saida/` e recusa o que reprova
   nas checagens. Um gráfico é um bloco `grafico` na fonte, com o
   destaque no que o título cita. Em planilha, cada aba traz os dados
   com unidade no cabeçalho, há uma aba de leitura e um dicionário de
   dados, e os gráficos são nativos. A sintaxe está em `formatos.md`.
   Se faltar um pacote, o script diz qual: instale, ou gere com as
   ferramentas que tiver e diga isso no relatório.
7. Olhe as imagens de `saida/conferencia/`, página por página. Procure
   texto que estoura a caixa, elemento cortado ou sobreposto, layout
   errado para o tipo de página e fonte trocada. Com o modelo novo em
   mãos, rode `gerar.py --layouts` e fixe em `_projeto/marca.md` o
   layout dos tipos que o gerador escolheu mal.
8. Um problema visto no arquivo é corrigido na fonte, e o arquivo é
   gerado de novo.
9. Uma tabela com mais linhas do que a página comporta vai para a
   planilha. A página mostra o recorte que prova o título.
10. Quando a audiência entende melhor mexendo (percorrer um fluxo,
    girar uma arquitetura, testar uma premissa), a página ganha uma
    peça de apoio com a skill `construir-interativo`.
