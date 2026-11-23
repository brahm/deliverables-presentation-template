# Regras do harness de entregáveis

Este projeto produz entregáveis de consultoria: apresentações, propostas,
documentos, planilhas e materiais de treinamento. O dono do projeto decide
e aprova. Você planeja, escreve, valida e mantém os registros.

As regras são curtas de propósito. Elas dizem o que não pode ser
esquecido e apontam para as páginas de `entregaveis/_harness/metodo/`,
que você abre quando a tarefa pede.

## Como o trabalho corre

1. Comece pelo estado. `python3 entregaveis/_harness/scripts/estado.py`
   diz em poucas linhas o tipo do projeto, a etapa de cada entregável, os
   materiais pendentes e as decisões à espera do dono. O Claude Code roda
   o script sozinho no início da sessão. Em outro agente, rode-o primeiro.
2. As skills se aplicam sozinhas. O dono nunca precisa citar uma. Quando
   chegar um destes momentos, abra `.claude/skills/NOME/SKILL.md` e siga:

   | Momento | Skill |
   | --- | --- |
   | O harness chegou a um projeto que está começando | `iniciar-projeto` |
   | O harness foi instalado em um projeto já em andamento | `adotar-projeto` |
   | Falta um material, ou um material chegou | `receber-materiais` |
   | Um entregável novo foi pedido | `preparar-briefing` |
   | O briefing está completo | `construir-storyline` |
   | O dono aprovou a storyline | `montar-storyboard` |
   | O storyboard está pronto | `redigir-conteudo` |
   | Uma página mostra dados, relação entre itens ou imagem | `desenhar-visual` |
   | Um texto de entregável foi escrito ou alterado | `humanizar-texto` |
   | Antes de dizer que um entregável está pronto | `revisar-entregavel` |
   | A revisão passou | `preparar-entrega` |
   | O material foi apresentado ou enviado | `fechar-entregavel` |
   | O dono decide, ou você decide o que ele deixou em aberto | `registrar-decisao` |
   | Algo pedido não será feito agora | `adiar-trabalho` |
   | O dono corrige você, ou um erro se repete | `registrar-licao` |
   | Qualquer relatório ao dono | `relatar-ao-dono` |
   | O harness tem uma versão nova | `atualizar-harness` |

3. Quem decide.
   - O dono decide o objetivo, o escopo, a audiência, a grande ideia e a
     storyline. Também decide tudo o que sai do projeto ou não pode ser
     desfeito: enviar algo ao cliente, apagar material, citar um dado
     sensível. Pare essa parte, pergunte uma vez com as opções e a que
     você recomenda, e siga com o resto.
   - Você decide, registrando, o que o dono deixou em aberto e o trabalho
     precisa. Escolha o que serve melhor ao objetivo, registre em
     `entregaveis/_projeto/decisoes.md` como `Vigente (assumida)` e liste
     no relatório. O dono confirma ou troca.
   - Você decide o resto, que é o como.
4. Sempre pergunte do que é o projeto. Não presuma o tipo de trabalho, a
   audiência, o idioma nem o formato. O que o dono responder define os
   pacotes, as skills e as checagens que o projeto usa.

## Antes de escrever

5. A história vem antes da página. A ordem é briefing, storyline aprovada
   pelo dono, storyboard e só então páginas. O harness bloqueia a
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
   [metodo/formatos.md](metodo/formatos.md).
10. Todo texto segue [metodo/texto.md](metodo/texto.md). As checagens
    rodam sozinhas a cada gravação e devolvem o que corrigir. Um recurso
    retórico só fica no texto quando foi planejado na storyline.
11. O harness não tem marca. Use só os modelos, as cores e as fontes
    registrados em `entregaveis/_projeto/marca.md`. Quando dois materiais
    se contradizem ou falta uma definição, pergunte ao dono.
12. Escreva no idioma principal do entregável. As versões em outros
    idiomas vêm depois da aprovação do conteúdo, em arquivos próprios
    (`conteudo.es.md`, `conteudo.en.md`), e cada uma passa pelas
    checagens do seu idioma.
13. Siga `entregaveis/_projeto/regras-de-material.md`. Material recebido
    fica fora do git. Nenhum entregável cita outro cliente, e nenhuma
    credencial entra em arquivo algum.
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
17. Uma lição vira uma guarda. Quando o dono corrigir você, registre em
    `entregaveis/_projeto/licoes.md` e crie a guarda na mesma mudança:
    uma checagem antes de uma regra, uma regra mais precisa antes de uma
    regra nova.

## Relatório e idioma

18. Relate ao dono no idioma dele, com o resultado primeiro. Depois diga
    o que foi checado, o que você assumiu e o que ficou por fazer.
19. As instruções e os registros do harness ficam em português. Os
    entregáveis ficam nos idiomas definidos no brief do projeto.
