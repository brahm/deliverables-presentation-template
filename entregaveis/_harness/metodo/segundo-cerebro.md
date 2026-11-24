# Segundo cérebro do projeto

O segundo cérebro guarda o que o projeto aprendeu, em um lugar só e em
forma que se acha depressa. Ele serve a duas perguntas: o que sabemos
sobre isto, e de onde veio. Fica em `entregaveis/_cerebro/`, dentro do
projeto, e nunca volta ao template.

## O método

O método junta duas práticas abertas, que não pedem programa nenhum.

| Prática | O que traz | Como aparece aqui |
| --- | --- | --- |
| PARA | Quatro pastas, da mais acionável para a menos: projetos, áreas, recursos e arquivo | As pastas `1-projetos/`, `2-areas/`, `3-recursos/` e `4-arquivo/` |
| CODE | Quatro passos: capturar, organizar, destilar e expressar | Os quatro passos da seção "O ciclo" |
| Wiki mantida pelo agente | Um índice, um registro de atualizações e uma conferência periódica, com o agente como quem escreve | Os arquivos `indice.md` e `registro.md` e o comando `--conferir` |

Tudo é Markdown puro. As ligações são as do próprio Markdown, com
caminho relativo, e abrem em qualquer editor e no GitHub.

## As quatro pastas

A pergunta que decide a pasta é quando a nota vai ser usada.

| Pasta | O que entra | Exemplos em um projeto de consultoria |
| --- | --- | --- |
| `1-projetos/` | O que tem prazo e fim | Um entregável em andamento, uma frente de trabalho, uma migração que o cliente conduz |
| `2-areas/` | O que é acompanhado enquanto o projeto existir | O cliente e a organização dele, cada pessoa da audiência, cada plataforma ou processo avaliado, o contrato |
| `3-recursos/` | O que serve de consulta | Um método, um conceito, uma referência de mercado, o resumo de um material recebido |
| `4-arquivo/` | O que deixou de estar ativo | Um entregável entregue, uma frente encerrada, o que valia na fase anterior |

Uma nota muda de pasta quando muda de uso. O comando `--mover` leva a
nota e refaz as ligações.

## O que entra e o que fica nos registros

Os registros de `_projeto/` são a fonte dos dados e não são copiados. A
nota diz o que o dado significa, liga um dado ao outro e cita o id.

| O que o projeto registra | Onde fica | O que vai para a nota |
| --- | --- | --- |
| Um número ou um achado | `evidencias.tsv` | O que ele significa para a decisão, com o id |
| Uma decisão, com a data e o motivo | `decisoes.md` | O que a decisão muda no que se sabe, com o id. O registro da decisão continua lá |
| Uma reunião | `reunioes.tsv` | O que se aprendeu sobre as pessoas e o contexto |
| Um risco, uma premissa ou um problema | `riscos.tsv`, `premissas.tsv`, `issues.tsv` | O que ele diz sobre o cliente ou sobre o trabalho |
| Uma lição | `licoes.md` | A lição, quando serve além da guarda que ela criou |
| Um material recebido | o registro do intake | Um resumo do que o material traz e de onde ele está |
| O brief, a audiência, o domínio, o briefing, a storyline aprovada e o fechamento | os próprios arquivos | Quem é o cliente, quem decide, o que cada entregável quis provocar e o que aconteceu |
| Uma tarefa, uma mudança de data, uma cobrança, um aviso, uma versão, a linha de base | os registros de cada um | Nada. São movimentos do projeto, e a busca acha todos eles no registro |

A decisão e a mudança de data são o caso que mais confunde. O histórico
delas é uma lista em ordem de tempo, e o lugar de uma lista assim é o
registro. O que entra na nota é a consequência: depois de D-008, as
duas plataformas saem em março.

## A nota

Uma nota trata de um assunto e cabe em uma tela.

| Parte | O que traz |
| --- | --- |
| Cabeçalho | `titulo`, `resumo` em uma frase, `fontes` com os ids e os arquivos, `atualizada` com a data |
| Em resumo | Até cinco linhas com o que alguém precisa saber em trinta segundos |
| O que sabemos | Uma afirmação por linha, com o id do registro entre parênteses |
| Em aberto | O que falta saber ou confirmar, e com quem |
| Ligações | As notas vizinhas, com o motivo de cada ligação |

Uma suposição é escrita como suposição. Uma afirmação sem id e sem
arquivo de origem não entra.

## O ciclo

1. Capturar. Cada gravação de registro, ata, material ou entregável
   deixa um item a absorver. `cerebro.py --pendentes` mostra a lista, e
   o estado do projeto mostra a contagem.
2. Organizar. Para cada item, ache a nota que trata do assunto com
   `--buscar`. Crie uma nota nova só quando nenhuma serve, com `--nova`,
   na pasta que a tabela acima indica.
3. Destilar. Escreva na nota o que o item ensina, com o id, e refaça a
   seção "Em resumo" se o que importa mudou. Ligue a nota às vizinhas.
4. Registrar. `--absorver ITENS --nota CAMINHO` marca os itens, data a
   nota, escreve a linha no registro de atualizações e refaz o índice.
   O comando recusa a nota que não cita o item. Um item que não ensina
   nada sai com `--absorver ITENS --nada MOTIVO`.
5. Expressar. Antes de escrever um briefing, uma storyline, um status ou
   uma resposta ao consultor, busque no segundo cérebro. O que a busca
   traz entra no texto com a fonte que a nota cita.

## A busca

`cerebro.py --buscar TERMOS` procura nas notas e nos registros de uma
vez, sem diferença entre maiúscula, minúscula e acento. As notas vêm
primeiro, ordenadas por título, resumo e corpo. Depois vêm as linhas dos
registros, com o arquivo e a linha. `cerebro.py --id E-008` mostra a
linha do registro e as notas que citam o id.

## A conferência

`cerebro.py --conferir` roda com as outras checagens e só avisa.

| Aviso | O que fazer |
| --- | --- |
| Ligação que não leva a lugar nenhum | Corrija o caminho ou tire a ligação |
| Id que não existe em nenhum registro | Corrija o id ou registre a fonte |
| Nota sem fonte | Ponha o id ou o arquivo de onde vem o que ela diz |
| Nota que repete a linha de um registro | Cite o id e diga o que o dado significa |
| Seção "Em resumo" ausente ou longa | Destile até cinco linhas |
| Nota para a qual nenhuma outra aponta | Ligue a uma nota de assunto vizinho |
| Nota de entregável entregue na pasta de projetos | Leve ao arquivo com `--mover` |
| Índice que não reflete as notas | Rode `--indice` |
| Item do projeto fora das notas | Absorva |

## Fontes

O método PARA e os passos CODE são de Tiago Forte, no livro *Building a
Second Brain* (2022). O índice, o registro de atualizações e a
conferência vêm da nota "LLM wiki", de Andrej Karpathy (2026). As duas
fontes estão descritas aqui com palavras próprias.
