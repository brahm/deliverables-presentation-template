#!/usr/bin/env python3
"""Hook de envio de mensagem: lembra o agente do ponto em que cada entregável está.

Escreve no máximo três linhas, para custar pouco a cada mensagem. Fica
calado quando não há entregável em andamento e a mensagem não fala de um.
Guarda também o que o segundo cérebro já tinha por absorver, para o fim
do turno cobrar só o que o turno registrou.
"""
from __future__ import annotations

import re

import _base
import cerebro
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

# Sinais de que o consultor dispensa algo: não será feito, ou não depende mais de aprovação.
DISPENSA = re.compile(
    r"\bn[ãa]o (?:vai|vamos|ser[áa]|precisa(?:mos)?|[ée]|faz) mais\b|\bn[ãa]o (?:depende|precisa) (?:mais )?de aprova[çc][ãa]o\b|"
    r"\bsem (?:necessidade de )?aprova[çc][ãa]o\b|\bcancel(?:e|a|ar|ei|ou|ado|ada|amos)\b|\bdeix(?:a|ou|aram) de (?:ser|existir)\b|"
    r"\bdesist(?:i|iu|imos|ir)\b|\bya no (?:se|es|hace)\b|\bno longer\b|\bwon't be\b|\bcancel(?:led|ed)\b",
    flags=re.IGNORECASE,
)
AVISO_DE_DISPENSA = (
    "Harness de entregáveis: a mensagem pode dizer que algo não será mais feito ou não depende mais de aprovação. Se for, "
    "aplique a skill registrar-dispensa: registre a decisão com o motivo e leve o efeito aos registros. Não presuma a dispensa."
)
# Sinais de que a mensagem traz uma ata ou o relato de uma reunião.
ATA = re.compile(r"\b(?:atas?|transcri[çc](?:[ãa]o|[õo]es)|actas?|meeting (?:notes|minutes)|minutes of)\b", flags=re.IGNORECASE)
AVISO_DE_ATA = (
    "Harness de entregáveis: se a mensagem traz uma ata ou conta o que houve em uma reunião, aplique a skill processar-ata. "
    "As atas ficam em entregaveis/_atas/, fora do git."
)
# Sinais de que o cliente respondeu, ou foi cobrado, sobre algo que o projeto esperava.
FOLLOW_UP = re.compile(
    r"\b(?:cliente|diretor[a]?|gerente|patrocinador[a]?)\b[^.\n]{0,60}\b(?:aprov(?:ou|aram)|respond(?:eu|eram)|confirm(?:ou|aram)|liber(?:ou|aram))\b|"
    r"\bcobr(?:ei|amos|ado)\b|\bfollow[- ]?up\b|\bfup\b",
    flags=re.IGNORECASE,
)
AVISO_DE_FOLLOW_UP = (
    "Harness de entregáveis: se o cliente respondeu ou foi cobrado sobre algo que o projeto esperava, registre com "
    "scripts/rotina.py --cobrado ID, com --resposta aprovou quando ele aprovou. O comando diz o que volta às próximas ações."
)


def guardar_pendencias_do_cerebro(dados: dict) -> None:
    """Guarda o que já estava por absorver quando o turno começou. O fim do turno só cobra o que veio depois."""
    if not dados.get("session_id") or not cerebro.PASTA.is_dir():
        return
    sessao = _base.ler_sessao(dados["session_id"])
    sessao["cerebro_antes"] = sorted(f"{f.ident}:{f.marca}" for f, _, _ in cerebro.pendentes())
    _base.gravar_sessao(dados["session_id"], sessao)


def principal() -> int:
    dados = _base.entrada()
    meta, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    iniciado = comum.normalizar(meta.get("iniciado", "nao")) == "sim"
    if not iniciado:
        if ASSUNTO.search(str(dados.get("prompt", ""))):
            print("Harness de entregáveis: o projeto não foi iniciado. Aplique iniciar-projeto (ou adotar-projeto, se o projeto já estava em andamento) antes de produzir material.")
        return 0
    guardar_pendencias_do_cerebro(dados)
    if MUDANCA_DE_FASE.search(str(dados.get("prompt", ""))):
        print(AVISO_DE_FASE)
    if DISPENSA.search(str(dados.get("prompt", ""))):
        print(AVISO_DE_DISPENSA)
    if ATA.search(str(dados.get("prompt", ""))):
        print(AVISO_DE_ATA)
    if FOLLOW_UP.search(str(dados.get("prompt", ""))):
        print(AVISO_DE_FOLLOW_UP)
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
