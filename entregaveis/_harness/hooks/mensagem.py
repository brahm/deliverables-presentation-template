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
# Sinais de que a mensagem fala de uma mudança de fase, e não de um ajuste de escopo.
MUDANCA_DE_FASE = re.compile(
    r"\b(?:vendid[ao]s?|vendemos|ganhamos|assinad[ao]s?|assinou|contratad[ao]s?|contratou|aditivo|extens[ãa]o|renova[çc][ãa]o|"
    r"nova fase|pr[óo]xima fase|virou (?:um |o )?projeto|vira (?:um |o )?projeto|mud(?:ar|ou|a) (?:o |de )tipo|"
    r"vendimos|ganamos|firmad[ao]s?|extensi[óo]n|nueva fase|"
    r"sold|we won|signed|contract extension|new phase|next phase)\b",
    flags=re.IGNORECASE,
)
AVISO_DE_FASE = (
    "Harness de entregáveis: a mensagem pode ser uma mudança de fase do projeto (algo foi vendido, uma extensão, outro tipo de "
    "trabalho). Se for, aplique a skill evoluir-projeto. Se for só ajuste de escopo da fase atual, registre com registrar-decisao. "
    "Na dúvida, pergunte uma vez ao consultor."
)


def principal() -> int:
    dados = _base.entrada()
    meta, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    iniciado = comum.normalizar(meta.get("iniciado", "nao")) == "sim"
    if not iniciado:
        if ASSUNTO.search(str(dados.get("prompt", ""))):
            print("Harness de entregáveis: o projeto não foi iniciado. Aplique iniciar-projeto (ou adotar-projeto, se o projeto já estava em andamento) antes de produzir material.")
        return 0
    if MUDANCA_DE_FASE.search(str(dados.get("prompt", ""))):
        print(AVISO_DE_FASE)
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
