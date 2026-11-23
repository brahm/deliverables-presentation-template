# Pacote: assessment de arquitetura de martech e adtech

## Quando usar

O projeto avalia as plataformas de marketing e de mídia de uma empresa e
recomenda o que manter, consolidar, substituir, desligar ou contratar.
Serve também quando o pedido é uma arquitetura alvo, um roadmap de
plataformas ou a escolha de uma plataforma específica.

Projeto de mídia sem pergunta de plataforma usa o pacote de mídia.
Projeto de rede de mídia de varejo usa o de retail media.

## O que perguntar ao consultor no início

Além das perguntas de `iniciar-projeto`:

- Que decisão motivou o assessment: renovação de contrato, corte de
  custo, troca de plataforma, nova estratégia de dados, auditoria?
- O escopo cobre martech, adtech ou os dois? Inclui dados e analytics?
- Há uma plataforma cuja permanência já foi decidida, ou cuja saída já
  foi decidida?
- Quem patrocina e quem pode vetar: marketing, tecnologia, dados,
  compras, jurídico?
- O cliente espera uma nota de maturidade? Com que referência de
  comparação?

## Entregáveis típicos

| Entregável | Veículo | Formato | Audiência que decide |
| --- | --- | --- | --- |
| Leitura executiva do assessment | projetado | pptx | Diretoria de marketing e de tecnologia |
| Relatório do assessment | leitura ou documento | pptx ou docx | Donos das plataformas e arquitetura |
| Inventário de plataformas | planilha | xlsx | Arquitetura, compras e donos das plataformas |
| Arquitetura alvo | leitura | pptx | Arquitetura e donos das plataformas |
| Roadmap e caso de negócio | projetado | pptx, com a base em xlsx | Diretoria e financeiro |
| Requisitos para escolha de plataforma | documento | docx, com a matriz em xlsx | Compras, arquitetura e a área usuária |

## Frameworks

Cada framework abaixo diz o que produz, de que dados precisa e que tipo
de página costuma mostrar o resultado.

### 1. Inventário de plataformas

A base de todo o resto. Uma linha por plataforma contratada ou
construída, na planilha. Colunas: nome, categoria, capacidade principal,
área dona, usuários ativos, contrato (início, fim, aviso de renovação),
custo anual (licença, serviços, operação), integrações, dados pessoais
que trata, e a decisão recomendada.

Uma plataforma que ninguém da empresa sabe dizer de quem é já é um
achado. Registre como está e não adivinhe o dono.

### 2. Mapa de capacidades em camadas

A arquitetura descrita pelo que ela precisa fazer, antes dos nomes dos
produtos. É um diagrama de pilha.

| Camada | Capacidades |
| --- | --- |
| Coleta e consentimento | Tags, SDKs, coleta pelo servidor, gestão de consentimento |
| Dados e identidade | Armazém de dados, perfil único de cliente, resolução de identidade, segmentação |
| Decisão e inteligência | Modelos de propensão, recomendação, regras de próxima ação, testes |
| Orquestração e conteúdo | Jornadas, automação de campanhas, gestão de conteúdo e de ativos |
| Entrega própria | E-mail, push, SMS, mensageria, site, aplicativo, atendimento |
| Mídia paga | Compra programática, servidor de anúncios, redes sociais e busca, verificação |
| Medição | Analytics, atribuição, modelo de mix de marketing, testes de incrementalidade |
| Governança e operação | Catálogo de dados, privacidade, acessos, monitoramento, custos |

Pinte cada capacidade pelo estado: atendida, atendida por mais de uma
plataforma, atendida em parte, não atendida. O mapa pintado é a página
que a audiência mais lembra.

### 3. Escala de maturidade

Declare a escala e os critérios antes de dar qualquer nota. A mesma
evidência precisa levar dois avaliadores à mesma nota.

| Nota | Nome | Critério geral |
| --- | --- | --- |
| 1 | Inicial | A capacidade não existe ou depende de trabalho manual e de uma pessoa. |
| 2 | Em formação | Existe em uma área ou canal, sem integração e sem dono definido. |
| 3 | Definida | Tem dono, processo e integração com os dados principais. O uso é irregular. |
| 4 | Gerida | É usada em rotina, medida por indicadores e revisada. |
| 5 | Otimizada | Melhora por teste contínuo e alimenta as outras capacidades. |

Dimensões: dados e identidade, ativação e jornadas, mídia e adtech,
medição, conteúdo, operação e governança, pessoas e processos.

Para cada dimensão, escreva o critério específico de cada nota e a
evidência que sustenta a nota dada: uma entrevista, um dado de uso, um
documento. Nota sem evidência é opinião e não entra. Só compare com
outras empresas quando houver uma fonte citável.

### 4. Sobreposição, lacuna e subuso

Uma matriz de capacidades (linhas) por plataformas (colunas). Marque o
que cada plataforma faz hoje e o que poderia fazer com a licença já
paga. Três leituras saem dela:

- sobreposição: duas ou mais plataformas pagas para a mesma capacidade;
- lacuna: capacidade necessária que nenhuma atende;
- subuso: capacidade licenciada e não usada.

Subuso costuma render mais do que troca de plataforma. Mostre o custo
da licença parada com o número do contrato.

### 5. Fluxo do dado

