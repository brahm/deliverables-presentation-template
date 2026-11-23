#!/usr/bin/env python3
"""Hook de envio de mensagem: lembra o agente do ponto em que cada entregável está.

Escreve no máximo três linhas, para custar pouco a cada mensagem. Fica
calado quando não há entregável em andamento e a mensagem não fala de um.
"""
from __future__ import annotations

import re

import _base
import comum
import estado

ASSUNTO = re.compile(
    r"apresenta|deck|slide|proposta|relat[óo]rio|documento|planilha|treinamento|workshop|"
    r"entreg[áa]vel|storyline|presentaci|propuesta|informe|taller|presentation|proposal|report|spreadsheet|training",
    flags=re.IGNORECASE,
)


def principal() -> int:
    dados = _base.entrada()
    meta, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    iniciado = comum.normalizar(meta.get("iniciado", "nao")) == "sim"
    if not iniciado:
        if ASSUNTO.search(str(dados.get("prompt", ""))):
            print("Harness de entregáveis: o projeto não foi iniciado. Aplique iniciar-projeto (ou adotar-projeto, se o projeto já estava em andamento) antes de produzir material.")
        return 0
    linhas = []
    for pasta in comum.entregaveis():
        m, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
        if comum.ETAPAS[comum.etapa(m)] == "entregue":
            continue
        linhas.append(f"{pasta.name}: {estado.proximo_passo(pasta)}.")
    if linhas:
        print("Harness de entregáveis, ponto atual:")
        print("\n".join(linhas[:3]))
    return 0


if __name__ == "__main__":
    _base.protegido(principal)
