"""Regras do domínio escritas em Python. Opcional.

Use quando uma expressão em checagens.tsv não alcança o que o método
exige: uma conta, uma comparação entre números do mesmo trecho, uma
lista fechada de valores.

Cada regra é uma função que recebe o texto de um trecho (uma página, um
parágrafo ou o texto visível de uma peça interativa) e devolve a
mensagem do que corrigir, ou None quando o trecho passa. Ela entra no
dicionário REGRAS com o id que os casos de casos.tsv citam. Como as
outras, só vale com um caso que acusa e um que passa.

Só a biblioteca padrão. Nada de rede e nada de ler arquivo fora do
projeto. O template traz este arquivo vazio: as regras são escritas no
projeto e ficam nele.

Este arquivo é código do projeto. Ele roda a cada gravação e na
integração contínua, com o acesso de quem está trabalhando. Revise cada
mudança como código, e não cole aqui um trecho que você não leu.

Formato, com um exemplo fictício:

    import re

    def soma_das_parcelas(texto):
        partes = [int(n) for n in re.findall(r"(\\d+)%", texto)]
        if "soma 100%" in texto and sum(partes[:-1]) != 100:
            return "As parcelas não somam 100%."
        return None

    REGRAS = {"D-900": soma_das_parcelas}
"""

REGRAS = {}
