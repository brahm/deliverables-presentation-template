# Veículos, formatos e idiomas

O veículo é como a audiência recebe o material. O formato é o arquivo
que sai. Os dois são definidos no briefing, antes da storyline.

## Veículos e seus limites

| Veículo | Quando usar | Título | Corpo da página |
| --- | --- | --- | --- |
| `projetado` | Alguém apresenta e a audiência olha a tela | Até 14 palavras | Recomendado até 40 palavras. Acima de 80, reprova |
| `workshop` | Sessão de trabalho com exercícios e discussão | Até 14 palavras | Recomendado até 60 palavras. Acima de 110, reprova |
| `leitura` | Deck lido sem apresentador, antes ou depois da reunião | Até 22 palavras | Recomendado até 150 palavras. Acima de 250, reprova |
| `documento` | Relatório, memorando, proposta escrita, apostila | Sem limite fixo | Aviso para parágrafo acima de 130 palavras e frase acima de 40 |
| `planilha` | Bases de dados, tabelas grandes, análises e gráficos | Não se aplica | Não se aplica |

O consultor troca qualquer limite em `entregaveis/_projeto/limites.tsv`.

Um material feito para ser projetado e também lido depois são dois
materiais: o que se projeta e o documento de leitura. Escreva a storyline
uma vez e gere os dois.

## Formatos de saída

| Formato | Para quê | Fonte no harness |
| --- | --- | --- |
| PowerPoint (`pptx`) | Apresentações e decks de leitura | `conteudo.md` |
| Word (`docx`) e PDF | Relatórios, propostas escritas, apostilas, pré-leituras | `documento.md` |
| Excel (`xlsx`) | Informação em massa, bases de dados, gráficos e análises | `planilha.md` e a pasta `dados/` |
| HTML interativo (`html`) | Peça de apoio que a audiência percorre, gira ou simula, em 2D ou 3D | `interativos/NOME.html`, que já é o arquivo final |

A fonte em Markdown é a verdade do entregável. O arquivo final é gerado a
partir dela, sobre o modelo registrado em `entregaveis/_projeto/marca.md`,
e fica em `saida/`. Uma correção feita só no arquivo final se perde na
próxima geração: corrija a fonte e gere de novo.

## Gerar o arquivo

`python3 entregaveis/_harness/scripts/gerar.py ID` gera o arquivo no
formato do briefing. O gerador recusa o entregável sem briefing completo
e storyline aprovada, e o que reprova nas checagens. Com `--rascunho`
ele gera assim mesmo e carimba a marca de rascunho em todas as páginas.

| Opção | O que faz |
| --- | --- |
| `--formato pptx`, `docx`, `pdf` ou `xlsx` | Gera em outro formato |
| `--idioma es` | Gera a versão de `conteudo.es.md` ou `documento.es.md` |
| `--pdf` | Gera também o PDF |
| `--imagens` | Gera uma imagem por página em `saida/conferencia/`, para conferir |
| `--modelo ARQUIVO` | Usa este modelo em vez do registrado |
| `--layouts` | Lista os layouts do modelo de apresentação, com os campos de cada um |

O gerador pede pacotes de fora, um por formato: `python-pptx`,
`python-docx` e `openpyxl`. O PDF e as imagens pedem o LibreOffice, e as
imagens também o `pdftoppm`. Sem eles, o script diz o que falta e o
agente gera o arquivo com as ferramentas que tiver.

O que entra em cada formato:

- PowerPoint. Cada página de `conteudo.md` vira um slide em um layout
  do modelo, escolhido pelo campo `tipo`. As páginas de exemplo do
  modelo saem. Parágrafos e listas vão para o campo de texto, as notas
  para as notas de quem apresenta, uma tabela Markdown vira tabela, uma
  imagem citada entra ajustada à área e um bloco `grafico` vira gráfico
  nativo. A página que cita evidência ganha a linha de fonte, com a
  origem e a data do registro.
- Word e PDF. `documento.md` vira um documento com os estilos do
  modelo: título, títulos de seção, listas, tabelas, citações e imagens.
  O texto de exemplo do modelo sai, e ficam o cabeçalho e o rodapé. As
  evidências citadas como `[E-001]` formam a seção de fontes no fim. Um
  bloco `grafico` entra como tabela: para uma figura, gere a imagem e
  cite-a.
- Excel. `planilha.md` e os arquivos `.csv` ou `.tsv` de `dados/` viram
  uma planilha com a aba de leitura, uma aba por arquivo com cabeçalho
  fixo, filtro e números como números, o dicionário de dados e os
  gráficos nativos dos blocos `grafico`.

Um gráfico é descrito na fonte, dentro de um bloco de código com o nome
`grafico`. Em apresentação, os dados vão no bloco ou em um arquivo de
`dados/`:

