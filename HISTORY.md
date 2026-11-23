# Histórico do kit

A skill `atualizar-harness` lê este arquivo a partir da versão instalada
no projeto. Cada versão diz o que mudou e o que o projeto precisa fazer.

## 0.7.1

- Um exemplo completo. A pasta `exemplo/` traz um projeto fictício do
  brief à entrega, com os registros, o domínio, a storyline aprovada, as
  páginas, a revisão, a entrega, o fechamento e o arquivo final. Tudo
  nele é inventado, e o guia `exemplo/LEIA-ME.md` conta o que a
  consultora disse em cada etapa.
- `tools/abrir_exemplo.py DESTINO` abre o exemplo em uma pasta nova, com
  o harness instalado. Os testes do kit abrem o exemplo a cada mudança e
  conferem se ele passa nas checagens de hoje.
- O README explica a criação do projeto pelo site do GitHub, pelo
  terminal e sem GitHub, com o link direto para o formulário.
- Sem modelo registrado, o gerador apaga das propriedades do arquivo o
  autor e a descrição que a biblioteca traz no arquivo de base dela.
- Nos modelos do domínio, o exemplo de regra passou a usar o id `R-001`,
  para não se confundir com as decisões, que usam `D-nnn`.

O que o projeto precisa fazer: nada. O exemplo e o comando que o abre
ficam só no repositório do template.

## 0.7.0

- O harness fora do Claude Code. `_harness/ambientes/` traz o texto de
  instruções para colar e os arquivos de conhecimento para enviar ao
  Claude desktop, ao ChatGPT desktop e ao Microsoft Copilot, com o passo
  a passo de cada um. Nesses ambientes não há trava nem checagem
  automática: as regras viram instruções, e o agente confere à mão.
- `scripts/empacotar.py --projeto` monta o pacote do projeto, com o
  brief, as fases, as decisões, as evidências e o domínio, em
  `entregaveis/_ambiente/`, que fica fora do git.
- A skill `usar-outro-ambiente` leva o trabalho para fora e traz de
  volta o registro e os materiais, que passam pelas checagens daqui.

O que o projeto precisa fazer: atualize com `--atualizar`, que acrescenta
`entregaveis/_ambiente/` ao `.gitignore`.

## 0.6.0

- Fases do projeto. Um projeto muda de natureza e continua o mesmo: a
  proposta vendida vira o trabalho contratado, e uma extensão abre outro
  tipo de trabalho. A skill `evoluir-projeto` reconhece a mudança pelo
  que o consultor diz, separa mudança de fase de mudança de escopo e,
  com o sim dele, abre a fase com `scripts/fase.py`.
- Abrir uma fase guarda o brief da anterior em `_projeto/fases/`, cria a
  página de passagem com os compromissos herdados, registra a mudança
  em `_projeto/fases.md` e ativa os pacotes do tipo novo. Decisões,
  evidências, glossário, marca, lições, domínio e entregáveis ficam
  onde estão.
- O brief ganhou o campo `fase`, e o briefing de cada entregável guarda
  a fase em que ele nasceu. O estado mostra a fase atual e o que a
  abertura dela deixou por fazer.
- O hook de mensagem avisa quando o pedido parece mudança de fase.

O que o projeto precisa fazer: atualize com `--atualizar` e rode
`python3 entregaveis/_harness/scripts/fase.py`, que registra a fase 1.
Um projeto sem o campo `fase` é lido como fase 1.

## 0.5.1

- Quem usa o harness passa a se chamar consultor nas regras, nas
  skills, no método, nos pacotes, nos modelos e nas mensagens dos
  scripts. "Dono" continua valendo para quem responde por uma ação, um
  processo ou uma plataforma.
- A skill `relatar-ao-dono` passou a se chamar `relatar-ao-consultor`.
- O campo `dono` de `_projeto/brief.md` passou a se chamar `consultor`.

O que o projeto precisa fazer: atualize com `--atualizar`, que retira a
skill de nome antigo. Renomeie o campo `dono` do brief para `consultor`.
Os registros já escritos continuam valendo como estão.

## 0.5.0

- Gerador de arquivos. `scripts/gerar.py ID` gera PowerPoint, Word, PDF
  e Excel a partir da fonte em Markdown, sobre o modelo registrado em
  `_projeto/marca.md`. Escolhe o layout pelo tipo de página, tira as
  páginas de exemplo do modelo, leva as notas, as tabelas, as imagens e
  a linha de fonte, e desenha gráficos nativos a partir de blocos
  `grafico`. Aceita modelo com mais de um slide mestre, com layouts de
  nome repetido e exportado por outro programa. Recusa o entregável sem storyline aprovada e o que reprova
  nas checagens, a não ser com `--rascunho`.
