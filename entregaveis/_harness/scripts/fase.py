#!/usr/bin/env python3
"""Abre uma fase nova do projeto sem perder nada da anterior.

Uso:
    fase.py                          mostra as fases e registra a primeira, se faltar
    fase.py --nova --tipo "TIPO" --origem "MOTIVO" [--pacotes a,b] [--data AAAA-MM-DD]
    fase.py --nova ... --simular     mostra o que mudaria, sem gravar

Uma fase é um trabalho com tipo, objetivo e escopo próprios dentro do
mesmo projeto: a proposta que foi vendida, o trabalho contratado, a
extensão. Abrir uma fase guarda o brief da anterior, cria a página de
passagem, registra a mudança em _projeto/fases.md, ativa os pacotes do
tipo novo e deixa o brief pronto para ser reescrito. As decisões, as
evidências, o glossário, a marca, as lições, o domínio e os entregáveis
ficam onde estão. Nada é apagado.

Abrir uma fase é decisão do consultor. A skill evoluir-projeto mostra a
simulação a ele antes de rodar o comando de verdade.
"""
from __future__ import annotations

import argparse
import datetime
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402
import preparar  # noqa: E402

FASES = comum.PROJETO / "fases.md"
BRIEF = comum.PROJETO / "brief.md"
EM_ANDAMENTO = "Em andamento"
ENCERRADA = "Encerrada"
# Seções do brief que são da fase e voltam ao modelo. O resto do brief passa adiante como está.
SECOES_DA_FASE = ["o que e o projeto", "a decisao que o projeto precisa provocar", "escopo e o que fica fora", "entregaveis previstos", "prazos e marcos"]


def limpo(texto: str) -> str:
    """Texto que cabe em uma célula de tabela."""
    return re.sub(r"\s+", " ", texto.replace("|", "/")).strip()


def fases() -> list[dict]:
    return [l for l in comum.tabela(comum.ler(FASES)) if l.get("fase", "").strip().isdigit()]


def pasta_da_fase(numero: int) -> Path:
    return comum.PROJETO / "fases" / f"fase-{numero}"


def iniciado() -> bool:
    meta, _ = comum.cabecalho(comum.ler(BRIEF))
    return bool(meta) and comum.normalizar(meta.get("iniciado", "nao")) == "sim"


def linha_de_tabela(numero: int, inicio: str, fim: str, tipo: str, pacotes: str, origem: str, estado: str) -> str:
    return f"| {numero} | {inicio} | {fim} | {limpo(tipo)} | {limpo(pacotes)} | {limpo(origem)} | {estado} |"


def acrescentar(linha: str) -> None:
    texto = comum.ler(FASES)
    FASES.write_text(texto + ("" if texto.endswith("\n") else "\n") + linha + "\n", encoding="utf-8")


def registrar_primeira(data: str) -> bool:
    """Um projeto iniciado tem ao menos a fase 1 no registro."""
    if not iniciado() or fases():
        return False
    preparar.preparar_projeto()
    meta, _ = comum.cabecalho(comum.ler(BRIEF))
    acrescentar(linha_de_tabela(1, data, "", meta.get("tipo", ""), meta.get("pacotes", ""), "início do projeto", EM_ANDAMENTO))
    return True


def em_aberto(ate: int) -> list[tuple[str, str]]:
    """Entregáveis não entregues das fases até a indicada, com a etapa de cada um."""
    abertos = []
    for pasta in comum.entregaveis():
        meta, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
        etapa = comum.ETAPAS[comum.etapa(meta)]
        if comum.fase_do_entregavel(meta) <= ate and etapa != "entregue":
            abertos.append((pasta.name, etapa))
    return abertos


def brief_da_fase(texto: str, numero: int, tipo: str) -> str:
    """O brief com o cabeçalho da fase nova e as seções da fase de volta ao modelo."""
    partes = texto.split("\n---", 1)
    topo, resto = (partes[0], "\n---" + partes[1]) if len(partes) == 2 else (texto, "")
    topo = re.sub(r"^tipo:.*$", f"tipo: {limpo(tipo)}", topo, count=1, flags=re.MULTILINE)
    topo = re.sub(r"^pacotes:.*$", "pacotes:", topo, count=1, flags=re.MULTILINE)
    if re.search(r"^fase:.*$", topo, flags=re.MULTILINE):
        topo = re.sub(r"^fase:.*$", f"fase: {numero}", topo, count=1, flags=re.MULTILINE)
    else:
        topo = re.sub(r"^(iniciado:.*)$", f"fase: {numero}\n\\1", topo, count=1, flags=re.MULTILINE)
    _, modelo = comum.cabecalho(comum.ler(comum.MODELOS / "projeto" / "brief.md"))
    do_modelo = comum.secoes(modelo)
    saida, pulando = [], False
    for linha in resto.splitlines():
        titulo = re.match(r"^##\s+(.+?)\s*$", linha)
        if titulo:
            nome = comum.normalizar(titulo.group(1))
            pulando = nome in SECOES_DA_FASE and nome in do_modelo
            saida.append(linha)
            if pulando:
                saida.extend(do_modelo[nome].rstrip("\n").splitlines() + [""])
            continue
        if not pulando:
            saida.append(linha)
    return topo + "\n".join(saida).rstrip("\n") + "\n"


def passagem(numero: int, data: str, origem: str, abertos: list[tuple[str, str]]) -> str:
    texto = comum.ler(comum.MODELOS / "fase" / "passagem.md")
    for chave, valor in (("da_fase", numero), ("para_a_fase", numero + 1), ("data", data), ("origem", limpo(origem))):
        texto = re.sub(rf"^{chave}:.*$", f"{chave}: {valor}", texto, count=1, flags=re.MULTILINE)
    linhas = "".join(f"| {nome} | {etapa} | {comum.MARCA} |\n" for nome, etapa in abertos) or "| nenhum | | |\n"
    return texto.replace("| --- | --- | --- |\n\n## O que a fase nova", "| --- | --- | --- |\n" + linhas + "\n## O que a fase nova", 1)


