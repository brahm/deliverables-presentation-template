#!/usr/bin/env python3
"""As checagens que o validar.py roda sobre os entregáveis.

Cada função devolve uma lista de achados. Um achado de nível "erro"
reprova; um de nível "aviso" só informa. O que exige julgamento (a página
é entendida em três segundos? os argumentos se sobrepõem?) não está aqui:
fica na rubrica de revisão, em metodo/rubrica.md.
"""
from __future__ import annotations

import datetime
import re
import subprocess
from functools import lru_cache
from pathlib import Path

import comum
from comum import Achado, MARCA

# Limites de palavras por veículo. O consultor pode trocar qualquer um em
# _projeto/limites.tsv (colunas: veiculo, limite, valor).
LIMITES = {
    "projetado": {"titulo": 14, "corpo_aviso": 40, "corpo_erro": 80, "marcadores": 5},
    "workshop": {"titulo": 14, "corpo_aviso": 60, "corpo_erro": 110, "marcadores": 6},
    "leitura": {"titulo": 22, "corpo_aviso": 150, "corpo_erro": 250, "marcadores": 8},
    "documento": {"paragrafo_aviso": 130, "frase_aviso": 40},
}

MARCAS_ESQUECIDAS = re.compile(
    r"\b(TBD|TBC|TODO|FIXME|lorem ipsum|a confirmar|por confirmar)\b|XX+\s?%|\?\?\?|\[inserir|\[insert|" + MARCA,
    flags=re.IGNORECASE,
)

SIGLAS_COMUNS = {"OK", "PDF", "PPT", "PPTX", "DOCX", "XLSX", "CSV", "TSV", "URL", "II", "III", "IV", "VI", "VII"}


def _limites(veiculo: str) -> dict:
    limites = dict(LIMITES.get(veiculo, LIMITES["leitura"]))
    for linha in comum.ler_tsv(comum.PROJETO / "limites.tsv"):
        if linha.get("veiculo") == veiculo and linha.get("valor", "").isdigit():
            limites[linha.get("limite", "")] = int(linha["valor"])
    return limites


def _meta(pasta: Path) -> dict:
    return comum.cabecalho(comum.ler(pasta / "briefing.md"))[0]


def _rigoroso(pasta: Path, rigoroso: bool) -> bool:
    """Marcas esquecidas e faltas viram erro a partir da etapa de revisão."""
    return rigoroso or comum.etapa(_meta(pasta)) >= comum.ETAPAS.index("revisao")


@lru_cache(maxsize=None)
def _padroes(nome: str) -> tuple:
    """Lê uma lista de padrões: nível, expressão regular e orientação."""
    padroes = []
    for linha in comum.ler(comum.LISTAS / nome).splitlines():
        if not linha.strip() or linha.startswith("#"):
            continue
        partes = linha.split("\t")
        if len(partes) >= 3:
            padroes.append((partes[0].strip(), re.compile(partes[1], flags=re.IGNORECASE), partes[2].strip()))
    return tuple(padroes)


# --- Projeto e briefing ---------------------------------------------------


def projeto() -> list[Achado]:
    """O brief do projeto está preenchido depois de iniciado."""
    arquivo = comum.PROJETO / "brief.md"
    meta, corpo = comum.cabecalho(comum.ler(arquivo))
    nome = comum.relativo(arquivo)
    if not meta:
        return [Achado("aviso", "projeto", nome, 0, "O projeto não foi iniciado: aplique a skill iniciar-projeto ou adotar-projeto.")]
    if comum.normalizar(meta.get("iniciado", "nao")) != "sim":
        return [Achado("aviso", "projeto", nome, 0, "O brief do projeto ainda não foi fechado (iniciado: nao).")]
    achados = []
    for campo in ("projeto", "tipo", "idiomas_dos_entregaveis", "classificacao"):
        if not meta.get(campo) or MARCA in meta.get(campo, ""):
            achados.append(Achado("erro", "projeto", nome, 0, f"O campo '{campo}' do brief está vazio."))
    if MARCA in corpo:
        achados.append(Achado("erro", "projeto", nome, 0, f"O brief ainda tem trechos marcados com {MARCA}."))
    fase = comum.fase_atual()
    passagem = comum.PROJETO / "fases" / f"fase-{fase - 1}" / "passagem.md"
    if fase > 1 and (not passagem.is_file() or MARCA in comum.ler(passagem)):
        achados.append(Achado("aviso", "projeto", comum.relativo(passagem), 0, f"A passagem da fase {fase - 1} para a {fase} ainda não foi escrita por inteiro: siga a skill evoluir-projeto."))
    return achados


def briefing(pasta: Path, rigoroso: bool = False) -> list[Achado]:
    """O briefing tem audiência, de e para, grande ideia, pedido e resistências."""
    arquivo = pasta / "briefing.md"
    nome = comum.relativo(arquivo)
    meta, corpo = comum.cabecalho(comum.ler(arquivo))
    etapa = comum.etapa(meta)
    nivel = "erro" if etapa >= 1 or rigoroso else "aviso"
    achados = [
        Achado(nivel, "briefing", nome, 0, f"A seção '{falta}' está vazia ou ainda tem {MARCA}.")
        for falta in comum.briefing_completo(pasta)
    ]
    for campo in ("tipo", "veiculo", "formato", "idiomas"):
        if not meta.get(campo) or MARCA in meta.get(campo, ""):
            achados.append(Achado(nivel, "briefing", nome, 0, f"O campo '{campo}' do cabeçalho está vazio."))
    mapa = comum.secoes(corpo)
    ideia = (comum.achar_secao(mapa, "grande ideia") or "").strip()
    if ideia and MARCA not in ideia:
        frases = [f for f in re.split(r"(?<=[.!?])\s+", ideia) if f.strip()]
        if comum.contar_palavras(ideia) < 7:
            achados.append(Achado(nivel, "briefing", nome, 0, "A grande ideia parece um assunto. Escreva uma frase completa com o ponto de vista e o que está em jogo."))
        elif len(frases) > 2:
            achados.append(Achado("aviso", "briefing", nome, 0, "A grande ideia tem mais de duas frases. Ela deve caber em uma."))
    pedido = comum.achar_secao(mapa, "chamada para acao") or ""
    if pedido.strip() and MARCA not in pedido:
        linhas = comum.tabela(pedido)
        completas = [l for l in linhas if l.get("dono") and l.get("prazo") and l.get("acao")]
        if not completas:
            achados.append(Achado(nivel, "briefing", nome, 0, "A chamada para ação precisa de ao menos uma linha com ação, dono e prazo."))
    return achados


