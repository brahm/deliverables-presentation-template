# HTML interativo e animado

Um HTML interativo é uma peça de apoio. Ele ajuda a audiência a entender
e a ler o material de entrega: percorrer um fluxo, girar uma
arquitetura, testar uma premissa. A decisão continua sendo provocada
pela apresentação, pela proposta ou pelo documento.

A peça é um arquivo completo. O estilo, o script, os dados e as imagens
ficam no próprio HTML, e toda imagem é um SVG embutido no código. Abre
com dois cliques em qualquer navegador, sem internet, sem pasta de apoio
e sem biblioteca externa. Vai por e-mail e
funciona dentro da rede do cliente.

## Quando uma peça interativa se paga

Faça uma peça quando a audiência entende melhor mexendo do que lendo:

| A audiência precisa | Peça | Modelo de partida |
| --- | --- | --- |
| Seguir uma sequência e ver onde está o problema | Fluxo guiado em 2D | `fluxo` |
| Ver como as partes de um sistema se empilham e se ligam | Camadas em 3D | `camadas-3d` |
| Testar premissas e ver o efeito no resultado | Simulador | `simulador` |
| Comparar o que é com o que poderia ser | Antes e depois, sobre um dos três modelos | o que servir melhor |

Não faça quando uma página estática já prova o título, quando o material
só vai ser impresso ou quando a interação seria enfeite. Uma peça que
ninguém precisa tocar para entender é uma imagem, e imagem vai na
página.

## A peça segue a história

- A peça nasce depois da storyline aprovada, como qualquer página. O
  harness bloqueia a gravação antes disso.
- Ela tem uma mensagem, escrita no cabeçalho do arquivo, e a mensagem é
  uma das mensagens da storyline. O título da peça diz o achado.
- O campo `apoia` diz qual página ou seção do entregável ela ajuda a
  ler. Uma peça sem página para apoiar não tem lugar no material.
- Todo número e todo achado da peça têm linha em `evidencias.tsv`, e o
  campo `fontes` lista os identificadores. A fonte e a data aparecem na
  tela. Dado de exemplo é marcado como exemplo.
- O texto visível segue [texto.md](texto.md) e passa pelas mesmas
  checagens das páginas.

O cabeçalho é um comentário logo depois da primeira linha do arquivo:

```html
<!-- interativo
titulo: nome curto da peça
mensagem: a frase que a audiência deve levar
apoia: página ou seção do entregável
fontes: E-012, E-015
idioma: pt-BR
-->
```

## Como desenhar a peça

1. A página está completa ao abrir. Quem não clica em nada já lê a
   mensagem e vê o estado que importa. A interação aprofunda.
2. O movimento explica uma mudança: de onde veio, para onde foi, o que
   cresceu. Movimento que só decora sai.
3. Um destaque por tela. O que a mensagem cita leva a cor de destaque e
   o resto fica em cinza, como em [visual.md](visual.md).
4. Barras, áreas e distâncias são desenhadas em escala. Quando duas
   medidas dividem um eixo, a peça diz isso.
5. A forma carrega informação. Estado e categoria são marcados por
   forma e rótulo além da cor, para que a leitura não dependa de
   enxergar a cor.
6. Os dados ficam separados do código, em um bloco JSON dentro do
   próprio arquivo. Trocar o dado não exige mexer no desenho.
7. As cores são variáveis declaradas uma vez, com valores para tema
   claro e tema escuro. As cores e as fontes vêm de
   `_projeto/marca.md`. Sem marca registrada, use o desenho neutro dos
   modelos e a fonte do sistema.
8. A peça funciona na tela do computador e na do celular, com margem
   lateral de pelo menos 16 px e sem rolagem para o lado.
9. Todo controle funciona pelo teclado e mostra o foco. O que muda na
   tela é anunciado para leitor de tela.
10. Quem pede menos movimento ao sistema recebe a peça sem animação e
    com o mesmo conteúdo. Animação contínua tem botão de pausa e para
    quando a aba sai de vista.
11. A peça tem uma versão para o papel, que mostra todos os estados de
    uma vez, e um texto para quem abre o arquivo sem script.

## As skills de design de interface

Todo HTML de entrega usa as skills de design de interface de Emil
Kowalski, que o kit instala em `.claude/skills/` junto com as suas.
Elas cuidam do acabamento: a curva e a duração do movimento, a ordem em
que as partes entram, o retorno ao toque, o foco, a tipografia e o
comportamento no celular. O harness continua decidindo o que a peça diz
e o que pode entrar no arquivo.

| Momento | Skill |
| --- | --- |
| Construir ou mudar qualquer HTML de entrega | `emil-design-eng` |
| A peça ganha uma animação | `animate` |
| Várias partes se movem juntas, como os passos de um fluxo ou a entrada das camadas | `choreograph` |
| A audiência arrasta, gira ou desliza | `gestures` |
| A peça vai ser aberta no celular | `mobile-native` |
| Profundidade, camadas translúcidas ou tipografia fina | `apple-design` |
| A animação engasga | `animation-performance` |
| Decidir onde o movimento ajuda e onde ele sai | `find-animation-opportunities` e `remove-animations` |
| Antes da revisão | `review-animations` e `break-ui` |

Abra `.claude/skills/NOME/SKILL.md` e siga, como nas skills do kit.
Algumas delas só são chamadas pelo nome, e o arquivo vale do mesmo
jeito.

Dentro do harness, elas valem com estes limites:

