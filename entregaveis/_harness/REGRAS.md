# Regras do Deliverables Presentation Template

Este projeto produz entregáveis de consultoria: apresentações, propostas,
documentos, planilhas e materiais de treinamento. O consultor decide
e aprova. Você planeja, escreve, valida e mantém os registros.

As regras são curtas de propósito. Elas dizem o que não pode ser
esquecido e apontam para as páginas de `entregaveis/_harness/metodo/`,
que você abre quando a tarefa pede.

## Como o trabalho corre

1. Comece pelo estado. `python3 entregaveis/_harness/scripts/estado.py`
   diz em poucas linhas o tipo do projeto, a etapa de cada entregável, os
   materiais pendentes, as decisões à espera do consultor e o que a
   rotina do dia tem a tratar. O Claude Code roda
   o script sozinho no início da sessão. Em outro agente, rode-o primeiro.
2. As skills se aplicam sozinhas. O consultor nunca precisa citar uma. Quando
   chegar um destes momentos, abra `.claude/skills/NOME/SKILL.md` e siga:

   | Momento | Skill |
   | --- | --- |
   | O harness chegou a um projeto que está começando | `iniciar-projeto` |
   | O harness foi instalado em um projeto já em andamento | `adotar-projeto` |
   | Falta um material, ou um material chegou | `receber-materiais` |
   | O consultor forneceu referências, métodos, contexto ou objetivo do projeto | `calibrar-dominio` |
   | Um entregável novo foi pedido | `preparar-briefing` |
   | O briefing está completo | `construir-storyline` |
   | O consultor aprovou a storyline | `montar-storyboard` |
   | O storyboard está pronto | `redigir-conteudo` |
   | Uma página mostra dados, relação entre itens ou imagem | `desenhar-visual` |
   | A audiência entende melhor mexendo, ou o consultor pede uma peça interativa | `construir-interativo` |
   | Um HTML de entrega é criado, alterado ou revisado | `emil-design-eng` |
   | Um texto de entregável foi escrito ou alterado | `humanizar-texto` |
   | Antes de dizer que um entregável está pronto | `revisar-entregavel` |
   | A revisão passou | `preparar-entrega` |
   | O material foi apresentado ou enviado | `fechar-entregavel` |
   | O projeto muda de natureza: a proposta foi vendida, uma extensão foi contratada, o trabalho é de outro tipo | `evoluir-projeto` |
   | O dia de trabalho começa ou termina, ou o estado mostra a rotina do dia | `rotina-diaria` |
   | Uma ata aparece na pasta de atas, ou o consultor conta o que houve em uma reunião | `processar-ata` |
   | Um arquivo aparece na pasta de entrada, ou o consultor fez um material à mão | `incorporar-material` |
   | O consultor diz que algo não será mais feito ou não depende mais de aprovação | `registrar-dispensa` |
   | O consultor decide, ou você decide o que ele deixou em aberto | `registrar-decisao` |
   | Algo pedido não será feito agora | `adiar-trabalho` |
   | O consultor corrige você, ou um erro se repete | `registrar-licao` |
   | Qualquer relatório ao consultor | `relatar-ao-consultor` |
   | O consultor leva o trabalho ao Claude desktop, ao ChatGPT ou ao Copilot, ou traz de lá o que foi feito | `usar-outro-ambiente` |
   | O brief foi fechado, o projeto foi adotado, o porte mudou ou o consultor pede, tira ou muda um material de governança | `definir-governanca` |
   | Chega o dia do status, o consultor pede um status, uma pauta ou um aceite, um entregável é enviado ou aceito, ou surge um pedido fora do combinado | `emitir-material` |
   | Um registro, uma ata, um material ou um entregável mudou, ou é preciso saber o que o projeto já sabe | `manter-cerebro` |
   | O harness tem uma versão nova | `atualizar-harness` |

   Um pacote ativo traz a sua própria skill, `pacote-NOME`, que se
   aplica nos momentos que a descrição dela diz, junto com as da tabela.

