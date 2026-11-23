# Pacote: treinamento

## Quando usar

O projeto entrega capacitação: curso, trilha de módulos, workshop,
material didático, exercícios, exames e guias para quem facilita. Serve
também para o workshop de trabalho de um projeto de consultoria, em que
o grupo precisa sair com uma decisão ou um produto.

Um treinamento existe para mudar o que as pessoas fazem no trabalho. Ele
é desenhado de trás para a frente: primeiro o que a pessoa fará de
diferente, depois como isso será verificado, e só então o conteúdo.

## O que perguntar ao consultor no início

Além das perguntas de `iniciar-projeto`:

- Quem são os participantes, quantos, com que experiência e em que
  idioma?
- O que eles precisam passar a fazer no trabalho depois do treinamento?
- Como a empresa saberá que funcionou?
- Qual é o formato: presencial, remoto ao vivo, autoinstrucional ou
  misto? Quanto tempo há e em quantas sessões?
- Quem facilita: o consultor, o time do cliente, outra pessoa? Com que
  domínio do assunto?
- Há exame, certificação ou nota mínima? O resultado tem consequência
  para o participante?
- Que ferramentas e dados os participantes usarão nos exercícios? Podem
  ser dados reais?
- Que materiais o cliente já tem sobre o assunto?

## Entregáveis típicos

| Entregável | Veículo | Formato | Para quem |
| --- | --- | --- | --- |
| Plano do curso | documento | docx | Patrocinador e recursos humanos, que aprovam |
| Slides de aula | workshop | pptx | Participantes, com as notas para quem facilita |
| Guia de quem facilita | documento | docx | Quem facilita |
| Caderno do participante | documento | docx ou pdf | Participantes |
| Caderno de exercícios | documento | docx, com dados em xlsx | Participantes |
| Gabarito comentado | documento | docx | Quem facilita e quem corrige |
| Exame e matriz de prova | documento | docx, com o banco de questões em xlsx | Quem aplica e quem corrige |
| Roteiro de workshop | documento | docx | Quem facilita e o patrocinador |
| Guia rápido de uma página | leitura | pdf | Participantes, depois do curso |

O gabarito e o banco de questões ficam em arquivos separados dos
materiais do participante, e a pasta `saida/` não os mistura.

## Frameworks

### 1. Análise de necessidade

Quatro perguntas: o que as pessoas fazem hoje, o que precisam fazer, por
que não fazem e o que o treinamento pode mudar. Quando a causa é falta
de ferramenta, de tempo ou de incentivo, treinamento não resolve, e o
plano do curso diz isso.

### 2. Objetivos de aprendizagem

Cada objetivo completa a frase "ao final, a pessoa é capaz de" com um
verbo que se observa. Os níveis, do mais simples ao mais exigente,
seguem a taxonomia de Bloom revisada:

| Nível | Verbos |
| --- | --- |
| Lembrar | listar, nomear, reconhecer |
| Entender | explicar, resumir, dar exemplo |
| Aplicar | usar, calcular, executar, configurar |
| Analisar | comparar, diagnosticar, separar causas |
| Avaliar | julgar, priorizar, recomendar, criticar |
| Criar | desenhar, planejar, propor, construir |

"Entender o funil" não se observa. "Diagnosticar em que etapa do funil
uma campanha perde mais" se observa. Três a cinco objetivos por módulo.

### 3. Desenho de trás para a frente

Para cada objetivo, nesta ordem:

1. a evidência de que a pessoa o atingiu: exercício, entrega ou questão;
2. a prática que a prepara para isso;
3. o conteúdo mínimo que a prática exige.

O conteúdo que não serve a nenhum objetivo sai, por mais interessante
que seja. Ele pode ir para a leitura complementar.

### 4. Estrutura de um módulo

| Momento | O que acontece | Parcela do tempo |
| --- | --- | --- |
| Abertura | Um caso ou uma pergunta que mostra por que isso importa | 5% a 10% |
| Conceito | Um conceito por vez, com o exemplo antes da regra | 20% a 30% |
| Demonstração | Quem facilita resolve um caso e pensa em voz alta | 10% a 15% |
| Prática | Os participantes resolvem, sozinhos ou em grupo | 35% a 50% |
| Retorno | Correção comentada e erros comuns | 10% a 15% |
| Fecho | O que levar para o trabalho e a ponte para o próximo módulo | 5% |

Nenhum bloco de exposição passa de 20 minutos sem atividade. Parta do
que o participante já sabe e peça que ele o diga primeiro.

### 5. Exercícios

Cada exercício tem: o objetivo que mede, o enunciado, os dados ou o
caso, o tempo, a forma de trabalho, o que entregar, o critério de
correção, o gabarito comentado e os erros comuns. Use casos do contexto
dos participantes. Dados reais só com autorização e sem dados pessoais.
A dificuldade sobe ao longo do módulo: exercício guiado, depois com
menos apoio, depois um caso aberto.

### 6. Exames

A matriz de prova vem antes das questões: objetivos nas linhas, níveis
nas colunas e o número de questões em cada célula, proporcional à
importância do objetivo. Regras para questões:

- cada questão mede um objetivo declarado;
- o enunciado traz uma situação, e não um pedido de definição, quando o
  objetivo é aplicar ou analisar;
