#!/usr/bin/env python3
"""A camada de domínio do projeto: regras próprias e os casos que as provam.

O template traz só o motor e o esqueleto. As regras de verdade são
escritas dentro de cada projeto, em _dominio/, a partir das referências,
dos métodos, do contexto e do objetivo que o consultor fornece. Elas nunca
voltam ao template.

Uso:
    dominio.py            roda os casos de teste de todas as regras
    dominio.py --listar   mostra as regras e quantos casos cada uma tem

Arquivos do projeto, em _dominio/:
    dominio.md            o método do projeto, em prosa, para o agente ler
    checagens.tsv         as regras: id, tipo, aplica, onde, padrao, mensagem, nivel, origem
    casos.tsv             os casos: checagem, espera (acusa ou passa), texto
    checagens_extra.py    opcional: regras em Python para o que uma expressão não alcança

Tipos de regra:
    proibido      o padrão não pode aparecer
    obrigatorio   o padrão precisa aparecer ao menos uma vez
    junto         'A => B': onde A aparece, B aparece na mesma página ou parágrafo
    ordem         'A => B': B só aparece depois de A

Onde a regra olha: titulos, conteudo, storyline, briefing ou tudo.
A coluna 'aplica' aceita '*', um tipo, um veículo, um formato ou o id de
um entregável, separados por vírgula.

Uma regra só vale com dois casos: um texto que ela acusa e um que ela
deixa passar. O texto de um caso usa \\n para quebra de linha, e uma
linha em branco separa páginas ou parágrafos.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402
from comum import Achado, MARCA  # noqa: E402

PASTA = comum.BASE / "_dominio"
TIPOS = ("proibido", "obrigatorio", "junto", "ordem")
LUGARES = ("titulos", "conteudo", "storyline", "briefing", "tudo")
OPCOES = re.IGNORECASE | re.MULTILINE

Unidade = tuple[str, int, str]  # arquivo, linha em que começa, texto


@dataclass
class Regra:
    ident: str
    tipo: str
    aplica: list[str]
    onde: str
    mensagem: str
    nivel: str
    a: re.Pattern | None = None
    b: re.Pattern | None = None
    funcao: object = None
    defeito: str = ""


def calibrado() -> bool:
    texto = comum.ler(PASTA / "dominio.md")
    return bool(texto) and MARCA not in texto


def _regra_da_linha(linha: dict) -> Regra:
    ident = linha.get("id", "").strip() or "?"
    tipo = comum.normalizar(linha.get("tipo", ""))
    onde = comum.normalizar(linha.get("onde", "")) or "tudo"
    nivel = comum.normalizar(linha.get("nivel", "")) or "erro"
    aplica = [p.strip() if p.strip() == "*" else comum.normalizar(p) for p in linha.get("aplica", "*").split(",") if p.strip()] or ["*"]
    regra = Regra(ident, tipo, aplica, onde, linha.get("mensagem", "").strip(), nivel)
    padrao = linha.get("padrao", "")
    if tipo not in TIPOS:
        regra.defeito = f"tipo '{linha.get('tipo', '')}' não existe (use {', '.join(TIPOS)})"
    elif onde not in LUGARES:
        regra.defeito = f"onde '{linha.get('onde', '')}' não existe (use {', '.join(LUGARES)})"
    elif nivel not in ("erro", "aviso"):
        regra.defeito = "nivel precisa ser erro ou aviso"
    elif not padrao.strip() or MARCA in padrao:
        regra.defeito = "padrao vazio"
    elif not regra.mensagem or MARCA in regra.mensagem:
        regra.defeito = "mensagem vazia: diga o que corrigir"
    else:
        partes = [p.strip() for p in padrao.split("=>")] if tipo in ("junto", "ordem") else [padrao.strip()]
        if tipo in ("junto", "ordem") and (len(partes) != 2 or not all(partes)):
            regra.defeito = "o padrao deste tipo tem a forma 'A => B'"
        else:
            try:
                regra.a = re.compile(partes[0], OPCOES)
                regra.b = re.compile(partes[1], OPCOES) if len(partes) == 2 else None
            except re.error as erro:
                regra.defeito = f"expressão inválida ({erro})"
    return regra


def _regras_em_python() -> tuple[list[Regra], str]:
    """Regras escritas em Python no projeto: um dicionário REGRAS de id para função(texto) -> mensagem ou None."""
    arquivo = PASTA / "checagens_extra.py"
    if not arquivo.is_file():
        return [], ""
    try:
        especificacao = importlib.util.spec_from_file_location("checagens_extra_do_projeto", arquivo)
        modulo = importlib.util.module_from_spec(especificacao)
        especificacao.loader.exec_module(modulo)
        tabela = getattr(modulo, "REGRAS", {})
        return [Regra(str(ident), "python", ["*"], "tudo", "", "erro", funcao=funcao) for ident, funcao in tabela.items() if callable(funcao)], ""
    except Exception as erro:  # noqa: BLE001 - código do projeto: um defeito vira achado, não queda
        return [], f"{type(erro).__name__}: {erro}"


def regras() -> tuple[list[Regra], str]:
    """Todas as regras do projeto, e o defeito de carga do arquivo Python, se houver."""
    lista = [_regra_da_linha(l) for l in comum.ler_tsv(PASTA / "checagens.tsv") if l.get("id") and MARCA not in l.get("id", "")]
    extras, defeito = _regras_em_python()
    return lista + extras, defeito


def casos() -> list[dict]:
    return [l for l in comum.ler_tsv(PASTA / "casos.tsv") if l.get("checagem") and MARCA not in l.get("checagem", "")]


def _paragrafos(arquivo: str, texto: str, inicio: int = 1) -> list[Unidade]:
    unidades, bloco, linha_do_bloco = [], [], inicio
    for n, linha in enumerate(texto.splitlines(), start=inicio):
        if linha.strip():
            if not bloco:
                linha_do_bloco = n
            bloco.append(linha)
        elif bloco:
            unidades.append((arquivo, linha_do_bloco, "\n".join(bloco)))
            bloco = []
    if bloco:
        unidades.append((arquivo, linha_do_bloco, "\n".join(bloco)))
    return unidades


def _de_arquivo(arquivo: Path) -> list[Unidade]:
    texto = comum.ler(arquivo)
    _, corpo = comum.cabecalho(texto)
    return _paragrafos(comum.relativo(arquivo), corpo, 1 + len(texto.splitlines()) - len(corpo.splitlines()))


def unidades(pasta: Path, onde: str) -> list[Unidade]:
    """Os trechos do entregável em que uma regra olha: páginas, parágrafos ou títulos."""
    resultado: list[Unidade] = []
    if onde in ("titulos", "conteudo", "tudo"):
        for arquivo in comum.arquivos_de_conteudo(pasta):
            nome, texto = comum.relativo(arquivo), comum.ler(arquivo)
            paginas = comum.paginas(texto)
            if onde == "titulos":
                if paginas:
                    resultado += [(nome, p.linha, p.titulo) for p in paginas]
                else:
                    resultado += [(nome, n, l.lstrip("# ").strip()) for n, l in enumerate(texto.splitlines(), 1) if re.match(r"#{1,6}\s", l)]
            elif paginas:
                resultado += [(nome, p.linha, f"{p.titulo}\n{p.corpo}".strip()) for p in paginas]
            else:
                resultado += _de_arquivo(arquivo)
        if onde != "titulos":
            for arquivo in comum.interativos(pasta):
                linhas = comum.texto_visivel(comum.ler(arquivo))
                if linhas:
                    resultado.append((comum.relativo(arquivo), linhas[0][0], "\n".join(l for _, l in linhas)))
    if onde in ("storyline", "tudo"):
        resultado += _de_arquivo(pasta / "storyline.md")
    if onde in ("briefing", "tudo"):
        resultado += _de_arquivo(pasta / "briefing.md")
    return [u for u in resultado if u[2].strip()]


def avaliar(regra: Regra, trechos: list[Unidade]) -> list[tuple[str, int, str]]:
    """Onde a regra acusa: (arquivo, linha, mensagem). Lista vazia quando o texto passa."""
    acusados: list[tuple[str, int, str]] = []
    if regra.tipo == "python":
        for arquivo, linha, texto in trechos:
            try:
                mensagem = regra.funcao(texto)
            except Exception as erro:  # noqa: BLE001
                mensagem = f"a regra quebrou ({type(erro).__name__}: {erro})"
            if mensagem:
                acusados.append((arquivo, linha, str(mensagem)))
        return acusados
    if regra.tipo == "proibido":
        for arquivo, linha, texto in trechos:
            m = regra.a.search(texto)
            if m:
                acusados.append((arquivo, linha + texto.count("\n", 0, m.start()), regra.mensagem))
    elif regra.tipo == "obrigatorio":
        if trechos and not any(regra.a.search(t) for _, _, t in trechos):
            acusados.append((trechos[0][0], 0, regra.mensagem))
    elif regra.tipo == "junto":
        for arquivo, linha, texto in trechos:
            m = regra.a.search(texto)
            if m and not regra.b.search(texto):
                acusados.append((arquivo, linha + texto.count("\n", 0, m.start()), regra.mensagem))
    elif regra.tipo == "ordem":
        visto = False
        for arquivo, linha, texto in trechos:
            a, b = regra.a.search(texto), regra.b.search(texto)
            if b and not visto and not (a and a.start() < b.start()):
                acusados.append((arquivo, linha + texto.count("\n", 0, b.start()), regra.mensagem))
                break
            visto = visto or bool(a)
    return acusados


def _vale_para(regra: Regra, pasta: Path) -> bool:
    if "*" in regra.aplica:
        return True
    meta, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
    proprios = {comum.normalizar(pasta.name)} | {comum.normalizar(meta.get(c, "")) for c in ("tipo", "veiculo", "formato")}
    return bool(proprios & set(regra.aplica))


def aplicar(pasta: Path, rigoroso: bool = False) -> list[Achado]:
    """Checagem 'dominio': as regras do projeto sobre um entregável."""
    achados: list[Achado] = []
    lista, _ = regras()
    for regra in lista:
        if regra.defeito or not _vale_para(regra, pasta):
            continue
        trechos = unidades(pasta, regra.onde)
        if regra.tipo == "obrigatorio" and regra.onde in ("conteudo", "titulos", "tudo") and not comum.tem_paginas_reais(pasta):
            continue  # o que é obrigatório no conteúdo só é cobrado quando há conteúdo escrito
        for arquivo, linha, mensagem in avaliar(regra, trechos):
            achados.append(Achado(regra.nivel, "dominio", arquivo, linha, f"{regra.ident}: {mensagem}"))
    return achados


def _texto_do_caso(bruto: str) -> list[Unidade]:
    return _paragrafos("caso", bruto.replace("\\n", "\n"))


def testar() -> list[Achado]:
    """Prova cada regra nos seus casos. Devolve o que está errado na camada de domínio."""
    achados: list[Achado] = []
    nome_regras, nome_casos = comum.relativo(PASTA / "checagens.tsv"), comum.relativo(PASTA / "casos.tsv")
    lista, defeito_python = regras()
    if defeito_python:
        achados.append(Achado("erro", "dominio", comum.relativo(PASTA / "checagens_extra.py"), 0, f"O arquivo não carrega: {defeito_python}."))
    por_id: dict[str, Regra] = {}
    for regra in lista:
        if regra.ident in por_id:
            achados.append(Achado("erro", "dominio", nome_regras, 0, f"{regra.ident}: id repetido."))
        por_id[regra.ident] = regra
        if regra.defeito:
            achados.append(Achado("erro", "dominio", nome_regras, 0, f"{regra.ident}: {regra.defeito}."))
    vistos: dict[str, set[str]] = {i: set() for i in por_id}
    for n, caso in enumerate(casos(), start=1):
        ident, espera = caso.get("checagem", ""), comum.normalizar(caso.get("espera", ""))
        regra = por_id.get(ident)
        if regra is None:
            achados.append(Achado("erro", "dominio", nome_casos, 0, f"Caso {n}: a regra '{ident}' não existe."))
            continue
        if espera not in ("acusa", "passa"):
            achados.append(Achado("erro", "dominio", nome_casos, 0, f"Caso {n} de {ident}: 'espera' precisa ser acusa ou passa."))
            continue
        if regra.defeito:
            continue
        vistos[ident].add(espera)
        acusou = bool(avaliar(regra, _texto_do_caso(caso.get("texto", ""))))
        if acusou != (espera == "acusa"):
            achados.append(Achado("erro", "dominio", nome_casos, 0, f"Caso {n} de {ident}: esperava '{espera}' e a regra {'acusou' if acusou else 'deixou passar'}. Corrija a regra ou o caso."))
    for ident, tem in vistos.items():
        if por_id[ident].defeito:
            continue
        faltam = [e for e in ("acusa", "passa") if e not in tem]
        if faltam:
            achados.append(Achado("erro", "dominio", nome_casos, 0, f"{ident}: falta caso de teste que '{' e que '.join(faltam)}'. Uma regra só vale com os dois."))
    return achados


def do_projeto() -> list[Achado]:
    """Checagem geral 'dominio': a camada existe, está calibrada e as regras estão provadas."""
    meta, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    if comum.normalizar(meta.get("iniciado", "nao")) != "sim":
        return []
    achados = testar()
    if not calibrado():
        achados.append(Achado("aviso", "dominio", comum.relativo(PASTA / "dominio.md"), 0, "O domínio do projeto não foi calibrado. Com as referências, os métodos, o contexto e o objetivo em mãos, aplique a skill calibrar-dominio."))
    elif not regras()[0]:
        achados.append(Achado("aviso", "dominio", comum.relativo(PASTA / "checagens.tsv"), 0, "O domínio foi descrito e não tem nenhuma regra. Transforme em regra o que o método exige e pode ser checado."))
    return achados


def main() -> int:
    analisador = argparse.ArgumentParser(description="Regras e casos de teste do domínio do projeto.")
    analisador.add_argument("--listar", action="store_true", help="mostra as regras e os casos de cada uma")
    args = analisador.parse_args()
    lista, _ = regras()
    todos = casos()
    if args.listar:
        for regra in lista:
            n = sum(1 for c in todos if c.get("checagem") == regra.ident)
            print(f"{regra.ident}\t{regra.tipo}\t{regra.onde}\t{regra.nivel}\t{n} caso(s)\t{regra.mensagem or 'regra em Python'}")
        if not lista:
            print("Nenhuma regra em _dominio/checagens.tsv.")
        return 0
    achados = testar()
    for a in achados:
        print(a.formatar())
    if achados:
        print(f"\n{len(achados)} problema(s) nas regras do domínio.")
        return 1
    print(f"Domínio: {len(lista)} regra(s) provada(s) em {len(todos)} caso(s)." if lista else "Domínio: nenhuma regra ainda.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
