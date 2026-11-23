# HTML interativo e animado

Um HTML interativo é uma peça de apoio. Ele ajuda a audiência a entender
e a ler o material de entrega: percorrer um fluxo, girar uma
arquitetura, testar uma premissa. A decisão continua sendo provocada
pela apresentação, pela proposta ou pelo documento.

A peça é um arquivo só. Abre com dois cliques em qualquer navegador, sem
internet, sem pasta de apoio e sem biblioteca externa. Vai por e-mail e
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

Imagem entra embutida no arquivo, como SVG ou em base64. Fonte externa
não entra: use a fonte do sistema ou embuta a fonte da marca quando a
licença permite. Nenhum pedido sai do arquivo, nem para medir acesso.

## O que a checagem cobra

A checagem `interativo` reprova:

- recurso fora do arquivo: script, folha de estilo, fonte, imagem,
  vídeo, quadro embutido ou chamada de rede;
- arquivo sem `doctype`, idioma, codificação, `viewport` ou título;
- animação sem o tratamento de `prefers-reduced-motion`;
- evidência citada que não existe no registro;
- peça gravada sem storyline aprovada;
- arquivo acima de 15 MB.

E avisa quando falta o cabeçalho, o texto para quem está sem script, a
versão de impressão, a descrição de um `canvas`, a pausa de uma
animação contínua ou a fonte visível. Na revisão, os avisos de
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
  dono decide, e a peça precisa respeitar
  `_projeto/regras-de-material.md`.
