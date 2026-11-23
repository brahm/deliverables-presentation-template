# Guia de uso

Este guia mostra tudo o que o harness faz e como usar cada recurso em um
projeto. Ele serve a quem está no primeiro projeto e a quem já conduziu
dezenas. Quem está começando segue a ordem das seções. Quem já tem
prática vai direto à tabela de recursos e à seção de ajustes.

A instalação está no `README.md` e no `INSTALL.md` do repositório do
template. Antes de começar, o agente confere se a máquina tem o que o
harness precisa e resolve com você o que faltar: veja a seção "Ambiente
da máquina".

## A ideia em um minuto

Você conversa com o agente como conversa com alguém do time. Você diz do
que é o projeto, entrega os materiais, pede os entregáveis e aprova a
história de cada um. O agente planeja, escreve, confere e mantém os
registros. Você nunca precisa citar uma skill nem decorar um comando.

Três coisas são sempre suas:

- o objetivo, o escopo, a audiência e a grande ideia de cada material;
- a aprovação da storyline, antes de qualquer página;
- tudo o que sai do projeto ou não pode ser desfeito, como o envio ao
  cliente.

O que você deixa em aberto, o agente decide, registra como decisão
assumida e mostra no relatório. Você confirma ou troca.

## O caminho de um entregável

| Etapa | O que você faz | O que o agente faz | Onde fica |
| --- | --- | --- | --- |
| 1. Projeto | Diz do que é o projeto e que decisão ele precisa provocar | Pergunta o que falta, fecha o brief e ativa os pacotes do tipo de trabalho | `_projeto/brief.md` |
| 2. Materiais | Entrega modelo, guia de marca, escopo, dados e regras do cliente | Registra cada material, pede o que falta e gera a lista de pedido de dados | `_intake/registro.tsv` |
| 3. Domínio | Entrega referências, métodos e o contexto do trabalho | Escreve o método do projeto, as regras de checagem e os casos de teste | `_dominio/` |
| 4. Briefing | Pede um entregável | Define audiência, grande ideia, pedido, resistências e veículo | `ID/briefing.md` |
| 5. Storyline | Lê a sequência de títulos e aprova, ou pede mudança | Monta a abertura, o resumo e os títulos de ação | `ID/storyline.md` |
| 6. Storyboard | | Decide o que cada página mostra e que evidência usa | `ID/storyboard.md` |
| 7. Redação | | Escreve as páginas, o documento ou a planilha | `ID/conteudo.md`, `documento.md` ou `planilha.md` |
| 8. Revisão | | Roda as checagens, aplica a rubrica e registra a revisão | `ID/revisao.md` |
| 9. Arquivo final | Abre e confere | Gera PowerPoint, Word, PDF ou Excel sobre o seu modelo | `ID/saida/` |
| 10. Entrega | Apresenta ou envia | Prepara versão curta, perguntas previstas, roteiro e texto de envio | `ID/entrega.md` |
| 11. Fechamento | Conta o que aconteceu na reunião | Registra decisões e lições e prepara o follow-up | `_projeto/decisoes.md`, `_projeto/licoes.md` |