# --- Storyline ------------------------------------------------------------


def _rotulo(titulo: str) -> bool:
    """Diz se o título é um rótulo de assunto, e não uma frase com mensagem."""
    rotulos = {comum.normalizar(l) for l in comum.ler(comum.LISTAS / "rotulos.txt").splitlines() if l.strip() and not l.startswith("#")}
    normal = comum.normalizar(titulo)
    if normal in rotulos:
        return True
    palavras = normal.split()
    return len(palavras) <= 3 and any(normal.startswith(r + " ") or normal == r for r in rotulos)


def storyline(pasta: Path, rigoroso: bool = False) -> list[Achado]:
    """Títulos de ação, resumo executivo, pedido e aprovação do consultor."""
    achados: list[Achado] = []
    meta = _meta(pasta)
    etapa = comum.etapa(meta)
    limites = _limites(comum.normalizar(meta.get("veiculo", "leitura")))
    arq_story = pasta / "storyline.md"
    nome_story = comum.relativo(arq_story)
    _, corpo_story = comum.cabecalho(comum.ler(arq_story))
    mapa = comum.secoes(corpo_story)
    sequencia = comum.tabela(comum.achar_secao(mapa, "sequencia") or "")
    sequencia = [l for l in sequencia if MARCA not in l.get("titulo de acao", MARCA)]

    if etapa >= 1 or sequencia:
        nivel = "erro" if etapa >= 2 or rigoroso else "aviso"
        resumo = comum.achar_secao(mapa, "resumo executivo") or ""
        if not resumo.strip() or MARCA in resumo:
            achados.append(Achado(nivel, "storyline", nome_story, 0, "Falta o resumo executivo: a história inteira em poucas frases, com a conclusão primeiro."))
        if not sequencia:
            achados.append(Achado(nivel, "storyline", nome_story, 0, "A sequência de títulos está vazia."))
    vistos: dict[str, str] = {}
    for linha in sequencia:
        titulo = linha.get("titulo de acao", "")
        tipo = comum.normalizar(linha.get("tipo", ""))
        achados.extend(_titulo(titulo, tipo, limites, nome_story, 0))
        chave = comum.normalizar(titulo)
        if chave in vistos:
            achados.append(Achado("erro", "storyline", nome_story, 0, f"Título repetido na sequência: '{titulo}'."))
        vistos[chave] = titulo
    if sequencia and not any(comum.normalizar(l.get("tipo", "")) == "pedido" for l in sequencia):
        achados.append(Achado("erro" if etapa >= 2 or rigoroso else "aviso", "storyline", nome_story, 0, "Nenhuma página do tipo 'pedido': a história precisa terminar no que a audiência deve fazer."))
    if (etapa >= 3 or comum.tem_paginas_reais(pasta)) and not comum.storyline_aprovada(pasta):
        achados.append(Achado("erro", "storyline", nome_story, 0, "Há conteúdo escrito e a storyline não foi aprovada pelo consultor (aprovada: sim)."))

    for arquivo in pasta.glob("conteudo*.md"):
        nome = comum.relativo(arquivo)
        paginas = [p for p in comum.paginas(comum.ler(arquivo)) if MARCA not in p.titulo]
        titulos: dict[str, int] = {}
        for p in paginas:
            tipo = comum.normalizar(p.meta.get("tipo", ""))
            achados.extend(_titulo(p.titulo, tipo, limites, nome, p.linha))
            chave = comum.normalizar(p.titulo)
            if chave in titulos and tipo not in comum.TIPOS_SEM_TITULO_DE_ACAO:
                achados.append(Achado("erro", "storyline", nome, p.linha, f"Título repetido (também na página {titulos[chave]})."))
            titulos[chave] = p.numero
        if paginas and arquivo.name == "conteudo.md" and sequencia:
            fora = [p for p in paginas if comum.normalizar(p.titulo) not in vistos and comum.normalizar(p.meta.get("tipo", "")) not in {"capa", "agenda", "secao", "apendice", "encerramento"}]
            if fora:
                numeros = ", ".join(str(p.numero) for p in fora[:8])
                achados.append(Achado("aviso", "storyline", nome, 0, f"Páginas com título diferente da storyline aprovada: {numeros}. Alinhe os dois ou peça nova aprovação."))
        if len(paginas) > 10 and not any(comum.normalizar(p.meta.get("tipo", "")) == "resumo" for p in paginas):
            achados.append(Achado("erro" if _rigoroso(pasta, rigoroso) else "aviso", "storyline", nome, 0, "Material com mais de 10 páginas e sem página do tipo 'resumo' no início."))
        if paginas and not any(comum.normalizar(p.meta.get("tipo", "")) == "pedido" for p in paginas):
            achados.append(Achado("erro" if _rigoroso(pasta, rigoroso) else "aviso", "storyline", nome, 0, "Nenhuma página do tipo 'pedido' com a chamada para ação."))
    return achados


def _titulo(titulo: str, tipo: str, limites: dict, nome: str, linha: int) -> list[Achado]:
    if tipo in comum.TIPOS_SEM_TITULO_DE_ACAO or not titulo.strip():
        return []
    achados = []
    if _rotulo(titulo):
        achados.append(Achado("erro", "storyline", nome, linha, f"'{titulo}' é um rótulo. Escreva a mensagem da página como frase, com verbo."))
    if titulo.rstrip().endswith(":"):
        achados.append(Achado("erro", "storyline", nome, linha, f"O título '{titulo}' termina em dois-pontos: ele anuncia a mensagem em vez de dizê-la."))
    n = comum.contar_palavras(titulo)
    maximo = limites.get("titulo", 22)
    if n > maximo:
        achados.append(Achado("erro", "storyline", nome, linha, f"Título com {n} palavras (limite do veículo: {maximo})."))
    return achados


