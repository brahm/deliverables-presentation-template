---
name: preparar-entrega
description: Use quando a revisão de um entregável passou e ele vai ser apresentado ou enviado. Prepara a versão curta, as perguntas previstas, as notas, a pré-leitura, as versões em outros idiomas e o texto de envio.
metadata:
  origem: harness-de-entregaveis
---

# Preparar a entrega

O método está em `entregaveis/_harness/metodo/metodo.md`, seção 8. Guarde
o resultado em `entrega.md`, na pasta do entregável.

1. Versão curta. Liste as páginas do caminho de cinco minutos: a
   conclusão, os argumentos e o pedido.
2. Perguntas previstas. Parta das resistências do briefing e do que a
   revisão levantou. Cada pergunta difícil tem uma resposta curta e, se
   preciso, uma página de apoio no apêndice.
3. Roteiro. Confira as notas de quem apresenta e marque em que página
   estar a cada quarto do tempo. Defina os dois pontos de encerramento.
4. Antes e depois. Diga o que vai como pré-leitura e o que fica como
   material de apoio.
5. Outros idiomas. Reescreva o conteúdo aprovado em `conteudo.xx.md` ou
   `documento.xx.md`, para o leitor daquele idioma. Números, fontes e
   títulos dizem o mesmo em todas as versões. Valide cada versão.
6. Arquivo final. Gere em `saida/` com a skill `desenhar-visual` e
   `gerar.py`, uma vez por idioma (`--idioma es`), renomeie para o
   padrão de nome do projeto e confira a marcação obrigatória. As
   peças de `interativos/` vão junto, cada uma com uma linha que diz
   para que serve e como abrir.
7. Em apresentação remota, prepare as instruções de acesso, um plano
   para falha de tecnologia e os momentos de interação.
8. Escreva o texto de envio: o pedido na primeira frase, o prazo e o que
   está anexo. Quem envia é o consultor. Nada sai do projeto sem ele.
9. Quando o consultor disser que apresentou ou enviou, mude o `estado` para
   `entregue` e siga `fechar-entregavel`.
