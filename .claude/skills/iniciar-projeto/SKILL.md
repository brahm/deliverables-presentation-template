---
name: iniciar-projeto
description: Use de imediato, sem esperar pedido, quando o estado diz que o projeto não foi iniciado e o trabalho está começando agora, ou quando o dono traz o brief de um projeto novo. Pergunta do que é o projeto, pede os materiais, ativa os pacotes do tipo de trabalho e fecha o brief com as suposições à vista.
metadata:
  origem: harness-de-entregaveis
---

# Iniciar o projeto

O dono diz o que quer com as palavras dele. O resto é seu, de uma vez,
sem esperar que ele dite cada passo.

1. Confira onde o projeto vai ficar, antes de escrever qualquer coisa
   sobre o cliente: `python3 entregaveis/_harness/scripts/repositorio.py`.
   Um projeto só é iniciado em pasta sem git, em git local ou em
   repositório privado. Se o remoto for público, pare e leve ao dono as
   saídas: criar um repositório privado a partir do template, tornar
   este privado, ou remover o remoto e seguir em git local. Se o remoto
   não pôde ser verificado, pergunte ao dono se ele é privado e registre
   a resposta com `repositorio.py --confirmar "palavras do dono"`.
   Depois rode `python3 entregaveis/_harness/scripts/preparar.py`. Ele
   cria `_projeto/`, `_intake/` e `_dominio/` a partir dos modelos. Se o projeto já tem
   apresentações, documentos, dados ou regras de agente anteriores ao
   harness, pare aqui e siga `adotar-projeto`.
2. Leia o que o dono já escreveu e tire dali o que der: cliente, tipo de
   trabalho, decisão esperada, entregáveis, prazos e idiomas.
3. Pergunte uma vez, em uma mensagem só, cada pergunta com a resposta
   que você assumiria. Se o dono mandar decidir ou não puder responder
   agora, siga com as suposições.
   - Do que é o projeto e que decisão ele precisa provocar. Esta você
     faz sempre: diga o que entendeu e peça a confirmação.
   - O tipo de trabalho: transformação de marketing, assessment de
     martech e adtech, mídia, retail media, processos agênticos,
     proposta, treinamento ou outro.
   - Os entregáveis previstos, com formato, audiência e prazo.
   - Os idiomas dos entregáveis.
   - As regras da organização e do cliente para materiais: onde podem
     ficar, o que o agente pode ler, a classificação, a marcação
     obrigatória e os padrões de projeto.
   - Os materiais: modelos de apresentação, documento e planilha, guia
     de marca, apresentações de referência, escopo contratado e uma
     amostra de texto do dono.
4. Preencha `_projeto/brief.md`, `audiencia.md` e
   `regras-de-material.md`. Ponha em `confidencial.tsv` os nomes que não
   podem aparecer em entregáveis.
5. Ative os pacotes do tipo de trabalho com
   `preparar.py --pacote NOME`. Os que existem estão listados em
   `entregaveis/_harness/pacotes/LEIA-ME.md`. Um pacote é ponto de
   partida genérico. O que é próprio deste trabalho entra no domínio do
   projeto: assim que o dono fornecer referências, métodos, contexto e
   objetivo, aplique `calibrar-dominio`, que escreve o método, as
   regras de checagem e os casos de teste em `_dominio/`.
6. Abra o intake com `receber-materiais`: uma linha por material pedido,
   mais a lista de pedido de dados do pacote.
7. Adapte o harness ao projeto. Um procedimento que vai se repetir vira
   uma skill, um limite diferente vai para `limites.tsv` e os termos do
   cliente abrem o glossário.
8. Registre as decisões com `registrar-decisao`. As do dono ficam
   `Vigente`, e as suas `Vigente (assumida)`.
9. Crie a pasta de cada entregável previsto com
   `preparar.py --entregavel ID --tipo T --veiculo V --formato F --idiomas I`.
10. Se o repositório foi criado a partir do template, apague os arquivos
    que só servem ao kit (a lista está em `_harness/kit.md`) e escreva
    um README do projeto.
11. Quando o brief não tiver mais `PREENCHER`, marque `iniciado: sim` e
    rode `python3 entregaveis/_harness/scripts/validar.py`.
12. Relate com `relatar-ao-dono`: o plano em poucas linhas, cada
    suposição com o id da decisão, os materiais pedidos e as perguntas
    em aberto.