# --- Densidade ------------------------------------------------------------


def densidade(pasta: Path, rigoroso: bool = False) -> list[Achado]:
    """Quantidade de texto por página ou parágrafo, conforme o veículo."""
    achados: list[Achado] = []
    veiculo = comum.normalizar(_meta(pasta).get("veiculo", "leitura"))
    limites = _limites(veiculo)
    for arquivo in pasta.glob("conteudo*.md"):
        nome = comum.relativo(arquivo)
        for p in comum.paginas(comum.ler(arquivo)):
            tipo = comum.normalizar(p.meta.get("tipo", ""))
            if tipo == "apendice" or MARCA in p.titulo:
                continue
            n = comum.contar_palavras(p.corpo)
            if n > limites.get("corpo_erro", 10**6):
                achados.append(Achado("erro", "densidade", nome, p.linha, f"Página {p.numero} com {n} palavras no corpo (limite: {limites['corpo_erro']}). Divida a página ou leve o detalhe ao apêndice."))
            elif n > limites.get("corpo_aviso", 10**6):
                achados.append(Achado("aviso", "densidade", nome, p.linha, f"Página {p.numero} com {n} palavras no corpo (recomendado: até {limites['corpo_aviso']})."))
            marcadores = len(re.findall(r"^\s*[-*+]\s+", p.corpo, flags=re.MULTILINE))
            if marcadores > limites.get("marcadores", 10**6):
                achados.append(Achado("aviso", "densidade", nome, p.linha, f"Página {p.numero} com {marcadores} marcadores. Veja se os itens formam um diagrama ou pedem páginas separadas."))
            if len(re.findall(r"^###\s+", p.corpo, flags=re.MULTILINE)) > 1 and veiculo in ("projetado", "workshop"):
                achados.append(Achado("aviso", "densidade", nome, p.linha, f"Página {p.numero} tem mais de um subtítulo. Uma ideia por página."))
    if veiculo == "documento":
        for arquivo in pasta.glob("documento*.md"):
            nome = comum.relativo(arquivo)
            paragrafo, inicio = "", 0
            for n, linha in list(comum.linhas_de_prosa(comum.ler(arquivo))) + [(0, "")]:
                if linha.strip() and not linha.lstrip().startswith(("#", "|", "-", "*", ">")):
                    inicio = inicio or n
                    paragrafo += " " + linha
                    continue
                if paragrafo:
                    palavras = comum.contar_palavras(paragrafo)
                    if palavras > limites.get("paragrafo_aviso", 130):
                        achados.append(Achado("aviso", "densidade", nome, inicio, f"Parágrafo com {palavras} palavras. Divida em dois."))
                    for frase in re.split(r"(?<=[.!?])\s+", paragrafo):
                        tamanho = comum.contar_palavras(frase)
                        if tamanho > limites.get("frase_aviso", 40):
                            achados.append(Achado("aviso", "densidade", nome, inicio, f"Frase com {tamanho} palavras: '{frase.strip()[:60]}...'"))
                paragrafo, inicio = "", 0
    return achados


# --- Evidência ------------------------------------------------------------


def _tem_numero(texto: str) -> bool:
    """Diz se o texto afirma algum número que pede fonte."""
    texto = re.sub(r"<!--.*?-->", " ", texto, flags=re.DOTALL)
    texto = re.sub(r"\b[EDBLM]-\d+\b", " ", texto)                 # ids dos registros
    texto = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", texto)            # datas completas
    texto = re.sub(r"\b\d{1,2}/\d{1,2}(/\d{2,4})?\b", " ", texto)  # datas curtas
    texto = re.sub(r"\b(19|20)\d{2}\b", " ", texto)                 # anos
    texto = re.sub(r"^\s*\d+[.)]\s", " ", texto, flags=re.MULTILINE)  # listas numeradas
    texto = re.sub(r"\b(p[áa]gina|slide|page|diapositiva|fase|onda|etapa|passo|step|wave|phase|ola|paso|Q|H|T)\s?\d+\b", " ", texto, flags=re.IGNORECASE)
    return bool(re.search(r"\d", texto))


def evidencia(pasta: Path, rigoroso: bool = False) -> list[Achado]:
    """Todo número tem fonte no registro de evidências. Nada de marcas esquecidas."""
    achados: list[Achado] = []
    registro = {l.get("id", "") for l in comum.ler_tsv(comum.PROJETO / "evidencias.tsv")}
    nivel_marca = "erro" if _rigoroso(pasta, rigoroso) else "aviso"
    for arquivo in comum.arquivos_de_conteudo(pasta):
        nome = comum.relativo(arquivo)
        texto = comum.ler(arquivo)
        for n, linha in comum.linhas_de_prosa(texto):
            m = MARCAS_ESQUECIDAS.search(linha)
            if m:
                achados.append(Achado(nivel_marca, "evidencia", nome, n, f"Marca esquecida no texto: '{m.group(0)}'."))
        for n, linha in enumerate(texto.splitlines(), start=1):
            for ident in re.findall(r"\bE-\d+\b", linha):
                if ident not in registro:
                    achados.append(Achado("erro", "evidencia", nome, n, f"{ident} não existe em _projeto/evidencias.tsv."))
        if arquivo.name.startswith("conteudo"):
            for p in comum.paginas(texto):
                if MARCA in p.titulo:
                    continue
                tipo = comum.normalizar(p.meta.get("tipo", ""))
                fonte = p.meta.get("fonte", "").strip()
                cita = fonte or re.search(r"\bE-\d+\b", p.corpo)
                if tipo == "dados" and not cita:
                    achados.append(Achado("erro", "evidencia", nome, p.linha, f"Página {p.numero} é de dados e não declara fonte."))
                elif not cita and _tem_numero(p.titulo + "\n" + p.corpo):
                    achados.append(Achado("erro", "evidencia", nome, p.linha, f"Página {p.numero} tem número sem fonte. Cite um E-nnn do registro no campo 'fonte', ou escreva 'fonte: nao-se-aplica' com o motivo."))
        elif arquivo.name.startswith("documento"):
            _, corpo = comum.cabecalho(texto)
            for titulo, bloco in comum.secoes(corpo).items():
                if _tem_numero(bloco) and not re.search(r"\bE-\d+\b|^\s*(Fonte|Fuente|Source)s?:", bloco, flags=re.MULTILINE | re.IGNORECASE):
                    achados.append(Achado("erro", "evidencia", nome, 0, f"A seção '{titulo}' tem números e nenhuma fonte (E-nnn ou linha 'Fonte:')."))
    return achados


