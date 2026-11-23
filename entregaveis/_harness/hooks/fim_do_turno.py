#!/usr/bin/env python3
"""Hook de fim de turno: nenhum entregável alterado fica sem revisão, e o que o turno aprendeu vai para o segundo cérebro.

Se o conteúdo de um entregável mudou nesta sessão e a revisão registrada
não é da versão atual, pede a revisão antes de encerrar. Pede uma vez por
versão: se o agente decidir parar mesmo assim, ele precisa dizer ao consultor
que a revisão ficou pendente.

Se o turno registrou algo que nenhuma nota do segundo cérebro guarda,
pede a absorção, uma vez por item. O que já estava pendente antes do
turno aparece no estado e na rotina do dia, e não segura o turno.
"""
from __future__ import annotations

import sys

import _base
import cerebro
import comum
import validar


def do_cerebro(sessao: dict) -> list[str]:
    """Os itens que este turno criou ou mudou e que ainda não foram absorvidos nem lembrados."""
    if not cerebro.PASTA.is_dir() or "cerebro_antes" not in sessao:
        return []  # sem o retrato do começo do turno não dá para saber o que é deste turno
    fora = set(sessao.get("cerebro_antes", [])) | set(sessao.get("cerebro_lembrados", []))
    novos = [f for f, _, _ in cerebro.pendentes() if f"{f.ident}:{f.marca}" not in fora]
    sessao["cerebro_lembrados"] = sorted(set(sessao.get("cerebro_lembrados", [])) | {f"{f.ident}:{f.marca}" for f in novos})
    return [f.ident for f in novos]


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
    a_absorver = do_cerebro(sessao)
    if not pendentes and not a_absorver:
        return 0
    _base.gravar_sessao(sessao_id, sessao)
    if pendentes:
        print(
            f"Harness: o conteúdo de {', '.join(pendentes)} mudou nesta sessão e a revisão registrada não é desta versão. "
            "Aplique a skill revisar-entregavel agora. Se a revisão não couber neste turno, diga ao consultor, "
            "com todas as letras, que ela ficou pendente e por quê.",
            file=sys.stderr,
        )
    if a_absorver:
        nomes = ", ".join(a_absorver[:8]) + ("..." if len(a_absorver) > 8 else "")
        print(
            f"Harness: este turno registrou {len(a_absorver)} item(ns) que o segundo cérebro ainda não guarda ({nomes}). "
            "Aplique a skill manter-cerebro agora: atualize as notas e rode scripts/cerebro.py --absorver. "
            "Se não couber neste turno, diga ao consultor que a absorção ficou para o fechamento do dia.",
            file=sys.stderr,
        )
    return 2


if __name__ == "__main__":
    _base.protegido(principal)
