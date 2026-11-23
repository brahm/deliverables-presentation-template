#!/usr/bin/env python3
"""Imprime o estado do projeto em poucas linhas.

O agente lê esta saída no início da sessão, em vez de abrir cinco
arquivos para descobrir onde o trabalho parou. O Claude Code roda o
script sozinho (hook de início de sessão); nos outros agentes, a regra 1
manda rodá-lo antes de qualquer coisa.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402
import repositorio  # noqa: E402
import validar  # noqa: E402


def proximo_passo(pasta: Path) -> str:
    """O que falta fazer no entregável, e com qual skill."""
    meta, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
    estado = comum.ETAPAS[comum.etapa(meta)]
    faltas = comum.briefing_completo(pasta)
    aprovada = comum.storyline_aprovada(pasta)
    if faltas:
        return "completar o briefing (skill preparar-briefing): falta " + ", ".join(faltas)
    if estado == "briefing":
        return "construir a storyline (skill construir-storyline)"
    if not aprovada:
        return "a storyline aguarda a aprovação do dono; nenhuma página pode ser escrita antes"
    if estado == "storyline":
        return "montar o storyboard (skill montar-storyboard)"
    if estado == "storyboard":
        return "redigir o conteúdo (skills redigir-conteudo e desenhar-visual)"
    if estado == "redacao":
        return "limpar o texto e revisar (skills humanizar-texto e revisar-entregavel)"
    if estado == "revisao":
        if validar.revisao_em_dia(pasta):
            return "preparar a entrega (skill preparar-entrega)"
        return "revisar a versão atual (skill revisar-entregavel)"
    return "entregue; fechar com follow-up e lições (skill fechar-entregavel)"


def linha_do_repositorio() -> list[str]:
    """Uma linha quando o repositório não serve para guardar um projeto de cliente."""
    try:
        geral, remotos = repositorio.situacao()
    except Exception:  # noqa: BLE001 - o estado nunca deixa de sair por causa desta linha
        return []
    if repositorio.aceita(geral):
        return []
    if geral == repositorio.PUBLICO:
        return [
            "Repositório PÚBLICO: um projeto de cliente não pode ser iniciado nem mantido aqui. "
            "O dono cria um repositório privado, torna este privado ou remove o remoto e segue em git local. "
            "Enquanto isso o harness bloqueia a gravação dos registros do projeto"
            + (" e o envio ao remoto." if repositorio.tem_projeto() else ".")
        ]
    return [
        "Repositório remoto não verificado: pergunte ao dono se ele é privado e registre com "
        "scripts/repositorio.py --confirmar. O harness bloqueia a gravação de registros e o envio enquanto isso."
    ]


def linhas_de_dominio() -> list[str]:
    """Uma linha enquanto o domínio do projeto não foi calibrado."""
    texto = comum.ler(comum.BASE / "_dominio" / "dominio.md")
    if texto and comum.MARCA not in texto:
        return []
    return ["Domínio do projeto ainda não calibrado: quando o dono fornecer referências, métodos, contexto e objetivo, aplique a skill calibrar-dominio."]


def linhas_de_estado() -> list[str]:
    brief = comum.PROJETO / "brief.md"
    meta, _ = comum.cabecalho(comum.ler(brief))
    if not meta or comum.normalizar(meta.get("iniciado", "nao")) != "sim":
        return [
            "Harness de entregáveis: o projeto ainda não foi iniciado.",
            "Antes de qualquer outro trabalho, aplique a skill iniciar-projeto.",
            "Se o projeto já estava em andamento quando o harness chegou, aplique adotar-projeto.",
        ] + linha_do_repositorio()
    linhas = linha_do_repositorio() + [
        f"Projeto: {meta.get('projeto', '?')} | tipo: {meta.get('tipo', '?')} | pacotes: {meta.get('pacotes', 'nenhum') or 'nenhum'}",
        f"Idiomas dos entregáveis: {meta.get('idiomas_dos_entregaveis', '?')} | classificação: {meta.get('classificacao', '?')}",
    ]
    linhas += linhas_de_dominio()
    pastas = comum.entregaveis()
    if not pastas:
        linhas.append("Nenhum entregável aberto. Crie um com scripts/preparar.py --entregavel ID.")
    for pasta in pastas:
        m, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
        linhas.append(f"- {pasta.name} ({m.get('formato', '?')}, etapa {comum.ETAPAS[comum.etapa(m)]}): {proximo_passo(pasta)}")
    pendentes = [l for l in comum.ler_tsv(comum.INTAKE / "registro.tsv") if comum.normalizar(l.get("estado", "")) in ("pedido", "em falta")]
    if pendentes:
        nomes = ", ".join(l.get("material", "?") for l in pendentes[:4])
        linhas.append(f"Materiais pendentes: {len(pendentes)} ({nomes}{'...' if len(pendentes) > 4 else ''}).")
    decisoes = comum.ler(comum.PROJETO / "decisoes.md")
    assumidas = sum(1 for linha in decisoes.splitlines() if linha.startswith("|") and "(assumida)" in linha)
    if assumidas:
        linhas.append(f"Decisões assumidas à espera do dono: {assumidas} (ver _projeto/decisoes.md).")
    adiados = [l for l in comum.ler_tsv(comum.PROJETO / "adiados.tsv") if comum.normalizar(l.get("estado", "")) == "aberto"]
    if adiados:
        linhas.append(f"Itens adiados em aberto: {len(adiados)} (ver _projeto/adiados.tsv).")
    return linhas


def main() -> int:
    print("\n".join(linhas_de_estado()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
