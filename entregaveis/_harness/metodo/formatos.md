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

O dono troca qualquer limite em `entregaveis/_projeto/limites.tsv`.

Um material feito para ser projetado e também lido depois são dois
materiais: o que se projeta e o documento de leitura. Escreva a storyline
uma vez e gere os dois.

## Formatos de saída

| Formato | Para quê | Fonte no harness |
| --- | --- | --- |
| PowerPoint (`pptx`) | Apresentações e decks de leitura | `conteudo.md` |
| Word (`docx`) e PDF | Relatórios, propostas escritas, apostilas, pré-leituras | `documento.md` |
| Excel (`xlsx`) | Informação em massa, bases de dados, gráficos e análises | `planilha.md` e a pasta `dados/` |

A fonte em Markdown é a verdade do entregável. O arquivo final é gerado a
partir dela, sobre o modelo registrado em `entregaveis/_projeto/marca.md`,
e fica em `saida/`. Uma correção feita só no arquivo final se perde na
próxima geração: corrija a fonte e gere de novo.

Antes de entregar um arquivo gerado, abra o resultado e olhe página por
página. Texto que estoura a caixa, gráfico cortado e fonte trocada só
aparecem no arquivo renderizado.

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