- em múltipla escolha, há uma alternativa correta, as erradas são erros
  que alguém comete de verdade e todas têm tamanho parecido;
- sem "todas as anteriores", sem "nenhuma das anteriores" e sem negação
  dupla;
- nenhuma questão dá a resposta de outra;
- questão aberta tem rubrica de correção com níveis e exemplos.

Defina a nota mínima e o que acontece com quem não a atinge antes de
aplicar. Faça um teste do exame com duas ou três pessoas do público. O
banco de questões guarda, para cada questão, o objetivo, o nível, a
resposta e a justificativa.

### 7. Workshop de trabalho

Um workshop tem um produto: uma decisão, uma lista priorizada, um
desenho. O roteiro traz:

- o objetivo e o produto esperado, em uma frase;
- os participantes e por que cada um está ali;
- o que cada um prepara antes;
- a agenda com horário, atividade, dinâmica, material e responsável;
- as perguntas exatas de cada atividade;
- como as decisões são tomadas e registradas;
- o plano para quando o tempo acabar ou o grupo travar;
- o que acontece depois, com donos e datas.

Planeje para 60% do tempo. Em sessão remota, uma atividade a cada dez
minutos e instruções de acesso enviadas antes.

### 8. Materiais

| Material | Regra |
| --- | --- |
| Slides de aula | Apoiam a fala. O texto de estudo fica no caderno |
| Caderno do participante | Lido sem apresentador, com exemplos e espaço para notas |
| Guia de quem facilita | Tempo por bloco, o que dizer, perguntas a fazer, respostas esperadas, erros comuns |
| Guia rápido | Uma página, para consultar no trabalho |
| Leitura prévia | Curta, com uma pergunta para trazer respondida |

Um termo novo aparece definido na primeira vez e entra no glossário.

### 9. Avaliação do treinamento

Quatro níveis, do modelo de Kirkpatrick: reação dos participantes,
aprendizagem medida por exercício ou exame, aplicação no trabalho
algumas semanas depois e resultado para o negócio. Planeje no início
como cada nível será medido. A pesquisa de reação sozinha não diz se
alguém aprendeu.

### 10. Sustentação

O que acontece depois da sala: prática espaçada, um desafio aplicado ao
trabalho, acompanhamento do gestor, horários para dúvidas, comunidade.
Sem isso, a maior parte se perde em semanas.

## Esqueletos de storyline

Em treinamento, a storyline é o plano do curso: os módulos em ordem, o
objetivo de cada um e a evidência de aprendizagem.

### Curso em módulos

1. Capa
2. Para quem é, o que a pessoa fará de diferente e como será verificado
3. O mapa do curso: módulos, duração e dependências
4. Módulo 1: abertura com um caso do contexto dos participantes
5. Módulo 1: conceito, com o exemplo antes da regra
6. Módulo 1: demonstração
7. Módulo 1: exercício
8. Módulo 1: correção e erros comuns
9. Módulo 1: o que levar para o trabalho
10. Os módulos seguintes, na mesma estrutura
11. Avaliação final
12. O que acontece depois do curso
13. Apêndice: glossário, leituras e guia rápido

### Workshop de trabalho

1. Por que estamos aqui e o que sai desta sessão
2. O que já sabemos, em uma página
3. Atividade 1: a pergunta, a dinâmica e o tempo
4. Síntese da atividade 1
5. Atividade 2
6. Síntese e decisão
7. Próximos passos, com donos e datas

### Exame

1. Instruções: tempo, material permitido, nota mínima
2. Questões, agrupadas por módulo e em ordem de dificuldade
3. Em arquivo separado: gabarito, justificativas e rubricas

## Evidência que cada afirmação pede

| Afirmação | Fonte aceitável |
| --- | --- |
| Lacuna de competência do público | Avaliação, entrevistas com gestores ou dados de desempenho, por grupo |
| Conteúdo técnico ensinado | Material do projeto, documentação oficial ou fonte citável |
| Caso usado em aula ou exercício | Caso do cliente autorizado, ou caso fictício marcado como fictício |
| Dados de exercício | Dados reais autorizados e sem dados pessoais, ou dados fictícios marcados |
| Resposta de uma questão | Justificativa escrita no banco de questões, com a fonte |
| Resultado do treinamento | Exame, avaliação de aplicação ou indicador, com data e número de pessoas |

Um caso fictício não finge ser real. Os números dele são coerentes entre
si e trazem a marca de exemplo.

## Armadilhas

- Começar pelo conteúdo e deixar a prática para o tempo que sobrar.
- Escrever objetivos com "entender" e "conhecer".
- Ensinar tudo o que se sabe sobre o assunto.
- Usar os slides como apostila.
- Exercício sem gabarito ou sem critério de correção.
- Questão que mede memória quando o objetivo é aplicar.
- Alternativa errada absurda, que ninguém marcaria.
- Gabarito no mesmo arquivo que vai para o participante.
- Medir só a satisfação dos participantes.
- Workshop sem produto definido.
- Agenda que usa todo o tempo e não deixa folga.
- Guia de quem facilita que só repete os slides.
- Dados reais com informação pessoal em exercício.
