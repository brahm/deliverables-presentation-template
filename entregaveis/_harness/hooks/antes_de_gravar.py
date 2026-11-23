#!/usr/bin/env python3
"""Hook de antes da gravação: a história vem antes da página.

Recusa gravar o corpo de um entregável enquanto o briefing estiver
incompleto ou a storyline não tiver a aprovação do dono. É um dos dois
pontos em que o harness bloqueia.
"""
from __future__ import annotations

import sys

import _base
import comum


def principal() -> int:
    dados = _base.entrada()
    arquivo = _base.arquivo_da_ferramenta(dados)
    if arquivo is None:
        return 0
    pasta = _base.entregavel_do_arquivo(arquivo)
    if pasta is None or not _base.e_conteudo(arquivo, pasta):
        return 0
    if not (pasta / "briefing.md").is_file():
        # Uma pasta que já existia no projeto e não é do harness só é barrada
        # quando recebe um arquivo com nome de corpo de entregável.
        if arquivo.parent != pasta:
            return 0
        print(
            f"Bloqueado pelo harness: '{pasta.name}' ainda não é um entregável. "
            f"Crie a pasta com scripts/preparar.py --entregavel {pasta.name} e siga a skill preparar-briefing.",
            file=sys.stderr,
        )
        return 2
    faltas = comum.briefing_completo(pasta)
    if faltas:
        print(
            f"Bloqueado pelo harness: o briefing de '{pasta.name}' está incompleto (falta: {', '.join(faltas)}). "
            "Complete o briefing com a skill preparar-briefing antes de escrever páginas.",
            file=sys.stderr,
        )
        return 2
    if not comum.storyline_aprovada(pasta):
        print(
            f"Bloqueado pelo harness: a storyline de '{pasta.name}' não foi aprovada pelo dono. "
            "Mostre a sequência de títulos ao dono e, depois do sim dele, registre 'aprovada: sim' em storyline.md "
            "com a data e as palavras dele. Não marque a aprovação por conta própria.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    _base.protegido(principal)
