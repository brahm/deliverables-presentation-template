# Histórico do kit

A skill `atualizar-harness` lê este arquivo a partir da versão instalada
no projeto. Cada versão diz o que mudou e o que o projeto precisa fazer.

## 0.15.0

- O kit instala as skills de design de interface de Emil Kowalski
  (<https://github.com/emilkowalski/skills>, licença MIT) em
  `.claude/skills/`, sem mudar uma linha do original. A origem, a
  licença e o hash de cada arquivo ficam em `_harness/terceiros/`, e o
  `tools/testar_kit.py` confere a cópia.
- Todo HTML de entrega usa essas skills. A regra 9, a tabela de
  momentos, `metodo/interativo.md`, `construir-interativo` e
  `revisar-entregavel` dizem quando cada uma entra e o que o harness
  não deixa passar, como biblioteca externa ou cor fora da marca.
- Regra nova para todo HTML que o harness gera: arquivo completo, com
  estilo, script, dados e imagens no próprio documento, e toda imagem
  em SVG embutido no código. A checagem `interativo` passa a reprovar
  imagem PNG, JPG, GIF ou WebP, mesmo em base64. Antes, a imagem em
  base64 era aceita.
- O hook de gravação lembra as skills na primeira gravação de cada HTML
  da sessão. A checagem `interativo` passa a avisar de
  `transition: all`, de `scale(0)` e de `ease-in`.
- O instalador reconhece uma skill do kit também pelo arquivo `.origem`
  ao lado, e compara todos os arquivos da skill, não só o `SKILL.md`.
  Antes, a mudança em um arquivo de apoio não chegava ao projeto.
- O projeto passa a se chamar Deliverables Presentation Template no
  README, no INSTALL, no guia, nas regras e nos blocos de instrução.
- Nova página `docs/instalar-e-usar.html`, que explica a instalação e
  o uso em um arquivo só.

O que o projeto precisa fazer: atualize com `--atualizar`. Se o projeto
já tem uma skill com o nome de uma das novas, como `animate`, ela é
mantida e o instalador avisa. Uma peça interativa com imagem em base64
passa a reprovar: redesenhe a imagem em SVG ou leve-a para a página do
entregável.

## 0.14.0

- Instalação em uma linha, para Linux, macOS e Windows com WSL:
  `curl -fsSL https://raw.githubusercontent.com/brahm/deliverables-presentation-template/main/install.sh | sh`,
  dentro da pasta do projeto. O `install.sh` baixa o kit para uma pasta
  temporária, roda o mesmo instalador na pasta atual e apaga o que
  baixou. As opções vão depois de `sh -s --`.
- O download só aceita HTTPS, o corpo do script roda de uma função
  chamada na última linha, para que um download cortado não execute um
  pedaço, e o instalador recusa a pasta pessoal e a raiz do disco quando
  não há `--destino`.
- `HARNESS_REF` fixa o ramo, a etiqueta ou o commit do kit.
  `HARNESS_ARQUIVO` instala de um pacote já baixado, sem internet.
- O `install.sh` passa a exigir o Python 3.9 também quando roda de uma
  cópia local do kit.

O que o projeto precisa fazer: nada. Para atualizar um projeto por este
caminho, rode a linha com `sh -s -- --atualizar`.

## 0.13.2

- O harness deixa de ter registro de horas. Saem o modelo
  `esforco.tsv`, a seção de esforço do status semanal e do status
  executivo e a pergunta de horas de `perguntas.tsv`. O catálogo de
  materiais não cita mais esforço realizado.
- A estimativa de esforço do plano continua na linha de base e no
  impacto de uma mudança, só como base de plano e de preço.

O que o projeto precisa fazer: atualize com `--atualizar`. Se o projeto
tem `_projeto/esforco.tsv`, o harness não o lê mais, e o consultor decide
se o guarda ou apaga.

## 0.13.1

Correções da revisão de código. Nenhum comando mudou de nome.

- Registros. Um registro salvo pelo Excel ou pelo Bloco de Notas em
  cp1252 ou em UTF-16 é lido, com um aviso, e volta em UTF-8 na
  gravação seguinte. Antes ele era lido como vazio e a gravação apagava
  as linhas. Um registro que não é texto ou está sem a linha de colunas
  para o comando, sem gravar. A gravação troca o arquivo inteiro de uma
  vez. Um campo a mais em uma linha é ignorado e não desloca as colunas.
- Travas com defeito. Quando a trava de gravação ou a de comando não
  consegue conferir o passo, ela barra e diz o defeito. Antes liberava
  em silêncio. Os outros hooks avisam o agente e deixam seguir.
- Repositório. A conferência segue os redirecionamentos até a resposta
  final, e só 401, 403 e 404 valem como privado. O endereço de envio de
  cada remoto e o endereço escrito no próprio comando são conferidos. A
  criação de repositório interno e a troca de visibilidade pela API são
  barradas. O usuário e o token de um endereço não aparecem nas
  mensagens nem em `_projeto/repositorio.tsv`.
- Números no gerador. O separador decimal vem da própria coluna e,
  quando ela não mostra, do idioma do entregável. Percentual e moeda
  viram número com formato. Um valor que não é número para a geração do
  gráfico e diz a linha e a coluna. Na planilha, texto que começa com
  `=` fica como texto, e código com zero à esquerda não perde o zero.
- Fundo escuro. O gerador lê a cor de fundo do modelo e dá cor clara ao
  texto que ele acrescenta: rótulos, eixos e legenda do gráfico, linha
  de fonte, caixas de texto e tabela. A linha `Cor do texto sobre o
  fundo`, nova em `_projeto/marca.md`, vence a escolha automática.
- Gráficos. A pizza sem destaque ganha uma cor por fatia, e os gráficos
  da planilha usam as cores da marca.
- Gerador, o resto. Lista numerada sai numerada. Asterisco solto não
  vira itálico. Tabela que não cabe no slide gera aviso. Modelo de Word
  sem um estilo não duplica o título. As seções do modelo de PowerPoint
  saem junto com os slides de exemplo. Imagem e arquivo de dados de
  fora da pasta do projeto são recusados.
- Pasta com outro nome. As mensagens dos scripts dizem o caminho real
  quando o harness foi instalado com `--pasta`.
- Cabeçalhos. Título com barra invertida ou quebra de linha entra como
  foi escrito. O carimbo da revisão mantém os comentários e os outros
  campos. Remarcar um entregável sem a linha `prazo:` cria o campo.
- Workflows. `permissions: contents: read`, ações fixadas pelo commit e
  pacotes do gerador com versão fixa.
- Desempenho. A gravação de um arquivo confere esse arquivo e não relê
  os dados do entregável. As regras do domínio leem o entregável uma vez
  e executam `checagens_extra.py` uma vez por execução. A lista do dia
  lê os prazos e percorre as dependências uma vez. `cerebro.py`,
  `governanca.py` e `emitir.py` entram na lista de comandos permitidos,
  e o agente deixa de pedir permissão a cada absorção.
- `tools/testar_kit.py` roda até quatro grupos ao mesmo tempo. `--serie`
  roda um depois do outro, e o nome de um grupo roda só ele.

O que o projeto precisa fazer: atualize com `--atualizar`. Para usar a
cor do texto sobre fundo escuro, acrescente em `_projeto/marca.md` a
linha `| Cor do texto sobre o fundo | | |`. Sem ela, vale a escolha
automática. Se `_projeto/repositorio.tsv` guarda um endereço com
usuário ou token, apague esse trecho da linha e troque o token.

## 0.13.0

- Pacote `proposta` refeito. Uma proposta não é um projeto, e o pacote
  deixa de trazer frameworks, esqueletos de storyline, lista de dados,
  roteiro de entrevista e glossário. O método de construção de proposta
  é do consultor e fica só no projeto.
- Informações que o consultor fornece. Um pacote pode trazer
  `insumos.tsv`: o que perguntar, antes de que etapa do entregável e
  onde a resposta fica. O de proposta pede objetivo, ponto de vista,
  abordagem, tarefas, cronograma, equipe recomendada e preço, e duas
  condicionais: o método da casa e o pedido formal do cliente.
- `governanca.py --insumos` mostra as informações dos pacotes ativos.
  `--insumo CODIGO` responde com `--recebido` (pede onde ficou e quem
  forneceu), `--nao-se-aplica` (pede o motivo) ou `--pendente`. As
  respostas ficam em `_projeto/insumos.tsv`. O estado e a lista do dia
  dizem o que falta, e o entregável que chega à etapa sem a informação
  é erro na checagem de governança.
- Nível de governança `proposta`, abaixo do enxuto: nenhum material é
  emitido. `governanca.py --sugerir` o propõe quando o pacote de
  proposta está ativo.
- A proposta tem dois controles, os dois antes do envio: aprovação do
  preço, do escopo e dos termos, e autorização para citar casos,
  clientes e pessoas. Enquanto o pacote de proposta está ativo, os
  controles dos outros pacotes esperam a venda.
- `fase.py --nova` limpa o nível `proposta`, e a fase do trabalho
  vendido escolhe o nível de novo.

O que o projeto precisa fazer: atualize com `--atualizar`. Um projeto
com o pacote `proposta` ativo passa a ver nove informações a pedir e
dois controles. Registre as que o consultor já forneceu com
`governanca.py --insumo CODIGO --recebido`. Os termos que o pacote
antigo somou ao glossário do projeto continuam lá.

## 0.12.0

- Controles de governança por tipo de projeto. Um pacote pode trazer
  `controles.tsv`: o que precisa ficar registrado e aprovado, antes de
  que etapa do entregável, e que evidência fecha. O controle não
  descreve método nem atividade.
- `governanca.py --controles` mostra os controles dos pacotes ativos.
  `--controle CODIGO` responde com `--cumprido` (pede a evidência e quem
  confirmou), `--nao-se-aplica` (pede o motivo) ou `--pendente`. As
  respostas ficam em `_projeto/controles.tsv`.
- O estado conta os controles pendentes e os que falta confirmar. A
  lista do dia pergunta pelo controle condicional e cobra o pendente
  quando o entregável chega à etapa. A checagem de governança avisa, e
  o registro de um envio diz que controles ficaram sem evidência.
- O pacote `martech-adtech` ganhou quatro controles: critérios
  aprovados antes de avaliar, achados com evidência, rastreabilidade e
  validação com os donos das plataformas.
- Pacote novo `processos-midia`, para definição de processos de mídia
  digital. Traz só governança: quatro controles fixos e dois
  condicionais. Um pacote passa a poder existir sem pedido de dados,
  roteiro de entrevista e glossário.

O que o projeto precisa fazer: atualize com `--atualizar`. Um projeto
com o pacote `martech-adtech` ativo passa a ver quatro controles
pendentes. Responda cada um com a evidência que já existe, ou dispense
com o motivo.

## 0.11.0

- Materiais montados dos registros. `scripts/emitir.py` monta o status
  semanal, o status executivo, a pauta, a nota de entrega, o pedido e a
  confirmação de aceite, o quadro de aprovações e a solicitação de
  mudança. O rascunho fica em `_projeto/emitidos/`, a emissão em
  `_projeto/emitidos.tsv`, e o consultor revisa e envia. O que os
  registros não trazem sai marcado para completar.
- Semáforo por regra. Vermelho com desvio da linha de base acima da
  tolerância ou issue escalada. Amarelo com desvio dentro da
  tolerância, item vencido sem data nova ou risco de exposição alta. O
  consultor troca a cor com `--cor` e `--motivo`, e o material mostra a
  cor dele e a da regra.
- Ciclo de aprovação. `governanca.py --versao` com `--enviada-a` abre
  uma aprovação do cliente em `acoes.tsv`, para o aprovador de
  `papeis.tsv`, com o prazo de resposta combinado ou o sinal novo
  `prazo_de_aprovacao` de `cadencias.tsv`. `--aceite` fecha a
  aprovação. O silêncio não vale como aceite: o item é cobrado pelo
  follow-up e entra no status como pendência do cliente.
- Ciclo de mudança. `governanca.py --mudanca` abre o pedido,
  `--analisar` grava o impacto em prazo, esforço e escopo e `--decidir`
  grava a decisão. A aprovação pede os três impactos. A linha de base
  que cita uma mudança só é gravada com a mudança aprovada. A mudança
  rejeitada vai para `adiados.tsv`.
- No dia do status, a agenda da lista do dia lembra o status semanal
  enquanto ele não foi montado.
- Skill nova `emitir-material`. A regra 21 passa a dizer que os
  materiais saem dos registros e que o silêncio não vale como aceite.

O que o projeto precisa fazer: atualize com `--atualizar`. Ele cria
`_projeto/emitidos.tsv` e acrescenta o sinal `prazo_de_aprovacao`. Os
envios já registrados e sem aceite aparecem no status como pendência do
cliente. Para ligar o relógio de um deles, registre o próximo envio com
`--versao` e `--enviada-a`.

## 0.10.0

- Segundo cérebro do projeto. O que o projeto aprende fica em notas de
  Markdown em `entregaveis/_cerebro/`, nas quatro pastas do método PARA:
  `1-projetos`, `2-areas`, `3-recursos` e `4-arquivo`. O agente escreve
  e mantém as notas, o `indice.md` e o `registro.md` de atualizações.
  Nenhum programa de terceiros é necessário.
- Os registros continuam sendo a fonte. A nota cita o id do registro e
  diz o que o dado significa. Tarefas, mudanças de data, cobranças,
  avisos, versões e o histórico das decisões ficam só nos registros.
- `scripts/cerebro.py` busca nas notas e nos registros de uma vez
  (`--buscar`, `--id`), mostra o que o projeto registrou e nenhuma nota
  guarda (`--pendentes`), marca o que cada nota absorveu (`--absorver`,
  que recusa a nota que não cita o item), cria e move notas (`--nova`,
  `--mover`), refaz o índice e confere as notas (`--conferir`).
- Gatilhos a cada ação do projeto: o hook de gravação lembra o item novo
  e confere a nota gravada, o hook de fim de turno pede a absorção do
  que o turno registrou, o estado conta as notas e o que falta, e a
  lista do dia mostra o que está fora das notas.
- Skill nova `manter-cerebro`, regra 22, página de método
  `metodo/segundo-cerebro.md` e checagem "Segundo cérebro", que só
  avisa.
- O pacote para outros ambientes leva o índice e as notas, e as
  instruções mandam consultar antes de escrever e devolver as notas
  novas.
- O exemplo ganhou seis notas, com o índice e o registro de
  atualizações.

O que o projeto precisa fazer: atualize com `--atualizar`. Ele cria a
pasta `_cerebro/` vazia. Depois o estado mostra quantos itens do projeto
estão fora das notas, e o agente absorve por assunto, começando pelo
cliente, pelas pessoas e pelo que é avaliado.

## 0.9.0

- Nível de governança. Depois do brief, o agente lê o porte do projeto
  e sugere o nível enxuto, padrão ou completo. O consultor escolhe e
  pode tirar, incluir ou pedir um material sob medida. O catálogo dos
  materiais está em `_harness/governanca/catalogo.tsv`, a escolha fica em
  `_projeto/governanca.tsv` e o estado mostra o nível. A skill nova é a
  `definir-governanca`, e o comando é `scripts/governanca.py`.
- Registros que existem em qualquer nível: `premissas.tsv`,
  `issues.tsv`, `dependencias.tsv`, `mudancas.tsv`, `papeis.tsv`,
  `linha-de-base.tsv`, `versoes.tsv`, `cobrancas.tsv` e `esforco.tsv`.
  O esforço não gera pergunta nem aviso. As ações ganharam as colunas
  `depende_de` e `entregavel`, e os riscos ganharam probabilidade,
  impacto, o item ameaçado e a resposta.
- Lista do dia. `scripts/rotina.py --lista` monta a caixa de entrada, as
  próximas ações, o que aguarda o cliente, a agenda e o que há a
  confirmar, e grava em `_projeto/afazeres.md`. No topo sobem no máximo
  três itens: o vencido sem data nova, o que trava outros ou é ameaçado
  por um risco de exposição alta, o prazo com menos folga e o que espera
  o cliente há mais tempo sem cobrança.
- Follow-up com o cliente. O trabalho que depende de aprovação, dado ou
  decisão do cliente só segue com a confirmação. O consultor informa, ou
  o agente pergunta se o follow-up foi feito, e cada cobrança fica em
  `_projeto/cobrancas.tsv`. A resposta entra com
  `scripts/rotina.py --cobrado ID`.
- Perguntas por frequência. Cada pergunta da lista é diária, semanal ou
  de marco, em `_projeto/perguntas.tsv`. O agente nunca pergunta por
  horas trabalhadas.
- Linha de base, desvios, versões e aceite, com
  `scripts/governanca.py --linha-de-base`, `--desvios`, `--versao` e
  `--aceite`. Uma versão nova da linha de base pede o motivo.
- A checagem "Governança" acusa nível ou estado inválido, material fora
  do catálogo, id citado que não existe e ação concluída antes da
  confirmação do cliente.
- O exemplo ganhou o nível enxuto, a linha de base, um risco, uma
  premissa e uma cobrança.

O que o projeto precisa fazer: atualize com `--atualizar`. Ele cria os
registros novos em branco e acrescenta as colunas e as linhas de
configuração novas aos registros que o projeto já tem, sem mudar
nenhuma linha sua. Depois o estado pede o nível de governança: o agente
sugere pelo porte e você confirma.

## 0.8.0

- Atas pela pasta. O consultor salva atas e transcrições em
  `entregaveis/_atas/`, e a skill `processar-ata` leva cada trecho ao
  registro certo com a reunião de origem. Só espera o sim do consultor o
  que toca o contrato ou sai do projeto. Uma ata alterada é lida de novo
  só na diferença, e uma reunião sem ata entra pelo relato do consultor.
- Rotina do dia. `scripts/rotina.py` mostra em uma tela o que chegou, o
  que espera o sim, os prazos e o que parou, e grava o diário do
  projeto. A skill `rotina-diaria` abre e fecha o dia, e o estado ganhou
  a linha da rotina.
- Avisos pelo cronograma, em três fases: parado dentro do prazo, com
  aviso leve dado uma vez, prazo próximo e prazo vencido. O vencido pede
  uma de três respostas: concluído, nova data ou não é mais necessário.
  A data nova guarda a anterior em `_projeto/prazos.tsv`, a segunda
  mudança do mesmo item é destacada e a terceira vira risco. Os limites
  ficam em `_projeto/cadencias.tsv`.
- Registros novos em `_projeto/`: `reunioes.tsv`, `ritos.tsv`,
  `acoes.tsv`, `riscos.tsv`, `prazos.tsv`, `cadencias.tsv`,
  `alertas.tsv` e `diario.md`. A checagem "Prazos" confere as ações.
- Duas skills para o que foge do fluxo: `incorporar-material`, para o
  que o consultor fez à mão ou recebeu por outro caminho e pôs em
  `entregaveis/_intake/entrada/`, e `registrar-dispensa`, para o que não
  será mais feito ou não depende mais de aprovação.
- Conferência do ambiente. `scripts/ambiente.py` diz o que a máquina tem
  e o comando que instala cada falta em Windows, macOS e Linux, e
  `--instalar` instala os pacotes do gerador. O instalador mostra o que
  falta, e as skills `iniciar-projeto` e `adotar-projeto` começam por
  essa conferência, com a oferta de o agente configurar tudo ou repassar
  o passo a passo.
- Outros agentes. As instruções para o Claude desktop, o ChatGPT desktop
  e o Microsoft Copilot mandam o agente conferir o próprio ambiente e
  trazem as atas e os prazos. `ambientes/LEIA-ME.md` ganhou o passo a
  passo de quem só tem o Copilot web, sem instalar nada.
- O exemplo ganhou a reunião de fechamento, as três tarefas que saíram
  dela e uma data remarcada.

O que o projeto precisa fazer: atualize com `--atualizar`. Ele cria os
registros novos em branco, a pasta de atas e a pasta de entrada, e põe
as duas fora do git. Depois diga ao agente quais reuniões se repetem,
para ele preencher `_projeto/ritos.tsv`, e leve às ações os prazos que
hoje estão só em atas ou em mensagens.

## 0.7.1

- Um exemplo completo. A pasta `exemplo/` traz um projeto fictício do
  brief à entrega, com os registros, o domínio, a storyline aprovada, as
  páginas, a revisão, a entrega, o fechamento e o arquivo final. Tudo
  nele é inventado, e o guia `exemplo/LEIA-ME.md` conta o que a
  consultora disse em cada etapa.
- Um guia de uso. `_harness/guia.md` apresenta todos os recursos do
  harness, o que dizer ao agente em cada momento, as três travas com a
  saída de cada uma e os ajustes para quem já tem prática. Ele é
  instalado com o harness em todo projeto.
- `tools/abrir_exemplo.py DESTINO` abre o exemplo em uma pasta nova, com
  o harness instalado. Os testes do kit abrem o exemplo a cada mudança e
  conferem se ele passa nas checagens de hoje.
- O README explica a criação do projeto pelo site do GitHub, pelo
  terminal e sem GitHub, com o link direto para o formulário.
- Sem modelo registrado, o gerador apaga das propriedades do arquivo o
  autor e a descrição que a biblioteca traz no arquivo de base dela.
- Nos modelos do domínio, o exemplo de regra passou a usar o id `R-001`,
  para não se confundir com as decisões, que usam `D-nnn`.

O que o projeto precisa fazer: atualize com `--atualizar` para receber o
guia. O exemplo e o comando que o abre ficam só no repositório do
template.

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