3. Quem decide.
   - O consultor decide o objetivo, o escopo, a audiência, a grande ideia e a
     storyline. Também decide tudo o que sai do projeto ou não pode ser
     desfeito: enviar algo ao cliente, apagar material, citar um dado
     sensível. Pare essa parte, pergunte uma vez com as opções e a que
     você recomenda, e siga com o resto.
   - Você decide, registrando, o que o consultor deixou em aberto e o trabalho
     precisa. Escolha o que serve melhor ao objetivo, registre em
     `entregaveis/_projeto/decisoes.md` como `Vigente (assumida)` e liste
     no relatório. O consultor confirma ou troca.
   - Você decide o resto, que é o como.
   - Mudança de escopo não é mudança de projeto. Quando mudam os
     entregáveis, um prazo ou uma audiência dentro do mesmo contrato e
     do mesmo tipo de trabalho, registre a decisão e siga. Quando muda o
     contrato, o tipo de trabalho ou a decisão que o projeto precisa
     provocar, o projeto entra em uma fase nova, que herda o contexto e
     o histórico: aplique `evoluir-projeto`. Na dúvida, diga qual das
     duas você entendeu e pergunte uma vez.
4. Sempre pergunte do que é o projeto. Não presuma o tipo de trabalho, a
   audiência, o idioma nem o formato. O que o consultor responder define os
   pacotes, as skills e as checagens que o projeto usa. As referências,
   os métodos, o contexto e o objetivo que ele fornecer viram o domínio
   do projeto, em `entregaveis/_dominio/`: o método, as regras de
   checagem e um caso de teste que acusa e outro que passa para cada
   regra. O domínio é escrito no projeto e nunca volta ao template.

## Antes de escrever

5. A história vem antes da página. A ordem é briefing, storyline aprovada
   pelo consultor, storyboard e só então páginas. O harness bloqueia a
   gravação de páginas fora dessa ordem.
6. Cada entregável tem uma audiência que decide, uma grande ideia em uma
   frase e um pedido com dono e prazo. Se você não consegue escrever os
   três, o briefing não está pronto.
7. Toda afirmação tem fonte. Cada número e cada achado tem uma linha em
   `entregaveis/_projeto/evidencias.tsv`, com fonte e data. Uma suposição
   é escrita como suposição.
8. Peça o que falta e não invente. Dados, nomes, casos, citações e
   números vêm dos materiais do projeto. O que falta vira um pedido no
   registro de intake e uma lacuna visível no material.

## Enquanto escreve

9. O veículo define a forma. Um slide projetado, um deck de leitura, um
   relatório e uma planilha têm limites diferentes, descritos em
   [metodo/formatos.md](metodo/formatos.md). Um HTML interativo é uma
   peça de apoio em arquivo único, sem recurso externo, e segue
   [metodo/interativo.md](metodo/interativo.md). Todo HTML que o
   harness gera, de qualquer tipo, é um arquivo completo: estilo,
   script, dados e imagens ficam no próprio documento, sem nada de fora,
   e toda imagem é um SVG embutido no código. Ele usa também as skills
   de design de interface que a mesma página lista, sempre dentro das
   regras do harness.
10. Todo texto segue [metodo/texto.md](metodo/texto.md). As checagens
    rodam sozinhas a cada gravação e devolvem o que corrigir. Um recurso
    retórico só fica no texto quando foi planejado na storyline.
11. O harness não tem marca. Use só os modelos, as cores e as fontes
    registrados em `entregaveis/_projeto/marca.md`. Quando dois materiais
    se contradizem ou falta uma definição, pergunte ao consultor.
12. Escreva no idioma principal do entregável. As versões em outros
    idiomas vêm depois da aprovação do conteúdo, em arquivos próprios
    (`conteudo.es.md`, `conteudo.en.md`), e cada uma passa pelas
    checagens do seu idioma.
13. Siga `entregaveis/_projeto/regras-de-material.md`. Material recebido
    fica fora do git. Nenhum entregável cita outro cliente, e nenhuma
    credencial entra em arquivo algum. Um projeto iniciado só vive em
    git local ou em repositório privado: o harness bloqueia a gravação
    dos registros e o envio enquanto o remoto for público ou não tiver
    sido verificado. Confira com
    `python3 entregaveis/_harness/scripts/repositorio.py` e não contorne
    a trava. Ela ouve os comandos de terminal: antes de enviar por outra
    ferramenta, como um conector de GitHub, confira o destino com o
    mesmo script.
14. Trabalhe enxuto. Abra uma página do método quando a tarefa tocar
    nela, leia do material recebido só o que a página pede e rode em
    paralelo o que for independente.

