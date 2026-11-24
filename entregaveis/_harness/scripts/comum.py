#!/usr/bin/env python3
"""Leitura dos arquivos do harness.

Os outros scripts e os hooks usam este módulo para achar as pastas, ler
cabeçalhos, seções, tabelas e páginas, e limpar o texto antes das
checagens. Só usa a biblioteca padrão do Python.

A pasta do harness é achada a partir deste arquivo, então o nome da pasta
de entregáveis pode ser outro no projeto em que o harness foi instalado.
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import sys
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
BASE = HARNESS.parent
RAIZ = BASE.parent
PROJETO = BASE / "_projeto"
INTAKE = BASE / "_intake"
MODELOS = HARNESS / "modelos"
LISTAS = HARNESS / "listas"

# Marca deixada nos modelos onde o agente ou o consultor precisa escrever.
MARCA = "PREENCHER"

ETAPAS = ["briefing", "storyline", "storyboard", "redacao", "revisao", "entregue"]

# Tipos de página que não levam título de ação.
TIPOS_SEM_TITULO_DE_ACAO = {"capa", "agenda", "secao", "frase", "citacao", "encerramento"}

SECOES_DO_BRIEFING = ["audiencia", "de e para", "grande ideia", "chamada para acao", "resistencias"]


@dataclass
class Achado:
    """Um problema encontrado por uma checagem."""

    nivel: str  # "erro" reprova; "aviso" só informa
    checagem: str
    arquivo: str
    linha: int
    texto: str

    def formatar(self) -> str:
        onde = self.arquivo + (f":{self.linha}" if self.linha else "")
        return f"{self.nivel.upper():5} [{self.checagem}] {onde}: {self.texto}"


@dataclass
class Pagina:
    """Uma página de apresentação lida de conteudo.md."""

    numero: int
    titulo: str
    linha: int
    meta: dict = field(default_factory=dict)
    corpo: str = ""
    notas: str = ""


_FORA_DE_UTF8: set[str] = set()


def _decodificar(dados: bytes) -> tuple[str, str] | None:
    """Texto e codificação do conteúdo de um arquivo. None quando o conteúdo não é texto.

    O Excel e o Bloco de Notas do Windows gravam em cp1252 ou em UTF-16.
    Um registro salvo assim continua sendo o registro do projeto, então
    ele é lido, e quem chamou é avisado.
    """
    if dados.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return dados.decode("utf-16"), "utf-16"
        except UnicodeDecodeError:
            return None
    try:
        return dados.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        pass
    if b"\x00" in dados:
        return None
    try:
        return dados.decode("cp1252"), "cp1252"
    except UnicodeDecodeError:
        return None


def ler(caminho: Path) -> str:
    """Devolve o texto do arquivo, ou vazio quando ele não existe ou não é texto.

    Um arquivo fora de UTF-8 é lido na codificação em que foi salvo, com
    um aviso na saída de erro, uma vez por arquivo.
    """
    try:
        dados = Path(caminho).read_bytes()
    except OSError:
        return ""
    lido = _decodificar(dados)
    if lido is None:
        return ""
    texto, codificacao = lido
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    if codificacao != "utf-8" and str(caminho) not in _FORA_DE_UTF8:
        _FORA_DE_UTF8.add(str(caminho))
        print(f"Aviso do harness: {relativo(caminho)} não está em UTF-8 e foi lido como {codificacao}. Salve o arquivo em UTF-8.", file=sys.stderr)
    return texto


def ilegivel(caminho: Path) -> bool:
    """Diz se o arquivo existe, tem conteúdo e não pôde ser lido como texto."""
    try:
        dados = Path(caminho).read_bytes()
    except OSError:
        return False
    return bool(dados.strip()) and _decodificar(dados) is None


def gravar(caminho: Path, texto: str) -> None:
    """Grava o arquivo inteiro de uma vez, em UTF-8.

    O texto vai para um arquivo temporário na mesma pasta e só então toma
    o lugar do original. Uma queda no meio da gravação deixa o original
    como estava.
    """
    caminho = Path(caminho)
    if caminho.is_symlink():
        caminho = caminho.resolve()  # o atalho continua atalho: quem muda é o arquivo para onde ele aponta
    caminho.parent.mkdir(parents=True, exist_ok=True)
    descritor, temporario = tempfile.mkstemp(dir=caminho.parent, prefix=f".{caminho.name}.", suffix=".tmp")
    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as saida:
            saida.write(texto)
        if caminho.exists():
            os.chmod(temporario, caminho.stat().st_mode & 0o777)
        else:
            os.chmod(temporario, 0o644)
        os.replace(temporario, caminho)
    except BaseException:
        try:
            os.unlink(temporario)
        except OSError:
            pass
        raise


def relativo(caminho: Path) -> str:
    """Caminho a partir da raiz do projeto, para as mensagens."""
    try:
        return str(Path(caminho).resolve().relative_to(RAIZ))
    except ValueError:
        return str(caminho)


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem pontuação, para comparar títulos."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    sem_acento = re.sub(r"[^\w\s]", " ", sem_acento.lower())
    return re.sub(r"\s+", " ", sem_acento).strip()


def cabecalho(texto: str) -> tuple[dict, str]:
    """Separa o cabeçalho entre linhas '---' do resto do arquivo.

    O cabeçalho é uma lista simples de 'chave: valor'. Não é YAML completo
    de propósito: assim nenhum pacote externo é necessário.
    """
    linhas = texto.splitlines()
    if not linhas or linhas[0].strip() != "---":
        return {}, texto
    meta: dict = {}
    for i, linha in enumerate(linhas[1:], start=1):
        if linha.strip() == "---":
            return meta, "\n".join(linhas[i + 1:])
        if ":" in linha and not linha.lstrip().startswith("#"):
            chave, valor = linha.split(":", 1)
            meta[chave.strip()] = valor.strip()
    return {}, texto


def trocar_campo(texto: str, chave: str, valor, acrescentar: bool = False) -> str:
    """Troca o valor de um campo 'chave: valor', de preferência no cabeçalho do arquivo.

    O valor entra como foi escrito e em uma linha só: uma barra invertida
    não é lida como comando de substituição, e uma quebra de linha não
    cria outro campo. Com 'acrescentar', o campo que não existe é criado
    no cabeçalho.
    """
    em_uma_linha = re.sub(r"\s+", " ", str(valor)).strip()
    linha = f"{chave}: {em_uma_linha}"
    padrao = re.compile(rf"^{re.escape(chave)}:.*$", flags=re.MULTILINE)
    linhas = texto.splitlines(keepends=True)
    fim = None
    if linhas and linhas[0].strip() == "---":
        fim = next((i for i, l in enumerate(linhas[1:], start=1) if l.strip() == "---"), None)
    if fim is not None:
        topo, resto = "".join(linhas[:fim]), "".join(linhas[fim:])
        novo, quantos = padrao.subn(lambda _: linha, topo, count=1)
        if quantos:
            return novo + resto
        if acrescentar:
            return topo + linha + "\n" + resto
    novo, quantos = padrao.subn(lambda _: linha, texto, count=1)
    if quantos or not acrescentar:
        return novo
    return f"---\n{linha}\n---\n" + texto


def secoes(texto: str) -> dict[str, str]:
    """Corpo de cada seção de nível 2, pela forma normalizada do título."""
    resultado: dict[str, str] = {}
    atual = None
    for linha in texto.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", linha)
        if m:
            atual = normalizar(m.group(1))
            resultado[atual] = ""
        elif atual is not None:
            resultado[atual] += linha + "\n"
    return resultado


def achar_secao(mapa: dict[str, str], nome: str) -> str | None:
    """Seção cujo título começa pelo nome pedido. None quando não existe."""
    for titulo, corpo in mapa.items():
        if titulo.startswith(nome):
            return corpo
    return None


def tabela(texto: str) -> list[dict]:
    """Linhas da primeira tabela Markdown do texto, como dicionários."""
    colunas: list[str] = []
    linhas: list[dict] = []
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha.startswith("|"):
            if colunas:
                break
            continue
        celulas = [c.strip() for c in linha.strip("|").split("|")]
        if not colunas:
            colunas = [normalizar(c) for c in celulas]
        elif all(re.fullmatch(r":?-{2,}:?", c) for c in celulas if c):
            continue
        else:
            linhas.append(dict(zip(colunas, celulas)))
    return linhas


def ler_tsv(caminho: Path) -> list[dict]:
    """Linhas de um arquivo TSV com cabeçalho. Linhas com '#' são comentário."""
    texto = ler(caminho)
    uteis = [l for l in texto.splitlines() if l.strip() and not l.startswith("#")]
    if not uteis:
        return []
    leitor = csv.reader(uteis, delimiter="\t", quoting=csv.QUOTE_NONE)
    colunas = [c.strip() for c in next(leitor)]
    # Um campo a mais que o cabeçalho é ignorado, e um a menos fica vazio.
    return [{c: (campos[i].strip() if i < len(campos) else "") for i, c in enumerate(colunas)} for campos in leitor if campos]


def paginas(texto: str) -> list[Pagina]:
    """Páginas de um conteudo.md.

    Cada página começa por '## N. Título'. A primeira linha de comentário
    HTML traz os campos da página ('tipo: dados; secao: X; fonte: E-001').
    O que vem depois de uma linha 'Notas:' são as notas de quem apresenta.
    """
    _, corpo = cabecalho(texto)
    deslocamento = len(texto.splitlines()) - len(corpo.splitlines())
    resultado: list[Pagina] = []
    atual: Pagina | None = None
    em_notas = False
    for n, linha in enumerate(corpo.splitlines(), start=1 + deslocamento):
        m = re.match(r"^##\s+(\d+)\.\s+(.+?)\s*$", linha)
        if m:
            atual = Pagina(numero=int(m.group(1)), titulo=m.group(2), linha=n)
            resultado.append(atual)
            em_notas = False
            continue
        if atual is None:
            continue
        campos = re.match(r"^\s*<!--(.*?)-->\s*$", linha)
        if campos and not atual.meta and not atual.corpo.strip():
            for par in campos.group(1).split(";"):
                if ":" in par:
                    chave, valor = par.split(":", 1)
                    atual.meta[normalizar(chave)] = valor.strip()
            continue
        if re.match(r"^\s*>?\s*Notas?:", linha, flags=re.IGNORECASE):
            em_notas = True
            linha = re.sub(r"^\s*>?\s*Notas?:\s*", "", linha, flags=re.IGNORECASE)
        if em_notas:
            atual.notas += linha + "\n"
        else:
            atual.corpo += linha + "\n"
    return resultado


_TRECHOS_FORA_DA_PROSA = [
    r"`[^`]*`",            # código em linha
    r"<!--.*?-->",         # comentário HTML
    r"\]\([^)]*\)",        # destino de link
    r"https?://\S+",       # endereço
    r"\"[^\"]*\"",         # citação entre aspas retas
    r"“[^”]*”",            # citação entre aspas curvas
    r"«[^»]*»",            # citação entre aspas angulares
]


def limpar_linha(linha: str) -> str:
    """Tira da linha o que não é prosa do autor: código, links e citações.

    Uma expressão citada entre aspas não é um vício de quem escreve, então
    as checagens de texto não olham para ela.
    """
    for padrao in _TRECHOS_FORA_DA_PROSA:
        linha = re.sub(padrao, " ", linha)
    return linha


def linhas_de_prosa(texto: str):
    """Gera (número, linha limpa) para as linhas que são prosa.

    Pula o cabeçalho, os blocos de código e as linhas que só separam
    colunas de tabela.
    """
    meta, corpo = cabecalho(texto)
    deslocamento = len(texto.splitlines()) - len(corpo.splitlines())
    em_codigo = False
    for n, linha in enumerate(corpo.splitlines(), start=1 + deslocamento):
        if linha.lstrip().startswith("```"):
            em_codigo = not em_codigo
            continue
        if em_codigo or re.fullmatch(r"[\s|:\-]*", linha):
            continue
        yield n, limpar_linha(linha)


def contar_palavras(texto: str) -> int:
    """Palavras do texto, sem marcação Markdown e sem os campos da página."""
    texto = re.sub(r"<!--.*?-->", " ", texto, flags=re.DOTALL)
    texto = re.sub(r"^\s*```.*?^\s*```", " ", texto, flags=re.DOTALL | re.MULTILINE)  # gráficos e código
    texto = re.sub(r"[#*_>|`\[\]()-]", " ", texto)
    return len(re.findall(r"\w+", texto))


def entregaveis() -> list[Path]:
    """Pastas de entregável: as que têm briefing.md e não começam por '_'."""
    if not BASE.is_dir():
        return []
    return sorted(
        p for p in BASE.iterdir()
        if p.is_dir() and not p.name.startswith(("_", ".")) and (p / "briefing.md").is_file()
    )


def fase_atual() -> int:
    """A fase em que o projeto está, pelo campo 'fase' do brief. Um projeto sem o campo está na fase 1."""
    meta, _ = cabecalho(ler(PROJETO / "brief.md"))
    valor = meta.get("fase", "").strip()
    return int(valor) if valor.isdigit() and int(valor) > 0 else 1


def fase_do_entregavel(meta: dict) -> int:
    """A fase em que o entregável nasceu. Sem o campo, é a fase 1."""
    valor = meta.get("fase", "").strip()
    return int(valor) if valor.isdigit() and int(valor) > 0 else 1


def arquivos_de_conteudo(pasta: Path) -> list[Path]:
    """Arquivos com o texto do entregável, em todos os idiomas."""
    achados: list[Path] = []
    for padrao in ("conteudo*.md", "documento*.md", "planilha*.md"):
        achados.extend(sorted(pasta.glob(padrao)))
    return achados


def interativos(pasta: Path) -> list[Path]:
    """Os HTML interativos do entregável: um arquivo único por peça."""
    return sorted((pasta / "interativos").glob("*.html"))


def cabecalho_do_interativo(texto: str) -> dict:
    """Campos do comentário '<!-- interativo ... -->' que abre o arquivo."""
    m = re.search(r"<!--\s*interativo\b(.*?)-->", texto, flags=re.DOTALL)
    campos: dict[str, str] = {}
    if m:
        for linha in m.group(1).splitlines():
            if ":" in linha:
                chave, valor = linha.split(":", 1)
                campos[normalizar(chave)] = valor.strip()
    return campos


def texto_visivel(html: str) -> list[tuple[int, str]]:
    """Linhas de texto que a pessoa lê em um HTML, com o número da linha.

    Scripts, estilos e comentários somem, mas as quebras de linha ficam,
    para que o número da linha continue valendo.
    """
    def apagar(m: re.Match) -> str:
        return "\n" * m.group(0).count("\n")

    limpo = re.sub(r"<!--.*?-->", apagar, html, flags=re.DOTALL)
    limpo = re.sub(r"<(script|style)\b.*?</\1\s*>", apagar, limpo, flags=re.DOTALL | re.IGNORECASE)
    limpo = re.sub(r"<[^>]*>", lambda m: " " + apagar(m), limpo, flags=re.DOTALL)
    limpo = re.sub(r"&nbsp;|&#160;", " ", limpo)
    return [(n, linha.strip()) for n, linha in enumerate(limpo.splitlines(), start=1) if linha.strip()]


def idiomas_do_arquivo(arquivo: Path, meta: dict) -> list[str]:
    """Idiomas a aplicar nas listas de texto: 'pt', 'es', 'en'.

    'conteudo.es.md' é espanhol. Sem sufixo, vale o primeiro idioma do
    briefing. Sem briefing, as três listas são aplicadas.
    """
    partes = arquivo.name.split(".")
    if len(partes) == 3 and len(partes[1]) in (2, 5):
        return [partes[1][:2].lower()]
    declarados = [i.strip()[:2].lower() for i in meta.get("idiomas", "").split(",") if i.strip()]
    return declarados[:1] or ["pt", "es", "en"]


def etapa(meta: dict) -> int:
    """Posição do estado do entregável na ordem das etapas."""
    estado = normalizar(meta.get("estado", "briefing"))
    return ETAPAS.index(estado) if estado in ETAPAS else 0


def carimbo(pasta: Path) -> str:
    """Resumo do conteúdo atual do entregável.

    A revisão guarda este valor. Quando o conteúdo muda, o valor muda e a
    revisão anterior deixa de valer.
    """
    resumo = hashlib.sha256()
    for arquivo in arquivos_de_conteudo(pasta) + interativos(pasta):
        resumo.update(arquivo.name.encode())
        resumo.update(arquivo.read_bytes())
    return resumo.hexdigest()[:16]


def tem_paginas_reais(pasta: Path) -> bool:
    """Diz se o entregável já tem conteúdo além do modelo."""
    if any(MARCA not in ler(arquivo) for arquivo in interativos(pasta)):
        return True
    for arquivo in arquivos_de_conteudo(pasta):
        texto = ler(arquivo)
        if MARCA not in texto and contar_palavras(cabecalho(texto)[1]) > 20:
            return True
        if any(MARCA not in p.titulo for p in paginas(texto)):
            return True
    return False


def briefing_completo(pasta: Path) -> list[str]:
    """Seções obrigatórias do briefing que faltam ou ainda têm a marca."""
    _, corpo = cabecalho(ler(pasta / "briefing.md"))
    mapa = secoes(corpo)
    faltas = []
    for nome in SECOES_DO_BRIEFING:
        texto = achar_secao(mapa, nome)
        if texto is None or MARCA in texto or not texto.strip():
            faltas.append(nome)
    return faltas


def storyline_aprovada(pasta: Path) -> bool:
    meta, _ = cabecalho(ler(pasta / "storyline.md"))
    return normalizar(meta.get("aprovada", "")) == "sim"
