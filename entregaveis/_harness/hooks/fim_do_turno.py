#!/usr/bin/env python3
"""Hook de fim de turno: nenhum entregável alterado fica sem revisão.

Se o conteúdo de um entregável mudou nesta sessão e a revisão registrada
não é da versão atual, pede a revisão antes de encerrar. Pede uma vez por
versão: se o agente decidir parar mesmo assim, ele precisa dizer ao dono
que a revisão ficou pendente.
"""
from __future__ import annotations

import sys

import _base
import comum
import validar


def principal() -> int:
    dados = _base.entrada()
    sessao_id = dados.get("session_id")
    if not sessao_id or dados.get("stop_hook_active"):
        return 0
    sessao = _base.ler_sessao(sessao_id)
    pendentes = []
    for nome in sessao.get("alterados", []):
        pasta = comum.BASE / nome
        if not (pasta / "briefing.md").is_file() or not comum.tem_paginas_reais(pasta):
            continue
        versao = comum.carimbo(pasta)
        if validar.revisao_em_dia(pasta) or sessao.get("avisados", {}).get(nome) == versao:
            continue
        pendentes.append(nome)
        sessao.setdefault("avisados", {})[nome] = versao
    if not pendentes:
        return 0
    _base.gravar_sessao(sessao_id, sessao)
    print(
        f"Harness: o conteúdo de {', '.join(pendentes)} mudou nesta sessão e a revisão registrada não é desta versão. "
        "Aplique a skill revisar-entregavel agora. Se a revisão não couber neste turno, diga ao dono, "
        "com todas as letras, que ela ficou pendente e por quê.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    _base.protegido(principal)
