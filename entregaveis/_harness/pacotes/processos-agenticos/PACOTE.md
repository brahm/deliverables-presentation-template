# Pacote: processos agênticos e automação de marketing

## Quando usar

O projeto redesenha um processo de marketing para que agentes de IA e
automações façam parte do trabalho: produção e adaptação de conteúdo,
planejamento e operação de campanhas, relatórios, atendimento, gestão de
audiências. Serve para o mapa de oportunidades, o desenho do processo
alvo, a especificação de um agente, o plano de piloto e o modelo de
operação.

Quando a mudança atinge a organização inteira, some o pacote de
transformação de marketing.

## O que perguntar ao dono no início

Além das perguntas de `iniciar-projeto`:

- Que processo, ou que conjunto de processos, está em escopo?
- O que o cliente espera ganhar: tempo, volume, qualidade, custo?
- Onde o ganho de tempo vai parar: mais produção, outras atividades ou
  redução de equipe? A resposta muda o caso de negócio e a resistência.
- Que plataformas de IA e de automação o cliente já tem ou pode usar?
- Que regras da empresa valem para IA: dados que não podem sair,
  aprovação jurídica, política de marca?
- O entregável é o desenho, ou o piloto precisa rodar?
- Quem será o dono do processo depois do projeto?

## Entregáveis típicos

| Entregável | Veículo | Formato | Audiência que decide |
| --- | --- | --- | --- |
| Mapa de oportunidades | projetado | pptx, com a matriz em xlsx | Diretoria de marketing e de tecnologia |
| Desenho do processo alvo | leitura | pptx | Dono do processo e equipes |
| Especificação do agente | documento | docx | Tecnologia, dono do processo, jurídico |
| Plano de piloto e de avaliação | leitura | pptx ou docx | Dono do processo e patrocinador |
| Resultado do piloto e decisão de escala | projetado | pptx | Diretoria |
| Modelo de operação e governança | documento | docx | Marketing, tecnologia, risco |

## Frameworks

### 1. Seleção de processos

Uma matriz de valor e viabilidade, na planilha. Valor: volume, tempo
gasto hoje, efeito no resultado. Viabilidade: regras claras, dados e
sistemas acessíveis, tolerância a erro, facilidade de conferir o
resultado. Comece por processo frequente, com resultado fácil de
conferir e erro barato. Deixe para depois o que é raro, ambíguo ou
irreversível.

### 2. Mapa do processo atual

Siga casos reais de ponta a ponta. Para cada etapa: quem faz, com que
entrada, em que sistema, que decisão toma, quanto tempo leva, quanto
espera e que exceções aparecem. As exceções importam mais do que o
caminho feliz, porque é nelas que a automação quebra. É um diagrama de
fluxo com raias por papel.

### 3. Classificação das tarefas

Cada tarefa do processo cai em uma de quatro classes:

| Classe | Quando |
| --- | --- |
| Automação por regra | A entrada é estruturada e a regra é fixa |
| Agente com aprovação humana | Exige leitura, redação ou julgamento, e o erro custa caro |
| Agente autônomo com amostragem | Exige julgamento, o erro é barato e reversível |
| Pessoa | Decisão de risco alto, relação com gente, ou responsabilidade que não se delega |

O processo alvo mostra, etapa por etapa, a classe e o motivo.

### 4. Níveis de autonomia

| Nível | O agente | A pessoa |
| --- | --- | --- |
| 0 | Não participa | Faz tudo |
| 1 | Sugere | Decide e executa |
| 2 | Prepara o trabalho | Revisa e aprova tudo |
| 3 | Executa | Aprova nos pontos de controle definidos |
| 4 | Executa | Audita por amostragem e trata exceções |

Declare o nível de cada etapa e o critério para subir de nível: quantos
casos, com que taxa de acerto, por quanto tempo.

### 5. Especificação do agente

Uma página por agente, com os mesmos campos:

- objetivo, em uma frase, e o que está fora dele;
- entradas e de onde vêm;
- ferramentas e sistemas que ele pode usar, e com que permissão;
- o que ele entrega e em que formato;
- critérios de qualidade, com exemplos de saída boa e ruim;
- limites: o que ele nunca faz sem uma pessoa;
- quando para e a quem passa o caso;
- o que registra de cada execução.

Dê ao agente o menor conjunto de permissões que o trabalho exige.

### 6. Dados e integrações

As fontes de que o processo precisa, a qualidade delas, quem dá acesso e
o que precisa ser conectado. Muito projeto para aqui: o agente funciona
na demonstração e não tem acesso aos dados reais.

### 7. Avaliação