- As regras desta página vêm primeiro. Quando uma skill sugere uma
  biblioteca, como Motion, Sonner, Vaul ou React, use o equivalente em
  CSS, SVG ou JavaScript escrito no próprio arquivo. A skill
  `pick-ui-library` não serve às peças de entrega.
- As cores e as fontes saem de `_projeto/marca.md`. A skill ajusta a
  curva, o tempo e o detalhe, e nunca troca a marca.
- `break-ui` testa a peça com o pior caso, como rótulo longo, número
  grande ou lista vazia, em uma cópia de trabalho. A chave entre dado de
  demonstração e pior caso não vai para o arquivo entregue.
- A correção de gosto que o consultor fizer vira lição pela skill
  `registrar-licao`, e não um `DESIGN.md` da skill `learn-taste`.
- `animate-expo`, `write-swift` e `ask-sonner` tratam de aplicativo
  nativo, Swift e uma biblioteca de React. Vêm no conjunto e ficam fora
  das peças de entrega.

Onde as skills não estão instaladas, como no ChatGPT ou no Copilot, o
resumo do que elas cobram é este:

- A transição diz as propriedades que mudam. Nunca `all`.
- Quem entra usa `ease-out`, e o que já está na tela se move com
  `ease-in-out`. Nunca `ease-in`. Prefira as curvas fortes,
  `cubic-bezier(0.23, 1, 0.32, 1)` para entrar e
  `cubic-bezier(0.77, 0, 0.175, 1)` para mover.
- O retorno da interface fica entre 150 ms e 250 ms e não passa de
  300 ms. Painel e janela sobreposta vão até 500 ms. A animação que
  explica um resultado pode durar mais.
- Nada nasce de `scale(0)`. Comece de `scale(0.95)` com opacidade zero.
- Anime `transform` e `opacity`. Largura, altura e posição redesenham a
  página a cada quadro.
- Botão responde ao clique com `scale(0.97)`. O efeito de passar o
  mouse fica em `@media (hover: hover) and (pointer: fine)`.
- Em um grupo, cada item entra de 30 ms a 80 ms depois do anterior, e
  a entrada nunca impede o clique.
- O que a pessoa faz pelo teclado não anima.

## 2D ou 3D

Use 2D sempre que o plano der conta. Use 3D quando a terceira dimensão
carrega informação: camadas que se sobrepõem, profundidade de uma pilha,
um volume que se compara. Girar uma peça plana no espaço não acrescenta
nada.

Toda peça em 3D tem na mesma página a leitura em 2D do que ela mostra:
a lista das camadas, a legenda, os números. Quem não consegue girar a
cena ainda recebe a mensagem.

## A escada de técnicas, sem biblioteca

Suba um degrau só quando o anterior não resolve.

| Degrau | Serve para |
| --- | --- |
| HTML e CSS, com transições | Fluxos, passos, abas, antes e depois, barras |
| SVG desenhado no arquivo | Diagramas, gráficos, mapas de relação, ícones |
| Transformações 3D do CSS | Camadas, pilhas, cartões no espaço |
| Canvas 2D | Muitos pontos, partículas, gráficos com centenas de marcas |
| WebGL escrito à mão | Cena 3D de verdade, com malha e luz. Raro |

Toda imagem é um SVG escrito dentro do próprio HTML, com a tag `<svg>`.
Foto, captura de tela ou ícone em PNG, JPG, GIF ou WebP não entra, nem
em base64: redesenhe em SVG ou leve a imagem para a página do
entregável que a peça apoia. Fonte externa não entra: use a fonte do sistema ou embuta a fonte da marca quando a
licença permite. Nenhum pedido sai do arquivo, nem para medir acesso.

## O que a checagem cobra

A checagem `interativo` reprova:

- recurso fora do arquivo: script, folha de estilo, fonte, imagem,
  vídeo, quadro embutido ou chamada de rede;
- imagem que não é SVG, como PNG, JPG, GIF ou WebP em base64;
- arquivo sem `doctype`, idioma, codificação, `viewport` ou título;
- animação sem o tratamento de `prefers-reduced-motion`;
- evidência citada que não existe no registro;
- peça gravada sem storyline aprovada;
- arquivo acima de 15 MB.

E avisa quando falta o cabeçalho, o texto para quem está sem script, a
versão de impressão, a descrição de um `canvas`, a pausa de uma
animação contínua ou a fonte visível, e quando o movimento usa
`transition: all`, `scale(0)` ou `ease-in`. Na revisão, os avisos de
cabeçalho viram reprovação.

## Conferir renderizado

A peça só está pronta depois de aberta. Confira no computador e no
celular, no tema claro e no escuro, com o teclado, com movimento
reduzido e na visualização de impressão. Onde há Node e Playwright,
`node entregaveis/_harness/scripts/conferir_interativo.js ARQUIVO.html`
faz essa conferência, bloqueia qualquer pedido de rede, lista os erros e
grava as imagens. Um problema visto na tela é corrigido no arquivo e
conferido de novo.

## Entregar

- O arquivo fica em `interativos/` dentro da pasta do entregável e vai
  junto com o material que ele apoia, com uma linha que diz para que
  serve e como abrir.
- A página do entregável que a peça apoia traz uma imagem do estado
  principal. O material precisa se sustentar sem a peça.
- Alguns serviços de e-mail barram anexo `.html`. Nesse caso, envie em
  um arquivo compactado ou pelo repositório de arquivos do projeto.
- Publicar a peça em um serviço de páginas é uma saída do projeto. O
  consultor decide, e a peça precisa respeitar
  `_projeto/regras-de-material.md`.