O caminho de um dado de cliente da coleta à ativação e à medição, com o
ponto em que o consentimento é verificado, os pontos de cópia manual e o
tempo entre o evento e o uso. É um diagrama de fluxo. Escolha um ou dois
casos reais, como carrinho abandonado ou exclusão de clientes de uma
campanha de aquisição, e siga o dado de ponta a ponta.

### 6. Cadeia de mídia e taxas

Para adtech: o caminho de um real investido até a impressão. Agência,
mesa de operação, plataforma de compra, dados de terceiros, verificação,
plataforma de venda e veículo. Cada elo com a taxa e com quem detém o
contrato e os dados. É um gráfico de cascata.

Pergunte de quem são as contas das plataformas, os dados de campanha e
as audiências. Em muitos casos pertencem à agência, e isso muda a
recomendação.

### 7. Identidade e sinais

Como a empresa reconhece uma pessoa entre canais e o que acontece com a
restrição de cookies de terceiros e de identificadores de dispositivo.
Itens a avaliar: taxa de usuários identificados, base com consentimento
por finalidade, envio de conversões pelo servidor, uso de dados próprios
na compra de mídia, salas limpas de dados.

### 8. Custo total e uso

Por plataforma: licença, serviços de implantação, integração, operação
interna e de parceiros. Ao lado, o uso: usuários ativos sobre licenças
pagas, volume usado sobre volume contratado, recursos usados sobre
recursos licenciados. A página mostra o custo por capacidade usada.

### 9. Decisão por plataforma

Uma das cinco, com o motivo e a evidência: manter, consolidar,
substituir, desligar, contratar. A decisão considera a data de renovação
do contrato, que define a janela em que a mudança é possível.

### 10. Casos de uso, roadmap e caso de negócio

Priorize casos de uso de negócio, e não plataformas, em uma matriz de
valor e esforço. Organize o caminho em ondas, cada uma com entrega que a
audiência reconhece. O caso de negócio separa custo evitado (licenças,
taxas, operação) de receita incremental, mostra as premissas e traz um
cenário conservador.

## Esqueletos de storyline

Pontos de partida. A storyline de cada entregável é escrita para a
audiência dele e aprovada pelo consultor.

### Leitura executiva do assessment

1. Capa
2. Resumo: a conclusão, o custo de não agir e o pedido
3. O que a empresa quer do marketing e o que a arquitetura entrega hoje
4. O mapa de capacidades pintado: onde há sobra, falta e subuso
5. O achado principal, com o número que o prova
6. O segundo achado
7. O terceiro achado
8. O que isso custa por ano
9. A arquitetura alvo em uma página
10. O caminho em ondas e o que cada onda entrega
11. O caso de negócio, com as premissas
12. O pedido: decisões, donos e datas
13. Apêndice: escala de maturidade, inventário, método e fontes

### Arquitetura alvo

1. Os princípios que guiaram o desenho, cada um ligado a um achado
2. O mapa de capacidades alvo
3. A decisão por plataforma
4. O fluxo do dado depois da mudança, no mesmo caso real do diagnóstico
5. O que muda para cada área
6. Riscos e dependências
7. O pedido

### Roadmap e caso de negócio

1. Resumo com o valor, o investimento e o prazo de retorno
2. Os casos de uso priorizados
3. As ondas
4. Custo evitado e receita incremental, com as premissas
5. O cenário conservador
6. O que precisa ser decidido agora, por causa das datas de renovação
7. O pedido

## Evidência que cada afirmação pede

| Afirmação | Fonte aceitável |
| --- | --- |
| Custo de uma plataforma | Contrato, fatura ou extrato de compras |
| Uso de uma plataforma | Relatório de uso da própria plataforma ou do administrador |
| Sobreposição de capacidade | Inventário validado pelos donos das duas plataformas |
| Nota de maturidade | Critério declarado mais entrevista, documento ou dado de uso |
| Tempo entre evento e ativação | Medição em um caso real, com data |
| Taxa na cadeia de mídia | Contrato ou relatório da agência e das plataformas |
| Comparação com o mercado | Estudo citável, com nome, autor e ano |
| Valor de um caso de uso | Premissas escritas, com a origem de cada uma |

## Armadilhas

- Começar pelos nomes dos produtos. A audiência executiva decide sobre
  capacidades e custo, e os produtos aparecem depois.
- Dar nota de maturidade sem critério declarado.
- Recomendar a troca de uma plataforma quando o problema é de processo,
  de dados ou de time. Uma plataforma nova herda os três.
- Chamar de redundância o que é uso legítimo por regiões ou marcas com
  necessidades diferentes. Pergunte antes de contar.
- Ignorar as datas de renovação. Uma recomendação fora da janela do
  contrato espera um ano.
- Apresentar o caso de negócio só com receita incremental. O financeiro
  acredita primeiro no custo evitado.
- Tratar privacidade como apêndice. Consentimento e base legal decidem o
  que a arquitetura pode ativar.
- Mostrar o diagrama de arquitetura completo em uma página projetada.
  Ele vai para o apêndice ou para o documento de leitura. A página
  projetada mostra o recorte que prova o título.
- Citar o nome de um fornecedor como recomendação sem um processo de
  escolha. O assessment define requisitos, e a escolha é outro trabalho.