# --- Texto ----------------------------------------------------------------


def texto(arquivo: Path, idiomas: list[str], recursos: dict[int, str] | None = None) -> list[Achado]:
    """Vícios de texto gerado por IA, pelas listas de cada idioma.

    'recursos' diz, por linha, que recurso retórico a página declarou no
    campo 'recurso'. Um contraste declarado não é tratado como vício.
    """
    return _texto_das_linhas(comum.relativo(arquivo), comum.linhas_de_prosa(comum.ler(arquivo)), idiomas, recursos)


def _texto_das_linhas(nome: str, linhas, idiomas: list[str], recursos: dict[int, str] | None = None) -> list[Achado]:
    achados: list[Achado] = []
    listas = ["texto-geral.tsv"] + [f"texto-{i}.tsv" for i in idiomas]
    recursos = recursos or {}
    for n, linha in linhas:
        declarado = comum.normalizar(recursos.get(n, ""))
        for lista in listas:
            for nivel, padrao, orientacao in _padroes(lista):
                m = padrao.search(linha)
                if not m:
                    continue
                if "contraste" in declarado and "contraste" in comum.normalizar(orientacao):
                    continue
                achados.append(Achado(nivel, "texto", nome, n, f"'{m.group(0).strip()}': {orientacao}"))
    return achados


def _recursos_por_linha(arquivo: Path) -> dict[int, str]:
    """Recurso retórico declarado em cada página, para cada linha dela."""
    mapa: dict[int, str] = {}
    paginas = comum.paginas(comum.ler(arquivo))
    total = len(comum.ler(arquivo).splitlines())
    for i, p in enumerate(paginas):
        fim = paginas[i + 1].linha if i + 1 < len(paginas) else total + 1
        if p.meta.get("recurso"):
            for n in range(p.linha, fim):
                mapa[n] = p.meta["recurso"]
    return mapa


def texto_do_entregavel(pasta: Path, rigoroso: bool = False) -> list[Achado]:
    achados: list[Achado] = []
    meta = _meta(pasta)
    for arquivo in comum.arquivos_de_conteudo(pasta) + [pasta / "storyline.md"]:
        if arquivo.is_file():
            achados.extend(texto(arquivo, comum.idiomas_do_arquivo(arquivo, meta), _recursos_por_linha(arquivo)))
    return achados


# --- Termos ---------------------------------------------------------------


def termos(pasta: Path, rigoroso: bool = False) -> list[Achado]:
    """Um termo por conceito, e sigla explicada."""
    achados: list[Achado] = []
    glossario = comum.ler_tsv(comum.PROJETO / "glossario.tsv")
    conhecidos = {l.get("termo", "").upper() for l in glossario}
    evitar = []
    for linha in glossario:
        for variante in linha.get("evitar", "").split(";"):
            if variante.strip():
                evitar.append((re.compile(r"(?<!\w)" + re.escape(variante.strip()) + r"(?!\w)", flags=re.IGNORECASE), linha.get("termo", "")))
    for arquivo in comum.arquivos_de_conteudo(pasta):
        nome = comum.relativo(arquivo)
        siglas_vistas: set[str] = set()
        inteiro = comum.ler(arquivo)
        for n, linha in comum.linhas_de_prosa(inteiro):
            for padrao, termo in evitar:
                m = padrao.search(linha)
                if m:
                    achados.append(Achado("erro", "termos", nome, n, f"'{m.group(0)}': o glossário manda usar '{termo}'."))
            for sigla in re.findall(r"(?<![\w-])[A-Z][A-Z0-9&]{1,5}(?![\w-])", linha):
                if sigla in SIGLAS_COMUNS or sigla in conhecidos or sigla in siglas_vistas:
                    continue
                siglas_vistas.add(sigla)
                if not re.search(r"\(" + re.escape(sigla) + r"\)|" + re.escape(sigla) + r"\s*\(", inteiro):
                    achados.append(Achado("aviso", "termos", nome, n, f"A sigla {sigla} não está no glossário nem é explicada no texto."))
    return achados


# --- Estrutura ------------------------------------------------------------


def estrutura(pasta: Path, rigoroso: bool = False) -> list[Achado]:
    """Numeração, seções e referências cruzadas."""
    achados: list[Achado] = []
    for arquivo in pasta.glob("conteudo*.md"):
        nome = comum.relativo(arquivo)
        texto_arq = comum.ler(arquivo)
        paginas = comum.paginas(texto_arq)
        for esperado, p in enumerate(paginas, start=1):
            if p.numero != esperado:
                achados.append(Achado("erro", "estrutura", nome, p.linha, f"Numeração quebrada: página {p.numero} onde se esperava {esperado}."))
                break
        reais = [p for p in paginas if MARCA not in p.titulo]
        if len(reais) > 8:
            sem_secao = [p.numero for p in reais if not p.meta.get("secao") and comum.normalizar(p.meta.get("tipo", "")) not in {"capa", "agenda", "encerramento"}]
            if sem_secao:
                achados.append(Achado("aviso", "estrutura", nome, 0, f"Páginas sem o campo 'secao': {', '.join(map(str, sem_secao[:10]))}. Sem seção não há navegação."))
        sem_tipo = [p.numero for p in reais if not p.meta.get("tipo")]
        if sem_tipo:
            achados.append(Achado("erro", "estrutura", nome, 0, f"Páginas sem o campo 'tipo': {', '.join(map(str, sem_tipo[:10]))}."))
        for n, linha in enumerate(texto_arq.splitlines(), start=1):
            for m in re.finditer(r"\b(?:p[áa]gina|slide|page|diapositiva)\s+(\d+)\b", linha, flags=re.IGNORECASE):
                if int(m.group(1)) > len(paginas) or int(m.group(1)) < 1:
                    achados.append(Achado("erro", "estrutura", nome, n, f"Referência a '{m.group(0)}', que não existe (o material tem {len(paginas)} páginas)."))
            for m in re.finditer(r"\b(ap[êeé]ndice|anexo|appendix)\s+([A-Z]|\d+)\b", linha):
                alvo = comum.normalizar(m.group(0))
                if not any(alvo in comum.normalizar(p.titulo) for p in paginas):
                    achados.append(Achado("erro", "estrutura", nome, n, f"Referência a '{m.group(0)}', e nenhuma página tem esse nome no título."))
    for arquivo in pasta.glob("documento*.md"):
        nome = comum.relativo(arquivo)
        _, corpo = comum.cabecalho(comum.ler(arquivo))
        niveis = [len(m.group(1)) for m in re.finditer(r"^(#{1,6})\s", corpo, flags=re.MULTILINE)]
        if niveis and niveis.count(1) != 1 and MARCA not in corpo:
            achados.append(Achado("aviso", "estrutura", nome, 0, f"O documento tem {niveis.count(1)} títulos de nível 1. Deve ter um."))
        for anterior, atual in zip(niveis, niveis[1:]):
            if atual > anterior + 1:
                achados.append(Achado("aviso", "estrutura", nome, 0, f"Os títulos pulam do nível {anterior} para o {atual}."))
                break
    return achados