- `--imagens` grava uma imagem por página, para a conferência do
  arquivo renderizado.
- `_projeto/marca.md` ganhou a seção "Layouts do modelo".
- Um bloco de código não conta mais nas palavras da página.

O que o projeto precisa fazer: instale os pacotes do formato que usa
(`python-pptx`, `python-docx`, `openpyxl`). Registre os modelos em
`_projeto/marca.md`, rode `gerar.py --layouts` e gere de novo os
arquivos finais a partir da fonte.

## 0.4.0

- HTML interativo e animado, em 2D e 3D, como peça de apoio de qualquer
  entregável. É um arquivo único, sem biblioteca, fonte, imagem ou
  chamada de rede de fora. Três modelos de partida (`fluxo`,
  `camadas-3d` e `simulador`), a página `metodo/interativo.md`, a skill
  `construir-interativo`, a checagem `interativo` e
  `preparar.py --entregavel ID --interativo NOME --base MODELO`.
  `scripts/conferir_interativo.js` abre a peça em um navegador sem
  interface, onde há Node e Playwright.
- Domínio por projeto. O template traz o esqueleto e o motor. O método,
  as regras de checagem e os casos de teste são escritos dentro de cada
  projeto, em `_dominio/`, pela skill `calibrar-dominio`, a partir das
  referências, dos métodos, do contexto e do objetivo que o dono
  fornece. Uma regra só vale com um caso que acusa e um que passa.
  `scripts/dominio.py` roda os casos. Nada de `_dominio/` volta ao
  template.
- Projeto só em git local ou em repositório privado.
  `scripts/repositorio.py` faz ao remoto o pedido de clone sem
  credencial. Com o remoto público ou não verificado, o harness bloqueia
  a gravação dos registros do projeto e o `git push`. Quando o servidor
  não responde, vale a confirmação do dono, registrada em
  `_projeto/repositorio.tsv`. É a terceira trava do harness, com um
  hook novo, `antes_de_comando.py`.
- README resumido, com foco em instalar e usar. As tabelas de checagens
  e de travas foram para `_harness/kit.md`.

O que o projeto precisa fazer: rode o instalador com `--atualizar`, que
cria `_dominio/` e liga o hook novo. Rode
`python3 entregaveis/_harness/scripts/repositorio.py`. Se o remoto for
público, torne-o privado ou remova-o antes de seguir. Se o projeto
montou um pacote próprio em `_projeto/pacote/`, leve o conteúdo para
`_dominio/` com a skill `calibrar-dominio`.

## 0.3.0

- Seis pacotes novos, no mesmo formato do primeiro:
  `transformacao-marketing`, `midia`, `retail-media`,
  `processos-agenticos`, `proposta` e `treinamento`. O de treinamento
  cobre cursos, workshops, material didático, exercícios e exames.
- Os pacotes se somam: um projeto pode ativar mais de um.

O que o projeto precisa fazer: ative com `preparar.py --pacote NOME` os
pacotes do seu tipo de trabalho. Se o projeto montou um pacote próprio
em `_projeto/pacote/` para um desses tipos, compare os dois e leve ao
dono o que mudar.

## 0.2.0

- Primeiro pacote por tipo de projeto: `martech-adtech`, para assessment
  de arquitetura de martech e adtech. Traz as perguntas de início, os
  entregáveis típicos, dez frameworks, três esqueletos de storyline, a
  evidência que cada afirmação pede, as armadilhas, a lista de pedido de
  dados, os roteiros de entrevista e o glossário.
- `preparar.py --pacote NOME` ativa um pacote: copia a skill, soma os
  termos ao glossário do projeto e preenche o campo `pacotes` do brief.
- O instalador atualiza a skill de um pacote já ativado no projeto.

O que o projeto precisa fazer: se o trabalho é um assessment de martech
e adtech, rode `preparar.py --pacote martech-adtech`.

## 0.1.0

Primeira versão.

- Regras em `entregaveis/_harness/REGRAS.md` e 17 skills aplicadas pelo
  momento do trabalho.
- Fluxo em etapas: briefing, storyline aprovada pelo dono, storyboard,
  redação, revisão e entrega.
- Checagens em script (`validar.py`): briefing, storyline, densidade,
  evidência, texto em português, espanhol e inglês, termos, estrutura,
  confidencialidade e intake.
- Cinco hooks do Claude Code. Dois bloqueiam: gravar páginas sem briefing
  completo e storyline aprovada, e encerrar o turno com conteúdo alterado
  e sem revisão. Os outros avisam.
- Instalador para projeto vazio ou em andamento (`install.sh`), com nome
  de pasta configurável e sem sobrescrever arquivo do projeto.

O que o projeto precisa fazer: nada.
