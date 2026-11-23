# Práticas de texto

Valem para todo texto de entregável: títulos, corpo de página, notas de
quem apresenta, documentos, propostas, e-mails de envio e material
didático. O princípio é um só: cada frase acrescenta algo que o leitor
ainda não tinha.

Um modelo de linguagem escreve o que serve a qualquer leitor e a
qualquer assunto. Uma pessoa escreve para um leitor e um assunto. Os
vícios abaixo são formas dessa escolha genérica, e o leitor os reconhece.

## O que cortar

| Vício | Exemplo | Como fica |
| --- | --- | --- |
| Contraste vazio: nega o que ninguém disse para dar peso ao que vem depois | "Não é apenas uma plataforma, é uma nova forma de trabalhar." | "A plataforma junta em uma tela as três aprovações que hoje passam por e-mail." |
| Anúncio do que vem | "Vamos explorar os principais achados." | Comece pelo primeiro achado. |
| Aviso de importância | "Vale ressaltar que o custo subiu." | "O custo subiu 18% em 2026." |
| Fecho que repete | Um parágrafo e depois "Esse é o verdadeiro ganho." | Corte o fecho, ou troque por um fato novo. |
| Resposta a objeção que ninguém fez | "Isso não significa que a equipe errou." | Corte, a menos que a audiência pense isso de fato. |
| Autoridade sem nome | "Especialistas apontam que..." | Cite a fonte do registro ou corte a afirmação. |
| Importância inflada | "Um marco na jornada de transformação." | Diga o que mudou e para quem. |
| Palavra de vitrine | "Solução robusta e inovadora." | Diga o que ela faz, com número ou exemplo. |
| Verbo comprido | "Serve como base", "destaca-se como" | "É a base", "é". |
| Gerúndio pendurado | "..., garantindo eficiência." | Diga a consequência em outra frase, se a fonte a sustenta. |
| Ressalva empilhada | "Pode potencialmente, em certa medida..." | Uma ressalva, e só quando a evidência pede. |
| Relação vaga | "Associado ao aumento de custo." | Diga a relação: causou, coincidiu, foi causado por. |
| Resto de conversa | "Espero que isso ajude." | Corte. |
| Texto que fala de si | "Esta seção apresenta..." | Apresente. |
| Título repetido na primeira frase | Título "Custos" e depois "Os custos importam." | Comece pelo conteúdo. |
| Trio forçado | "Mais ágil, mais simples e mais eficiente." | Fique com os itens que têm prova. |

Pontuação e forma:

- Sem travessão. Use vírgula, ponto, dois-pontos ou parênteses.
- Negrito só para o que o leitor precisa achar de relance. Rótulo em
  negrito em toda linha de uma lista é decoração.
- Títulos com maiúscula só na primeira palavra e em nomes próprios.
- Sem emoji e sem seta no meio da frase.
- Voz ativa quando ela diz quem faz. "A equipe de mídia aprova" é melhor
  que "a aprovação é realizada".

## O que fica quando foi planejado

Uma apresentação persuasiva usa recursos que, espalhados sem critério,
seriam vícios. Eles ficam quando foram planejados na seção "Recursos
planejados" da storyline e declarados no campo `recurso` da página.

| Recurso | Quando fica |
| --- | --- |
| Contraste entre o que é e o que poderia ser | As duas metades trazem informação. É a estrutura da narrativa. Declare `recurso: contraste`. |
| Repetição de uma frase ao longo do material | É a frase que a audiência deve repetir depois. Uma por material. |
| Frase curta e isolada | Em página do tipo `frase`, quando ela prepara ou fecha um momento. |
| Pergunta que abre a lacuna | "E se o plano de mídia fechasse em dois dias?", seguida da resposta. |
| Metáfora | Uma, escolhida para esta audiência, que atravessa o material. |
| História com emoção | Um caso real, com quem, onde, conflito e desfecho. |
| Trio | Quando os itens são três de fato e cada um tem a sua prova. |
| Rótulo em negrito | Em slide, quando o rótulo é parte do desenho da página. |

Sem a declaração, as checagens tratam o contraste como vício. Os outros
recursos são julgados na revisão.

## Por tipo de texto

| Texto | Forma |
| --- | --- |
| Título de página | Uma frase com verbo que diz a mensagem. Até duas linhas. |
| Corpo de slide projetado | Só o que ajuda a audiência a entender e lembrar. O que serve de lembrete para quem fala vai para as notas. |
| Corpo de deck de leitura | Frases completas e curtas. O leitor está sozinho com a página. |
| Documento | A conclusão no primeiro parágrafo. Parágrafos curtos. Lista só para itens paralelos. |
| Notas de quem apresenta | Linguagem de fala, com as transições e a história que a página não mostra. |
| E-mail de envio | O pedido na primeira frase, o prazo e o que está anexo. |
| Material didático | Um conceito por vez, exemplo antes da regra, exercício logo depois. |

## Voz

Quando o registro de intake tem uma amostra de texto do consultor (tipo
`voz`), leia a amostra antes de escrever. Siga o tamanho das frases, o
vocabulário e as transições dela. A amostra vence as regras de pontuação
desta página, menos a do travessão em material para cliente.

Sem amostra, o tom é o de um colega competente explicando o assunto a
quem não estava na sala.

## Como isso é aplicado

- A cada gravação de um arquivo de entregável, o hook roda as listas de
  `_harness/listas/` do idioma do arquivo e devolve os achados.
- `validar.py --so texto` roda as mesmas listas em todo o entregável.
- A skill `humanizar-texto` cobre o que uma lista não vê: fechos que
  repetem, trios, texto escrito para o leitor errado.

Um trecho citado entre aspas não é examinado. Quando o material precisa
citar uma expressão da lista, ponha a expressão entre aspas.