# --- Confidencialidade ----------------------------------------------------


def confidencialidade(pasta: Path, rigoroso: bool = False) -> list[Achado]:
    """Nomes proibidos, credenciais e a marcação exigida pelo projeto."""
    achados: list[Achado] = []
    proibidos = [
        (re.compile(r"(?<!\w)" + re.escape(l["termo"]) + r"(?!\w)", flags=re.IGNORECASE), l.get("motivo", ""))
        for l in comum.ler_tsv(comum.PROJETO / "confidencial.tsv") if l.get("termo")
    ]
    segredos = _padroes("segredos.tsv")
    for arquivo in sorted(pasta.rglob("*")):
        if not arquivo.is_file() or arquivo.suffix.lower() not in {".md", ".txt", ".csv", ".tsv", ".json", ".html"}:
            continue
        nome = comum.relativo(arquivo)
        for n, linha in enumerate(comum.ler(arquivo).splitlines(), start=1):
            for padrao, motivo in proibidos:
                m = padrao.search(linha)
                if m:
                    achados.append(Achado("erro", "confidencialidade", nome, n, f"'{m.group(0)}' está na lista de termos proibidos do projeto ({motivo})."))
            for _, padrao, orientacao in segredos:
                if padrao.search(linha):
                    achados.append(Achado("erro", "confidencialidade", nome, n, orientacao))
    brief, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    marcacao = brief.get("marcacao_obrigatoria", "").strip()
    if marcacao and MARCA not in marcacao and _rigoroso(pasta, rigoroso):
        for arquivo in comum.arquivos_de_conteudo(pasta):
            inicio = "\n".join(comum.ler(arquivo).splitlines()[:40])
            if marcacao.lower() not in inicio.lower():
                achados.append(Achado("erro", "confidencialidade", comum.relativo(arquivo), 0, f"Falta a marcação '{marcacao}' na capa ou no início do documento."))
    return achados


def materiais_fora_do_git() -> list[Achado]:
    """Nenhum material recebido, nenhuma ata e nenhum arquivo da pasta de entrada está versionado."""
    achados: list[Achado] = []
    pastas = [(comum.INTAKE / "materiais", "de material recebido"), (comum.INTAKE / "entrada", "da pasta de entrada"), (comum.BASE / "_atas", "de ata ou transcrição")]
    for pasta, nome in pastas:
        if not pasta.is_dir():
            continue
        try:
            saida = subprocess.run(
                ["git", "-C", str(comum.RAIZ), "ls-files", "--", str(pasta)],
                capture_output=True, text=True, timeout=20,
            )
        except (OSError, subprocess.SubprocessError):
            return achados
        rastreados = [l for l in saida.stdout.splitlines() if l.strip() and not l.endswith((".gitkeep", "_atas/LEIA-ME.md"))]
        if saida.returncode == 0 and rastreados:
            achados.append(Achado("erro", "confidencialidade", comum.relativo(pasta), 0, f"{len(rastreados)} arquivo(s) {nome} estão no git. Tire-os do controle de versão."))
    return achados


def repositorio_do_projeto() -> list[Achado]:
    """Um projeto com conteúdo só fica em git local ou em repositório privado."""
    import repositorio

    if not repositorio.tem_projeto():
        return []
    geral, remotos = repositorio.situacao()
    if repositorio.aceita(geral):
        return []
    return [Achado("erro", "repositorio", ".git", 0, repositorio.explicar(geral, remotos))]


# --- Intake ---------------------------------------------------------------


def intake() -> list[Achado]:
    """Materiais pedidos e ainda não recebidos."""
    achados: list[Achado] = []
    hoje = datetime.date.today().isoformat()
    nome = comum.relativo(comum.INTAKE / "registro.tsv")
    for linha in comum.ler_tsv(comum.INTAKE / "registro.tsv"):
        estado = comum.normalizar(linha.get("estado", ""))
        if estado in ("pedido", "em falta"):
            prazo = linha.get("prazo", "")
            atraso = " O prazo passou." if re.fullmatch(r"\d{4}-\d{2}-\d{2}", prazo) and prazo < hoje else ""
            achados.append(Achado("aviso", "intake", nome, 0, f"{linha.get('id', '?')} ({linha.get('material', '')}) está '{linha.get('estado', '')}'.{atraso}"))
    return achados


# --- Prazos e reuniões ----------------------------------------------------

_ESTADOS_DE_ACAO = {"proposta", "aberta", "concluida", "cancelada"}


