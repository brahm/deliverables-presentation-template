# Guia de uso

Este guia mostra tudo o que o harness faz e como usar cada recurso em um
projeto. Ele serve a quem está no primeiro projeto e a quem já conduziu
dezenas. Quem está começando segue a ordem das seções. Quem já tem
prática vai direto à tabela de recursos e à seção de ajustes.

A instalação está no `README.md` e no `INSTALL.md` do repositório do
template.

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
| Fechar um entregável | "Apresentei hoje. Aprovaram a saída de duas plataformas e perguntaram pela multa." |
| Mudar a natureza do projeto | "A proposta foi vendida. Agora começa o diagnóstico." |
| Levar a outro aplicativo | "Vou continuar isto no Copilot. Monte o pacote." |
| Saber onde tudo está | "Como está o projeto?" |

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