~~~text
```grafico
tipo: barras
destaque: E-mail
dados:
Função | Plataformas
E-mail | 2
Dados | 1
```
~~~

`tipo` aceita `barras`, `colunas`, `linhas` e `pizza`. `destaque` é a
categoria ou a série que o título cita: ela leva a cor de destaque e o
resto fica em cinza. Uma pizza sem `destaque` sai com uma cor por
fatia. `arquivo: dados/NOME.csv` substitui a tabela do bloco. O título
do gráfico é o título da página, e por isso o campo `titulo` é
opcional. Em planilha, o bloco aponta para os dados de uma aba, com os
campos `aba`, `categorias` e `valores`.

Os números são lidos como o idioma do entregável escreve. Em português
e em espanhol, `1.234` é mil duzentos e trinta e quatro e `12,5` é doze
e meio. Em inglês vale o contrário. Quando um valor da coluna não deixa
dúvida, como `12,5`, ele decide a leitura da coluna inteira. `12%` e
`R$ 1.200` entram como números e saem no rótulo com o percentual e a
moeda. Uma célula vazia é um ponto sem valor. Qualquer outro texto em
uma coluna de valores para a geração, com a linha e a coluna do
problema. Em planilha, um código com zero à esquerda, como um CEP,
fica como texto, e nenhum texto vira fórmula.

O layout de cada tipo de página é escolhido pelo nome e pelos campos
dos layouts do modelo, em todos os slides mestres. Quando a escolha não
serve, fixe o layout por tipo na seção "Layouts do modelo" de
`_projeto/marca.md`, ou em uma página só, com o campo `layout` no
comentário da página. Vale o nome do layout ou o número que
`gerar.py --layouts` mostra, que resolve o modelo com nomes repetidos.
O título que não cabe no campo do layout sai com a letra menor, até 60%
do tamanho do modelo. Se nem assim couber, o script avisa: encurte o
título ou troque o layout. As cores de
destaque e de apoio dos gráficos vêm da linha "Cores de destaque em
gráficos" da mesma página, em código hexadecimal.

O gerador lê o fundo de cada layout: a cor ou a imagem de fundo do
layout e do slide mestre, e a forma que cobre o slide inteiro. Em fundo
escuro, o texto que ele mesmo cria sai claro: os rótulos, o eixo e a
legenda do gráfico, a linha de fonte e as caixas de texto. A tabela
ganha células escuras com letra clara. Quando a leitura não acerta,
como em um fundo de fotografia, registre a cor na linha "Cor do texto
sobre o fundo" de `_projeto/marca.md`, e ela passa a valer em todas as
páginas.

Antes de entregar um arquivo gerado, abra o resultado e olhe página por
página. Texto que estoura a caixa, gráfico cortado e fonte trocada só
aparecem no arquivo renderizado.

## HTML interativo

Uma peça interativa apoia a leitura de um entregável e não o
substitui. É um arquivo completo, sem biblioteca, estilo ou imagem de
fora, com toda imagem em SVG embutido no código, e fica
em `interativos/` dentro da pasta do entregável. Qualquer entregável
pode ter uma, depois da storyline aprovada. Quando fazer, como desenhar
e o que a checagem cobra estão em [interativo.md](interativo.md).

## Quando a planilha é o entregável certo

- A audiência vai filtrar, ordenar ou recalcular os dados.
- A tabela tem mais linhas do que cabem em uma página.
- O número de uma apresentação precisa de uma base que possa ser
  auditada.

Uma planilha de entrega tem uma aba de leitura com o que ela responde, a
origem e a data dos dados. Tem também um dicionário de dados, com a
definição e a unidade de cada coluna. Os gráficos seguem
[visual.md](visual.md): título que diz o achado, destaque no que importa.

## Idiomas

- O brief do projeto lista os idiomas dos entregáveis. Cada entregável
  pode usar um subconjunto.
- O primeiro idioma do campo `idiomas` é o principal. O conteúdo é
  escrito e aprovado nele.
- As versões ficam ao lado da principal, com o código do idioma no nome:
  `conteudo.es.md`, `documento.en.md`.
- Uma versão é reescrita para o leitor daquele idioma. Tradução palavra
  por palavra carrega a sintaxe do original.
- Os números, as fontes e os títulos de ação dizem o mesmo em todas as
  versões. O glossário tem uma linha por termo e por idioma.
- Cada versão passa pelas checagens de texto do seu idioma.

## Nomes de arquivo

Siga o padrão registrado em `entregaveis/_projeto/regras-de-material.md`.
Sem padrão definido: `cliente_entregavel_idioma_AAAA-MM-DD_vN`.