Antes do piloto, monte um conjunto de casos de teste com a resposta
esperada, incluindo as exceções. Indicadores: qualidade segundo o
critério declarado, tempo de ciclo, custo por execução, taxa de casos
passados a uma pessoa e taxa de retrabalho. No piloto, compare com o
processo atual no mesmo período e com o mesmo tipo de caso.

### 8. Riscos e guardas

| Risco | Guarda |
| --- | --- |
| Erro de fato ou promessa indevida em conteúdo | Fontes aprovadas, revisão humana, lista do que não se afirma |
| Desvio de marca e de tom | Guia de marca nas instruções, exemplos, revisão por amostragem |
| Uso indevido de dados pessoais | Dados mínimos, base legal conferida, ambiente aprovado |
| Instrução maliciosa em conteúdo lido pelo agente | Separar dados de instruções, permissões mínimas, aprovação para ações externas |
| Ação irreversível errada | Aprovação humana antes de enviar, publicar, gastar ou apagar |
| Falta de rastro | Registro de cada execução: entrada, saída, quem aprovou |
| Dependência de fornecedor ou de modelo | Critérios de saída e testes que podem ser repetidos em outro modelo |

Cada risco do processo em escopo tem dono e guarda na especificação.

### 9. Modelo de operação

Quem é o dono do processo e de cada agente, quem mantém instruções e
integrações, quem monitora a qualidade, como uma mudança é testada antes
de entrar e o que acontece quando o agente erra. Papéis novos costumam
aparecer: dono do agente, revisor, responsável pela avaliação.

### 10. Pessoas e mudança

O que cada papel para de fazer, começa a fazer e continua fazendo. Quem
revisa o trabalho do agente precisa saber o que procurar. Diga com
clareza o destino do tempo liberado, porque é a primeira pergunta das
equipes.

### 11. Caso de negócio

Tempo de ciclo, volume, qualidade e custo, antes e depois. O custo
inclui plataforma, uso do modelo, integração, revisão humana e
operação. Hora liberada só vira economia se alguém decidir o que fazer
com ela: declare a premissa. Use os números do piloto e um cenário
conservador.

## Esqueletos de storyline

### Mapa de oportunidades

1. Capa
2. Resumo: onde começar, o que se ganha e o pedido
3. Como o trabalho anda hoje, em um caso real
4. Onde o tempo vai e onde ficam as esperas
5. Os processos avaliados, na matriz de valor e viabilidade
6. Os dois ou três processos para começar, e por quê
7. O que fica para depois, e por quê
8. O que precisa existir antes: dados, acessos, regras
9. O piloto proposto e como será avaliado
10. O pedido: decisões, donos e datas
11. Apêndice: método, critérios da matriz e fontes

### Desenho do processo alvo

1. O processo hoje e o que ele custa
2. O processo alvo, etapa por etapa, com a classe de cada tarefa
3. O nível de autonomia de cada etapa e o critério para subir
4. Os agentes: uma página cada
5. Os pontos de controle humano
6. Riscos e guardas
7. O que muda para cada papel
8. O plano de piloto
9. O pedido

### Resultado do piloto

1. Resumo: o resultado, a recomendação e o pedido
2. O que foi testado e como
3. Qualidade, tempo e custo, contra o processo atual
4. Onde o agente errou e o que foi feito
5. O que as equipes disseram
6. A decisão: escalar, ajustar ou parar
7. O que a escala exige
8. O pedido

## Evidência que cada afirmação pede

| Afirmação | Fonte aceitável |
| --- | --- |
| Tempo e volume do processo atual | Registros do fluxo de trabalho ou medição acompanhada, com período |
| Qualidade da saída do agente | Avaliação no conjunto de casos de teste, com critério declarado |
| Ganho de tempo | Piloto comparado ao processo atual, mesmo tipo de caso |
| Custo por execução | Fatura ou preço público da plataforma, mais o tempo de revisão medido |
| Taxa de erro e de casos passados a pessoas | Registro das execuções do piloto |
| Capacidade de uma plataforma | Documentação do fornecedor ou teste feito no projeto |
| Economia anual | Cálculo na planilha, com a premissa sobre o destino das horas |
| Opinião das equipes | Entrevistas ou pesquisa, com o número de respondentes |

## Armadilhas

- Começar pela tecnologia e procurar um processo para ela.
- Mapear só o caminho feliz.
- Mostrar uma demonstração como prova. A prova é o piloto com casos
  reais e critério declarado.
- Prometer economia de horas sem dizer para onde as horas vão.
- Dar ao agente mais permissões do que a tarefa exige.
- Deixar sem aprovação humana o que envia, publica, gasta ou apaga.
- Esquecer o custo da revisão humana no caso de negócio.
- Entregar o desenho sem dono para a operação.
- Afirmar o que uma plataforma faz com base no material de venda dela.
- Usar termos de IA que a audiência não usa. Traduza na primeira vez e
  ponha no glossário.