def nova(tipo: str, pacotes: list[str], origem: str, data: str, simular: bool) -> list[str]:
    if not iniciado():
        raise SystemExit("O projeto ainda não foi iniciado. Aplique a skill iniciar-projeto antes de abrir outra fase.")
    if not tipo.strip() or not origem.strip():
        raise SystemExit("Diga o tipo de trabalho da fase nova (--tipo) e o que a abriu (--origem), com as palavras do consultor.")
    disponiveis = preparar.pacotes_disponiveis()
    for nome in pacotes:
        if nome not in disponiveis:
            raise SystemExit(f"Não existe o pacote '{nome}'. Disponíveis: {', '.join(disponiveis) or 'nenhum'}.")
    atual = comum.fase_atual()
    guarda = pasta_da_fase(atual)
    if (guarda / "brief.md").exists():
        raise SystemExit(f"{comum.relativo(guarda)} já existe: a fase {atual} parece ter sido encerrada antes. Confira {comum.relativo(FASES)} e o campo 'fase' do brief.")
    abertos = em_aberto(atual)
    meta, _ = comum.cabecalho(comum.ler(BRIEF))
    passos = [
        f"A fase {atual} ({meta.get('tipo', '?')}) é encerrada em {data}, e o brief dela é guardado em {comum.relativo(guarda / 'brief.md')}.",
        f"A fase {atual + 1} ({limpo(tipo)}) é aberta por: {limpo(origem)}.",
        f"Pacotes da fase nova: {', '.join(pacotes) or 'nenhum'}.",
        f"A página de passagem é criada em {comum.relativo(guarda / 'passagem.md')}.",
        "No brief, as seções do projeto, da decisão, do escopo, dos entregáveis e dos prazos voltam ao modelo, para serem escritas de novo. O resto fica.",
        "Ficam como estão: decisões, evidências, glossário, marca, audiência, lições, domínio, materiais e todos os entregáveis.",
        (f"Entregáveis em aberto que pedem um destino: {', '.join(nome for nome, _ in abertos)}." if abertos else "Nenhum entregável em aberto."),
    ]
    if simular:
        return passos
    preparar.preparar_projeto()
    if not fases():
        acrescentar(linha_de_tabela(atual, "", "", meta.get("tipo", ""), meta.get("pacotes", ""), "início do projeto", EM_ANDAMENTO))
    guarda.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BRIEF, guarda / "brief.md")
    (guarda / "passagem.md").write_text(passagem(atual, data, origem, abertos), encoding="utf-8")
    # Fecha a linha da fase atual e abre a da nova.
    linhas = []
    for linha in comum.ler(FASES).splitlines():
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if linha.strip().startswith("|") and celulas and celulas[0] == str(atual) and len(celulas) >= 7:
            linha = linha_de_tabela(atual, celulas[1], data, celulas[3], celulas[4], celulas[5], ENCERRADA)
        linhas.append(linha)
    FASES.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    acrescentar(linha_de_tabela(atual + 1, data, "", tipo, ", ".join(pacotes), origem, EM_ANDAMENTO))
    BRIEF.write_text(brief_da_fase(comum.ler(BRIEF), atual + 1, tipo), encoding="utf-8")
    for nome in pacotes:
        preparar.ativar_pacote(nome)
    return passos


def mostrar() -> None:
    linhas = fases()
    if not linhas:
        print("O projeto ainda não tem fases registradas.")
        return
    for l in linhas:
        periodo = l.get("inicio") or "?"
        periodo += f" a {l['fim']}" if l.get("fim") else ""
        print(f"Fase {l['fase']} ({l.get('estado', '?')}, {periodo}): {l.get('tipo', '?')} | pacotes: {l.get('pacotes') or 'nenhum'} | origem: {l.get('origem') or '?'}")


def main() -> int:
    analisador = argparse.ArgumentParser(description="Mostra as fases do projeto ou abre uma fase nova.")
    analisador.add_argument("--nova", action="store_true", help="abre uma fase nova")
    analisador.add_argument("--tipo", default="", help="o tipo de trabalho da fase nova")
    analisador.add_argument("--pacotes", default="", help="os pacotes da fase nova, separados por vírgula")
    analisador.add_argument("--origem", default="", help="o que abriu a fase: proposta vendida, extensão contratada")
    analisador.add_argument("--data", default="", help="a data da mudança, AAAA-MM-DD (padrão: hoje)")
    analisador.add_argument("--simular", action="store_true", help="mostra o que mudaria, sem gravar")
    args = analisador.parse_args()
    data = args.data or datetime.date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
        raise SystemExit("A data vai no formato AAAA-MM-DD.")
    if not args.nova:
        if registrar_primeira(data):
            print(f"Fase 1 registrada em {comum.relativo(FASES)}.")
        mostrar()
        return 0
    pacotes = [p.strip() for p in args.pacotes.split(",") if p.strip()]
    passos = nova(args.tipo, pacotes, args.origem, data, args.simular)
    print("Simulação. Nada foi gravado:" if args.simular else "Fase nova aberta:")
    for passo in passos:
        print(f"  - {passo}")
    if args.simular:
        print("Mostre esta lista ao consultor. Com o sim dele, rode o mesmo comando sem --simular.")
    else:
        print("Agora siga a skill evoluir-projeto: escreva a passagem, feche o brief da fase nova com o consultor e dê destino aos entregáveis em aberto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
