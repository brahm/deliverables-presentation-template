---
name: iniciar-projeto
description: Use de imediato, sem esperar pedido, quando o estado diz que o projeto não foi iniciado e o trabalho está começando agora, ou quando o consultor traz o brief de um projeto novo. Pergunta do que é o projeto, pede os materiais, ativa os pacotes do tipo de trabalho e fecha o brief com as suposições à vista.
metadata:
  origem: harness-de-entregaveis
---

# Iniciar o projeto

O consultor diz o que quer com as palavras dele. O resto é seu, de uma vez,
sem esperar que ele dite cada passo.

1. Confira a máquina: `python3 entregaveis/_harness/scripts/ambiente.py`.
   Se faltar algo, diga o que falta e para que serve, e ofereça as duas
   saídas: você instala, com o sim do consultor, ou ele segue o passo a
   passo que o script imprime. O que é essencial vem antes de tudo. O
   que só um formato de arquivo pede pode esperar a hora de gerar. Se o
   Python não roda, confira com `python --version` e `py -3 --version`.
   Onde nada pode ser instalado, leve o consultor ao caminho sem
   instalação de `entregaveis/_harness/ambientes/LEIA-ME.md`.
2. Confira onde o projeto vai ficar, antes de escrever qualquer coisa
   sobre o cliente: `python3 entregaveis/_harness/scripts/repositorio.py`.
   Um projeto só é iniciado em pasta sem git, em git local ou em
   repositório privado. Se o remoto for público, pare e leve ao consultor as
   saídas: criar um repositório privado a partir do template, tornar
   este privado, ou remover o remoto e seguir em git local. Se o remoto
   não pôde ser verificado, pergunte ao consultor se ele é privado e registre
   a resposta com `repositorio.py --confirmar "palavras do consultor"`.
   Depois rode `python3 entregaveis/_harness/scripts/preparar.py`. Ele
   cria `_projeto/`, `_intake/`, `_dominio/` e `_atas/` a partir dos modelos. Se o projeto já tem
   apresentações, documentos, dados ou regras de agente anteriores ao
   harness, pare aqui e siga `adotar-projeto`.
3. Leia o que o consultor já escreveu e tire dali o que der: cliente, tipo de
   trabalho, decisão esperada, entregáveis, prazos e idiomas.
4. Pergunte uma vez, em uma mensagem só, cada pergunta com a resposta
   que você assumiria. Se o consultor mandar decidir ou não puder responder
   agora, siga com as suposições.
   - Do que é o projeto e que decisão ele precisa provocar. Esta você
     faz sempre: diga o que entendeu e peça a confirmação.
   - O tipo de trabalho: transformação de marketing, assessment de
     martech e adtech, mídia, definição de processos de mídia digital,
     retail media, processos agênticos, proposta, treinamento ou outro.
   - Os entregáveis previstos, com formato, audiência e prazo.
   - Os idiomas dos entregáveis.
   - As regras da organização e do cliente para materiais: onde podem
     ficar, o que o agente pode ler, a classificação, a marcação
     obrigatória e os padrões de projeto.
   - Os materiais: modelos de apresentação, documento e planilha, guia
     de marca, apresentações de referência, escopo contratado e uma
     amostra de texto do consultor.
   - As reuniões que se repetem, com a frequência e a data da
     primeira. Elas vão para `_projeto/ritos.tsv`. Diga que as atas são
     salvas em `entregaveis/_atas/` e que a rotina do dia parte dali.
5. Preencha `_projeto/brief.md`, `audiencia.md` e
   `regras-de-material.md`. Ponha em `confidencial.tsv` os nomes que não
   podem aparecer em entregáveis.
6. Ative os pacotes do tipo de trabalho com
   `preparar.py --pacote NOME`. Os que existem estão listados em
   `entregaveis/_harness/pacotes/LEIA-ME.md`. Um pacote é ponto de
   partida genérico. O que é próprio deste trabalho entra no domínio do
   projeto: assim que o consultor fornecer referências, métodos, contexto e
   objetivo, aplique `calibrar-dominio`, que escreve o método, as
   regras de checagem e os casos de teste em `_dominio/`.
7. Abra o intake com `receber-materiais`: uma linha por material pedido,
   mais a lista de pedido de dados do pacote.
8. Adapte o harness ao projeto. Um procedimento que vai se repetir vira
   uma skill, um limite diferente vai para `limites.tsv` e os termos do
   cliente abrem o glossário.
9. Registre as decisões com `registrar-decisao`. As do consultor ficam
   `Vigente`, e as suas `Vigente (assumida)`.
10. Crie a pasta de cada entregável previsto com
   `preparar.py --entregavel ID --tipo T --veiculo V --formato F --idiomas I`.
   Depois defina a governança com `definir-governanca`: o nível pelo
   porte, os materiais que o projeto emite, quem aprova cada entregável
   e a linha de base.
11. Se o repositório foi criado a partir do template, apague os arquivos
    que só servem ao kit (a lista está em `_harness/kit.md`) e escreva
    um README do projeto.
12. Quando o brief não tiver mais `PREENCHER`, marque `iniciado: sim`,
    rode `python3 entregaveis/_harness/scripts/fase.py`, que registra a
    fase 1 em `_projeto/fases.md`, e depois
    `python3 entregaveis/_harness/scripts/validar.py`. Quando o projeto
    mudar de natureza, a skill `evoluir-projeto` abre a fase seguinte.
13. Relate com `relatar-ao-consultor`: o plano em poucas linhas, cada
    suposição com o id da decisão, os materiais pedidos e as perguntas
    em aberto.
