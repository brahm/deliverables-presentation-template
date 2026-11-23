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

import cerebro  # noqa: E402
import comum  # noqa: E402
import governanca  # noqa: E402
import repositorio  # noqa: E402
import rotina  # noqa: E402
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
        return "a storyline aguarda a aprovação do consultor; nenhuma página pode ser escrita antes"
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
            "O consultor cria um repositório privado, torna este privado ou remove o remoto e segue em git local. "
            "Enquanto isso o harness bloqueia a gravação dos registros do projeto"
            + (" e o envio ao remoto." if repositorio.tem_projeto() else ".")
        ]
    return [
        "Repositório remoto não verificado: pergunte ao consultor se ele é privado e registre com "
        "scripts/repositorio.py --confirmar. O harness bloqueia a gravação de registros e o envio enquanto isso."
    ]


def linhas_de_dominio() -> list[str]:
    """Uma linha enquanto o domínio do projeto não foi calibrado."""
    texto = comum.ler(comum.BASE / "_dominio" / "dominio.md")
    if texto and comum.MARCA not in texto:
        return []
    return ["Domínio do projeto ainda não calibrado: quando o consultor fornecer referências, métodos, contexto e objetivo, aplique a skill calibrar-dominio."]


def linhas_de_fase() -> list[str]:
    """A fase em que o projeto está e o que a abertura dela deixou por fazer."""
    atual = comum.fase_atual()
    if atual < 2:
        return []
    registro = [l for l in comum.tabela(comum.ler(comum.PROJETO / "fases.md")) if l.get("fase", "").strip() == str(atual)]
    origem = registro[0].get("origem", "") if registro else ""
    linhas = [f"Fase {atual} do projeto" + (f", aberta por: {origem}" if origem else "") + ". As fases anteriores estão em _projeto/fases.md."]
    passagem = comum.PROJETO / "fases" / f"fase-{atual - 1}" / "passagem.md"
    if comum.MARCA in comum.ler(passagem):
        linhas.append(f"A passagem da fase {atual - 1} para a {atual} ainda tem trechos por escrever ({comum.relativo(passagem)}): siga a skill evoluir-projeto.")
    _, corpo = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    if comum.MARCA in corpo:
        linhas.append(f"O brief da fase {atual} ainda não foi fechado com o consultor: siga a skill evoluir-projeto antes de abrir entregáveis.")
    return linhas


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
    linhas += linhas_de_fase()
    linhas += governanca.linha_de_estado()
    linhas += linhas_de_dominio()
    linhas += cerebro.linha_de_estado()
    pastas = comum.entregaveis()
    if not pastas:
        linhas.append("Nenhum entregável aberto. Crie um com scripts/preparar.py --entregavel ID.")
    atual = comum.fase_atual()
    entregues_antes = 0
    for pasta in pastas:
        m, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
        etapa = comum.ETAPAS[comum.etapa(m)]
        fase = comum.fase_do_entregavel(m)
        if fase < atual and etapa == "entregue":
            entregues_antes += 1  # o que as fases anteriores entregaram fica guardado e não pede ação
            continue
        de_antes = f"fase {fase}, " if fase < atual else ""
        linhas.append(f"- {pasta.name} ({de_antes}{m.get('formato', '?')}, etapa {etapa}): {proximo_passo(pasta)}")
    if entregues_antes:
        linhas.append(f"Entregues em fases anteriores: {entregues_antes}. Eles seguem nas pastas deles, como história e como fonte.")
    pendentes = [l for l in comum.ler_tsv(comum.INTAKE / "registro.tsv") if comum.normalizar(l.get("estado", "")) in ("pedido", "em falta")]
    if pendentes:
        nomes = ", ".join(l.get("material", "?") for l in pendentes[:4])
        linhas.append(f"Materiais pendentes: {len(pendentes)} ({nomes}{'...' if len(pendentes) > 4 else ''}).")
    decisoes = comum.ler(comum.PROJETO / "decisoes.md")
    assumidas = sum(1 for linha in decisoes.splitlines() if linha.startswith("|") and "(assumida)" in linha)
    if assumidas:
        linhas.append(f"Decisões assumidas à espera do consultor: {assumidas} (ver _projeto/decisoes.md).")
    adiados = [l for l in comum.ler_tsv(comum.PROJETO / "adiados.tsv") if comum.normalizar(l.get("estado", "")) == "aberto"]
    if adiados:
        linhas.append(f"Itens adiados em aberto: {len(adiados)} (ver _projeto/adiados.tsv).")
    linhas += rotina.linha_de_estado()
    return linhas


def main() -> int:
    print("\n".join(linhas_de_estado()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