def prazos() -> list[Achado]:
    """Ações com campo fora do formato e itens vencidos que esperam a resposta do consultor."""
    import rotina

    achados: list[Achado] = []
    nome = comum.relativo(comum.PROJETO / "acoes.tsv")
    for linha in comum.ler_tsv(comum.PROJETO / "acoes.tsv"):
        ident, estado = linha.get("id", "?"), comum.normalizar(linha.get("estado", ""))
        if estado not in _ESTADOS_DE_ACAO:
            achados.append(Achado("erro", "prazos", nome, 0, f"{ident}: o estado '{linha.get('estado', '')}' não existe. Vale proposta, aberta, concluida ou cancelada."))
        for campo in ("inicio", "prazo"):
            if linha.get(campo, "") and not rotina.data(linha[campo]):
                achados.append(Achado("erro", "prazos", nome, 0, f"{ident}: o campo '{campo}' precisa de uma data no formato AAAA-MM-DD."))
        if estado == "aberta" and not linha.get("prazo", ""):
            achados.append(Achado("aviso", "prazos", nome, 0, f"{ident} está aberta sem prazo. Pergunte a data ao consultor, ou deixe o item como proposta."))
        if estado == "aberta" and not linha.get("dono", ""):
            achados.append(Achado("aviso", "prazos", nome, 0, f"{ident} está aberta sem dono."))
    parametros = rotina.parametros()
    hoje = datetime.date.today()
    if parametros["pausa_ate"] and parametros["pausa_ate"] >= hoje:
        return achados
    for item in rotina.itens_com_prazo():
        if hoje > item.prazo:
            achados.append(Achado("aviso", "prazos", comum.relativo(comum.PROJETO), 0, f"{item.ident} ({item.tipo}) venceu em {item.prazo} e está sem resposta: concluído, nova data (rotina.py --remarcar) ou não é mais necessário (rotina.py --dispensar)."))
    return achados


# --- Governança -----------------------------------------------------------

_ESTADOS_DE_GOVERNANCA = {
    "premissas.tsv": {"a confirmar", "confirmada", "falsa"},
    "issues.tsv": {"aberta", "resolvida"},
    "dependencias.tsv": {"aberta", "atendida", "cancelada"},
    "mudancas.tsv": {"proposta", "em analise", "aprovada", "rejeitada"},
}


def cerebro_do_projeto() -> list[Achado]:
    """Nota com ligação quebrada, id que não existe, sem fonte ou órfã, e o que o projeto registrou e nenhuma nota guarda."""
    import cerebro

    return cerebro.conferir()


def governanca_do_projeto() -> list[Achado]:
    """Nível e estados fora do combinado, dependência que aponta para o vazio e trabalho concluído à frente do cliente."""
    import afazeres
    import governanca

    achados: list[Achado] = []
    nivel = governanca.nivel_atual()
    if nivel and nivel not in governanca.NIVEIS + ["personalizado"]:
        achados.append(Achado("erro", "governanca", comum.relativo(comum.PROJETO / "brief.md"), 0, f"O nível de governança '{nivel}' não existe. Vale enxuto, padrao, completo ou personalizado. Grave com governanca.py --nivel."))
    for nome, validos in _ESTADOS_DE_GOVERNANCA.items():
        for linha in comum.ler_tsv(comum.PROJETO / nome):
            if comum.normalizar(linha.get("estado", "")) not in validos:
                achados.append(Achado("erro", "governanca", comum.relativo(comum.PROJETO / nome), 0, f"{linha.get('id', '?')}: o estado '{linha.get('estado', '')}' não existe. Vale {', '.join(sorted(validos))}."))
    riscos = comum.relativo(comum.PROJETO / "riscos.tsv")
    for linha in comum.ler_tsv(comum.PROJETO / "riscos.tsv"):
        for campo in ("probabilidade", "impacto"):
            if linha.get(campo, "") and comum.normalizar(linha[campo]) not in afazeres.GRAU:
                achados.append(Achado("erro", "governanca", riscos, 0, f"{linha.get('id', '?')}: '{campo}' é alta, media ou baixa, e não '{linha[campo]}'."))
    codigos = {m["codigo"] for m in governanca.catalogo()}
    for linha in comum.ler_tsv(comum.PROJETO / "governanca.tsv"):
        codigo = linha.get("codigo", "")
        if codigo not in codigos and not re.fullmatch(r"SM-\d+", codigo):
            achados.append(Achado("erro", "governanca", comum.relativo(comum.PROJETO / "governanca.tsv"), 0, f"O material '{codigo}' não está no catálogo. Um material próprio entra com governanca.py --sob-medida."))
    # Quem depende de quem: um id que não existe quebra a lista do dia em silêncio.
    acoes = comum.ler_tsv(comum.PROJETO / "acoes.tsv")
    conhecidos = {l.get("id", "") for l in acoes} | {l.get("id", "") for l in comum.ler_tsv(comum.INTAKE / "registro.tsv")}
    conhecidos |= {l.get("id", "") for l in comum.ler_tsv(comum.PROJETO / "dependencias.tsv")} | {p.name for p in comum.entregaveis()}
    apontam = [("acoes.tsv", l.get("id", "?"), campo, l.get(campo, "")) for l in acoes for campo in ("depende_de", "entregavel")]
    apontam += [("riscos.tsv", l.get("id", "?"), "ameaca", l.get("ameaca", "")) for l in comum.ler_tsv(comum.PROJETO / "riscos.tsv")]
    apontam += [("dependencias.tsv", l.get("id", "?"), "afeta", l.get("afeta", "")) for l in comum.ler_tsv(comum.PROJETO / "dependencias.tsv")]
    for nome, ident, campo, valor in apontam:
        for alvo in afazeres.ids(valor):
            if alvo not in conhecidos:
                achados.append(Achado("aviso", "governanca", comum.relativo(comum.PROJETO / nome), 0, f"{ident}: o campo '{campo}' cita {alvo}, que não existe nos registros."))
    abertos = afazeres.itens_abertos()
    for linha in acoes:
        if comum.normalizar(linha.get("estado", "")) != "concluida":
            continue
        for alvo in afazeres.ids(linha.get("depende_de", "")):
            if alvo in abertos and abertos[alvo].lado != "consultoria":
                achados.append(Achado("aviso", "governanca", comum.relativo(comum.PROJETO / "acoes.tsv"), 0, f"{linha.get('id', '?')} foi concluída, mas dependia de {alvo}, que ainda espera o cliente. Confirme com rotina.py --cobrado {alvo}."))
    if nivel:
        aprova = {l.get("item", ""): l.get("aprova", "") for l in comum.ler_tsv(comum.PROJETO / "papeis.tsv")}
        for pasta in comum.entregaveis():
            aberto = comum.ETAPAS[comum.etapa(_meta(pasta))] != "entregue"
            if aberto and comum.fase_do_entregavel(_meta(pasta)) == comum.fase_atual() and not aprova.get(pasta.name, ""):
                achados.append(Achado("aviso", "governanca", comum.relativo(comum.PROJETO / "papeis.tsv"), 0, f"O entregável '{pasta.name}' não tem quem aprova. Pergunte ao consultor e preencha a linha dele."))
    return achados