`ID` é a pasta do entregável, dentro de `entregaveis/`. Um projeto
fictício inteiro, com todas essas etapas preenchidas, está na pasta
[exemplo do template](https://github.com/brahm/deliverables-presentation-template/tree/main/exemplo).

## O que dizer em cada momento

As frases abaixo são exemplos. Use as suas palavras.

| Momento | Uma frase que funciona |
| --- | --- |
| Começar um projeto | "Este projeto é um assessment de martech para um varejista. A diretoria precisa decidir quais plataformas renova em março." |
| Trazer um projeto em andamento | "Este projeto já está na quarta semana. Levante o que existe aqui antes de propor qualquer coisa." |
| Entregar um material | "Pus o modelo de apresentação do cliente e os contratos na pasta de materiais." |
| Calibrar o método | "Uso este roteiro de avaliação e esta escala de maturidade. Aplique em todos os entregáveis." |
| Pedir um entregável | "Preciso de uma leitura executiva de 30 minutos para a diretoria, no dia 5." |
| Aprovar a história | "Aprovada. Só ponha o custo antes da nota de maturidade." |
| Pedir uma peça interativa | "A diretoria entende melhor mexendo. Faça um simulador do custo evitado." |
| Pedir outro idioma | "Preciso desta apresentação também em espanhol." |
| Adiar algo | "A análise de subuso fica para depois dos relatórios de uso." |
| Corrigir o agente | "A diretoria diz plataforma, não ferramenta. Não repita." |
| Começar o dia | "O que temos para hoje?" |
| Entregar uma ata | "Salvei a ata da reunião de ontem na pasta de atas." |
| Contar uma reunião sem ata | "Falei com a diretora financeira hoje. Ela aprovou o prazo e pediu o custo por loja." |
| Responder a um prazo vencido | "A nomeação fica para o dia 20, porque o diretor está de férias." |
| Dispensar algo | "O relatório de uso não é mais necessário. O cliente desistiu dessa frente." |
| Contar um follow-up | "Cobrei a diretora financeira hoje. Ela responde até sexta." |
| Confirmar uma aprovação | "A diretora de marketing aprovou o plano de migração." |
| Escolher a governança | "Fique no nível enxuto e inclua a pauta da reunião semanal." |
| Trazer um pedido fora do combinado | "O cliente pediu o custo por loja, que não estava no escopo." |
| Trazer algo feito à mão | "Montei esta planilha de custos no fim de semana. Está na pasta de entrada." |
| Encerrar o dia | "Por hoje é isso." |
| Fechar um entregável | "Apresentei hoje. Aprovaram a saída de duas plataformas e perguntaram pela multa." |
| Mudar a natureza do projeto | "A proposta foi vendida. Agora começa o diagnóstico." |
| Levar a outro aplicativo | "Vou continuar isto no Copilot. Monte o pacote." |
| Saber onde tudo está | "Como está o projeto?" |
| Lembrar de algo | "O que sabemos sobre a multa de rescisão?" |

## Os recursos, um por um

### História antes de página

Cada entregável tem uma audiência que decide, uma grande ideia em uma
frase e um pedido com dono e prazo. A storyline conta a história inteira
em títulos de ação, e você a aprova antes de existir qualquer página. O
agente não consegue gravar páginas fora dessa ordem. O método completo
está em [metodo.md](metodo/metodo.md).

### Registros do projeto

O agente mantém os registros em `entregaveis/_projeto/`. Eles são a
memória do projeto: uma sessão nova lê os registros e continua de onde a
anterior parou.

| Registro | O que guarda |
| --- | --- |
| `brief.md` | O que é o projeto, o tipo de trabalho, os idiomas e a classificação dos materiais |
| `audiencia.md` | Quem decide, quem influencia, o que cada um quer e teme |
| `decisoes.md` | Toda decisão, sua ou assumida pelo agente, sem apagar nenhuma |
| `evidencias.tsv` | Cada número e cada achado, com fonte, data e confiança |
| `glossario.tsv` | Os termos do projeto e as variantes a evitar, por idioma |
| `marca.md` | Modelos, fontes, cores e marcações que o projeto usa |
| `regras-de-material.md` | O que pode ser citado, o padrão de nome de arquivo e os cuidados do cliente |
| `confidencial.tsv` | Termos que não podem aparecer em nenhum entregável |
| `adiados.tsv` | O que foi pedido e não foi feito, com o motivo |
| `licoes.md` | O que deu errado e a guarda que impede a repetição |
| `limites.tsv` | Os limites de palavras por veículo, quando você muda o padrão |
| `fases.md` | As fases do projeto: proposta, trabalho vendido, extensão |
| `reunioes.tsv` e `ritos.tsv` | As atas processadas, as reuniões sem ata e as reuniões que se repetem |
| `acoes.tsv` | As tarefas, os marcos, as decisões pedidas e as aprovações, com dono e prazo |
| `riscos.tsv` | Os riscos, com causa, efeito e dono |
| `prazos.tsv` | O histórico de cada data mudada |
| `diario.md` | O fechamento de cada dia de trabalho |

### Materiais e pedido de dados

O agente pede o que falta e não inventa. Cada material pedido ou
recebido tem uma linha em `_intake/registro.tsv`, com dono, prazo e
estado. Os arquivos recebidos ficam em `_intake/materiais/`, fora do
git. Um dado que não chegou vira uma lacuna visível na página e um item
adiado.

### Domínio do projeto

O template não traz método de consultoria pronto. Você entrega as suas
referências, escalas e critérios, e o agente escreve o domínio em
`entregaveis/_dominio/`: o método, as regras de checagem e, para cada
regra, um caso que ela acusa e um que ela deixa passar. Essas regras
passam a rodar em todo entregável do projeto. O domínio fica no projeto
e nunca volta ao template.

### Pacotes por tipo de projeto

Sete pacotes adaptam o harness ao tipo de trabalho: transformação de
marketing, martech e adtech, mídia, retail media, processos agênticos,
proposta e treinamento. Cada um traz perguntas a fazer, entregáveis
típicos, esqueletos de storyline, lista de pedido de dados, roteiro de
entrevista e glossário. O agente ativa os que servem quando você diz do
que é o projeto. Os pacotes se somam. A lista está em
[pacotes/LEIA-ME.md](pacotes/LEIA-ME.md).

### Checagens automáticas

A cada arquivo gravado, o agente recebe de volta o que corrigir. As
checagens pegam título que é rótulo, texto acima do limite do veículo,
número sem fonte, termo fora do glossário, sigla sem definição, material
confidencial, falta da marcação obrigatória e as regras do seu domínio.
A tabela completa está em [kit.md](kit.md).

### Texto sem vício de IA

Todo texto de entregável passa por uma lista de vícios de texto gerado,
em português, espanhol e inglês: fecho que repete, contraste vazio,
trio forçado, importância inflada. O agente corrige
antes de mostrar o texto a você. Um recurso retórico só fica quando foi
planejado na storyline. As práticas estão em [texto.md](metodo/texto.md).

### Formatos e arquivo final

A fonte de cada entregável é um arquivo Markdown, e o arquivo final é
gerado a partir dela.

| Você precisa de | O harness gera | A partir de |
| --- | --- | --- |
| Apresentação ou deck de leitura | PowerPoint, com PDF opcional | `conteudo.md` |
| Relatório, proposta escrita ou apostila | Word e PDF | `documento.md` |
| Base de dados, análise ou tabela grande | Excel, com aba de leitura e dicionário de dados | `planilha.md` e a pasta `dados/` |
| Peça que a audiência percorre ou simula | HTML em arquivo único | `interativos/NOME.html` |

O PowerPoint e o Word saem sobre o modelo do projeto, com os layouts, as
fontes e as cores dele. Sem modelo registrado, o arquivo sai em um
desenho neutro e o agente pede o modelo. Gráficos são nativos, com o
destaque no que o título diz. Uma correção é feita na fonte, e o arquivo
é gerado de novo. Os detalhes estão em [formatos.md](metodo/formatos.md)
e em [visual.md](metodo/visual.md).

### Veículo e limites

O veículo define quanto texto cabe. Uma página projetada aceita até 14
palavras no título e cerca de 40 no corpo. Um deck de leitura aceita
mais, e um documento não tem limite fixo. Você muda qualquer limite em
`_projeto/limites.tsv`.

### Peças interativas

Quando a audiência entende melhor mexendo, o agente constrói uma peça
em HTML, em 2D ou 3D, a partir de três bases: fluxo, camadas e
simulador. A peça é um arquivo só, abre sem internet e apoia uma página
do entregável sem substituí-la. O método está em
[interativo.md](metodo/interativo.md).

### Idiomas

As instruções e os registros ficam em português. Os entregáveis saem em
português, espanhol e inglês, conforme o brief. O conteúdo é escrito e
aprovado no idioma principal. As outras versões vêm depois, reescritas
para o leitor de cada idioma, e passam pelas checagens de texto dele.

### Revisão

Antes de dizer que um material está pronto, o agente roda as checagens e
aplica uma rubrica de 30 critérios no papel do decisor mais difícil:
história, audiência, evidência, página, texto e entrega. O resultado
fica em `revisao.md`. Uma mudança no conteúdo depois da revisão pede
revisão nova. A rubrica está em [rubrica.md](metodo/rubrica.md).

### Entrega e fechamento

Para a entrega, o agente prepara o caminho de cinco minutos, as
perguntas difíceis com resposta, o roteiro por minuto, a pré-leitura e o
texto de envio. Quem envia é você. Depois da reunião, você conta o que
aconteceu, e o agente registra as decisões, as lições e o follow-up.

### Decisões, adiados e lições

Nada some em silêncio. Uma decisão sua fica registrada com as suas
palavras. Uma decisão que o agente tomou por você fica como `Vigente
(assumida)` até você confirmar. O que foi pedido e não foi feito ganha
uma linha com o motivo. Uma correção sua vira uma lição com guarda: de
preferência uma checagem, que impede a repetição.

### Atas e reuniões

Você salva a ata ou a transcrição em `entregaveis/_atas/`, em texto,
Markdown, Word ou legenda de gravação. O agente acha o arquivo novo, lê
e leva cada trecho ao registro certo, sempre com a reunião de origem:
decisão, tarefa com dono e prazo, risco, dado novo, pedido de material.
Você vê o que mudou no resumo do dia e corrige ali. Só espera o seu sim
o que toca o contrato ou sai do projeto: escopo novo, data de base,
aceite e mensagem ao cliente. Uma ata corrigida é lida de novo só no
trecho que mudou. Sem ata, você conta a reunião e o agente registra do
mesmo jeito, marcando que a fonte é o seu relato. A pasta fica fora do
git.

### Rotina do dia

No começo do dia, o agente mostra a lista do dia, descrita a seguir. No
fim, grava no diário o que foi feito e o que fica para amanhã. As reuniões que se repetem ficam em
`_projeto/ritos.tsv`, e o agente avisa quando uma delas passa sem ata.
Em uma pausa do projeto, diga até quando, e os avisos param até essa
data.

### Segundo cérebro

O segundo cérebro guarda o que o projeto aprendeu, em notas curtas de
Markdown dentro de `entregaveis/_cerebro/`. Você não precisa pedir: a
cada registro, ata, material ou entregável que muda, o agente atualiza a
nota do assunto. Para lembrar de algo, pergunte, e o agente busca nas
notas e nos registros de uma vez.

As notas ficam em quatro pastas, pela ordem em que são usadas.

| Pasta | O que guarda |
| --- | --- |
| `1-projetos/` | O que tem prazo e fim: cada entregável em andamento e cada frente |
| `2-areas/` | O que é acompanhado sempre: o cliente, as pessoas, as plataformas, os processos |
| `3-recursos/` | O que serve de consulta: métodos, conceitos e o resumo de cada material |
| `4-arquivo/` | O que deixou de estar ativo |

Cada nota abre com um resumo de até cinco linhas e cita o id do registro
de onde vem cada afirmação. O `indice.md` traz uma linha por nota, e o
`registro.md` diz o que entrou e quando.

Os registros continuam sendo a fonte dos dados, e nada é copiado. Uma
decisão, uma mudança de data, uma cobrança e uma tarefa ficam só no
registro de cada uma. A nota diz o que elas mudam no que se sabe, e a
busca acha todas. O método junta as pastas PARA e os passos CODE, de
Tiago Forte, com um índice e uma conferência mantidos pelo agente. Tudo
é Markdown puro e abre em qualquer editor, sem programa extra. A página
[metodo/segundo-cerebro.md](metodo/segundo-cerebro.md) traz o método
inteiro.

### Lista do dia

A lista junta tudo o que está aberto e separa em cinco partes: a caixa
de entrada, com o que chegou e ainda não foi classificado, as próximas
ações, que são as suas e as da equipe, o que aguarda o cliente, a agenda
do dia e o que há a confirmar. O que foi adiado fica fora da vista até a
revisão da semana.

No topo sobem no máximo três itens, nesta ordem de critério:

| Critério | O que sobe |
| --- | --- |
| Vencimento | O item vencido que ainda não tem data nova |
| Bloqueio e risco | O item que trava outros, ou que é ameaçado por um risco de exposição alta |
| Folga | O prazo próximo com menos dias úteis de folga |
| Espera | O item que aguarda o cliente há mais tempo sem cobrança |

A exposição de um risco é a probabilidade vezes o impacto, cada um em
baixa, média ou alta. Cada item do topo diz por que subiu. A lista é
gravada em `_projeto/afazeres.md`, com uma caixa por item.

As perguntas da parte de confirmar têm frequência. As de reunião sem
registro e de dispensa vêm todo dia. As de riscos, retorno do cliente,
premissas, adiados e nível de governança vêm uma vez por semana, na
véspera do status. As de satisfação e de benefício vêm a cada marco. A
frequência de cada uma fica em `_projeto/perguntas.tsv` e é sua para
mudar. O agente nunca pergunta por horas trabalhadas.

### Follow-up com o cliente

Um trabalho que depende de aprovação, dado ou decisão do cliente só
segue com a confirmação. Você informa quando ela chega, ou o agente
pergunta na lista do dia se o follow-up foi feito. As respostas são
quatro: aprovou, cobrei hoje, ainda não cobrei ou não depende mais de
aprovação. Cada cobrança fica em `_projeto/cobrancas.tsv`, com a data, e
aparece na lista e no status. Enquanto a confirmação não chega, o agente
recusa marcar como concluído ou em andamento o trabalho que depende
dela.

### Nível de governança

Depois do brief, o agente lê o porte do projeto e sugere um de três
níveis. Você escolhe, e pode tirar, incluir ou pedir um material
diferente.

| Nível | Quando serve | O que é emitido |
| --- | --- | --- |
| Enxuto | Até oito semanas, uma frente, equipe de até três pessoas, sem comitê formal | Sete materiais curtos: abertura, status semanal, nota de reunião, pedidos ao cliente, aceite, mudança e encerramento |
| Padrão | Mais de oito semanas, duas a quatro frentes, comitê formal ou pagamento por marco | Os do enxuto em versão formal, mais plano integrado, matriz de papéis, pauta, status executivo e ciclo de aprovação, entre outros |
| Completo | Mais de seis meses, mais de quatro frentes, comitê em mais de um nível ou benefício comprometido | Os do padrão, mais matriz de riscos, painel, status diário e os controles de benefícios e de contrato |

O nível escolhe o que é emitido, e os registros existem em qualquer
nível. Ações, riscos, issues, premissas, dependências, decisões,
mudanças, versões e linha de base são mantidos pelo agente a cada
evento, sem custo para você. Um material que o catálogo não tem entra
sob medida: você diz o destinatário, a cadência e o que ele traz. O
agente revê o nível quando o projeto cresce ou encolhe e pergunta uma
vez por semana se os sinais pedirem outro.

### Mudanças, linha de base e versões

Um pedido fora do combinado entra em `_projeto/mudancas.tsv`, com o
impacto em prazo, esforço e escopo, e espera a sua decisão e a do
cliente. A linha de base guarda as datas combinadas dos entregáveis, dos
marcos e das ações de contrato. Uma versão nova da linha de base pede o
motivo e quem aprovou, e o agente mostra o desvio de cada item contra
ela. Cada envio de um entregável ganha uma versão em
`_projeto/versoes.tsv`, com o que mudou e quem recebeu. O aceite é
registrado com o nome de quem aceitou, e esse nome vem do cliente.

### Prazos pelo cronograma

Os avisos acompanham o cronograma e têm três fases.

| Fase | Quando | O que você vê |
| --- | --- | --- |
| Parado dentro do prazo | O item não se move há mais de um terço da janela dele, e há pelo menos dois dias úteis | Um aviso leve, uma vez só |
| Prazo próximo | Resta um quinto da janela ou menos, entre um e cinco dias úteis, ou as etapas que faltam não cabem no tempo | Aviso em todo resumo |
| Vencido | A data passou | Aviso em todo resumo, até você responder |

Um item vencido pede uma de três respostas: concluído, nova data ou não
é mais necessário. Com a data nova, a anterior fica guardada em
`_projeto/prazos.tsv`, com quem mudou e o motivo, e aparece nos
relatórios de estado como deslocamento. A segunda mudança do mesmo item
é destacada, e a terceira vira um risco. Uma data de base, que está no
contrato ou foi acordada com o cliente, só muda com a concordância dele.
Os limites ficam em `_projeto/cadencias.tsv` e são seus para ajustar. Os
dias úteis vão de segunda a sexta e não contam feriados.

### Dispensas

Quando algo deixa de ser necessário ou não depende mais de aprovação,
diga com as suas palavras. O agente registra a decisão com o motivo,
cancela o item sem apagar nada, leva o efeito a todos os registros que o
citam e para de avisar. Ele nunca presume uma dispensa: sem a sua frase,
o item segue cobrado.

### Material feito à mão

O que você fez fora do fluxo ou recebeu por outro caminho vai para
`entregaveis/_intake/entrada/`. O agente classifica cada arquivo, leva
ao lugar certo e confere se ele contradiz os registros. Você não refaz
nada.

### Fases do projeto

Um projeto muda de natureza e continua o mesmo: a proposta vendida vira
o trabalho contratado, e uma extensão abre outro tipo de trabalho. O
agente abre uma fase nova, que herda decisões, evidências, glossário,
marca, lições, domínio e entregáveis das anteriores.

### Sigilo e repositório

Um projeto iniciado só vive em pasta sem git, em git local ou em
repositório privado. O agente confere o remoto e não grava registros nem
envia nada enquanto ele for público. Material recebido fica fora do git,
nenhum entregável cita outro cliente e nenhuma credencial entra em
arquivo.

### Outros aplicativos

O harness completo roda no Claude Code. Em outros agentes que leem
`AGENTS.md` e rodam comandos, valem as regras, as skills e as checagens.
No Claude desktop, no ChatGPT desktop e no Microsoft Copilot, o método
chega como um texto de instruções e arquivos de conhecimento, sem as
travas. O agente monta o pacote e traz de volta o que foi feito fora. O
passo a passo está em [ambientes/LEIA-ME.md](ambientes/LEIA-ME.md).

### Ambiente da máquina

O harness usa scripts em Python. No início do projeto e na instalação, o
agente confere a máquina: o Python, o Git e os programas que geram os
arquivos. Para cada falta, ele mostra o comando do seu sistema e
pergunta se instala ele mesmo ou se você prefere seguir o passo a passo.
Só o Python é essencial. O resto é pedido na hora de gerar o arquivo de
um formato.

Quem não pode instalar nada tem saída. No projeto do Claude desktop e do
ChatGPT desktop e no Microsoft Copilot, o método roda no ambiente do
próprio aplicativo. Quem só tem o Copilot web usa um caderno do Copilot
ou uma conversa com as instruções e os arquivos de conhecimento
anexados. Nesses casos não há checagem em script: o agente confere à mão
e diz isso no relatório.

### Atualização

Quando o template tem versão nova, diga ao agente para atualizar. Ele
traz regras, skills e checagens novas e mantém o que é do projeto.

## As três travas

No Claude Code, três situações bloqueiam o agente. Todas têm saída.

| O que você vê | Por quê | O que fazer |
| --- | --- | --- |
| O agente não escreve páginas nem gera o arquivo | O briefing está incompleto ou a storyline não foi aprovada | Responda ao que falta no briefing e aprove a storyline |
| O agente não encerra a tarefa | O conteúdo mudou e a revisão registrada é de outra versão | Deixe o agente revisar, ou peça para ele adiar o que não dá para corrigir agora |
| O agente não grava registros nem envia ao remoto | O repositório é público ou não foi verificado | Torne o repositório privado, ou confirme ao agente que ele é privado |

## Outras situações comuns

| O que você vê | O que fazer |
| --- | --- |
| O arquivo saiu sem a marca do cliente | Entregue o modelo. O agente registra em `_projeto/marca.md` e gera de novo |
| O gerador escolheu um layout ruim para um tipo de página | Peça ao agente para listar os layouts do modelo e fixar o certo em `_projeto/marca.md` |
| O gerador diz que falta um pacote | Instale `python-pptx`, `python-docx` ou `openpyxl`. Para PDF, instale o LibreOffice |
| Uma checagem acusa algo que você quer manter | Diga o motivo. O agente ajusta o limite, o glossário ou a regra do projeto e registra a decisão |
| A página ficou com uma lacuna visível | Falta um dado. Veja o pedido em `_intake/registro.tsv` e o item em `_projeto/adiados.tsv` |
| O agente diz que falta algo na máquina | Diga sim para ele instalar, ou siga os comandos que ele mostrar. Só o Python impede o trabalho |
| Um aviso de prazo não faz mais sentido | Diga se foi concluído, a data nova ou que não é mais necessário. O aviso some com a resposta |
| Os avisos chegam cedo ou tarde demais para este projeto | Peça ao agente para ajustar os limites em `_projeto/cadencias.tsv` |
| A lista do dia pergunta demais, ou de menos | Peça ao agente para mudar a frequência da pergunta em `_projeto/perguntas.tsv` |
| Uma nota do segundo cérebro está errada ou velha | Corrija a nota ou diga ao agente o que mudou. Ele corrige o registro de origem e a nota |
| O projeto emite material demais para o tamanho dele | Diga qual material tirar e o motivo. O registro por trás dele continua mantido |
| Uma sessão nova parece não lembrar do projeto | Pergunte "como está o projeto?". O agente lê os registros e retoma |

## Ajustes para quem já tem prática

- O seu método entra em `_dominio/`, com regras que rodam sozinhas e
  critérios próprios de revisão.
- Os limites de densidade mudam em `_projeto/limites.tsv`.
- Um vício de texto que você quer barrar entra em uma lista de
  `listas/`, com uma linha em `_projeto/licoes.md`.
- Um procedimento que o projeto repete vira uma skill nova em
  `.claude/skills/`, com uma linha na tabela de momentos de
  [REGRAS.md](REGRAS.md).
- O layout de cada tipo de página pode ser fixado em `_projeto/marca.md`.
- Em um repositório no GitHub, a instalação com `--ci` roda as checagens
  a cada pull request.

As peças do harness e o dono de cada arquivo estão em [kit.md](kit.md).

## Comandos para acompanhar

Você não precisa deles, e eles ajudam a ver o projeto sem perguntar.
Rode na raiz do projeto.

| Comando | O que mostra ou faz |
| --- | --- |
| `python3 entregaveis/_harness/scripts/estado.py` | A etapa de cada entregável, os materiais pendentes e as decisões à sua espera |
| `python3 entregaveis/_harness/scripts/validar.py` | Todas as checagens. Com `--rigoroso`, as faltas viram erro |
| `python3 entregaveis/_harness/scripts/gerar.py ID --pdf --imagens` | O arquivo final, o PDF e uma imagem por página para conferir |
| `python3 entregaveis/_harness/scripts/gerar.py --layouts` | Os layouts do modelo de apresentação |
| `python3 entregaveis/_harness/scripts/dominio.py` | Os casos de teste das regras do domínio |
| `python3 entregaveis/_harness/scripts/fase.py` | As fases do projeto |
| `python3 entregaveis/_harness/scripts/repositorio.py` | Se o remoto é local, privado ou público |
| `python3 entregaveis/_harness/scripts/empacotar.py --projeto` | O pacote para levar o projeto a outro aplicativo |
| `python3 entregaveis/_harness/scripts/rotina.py` | O resumo do dia: o que chegou, o que espera o seu sim e os prazos |
| `python3 entregaveis/_harness/scripts/rotina.py --datas` | As datas que mudaram, com a original e o motivo |
| `python3 entregaveis/_harness/scripts/rotina.py --lista` | A lista do dia, com os três itens que pedem atenção primeiro |
| `python3 entregaveis/_harness/scripts/governanca.py` | O nível de governança e os materiais que o projeto emite |
| `python3 entregaveis/_harness/scripts/governanca.py --desvios` | O desvio de cada data contra a linha de base |
| `python3 entregaveis/_harness/scripts/cerebro.py --buscar TERMOS` | As notas e as linhas dos registros que falam dos termos |
| `python3 entregaveis/_harness/scripts/cerebro.py --pendentes` | O que o projeto registrou e nenhuma nota guarda ainda |
| `python3 entregaveis/_harness/scripts/ambiente.py` | O que a máquina tem e o que falta, com o comando de cada falta |
