---
name: construir-interativo
description: Use quando o dono pede uma peça interativa ou animada, em 2D ou 3D, e quando uma página do storyboard fica mais fácil de entender com a audiência mexendo (percorrer um fluxo, girar uma arquitetura, testar uma premissa). Constrói um HTML de arquivo único, sem biblioteca nem recurso externo, que apoia a leitura do entregável.
metadata:
  origem: harness-de-entregaveis
---

# Construir um HTML interativo

As práticas estão em `entregaveis/_harness/metodo/interativo.md`. Leia a
página antes da primeira peça do projeto.

1. Confirme que a peça se paga. Diga em uma frase o que a audiência
   entende mexendo que não entenderia lendo a página. Sem essa frase,
   faça uma página estática com a skill `desenhar-visual`.
2. A história vem antes. A peça só nasce com o briefing completo e a
   storyline aprovada pelo dono, e a mensagem dela é uma das mensagens
   da storyline. O harness bloqueia a gravação fora dessa ordem.
3. Escolha o modelo de partida pela pergunta da audiência: `fluxo` para
   uma sequência, `camadas-3d` para partes que se empilham, `simulador`
   para premissas e resultado. Use 3D só quando a terceira dimensão
   carrega informação.
4. Crie o arquivo:
   `python3 entregaveis/_harness/scripts/preparar.py --entregavel ID --interativo NOME --base fluxo`.
   Ele nasce em `interativos/NOME.html`, dentro da pasta do entregável.
5. Preencha o cabeçalho do arquivo: `titulo`, `mensagem`, `apoia`,
   `fontes` e `idioma`. Em `fontes` entram os identificadores de
   `_projeto/evidencias.tsv`.
6. Troque os dados de exemplo pelos do projeto, no bloco JSON do
   arquivo. Dado que falta vira pedido no intake e fica marcado na tela
   como "A confirmar (M-nnn)". Não invente número para a peça ficar
   bonita.
7. Adapte o desenho. Aplique as cores e as fontes de
   `_projeto/marca.md` nas variáveis do início do estilo, nos dois
   temas. Mantenha um destaque por tela e as barras em escala.
8. Tudo fica dentro do arquivo: estilo, script, dados, SVG e imagens em
   base64. Nenhuma biblioteca, fonte, imagem ou chamada de rede de fora.
   Quando o modelo não basta, suba a escada de técnicas da página de
   método, um degrau por vez.
9. Mantenha o que os modelos já trazem: página completa ao abrir,
   teclado e foco visível, leitura em 2D ao lado de qualquer cena em 3D,
   pausa na animação contínua, movimento reduzido, versão de impressão,
   texto para quem está sem script, fonte e marcação na tela.
10. A cada gravação o hook roda a checagem `interativo` e devolve o que
    corrigir. O texto visível passa pela skill `humanizar-texto`.
11. Confira renderizado: computador e celular, tema claro e escuro,
    teclado, movimento reduzido e impressão. Onde há Node e Playwright,
    rode `node entregaveis/_harness/scripts/conferir_interativo.js`
    com o caminho do arquivo e olhe as imagens geradas. Sem eles, peça
    ao dono para abrir o arquivo e diga no relatório que a conferência
    renderizada não foi feita por você.
12. Ligue a peça ao material. A página que ela apoia recebe uma imagem
    do estado principal e uma linha que diz como abrir a peça. O
    material precisa se sustentar sem ela.
13. A peça entra na revisão junto com o entregável, com a skill
    `revisar-entregavel`. Publicar em um serviço de páginas ou enviar ao
    cliente é decisão do dono.