# --- HTML interativo ------------------------------------------------------

# O que faz um HTML depender de algo fora dele. Cada item: onde procurar
# ("tags", "css" ou "js"), a expressão e o que dizer.
_FORA_DO_ARQUIVO = [
    ("tags", r"<(?:script|img|iframe|video|audio|source|embed|track|input)\b[^>]*?\bsrc\s*=\s*[\"']?(?!data:|blob:|about:blank|#)([^\"'\s>]+)", "carrega '{0}' de fora do arquivo"),
    ("tags", r"<link\b[^>]*?\bhref\s*=\s*[\"']?(?!data:|#)([^\"'\s>]+)", "a tag link aponta para '{0}'"),
    ("tags", r"<object\b[^>]*?\bdata\s*=\s*[\"']?(?!data:)([^\"'\s>]+)", "a tag object carrega '{0}'"),
    ("tags", r"<(?:image|use|feImage)\b[^>]*?\bhref\s*=\s*[\"'](?!data:|#)([^\"']+)", "o SVG carrega '{0}' de fora do arquivo"),
    ("tags", r"\bsrcset\s*=\s*[\"'](?!data:)([^\"']+)", "srcset aponta para '{0}'"),
    ("tags", r"<base\b", "a tag base muda o endereço dos recursos"),
    ("css", r"url\(\s*[\"']?(?!data:|#)([^\"')\s]+)", "o CSS carrega '{0}'"),
    ("css", r"@import\b", "o CSS usa @import"),
    ("js", r"\bfetch\s*\(|\bXMLHttpRequest\b|\bnew\s+WebSocket\b|\bEventSource\s*\(|\bsendBeacon\s*\(|\bimportScripts\s*\(", "o script faz uma chamada de rede"),
    ("js", r"\bimport\s*\(|^\s*import\s[^;]*\bfrom\s*[\"']|^\s*import\s*[\"']", "o script importa um módulo de outro arquivo"),
]

_TEM_MOVIMENTO = re.compile(r"@keyframes|requestAnimationFrame|\btransition\s*:|\banimation\s*:|\.animate\s*\(|<animate", flags=re.IGNORECASE)


def _linha_de(texto: str, posicao: int) -> int:
    return texto.count("\n", 0, posicao) + 1


