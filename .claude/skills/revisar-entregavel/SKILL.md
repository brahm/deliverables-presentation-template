---
name: revisar-entregavel
description: Use antes de dizer que um entregável está pronto, antes de mostrá-lo ao dono como versão para envio e quando o hook de fim de turno pedir. Roda as checagens, aplica a rubrica como quem não escreveu e registra a revisão da versão atual.
metadata:
  origem: harness-de-entregaveis
---

# Revisar o entregável

1. Rode `python3 entregaveis/_harness/scripts/validar.py ID --rigoroso`.
   Corrija todos os erros. Em cada aviso, corrija ou anote o motivo de
   manter.
2. Gere o arquivo final, se houver, e olhe página por página.
3. Aplique a rubrica de `entregaveis/_harness/metodo/rubrica.md` no papel
   do decisor mais difícil do briefing. Se o agente permite um revisor
   independente, entregue a ele o material e o briefing, sem as suas
   conclusões, e use o que ele achar.
4. Faça dois testes. Leia só os títulos, em ordem, e veja se contam a
   história. Depois percorra o caminho de cinco minutos e veja se ele
   leva ao pedido.
5. Preencha `revisao.md`: uma linha por critério da rubrica, com o
   veredito e a página.
6. Corrija o que reprovou. O que não der para corrigir agora vai para
   `adiar-trabalho`, com o motivo.
7. Rode `python3 entregaveis/_harness/scripts/validar.py --carimbar ID`.
   O comando registra a revisão desta versão do conteúdo e falha se
   ainda houver erro. Mude o `estado` do briefing para `revisao`.
8. Relate com `relatar-ao-dono`: o que passou, o que foi corrigido e o
   que ficou pendente. Não diga que um material foi revisado sem o
   registro do passo 7. Uma alteração no conteúdo depois do registro
   pede nova revisão.
