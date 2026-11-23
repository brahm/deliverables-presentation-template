# Pacote: proposta

## Quando usar

O trabalho é uma proposta: proposta comercial, resposta a uma
concorrência, apresentação oral da proposta, extensão de um projeto em
andamento ou pedido interno de investimento.

Uma proposta não é um projeto. Ela dura pouco, não tem linha de base,
status nem aceite, e por isso pede menos governança do que o nível
enxuto. Este pacote faz duas coisas: pede ao consultor as informações de
que a proposta é feita e mantém dois controles.

Ele não traz método de construção de proposta, roteiro de seções,
esqueleto de história nem argumento pronto. O método, o contexto e o
conteúdo chegam do consultor durante a construção e ficam em
`entregaveis/_dominio/`, pela skill `calibrar-dominio`. A forma do texto
e da história continua vindo das páginas de método do harness.

Quando a proposta é de um trabalho que tem pacote próprio, some esse
pacote. Enquanto o projeto for uma proposta, os controles dele ficam em
espera e passam a valer quando o trabalho for vendido.

## O que perguntar ao consultor no início

Além das perguntas de `iniciar-projeto`:

- Quem decide a compra, quem influencia e quem pode vetar?
- Há concorrência e pedido formal do cliente, com formato e prazo?
- A organização do consultor tem método, roteiro ou modelo próprio de
  proposta que este material precisa seguir?
- Quem aprova o preço, o escopo e os termos do lado do consultor?
- Que casos, clientes e pessoas podem ser citados, e quem autoriza?
- Em que ordem o consultor prefere fornecer as informações da tabela
  abaixo, e quais ele já tem prontas?

## Informações que o consultor fornece

As informações estão em `insumos.tsv` e aparecem com
`governanca.py --insumos`. O agente pede cada uma, guarda onde a tabela
diz e não escreve nenhuma no lugar do consultor.

| Informação | Vale | Antes de | O que perguntar |
| --- | --- | --- | --- |
| Objetivo da proposta | Sempre | Storyline | O que o cliente quer alcançar e que decisão a proposta precisa provocar |
| Ponto de vista | Sempre | Storyline | A leitura do consultor sobre o problema e a tese que a proposta defende |
| Abordagem | Sempre | Storyline | Como o trabalho será feito, em que fases e com que entregas |
| Tarefas | Sempre | Redação | As tarefas de cada fase, o que está dentro, o que está fora e o que depende do cliente |
| Cronograma | Sempre | Redação | A duração de cada fase, os marcos e as datas já fixadas |
| Equipe recomendada | Sempre | Redação | Quem compõe a equipe, com que papel e dedicação |
| Preço | Sempre | Revisão | O preço, as premissas, as condições comerciais e quem aprovou |
| Método e modelo de proposta da casa | Quando a organização do consultor tem método ou modelo próprio | Storyline | O método, o roteiro de seções e o modelo a seguir |
| Pedido formal do cliente | Quando o cliente enviou pedido, requisitos ou critérios | Storyline | Os requisitos, o formato obrigatório, os critérios e o prazo |

A informação condicional começa como "a confirmar", e o consultor diz se
vale. A lista do dia mostra o que falta. Um entregável que chega à etapa
sem a informação é acusado como erro pelo `validar.py`, e a página que
dependia dela fica com a lacuna à vista.

## Controles de governança

Os controles estão em `controles.tsv` e aparecem com
`governanca.py --controles`.

| Controle | Vale | Antes de | O que protege |
| --- | --- | --- | --- |
| Aprovação do preço, do escopo e dos termos | Sempre | Envio | Nada chega ao cliente com um número ou uma condição que ninguém aprovou |
| Autorização para citar casos, clientes e pessoas | Quando a proposta cita um caso, outro cliente, um resultado ou um currículo | Envio | Nenhum outro cliente e nenhuma pessoa aparecem sem autorização registrada |

Um controle só é dado como cumprido com a evidência e com o nome de quem
confirmou. A dispensa é do consultor, com o motivo.

## Nível de governança

`governanca.py --sugerir` propõe o nível proposta, que fica abaixo do
enxuto: nenhum material de governança é emitido. Os registros continuam
disponíveis para o que precisar ser anotado, como uma decisão ou uma
premissa. O consultor pode pedir um material avulso ou escolher um nível
de projeto, se quiser acompanhar a proposta como um.

Quando a proposta é vendida, a skill `evoluir-projeto` abre a fase do
trabalho. O que a proposta prometeu vira a linha de base dessa fase, e o
nível de governança é escolhido de novo.

## O que este pacote não traz

- O método e o processo de construção de proposta.
- O roteiro de seções, a ordem do material e o modelo de documento.
- Os argumentos, os temas, os casos e as provas.
- A forma de calcular e de apresentar o preço.
- O contexto do cliente e da concorrência.

Tudo isso é do consultor ou da organização dele, chega durante a
construção da proposta e fica só no projeto.