def interativo(pasta: Path, rigoroso: bool = False) -> list[Achado]:
    """HTML interativo: arquivo único, com mensagem, fonte e movimento com respeito a quem lê."""
    achados: list[Achado] = []
    arquivos = comum.interativos(pasta)
    if not arquivos:
        return achados
    meta = _meta(pasta)
    registro = {l.get("id", "") for l in comum.ler_tsv(comum.PROJETO / "evidencias.tsv")}
    falta = "erro" if _rigoroso(pasta, rigoroso) else "aviso"
    brief, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    marcacao = brief.get("marcacao_obrigatoria", "").strip()
    if not comum.storyline_aprovada(pasta):
        achados.append(Achado("erro", "interativo", comum.relativo(pasta / "storyline.md"), 0, "Há HTML interativo e a storyline não foi aprovada pelo consultor (aprovada: sim)."))
    for arquivo in arquivos:
        nome = comum.relativo(arquivo)
        html = comum.ler(arquivo)

        # 1. Arquivo único: nada vem de fora.
        so_tags = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", lambda m: m.group(0)[:m.group(0).find(">") + 1] + "\n" * m.group(0).count("\n"), html, flags=re.DOTALL | re.IGNORECASE)
        partes = {"tags": [(0, so_tags)], "css": [], "js": []}
        for m in re.finditer(r"<style\b[^>]*>(.*?)</style\s*>", html, flags=re.DOTALL | re.IGNORECASE):
            partes["css"].append((m.start(1), m.group(1)))
        for m in re.finditer(r"\bstyle\s*=\s*\"([^\"]*)\"", so_tags, flags=re.IGNORECASE):
            partes["css"].append((m.start(1), m.group(1)))
        for m in re.finditer(r"<script\b([^>]*)>(.*?)</script\s*>", html, flags=re.DOTALL | re.IGNORECASE):
            if not re.search(r"type\s*=\s*[\"']application/(?:ld\+)?json", m.group(1), flags=re.IGNORECASE):
                partes["js"].append((m.start(2), m.group(2)))
        for onde, expressao, mensagem in _FORA_DO_ARQUIVO:
            for inicio, trecho in partes[onde]:
                for m in re.finditer(expressao, trecho, flags=re.IGNORECASE | re.MULTILINE):
                    alvo = (m.group(1) if m.groups() else "")[:60]
                    achados.append(Achado("erro", "interativo", nome, _linha_de(html, inicio + m.start()), f"O HTML precisa ser um arquivo único: {mensagem.format(alvo)}. Ponha o conteúdo dentro do arquivo (script, estilo, SVG ou data:)."))

        # 2. Estrutura mínima de um documento que abre sozinho.
        for expressao, texto in (
            (r"<!doctype html", "Falta '<!doctype html>' na primeira linha."),
            (r"<html\b[^>]*\blang\s*=", "Falta o idioma em '<html lang=\"...\">'."),
            (r"<meta\b[^>]*charset", "Falta '<meta charset=\"utf-8\">'."),
            (r"<meta\b[^>]*name\s*=\s*[\"']viewport", "Falta a meta 'viewport', e a página não se ajusta à tela do celular."),
            (r"<title>\s*[^<\s][^<]*</title>", "Falta o '<title>' com o nome da peça."),
        ):
            if not re.search(expressao, html, flags=re.IGNORECASE):
                achados.append(Achado("erro", "interativo", nome, 0, texto))

        # 3. O plano da peça, no comentário que abre o arquivo.
        campos = comum.cabecalho_do_interativo(html)
        for campo, texto in (
            ("mensagem", "o que a pessoa deve entender depois de usar a peça, em uma frase"),
            ("apoia", "a página ou a seção do entregável que a peça ajuda a entender"),
            ("fontes", "os E-nnn do registro de evidências, ou 'nao-se-aplica' com o motivo"),
        ):
            if not campos.get(campo) or MARCA in campos.get(campo, ""):
                achados.append(Achado(falta, "interativo", nome, 0, f"O comentário '<!-- interativo -->' do início não diz '{campo}': {texto}."))
        for ident in re.findall(r"\bE-\d+\b", html):
            if ident not in registro:
                achados.append(Achado("erro", "interativo", nome, 0, f"{ident} não existe em _projeto/evidencias.tsv."))
                break

        # 4. Movimento, leitura sem script e impressão.
        if _TEM_MOVIMENTO.search(html) and "prefers-reduced-motion" not in html:
            achados.append(Achado("erro", "interativo", nome, 0, "A peça tem animação e não trata 'prefers-reduced-motion'. Quem pediu menos movimento ao sistema vê o estado final, parado."))
        if "requestAnimationFrame" in html and not re.search(r"visibilitychange|pausa|pause", html, flags=re.IGNORECASE):
            achados.append(Achado("aviso", "interativo", nome, 0, "A animação contínua não tem pausa. Dê um controle de pausar e pare o laço quando a aba não estiver visível."))
        for m in re.finditer(r"<canvas\b([^>]*)>(.*?)</canvas>", html, flags=re.DOTALL | re.IGNORECASE):
            if not re.search(r"aria-label|aria-labelledby|aria-hidden", m.group(1)) and not m.group(2).strip():
                achados.append(Achado("aviso", "interativo", nome, _linha_de(html, m.start()), "O canvas não tem descrição. Ponha 'role=\"img\"' com 'aria-label', ou um texto dentro da tag."))
        if "<noscript" not in html.lower():
            achados.append(Achado("aviso", "interativo", nome, 0, "Falta '<noscript>' com a mensagem e os números principais, para quem abre sem script."))
        if "@media print" not in html:
            achados.append(Achado("aviso", "interativo", nome, 0, "Falta '@media print'. A peça costuma ser impressa ou salva em PDF junto com o material."))
        if re.search(r"\b(?:alert|confirm|prompt)\s*\(", " ".join(t for _, t in partes["js"])):
            achados.append(Achado("aviso", "interativo", nome, 0, "O script usa alert, confirm ou prompt. Mostre a mensagem na própria página."))
        tamanho = arquivo.stat().st_size
        if tamanho > 15 * 1024 * 1024:
            achados.append(Achado("erro", "interativo", nome, 0, f"O arquivo tem {tamanho // (1024 * 1024)} MB. Acima de 15 MB ele não passa por e-mail nem abre bem no celular."))
        elif tamanho > 3 * 1024 * 1024:
            achados.append(Achado("aviso", "interativo", nome, 0, f"O arquivo tem {tamanho / (1024 * 1024):.1f} MB. Veja se as imagens embutidas podem ser menores."))

        # 5. O texto que a pessoa lê segue as mesmas práticas do resto.
        linhas = [(n, comum.limpar_linha(l)) for n, l in comum.texto_visivel(html)]
        declarado = campos.get("idioma", "")[:2].lower()
        idiomas = [declarado] if declarado in ("pt", "es", "en") else comum.idiomas_do_arquivo(arquivo, meta)
        for achado in _texto_das_linhas(nome, linhas, idiomas):
            achados.append(Achado(achado.nivel, "interativo", achado.arquivo, achado.linha, achado.texto))
        for n, linha in linhas:
            m = MARCAS_ESQUECIDAS.search(linha)
            if m:
                achados.append(Achado(falta, "interativo", nome, n, f"Marca esquecida no texto: '{m.group(0)}'."))
        exemplos = len(re.findall(r'"(?:Exemplo|Ejemplo|Example)[:. ]', html))
        if exemplos:
            achados.append(Achado(falta, "interativo", nome, 0, f"A peça ainda traz {exemplos} dado(s) de exemplo do modelo. Troque pelos dados do projeto, com a fonte."))
        visivel = "\n".join(l for _, l in linhas)
        fontes = campos.get("fontes", "")
        if re.search(r"\bE-\d+\b", fontes) and not re.search(r"\b(?:Fontes?|Fuentes?|Sources?)\s*:", visivel, flags=re.IGNORECASE):
            achados.append(Achado(falta, "interativo", nome, 0, "A peça usa dados do registro e não mostra a fonte e a data na tela (uma linha 'Fonte: ...')."))
        if marcacao and MARCA not in marcacao and _rigoroso(pasta, rigoroso) and marcacao.lower() not in visivel.lower():
            achados.append(Achado("erro", "interativo", nome, 0, f"Falta a marcação '{marcacao}' no texto visível da peça."))
    return achados


def dominio_do_entregavel(pasta: Path, rigoroso: bool = False) -> list[Achado]:
    """As regras que o projeto escreveu para o seu domínio, em _dominio/checagens.tsv."""
    import dominio

    return dominio.aplicar(pasta, rigoroso)


def dominio_do_projeto() -> list[Achado]:
    """As regras do domínio estão provadas pelos seus casos de teste."""
    import dominio

    return dominio.do_projeto()


POR_ENTREGAVEL = {
    "briefing": briefing,
    "storyline": storyline,
    "densidade": densidade,
    "evidencia": evidencia,
    "texto": texto_do_entregavel,
    "termos": termos,
    "estrutura": estrutura,
    "confidencialidade": confidencialidade,
    "interativo": interativo,
    "dominio": dominio_do_entregavel,
}