## Antes de entregar

15. Valide e revise. `python3 entregaveis/_harness/scripts/validar.py`
    roda as checagens, e a skill `revisar-entregavel` aplica a rubrica.
    Nunca diga que uma checagem passou sem ter rodado, e nunca afrouxe
    uma checagem para ela passar. O harness impede encerrar o turno com
    conteúdo alterado e sem revisão.
16. Nada some em silêncio. O que foi pedido e não foi feito ganha uma
    linha em `entregaveis/_projeto/adiados.tsv`, com o motivo, e uma
    frase no relatório.
17. Uma lição vira uma guarda. Quando o consultor corrigir você, registre em
    `entregaveis/_projeto/licoes.md` e crie a guarda na mesma mudança:
    uma checagem antes de uma regra, uma regra mais precisa antes de uma
    regra nova.

## O dia a dia do projeto

18. As atas entram pela pasta. O consultor salva atas e transcrições em
    `entregaveis/_atas/`, e o que chegou ou foi feito à mão em
    `entregaveis/_intake/entrada/`. As duas pastas ficam fora do git.
    Cada item extraído leva a reunião de origem. O que toca o contrato
    ou sai do projeto espera o sim do consultor.
19. O cronograma manda nos avisos. Um item dentro do prazo recebe no
    máximo um aviso leve. Prazo próximo e prazo vencido são avisados
    sempre. O vencido pede uma de três respostas: concluído, nova data
    ou não é mais necessário. Um prazo só muda com
    `python3 entregaveis/_harness/scripts/rotina.py --remarcar`, que
    guarda a data anterior. Uma dispensa nunca é presumida.
20. O dia chega em uma lista. `rotina.py --lista` monta a caixa de
    entrada, as próximas ações, o que aguarda o cliente, a agenda e o
    que há a confirmar. No topo sobem no máximo três itens: vencido sem
    data nova, item que trava outros ou é ameaçado por um risco de
    exposição alta, prazo com menos folga e item que espera o cliente
    há mais tempo sem cobrança. O trabalho que depende de aprovação,
    dado ou decisão do cliente só segue com a confirmação, que o
    consultor informa ou você pergunta pelo follow-up. Cada pergunta tem
    a sua frequência em `entregaveis/_projeto/perguntas.tsv`. Nunca
    pergunte por horas trabalhadas.
21. O nível de governança escolhe o que é emitido, e os registros
    existem em qualquer nível. Premissas, issues, dependências,
    mudanças, papéis, linha de base e versões são mantidos por você a
    cada evento. O nível é do consultor: sugira pelo porte, mostre a
    lista de materiais e grave a escolha. Os materiais são montados dos
    registros com `python3 entregaveis/_harness/scripts/emitir.py`, e o
    consultor revisa e envia. Pedido fora do combinado passa por
    `entregaveis/_projeto/mudancas.tsv`, com o impacto e a decisão,
    antes de qualquer trabalho. O aceite vem do cliente, e o silêncio
    não vale como aceite. Um pacote ativo pode trazer controles de
    governança do tipo de projeto, que saem com `governanca.py
    --controles`. Um controle fecha com a evidência e com quem
    confirmou, e a dispensa é do consultor. Um pacote também pode pedir
    informações que só o consultor fornece, que saem com `governanca.py
    --insumos`: peça cada uma e não escreva no lugar dele. Uma proposta
    não é um projeto e usa o nível proposta, que não emite material.

22. O que o projeto aprende vai para o segundo cérebro, em
    `entregaveis/_cerebro/`. Cada ação que grava um registro, uma ata,
    um material ou um entregável termina com a nota do assunto
    atualizada e com `python3 entregaveis/_harness/scripts/cerebro.py --absorver`.
    A nota cita o id do registro e não copia a linha. Decisões, datas,
    cobranças e avisos continuam só nos registros. Antes de escrever ou
    de responder o que o projeto sabe, busque com `cerebro.py --buscar`.
    O método está em [metodo/segundo-cerebro.md](metodo/segundo-cerebro.md).

## Relatório e idioma

23. Relate ao consultor no idioma dele, com o resultado primeiro. Depois diga
    o que foi checado, o que você assumiu e o que ficou por fazer.
24. As instruções e os registros do harness ficam em português. Os
    entregáveis ficam nos idiomas definidos no brief do projeto.
