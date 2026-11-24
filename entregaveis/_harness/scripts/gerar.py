#!/usr/bin/env python3
"""Gera o arquivo final de um entregável a partir da fonte em Markdown.

Uso:
    gerar.py ID                    gera no formato do briefing (pptx, docx, pdf ou xlsx)
    gerar.py ID --formato docx     gera em outro formato
    gerar.py ID --idioma es        gera a versão de conteudo.es.md ou documento.es.md
    gerar.py ID --pdf              gera também o PDF do arquivo
    gerar.py ID --imagens          gera também uma imagem por página, para conferir
    gerar.py ID --rascunho         gera mesmo com erro nas checagens, com a marca de rascunho
    gerar.py ID --modelo ARQUIVO   usa este modelo em vez do registrado em _projeto/marca.md
    gerar.py --layouts [ARQUIVO]   lista os layouts de um modelo de apresentação

A fonte é a verdade do entregável: conteudo.md vira PowerPoint,
documento.md vira Word e PDF, e planilha.md com a pasta dados/ vira
Excel. O arquivo sai em saida/, sobre o modelo registrado em
_projeto/marca.md. Sem modelo, o desenho é neutro e o script avisa.

O gerador recusa o entregável sem briefing completo e storyline
aprovada, e o que reprova nas checagens, a não ser como rascunho.

Diferente do resto do harness, este script precisa de pacotes de fora:
python-pptx, python-docx e openpyxl, um para cada formato. O PDF e as
imagens pedem o LibreOffice (soffice), e as imagens também o pdftoppm.
"""
from __future__ import annotations

import argparse
import colorsys
import csv
import io
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402
import validar  # noqa: E402

PACOTES = {"pptx": ("pptx", "python-pptx"), "docx": ("docx", "python-docx"), "xlsx": ("openpyxl", "openpyxl")}
ROTULO_DE_FONTE = {"pt": "Fonte", "es": "Fuente", "en": "Source"}
ROTULO_DE_FONTES = {"pt": "Fontes", "es": "Fuentes", "en": "Sources"}
ROTULO_DE_RASCUNHO = {"pt": "RASCUNHO", "es": "BORRADOR", "en": "DRAFT"}
COR_DE_DESTAQUE, COR_NEUTRA = "0B5CAD", "A9B3BD"
TEXTO_CLARO, TEXTO_ESCURO = "FFFFFF", "1F2933"
RASCUNHO_NO_CLARO, RASCUNHO_NO_ESCURO = "A3382C", "FF9B8F"

avisos: list[str] = []


def exigir(formato: str):
    modulo, pacote = PACOTES[formato]
    try:
        return __import__(modulo)
    except ImportError:
        raise SystemExit(f"Para gerar {formato} é preciso o pacote {pacote}. Instale com: python3 -m pip install {pacote}")


# --- Leitura da fonte -----------------------------------------------------


def trechos(texto: str) -> list[tuple[str, bool, bool]]:
    """Divide uma linha em (texto, negrito, itálico), a partir da marcação Markdown."""
    texto = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", texto)
    texto = texto.replace("`", "")
    resultado = []
    # O asterisco só abre um destaque quando vem colado à palavra que destaca e não está no meio de outra.
    # Assim '2 * 3 e 4 * 5' e '2*3 e 4*5' continuam sendo contas.
    for parte in re.split(r"(\*\*(?=\S)[^*]+(?<=\S)\*\*|(?<![\w*])\*(?=\S)[^*]+(?<=\S)\*(?![\w*])|(?<!\w)_[^_]+_(?!\w))", texto):
        if not parte:
            continue
        if parte.startswith("**"):
            resultado.append((parte[2:-2], True, False))
        elif parte[0] in "*_" and parte[-1] == parte[0] and len(parte) > 2:
            resultado.append((parte[1:-1], False, True))
        else:
            resultado.append((parte, False, False))
    return resultado


def plano(texto: str) -> str:
    return "".join(t for t, _, _ in trechos(texto))


def dentro_do_projeto(caminho: Path) -> bool:
    """Diz se o caminho, depois de resolvido, fica dentro da pasta do projeto."""
    try:
        caminho.resolve().relative_to(comum.RAIZ.resolve())
        return True
    except ValueError:
        return False


def ler_grafico(linhas: list[str], pasta: Path) -> dict:
    """Lê um bloco 'grafico': campos 'chave: valor' e, depois de 'dados:', uma tabela separada por '|'."""
    spec: dict = {"tipo": "barras", "linhas": []}
    em_dados = False
    for linha in linhas:
        if not linha.strip():
            continue
        if em_dados:
            celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in celulas):
                spec["linhas"].append(celulas)
        elif re.match(r"^\s*dados\s*:\s*$", linha):
            em_dados = True
        elif ":" in linha:
            chave, valor = linha.split(":", 1)
            spec[comum.normalizar(chave)] = valor.strip()
    if spec.get("arquivo"):
        if not dentro_do_projeto(pasta / spec["arquivo"]):
            raise SystemExit(f"O bloco 'grafico' cita '{spec['arquivo']}', que fica fora da pasta do projeto. Leve os dados para a pasta dados/ do entregável.")
        spec["linhas"] = ler_dados(pasta / spec["arquivo"])
    return spec


def blocos(texto: str, pasta: Path) -> list[dict]:
    """Transforma Markdown em blocos: titulo, paragrafo, lista, tabela, imagem, grafico e citacao."""
    resultado: list[dict] = []
    linhas = texto.splitlines()
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        if not linha.strip() or re.fullmatch(r"\s*<!--.*?-->\s*", linha):
            i += 1
            continue
        cerca = re.match(r"^\s*```\s*(\w*)", linha)
        if cerca:
            fim = next((j for j in range(i + 1, len(linhas)) if linhas[j].lstrip().startswith("```")), len(linhas))
            dentro = linhas[i + 1:fim]
            if comum.normalizar(cerca.group(1)) in ("grafico", "chart"):
                resultado.append({"tipo": "grafico", "spec": ler_grafico(dentro, pasta)})
            else:
                resultado.append({"tipo": "paragrafo", "texto": "\n".join(dentro), "codigo": True})
            i = fim + 1
            continue
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", linha)
        if m:
            resultado.append({"tipo": "titulo", "nivel": len(m.group(1)), "texto": m.group(2)})
            i += 1
            continue
        m = re.match(r"^\s*!\[([^\]]*)\]\(([^)\s]+)[^)]*\)\s*$", linha)
        if m:
            resultado.append({"tipo": "imagem", "alt": m.group(1), "caminho": m.group(2)})
            i += 1
            continue
        if linha.lstrip().startswith("|"):
            tabela = []
            while i < len(linhas) and linhas[i].lstrip().startswith("|"):
                celulas = [c.strip() for c in linhas[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in celulas if c):
                    tabela.append(celulas)
                i += 1
            if tabela:
                resultado.append({"tipo": "tabela", "linhas": tabela})
            continue
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", linha):
            itens = []
            while i < len(linhas):
                m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", linhas[i])
                if m:
                    itens.append([min(len(m.group(1).expandtabs(4)) // 2, 3), m.group(2)[0].isdigit(), m.group(3)])
                elif linhas[i].strip() and linhas[i].startswith(" ") and itens:
                    itens[-1][2] += " " + linhas[i].strip()
                else:
                    break
                i += 1
            resultado.append({"tipo": "lista", "itens": itens})
            continue
        if linha.lstrip().startswith(">"):
            citacao = []
            while i < len(linhas) and linhas[i].lstrip().startswith(">"):
                citacao.append(linhas[i].lstrip()[1:].strip())
                i += 1
            resultado.append({"tipo": "citacao", "texto": " ".join(citacao)})
            continue
        paragrafo = [linha.strip()]
        i += 1
        while i < len(linhas) and linhas[i].strip() and not re.match(r"^\s*(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|\||>|```|!\[)", linhas[i]):
            paragrafo.append(linhas[i].strip())
            i += 1
        resultado.append({"tipo": "paragrafo", "texto": " ".join(paragrafo)})
    return resultado


def ler_dados(arquivo: Path) -> list[list[str]]:
    """Linhas de um arquivo .csv ou .tsv, com o separador descoberto pelo cabeçalho."""
    if not arquivo.is_file():
        raise SystemExit(f"Arquivo de dados não encontrado: {comum.relativo(arquivo)}")
    if comum.ilegivel(arquivo):
        raise SystemExit(f"{comum.relativo(arquivo)} não pôde ser lido como texto. Salve os dados como CSV em UTF-8.")
    texto = comum.ler(arquivo)  # lê também o CSV que o Excel grava em cp1252 ou UTF-16, e avisa
    primeira = texto.splitlines()[0] if texto.strip() else ""
    separador = "\t" if arquivo.suffix == ".tsv" or "\t" in primeira else (";" if primeira.count(";") > primeira.count(",") else ",")
    return [linha for linha in csv.reader(texto.splitlines(), delimiter=separador) if any(c.strip() for c in linha)]


# Como o número é escrito em cada idioma: o separador decimal. O de milhar é o outro.
DECIMAL_DO_IDIOMA = {"pt": ",", "es": ",", "en": "."}
_MOEDA = r"(?:R\$|US\$|\$|€|£)"
_NUMERO = re.compile(rf"([-−+]?)\s*({_MOEDA})?\s*([-−+]?)(\d[\d., ]*?)\s*({_MOEDA}|%)?")


def _partes_do_numero(valor: str) -> tuple[bool, str, str, bool] | None:
    """(negativo, algarismos com os separadores, moeda, percentual) de um texto que tem cara de número."""
    limpo = re.sub(r"[\u00a0\u2009\u202f]", " ", valor).strip()
    m = _NUMERO.fullmatch(limpo)
    if not m:
        return None
    sufixo = m.group(5) or ""
    return bool(set("-−") & {m.group(1), m.group(3)}), m.group(4), m.group(2) or sufixo.replace("%", ""), sufixo == "%"


def _pista_do_decimal(algarismos: str) -> str:
    """',' ou '.' quando o número mostra sozinho qual é o separador decimal. Vazio quando não mostra.

    '1.234,5' e '12,5' mostram. '1.234' não mostra: pode ser mil duzentos e
    trinta e quatro ou um vírgula duzentos e trinta e quatro.
    """
    algarismos = algarismos.replace(" ", "")
    if "." in algarismos and "," in algarismos:
        return "." if algarismos.rfind(".") > algarismos.rfind(",") else ","
    for separador, outro in ((".", ","), (",", ".")):
        if algarismos.count(separador) > 1:
            return outro  # um separador repetido é o de milhar
        if algarismos.count(separador) == 1:
            antes, depois = algarismos.split(separador)
            if len(depois) != 3 or not re.fullmatch(r"[1-9]\d{0,2}", antes):
                return separador  # não tem a forma de um grupo de milhar
    return ""


def decimal_da_coluna(valores: list[str], idioma: str) -> str:
    """O separador decimal de uma coluna de dados.

    Vale o que os próprios valores mostram: uma coluna com '12,5' usa a
    vírgula, e então '1.234' é milhar. Quando nenhum valor mostra, ou os
    valores se contradizem, vale o costume do idioma do entregável.
    """
    pistas = {_pista_do_decimal(partes[1]) for v in valores if (partes := _partes_do_numero(v))} - {""}
    return pistas.pop() if len(pistas) == 1 else DECIMAL_DO_IDIOMA.get(idioma, ",")


def _converter(algarismos: str, decimal: str) -> tuple[int | float, int, bool] | None:
    """(valor, casas decimais, se veio com separador de milhar) de algarismos escritos com este separador decimal."""
    milhar = "," if decimal == "." else "."
    m = re.fullmatch(rf"([1-9]\d{{0,2}}(?:{re.escape(milhar)}\d{{3}})+|\d+)(?:{re.escape(decimal)}(\d+))?", algarismos)
    if not m:
        return None
    inteiro, fracao = m.group(1).replace(milhar, ""), m.group(2) or ""
    return (float(f"{inteiro}.{fracao}") if fracao else int(inteiro)), len(fracao), milhar in m.group(1)


def ler_numero(valor: str, decimal: str = ",") -> tuple[int | float, str] | None:
    """(número, formato de exibição) do texto de uma célula. None quando o texto não é um número.

    Aceita o percentual e a moeda: '12%' é 0,12 com o formato '0%', e
    'R$ 1.200' é 1200 com o formato de moeda. Um código com zero à
    esquerda, como um CEP, e um número com mais de 15 algarismos não são
    números de conta: ficam como texto, para não perder algarismo.
    """
    partes = _partes_do_numero(valor)
    if partes is None:
        return None
    negativo, algarismos, moeda, percentual = partes
    so_algarismos = re.sub(r"\D", "", algarismos)
    if re.fullmatch(r"0\d+", algarismos) or len(so_algarismos) > 15:
        return None
    if " " in algarismos:
        compacto = algarismos.replace(" ", "")
        if not re.fullmatch(r"[1-9]\d{0,2}(?: \d{3})+(?:[.,]\d+)?", algarismos):
            return None
        resto = "," if "," in compacto else "."
        lido = _converter(compacto, resto)
        lido = (lido[0], lido[1], True) if lido else None
    else:
        lido = _converter(algarismos, decimal) or _converter(algarismos, "." if decimal == "," else ",")
    if lido is None:
        return None
    numero_lido, casas, agrupado = lido
    if negativo:
        numero_lido = -numero_lido
    zeros = ("." + "0" * casas) if casas else ""
    if percentual:
        return round(numero_lido / 100, casas + 2), f"0{zeros}%"
    if moeda:
        return numero_lido, f'"{moeda}" #,##0{zeros}'
    return numero_lido, (f"#,##0{zeros}" if agrupado else "")


# --- Marca do projeto -----------------------------------------------------


def marca() -> dict:
    """O que _projeto/marca.md registra: modelos, cores de gráfico e o layout de cada tipo de página."""
    texto = comum.ler(comum.PROJETO / "marca.md")
    itens = {comum.normalizar(l.get("item", "")): l.get("valor", "").strip() for l in comum.tabela(texto)}
    layouts = {}
    secao = comum.achar_secao(comum.secoes(texto), "layouts do modelo")
    if secao:
        for linha in comum.tabela(secao):
            tipo, layout = comum.normalizar(linha.get("tipo de pagina", "")), linha.get("layout", "").strip()
            if tipo and layout and comum.MARCA not in layout:
                layouts[tipo] = layout
    cores = re.findall(r"#([0-9A-Fa-f]{6})\b", itens.get("cores de destaque em graficos", ""))
    sobre_o_fundo = re.findall(r"#([0-9A-Fa-f]{6})\b", itens.get("cor do texto sobre o fundo", ""))
    return {
        "pptx": itens.get("modelo de apresentacao", ""),
        "docx": itens.get("modelo de documento", ""),
        "xlsx": itens.get("modelo de planilha", ""),
        "destaque": (cores[0] if cores else COR_DE_DESTAQUE).upper(),
        "neutra": (cores[1] if len(cores) > 1 else COR_NEUTRA).upper(),
        "paleta": [c.upper() for c in cores],
        "texto": sobre_o_fundo[0].upper() if sobre_o_fundo else "",
        "layouts": layouts,
    }


def achar_modelo(formato: str, indicado: str | None, registro: dict) -> Path | None:
    valor = indicado or registro.get(formato, "")
    valor = re.sub(r"[`*]", "", valor).strip()
    if not valor or comum.MARCA in valor:
        avisos.append(f"Sem modelo de {formato} registrado em _projeto/marca.md: o arquivo saiu com desenho neutro. Peça o modelo ao consultor.")
        return None
    for base in (Path.cwd(), comum.RAIZ, comum.BASE, comum.INTAKE / "materiais"):
        candidato = (base / valor).resolve() if not Path(valor).is_absolute() else Path(valor)
        if candidato.is_file():
            return candidato
    raise SystemExit(f"O modelo '{valor}' não foi encontrado. Corrija o caminho em _projeto/marca.md ou passe --modelo.")


def evidencias() -> dict[str, dict]:
    return {l.get("id", ""): l for l in comum.ler_tsv(comum.PROJETO / "evidencias.tsv")}


def linha_de_fonte(campo: str, idioma: str, registro: dict[str, dict]) -> str:
    """'Fonte: origem, data' para os E-nnn citados. Vazio quando a página não cita evidência."""
    partes = []
    for ident in re.findall(r"\bE-\d+\b", campo or ""):
        linha = registro.get(ident)
        if linha:
            texto = ", ".join(v for v in (linha.get("fonte", ""), linha.get("data", "")) if v)
            if texto and texto not in partes:
                partes.append(texto)
    return f"{ROTULO_DE_FONTE.get(idioma, 'Fonte')}: {'; '.join(partes)}." if partes else ""


def por_titulo_no_arquivo(documento, titulo: str, neutro: bool = False) -> None:
    """Grava o título nas propriedades do arquivo. Um modelo que liga as propriedades por uma relação
    fora do padrão fica como está: criar outra parte com o mesmo nome estraga o arquivo. No desenho
    neutro, apaga o autor e a descrição que a biblioteca traz no arquivo de base dela."""
    pacote = documento.part.package
    padrao = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
    try:
        pacote.part_related_by(padrao)
    except KeyError:
        if any(str(parte.partname).lower() == "/docprops/core.xml" for parte in pacote.iter_parts()):
            return
    documento.core_properties.title = titulo
    if neutro:
        for campo in ("author", "last_modified_by", "comments"):
            setattr(documento.core_properties, campo, "")


# --- Cores e fundo do slide -----------------------------------------------

_NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def _nome(no) -> str:
    return no.tag.rsplit("}", 1)[-1] if isinstance(no.tag, str) else ""


def em_rgb(cor: str) -> tuple[float, float, float]:
    return tuple(int(cor[i:i + 2], 16) / 255 for i in (0, 2, 4))


def em_hexa(rgb) -> str:
    return "".join(f"{round(min(1.0, max(0.0, c)) * 255):02X}" for c in rgb)


def misturar(cor: str, outra: str, quanto: float) -> str:
    """A cor a caminho da outra: 0 é a própria cor, 1 é a outra."""
    return em_hexa(a + (b - a) * quanto for a, b in zip(em_rgb(cor), em_rgb(outra)))


def luminancia(cor: str) -> float:
    """Luminância relativa, de 0 (preto) a 1 (branco), como a regra de contraste da WCAG calcula."""
    canais = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in em_rgb(cor)]
    return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]


def escuro(cor: str) -> bool:
    """Diz se o texto branco contrasta mais com esta cor do que o texto preto."""
    return luminancia(cor) < 0.179


def texto_sobre(cor: str) -> str:
    return TEXTO_CLARO if escuro(cor) else TEXTO_ESCURO


def _tema_e_mapa(layout) -> tuple[dict, dict]:
    """As cores do tema do slide mestre e o mapa que diz qual delas é o fundo e qual é o texto."""
    from lxml import etree

    mestre = layout.slide_master
    tema: dict[str, str] = {}
    for relacao in mestre.part.rels.values():
        if relacao.reltype.endswith("/theme") and not relacao.is_external:
            esquema = etree.fromstring(relacao.target_part.blob).find(".//a:clrScheme", _NS)
            for no in (esquema if esquema is not None else []):
                if len(no):
                    tema[_nome(no)] = (no[0].get("lastClr") or no[0].get("val") or "").upper()
    mapa: dict[str, str] = {}
    do_mestre = mestre._element.find("p:clrMap", _NS)
    if do_mestre is not None:
        mapa = dict(do_mestre.attrib)
    do_layout = layout._element.find("p:clrMapOvr/a:overrideClrMapping", _NS)
    if do_layout is not None:
        mapa = dict(do_layout.attrib)
    return tema, mapa


def _cor_do_no(no, tema: dict, mapa: dict) -> str | None:
    """A cor de um nó de cor do arquivo (srgbClr, schemeClr, sysClr ou prstClr), com os ajustes de luminosidade."""
    tipo, valor = _nome(no), no.get("val", "")
    if tipo == "srgbClr":
        cor = valor
    elif tipo == "sysClr":
        cor = no.get("lastClr") or {"window": "FFFFFF", "windowText": "000000"}.get(valor, "")
    elif tipo == "schemeClr":
        cor = tema.get(mapa.get(valor, valor), "")
    elif tipo == "prstClr":
        cor = {"black": "000000", "white": "FFFFFF"}.get(valor, "")
    else:
        return None
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", cor or ""):
        return None
    matiz, luz, saturacao = colorsys.rgb_to_hls(*em_rgb(cor))
    for ajuste in no:
        try:
            quanto = int(ajuste.get("val", "100000")) / 100000
        except ValueError:
            continue
        if _nome(ajuste) in ("lumMod", "shade"):
            luz *= quanto
        elif _nome(ajuste) == "lumOff":
            luz += quanto
        elif _nome(ajuste) == "tint":
            luz = luz * quanto + (1 - quanto)
    return em_hexa(colorsys.hls_to_rgb(matiz, min(1.0, max(0.0, luz)), saturacao))


def _cor_da_imagem(dados: bytes) -> str | None:
    """A cor média de uma imagem de fundo. None quando o formato não é lido."""
    try:
        from PIL import Image

        with Image.open(io.BytesIO(dados)) as imagem:
            return em_hexa(c / 255 for c in imagem.convert("RGB").resize((1, 1)).getpixel((0, 0)))
    except Exception:  # noqa: BLE001 - formato que a biblioteca não lê, como EMF
        return None


def _cor_do_preenchimento(pai, parte, tema: dict, mapa: dict) -> str | None:
    """A cor de um preenchimento sólido, a média de um degradê ou a média de uma imagem. None quando não há preenchimento."""
    if pai is None:
        return None
    solido = pai.find("a:solidFill", _NS)
    if solido is not None and len(solido):
        return _cor_do_no(solido[0], tema, mapa)
    paradas = [c for parada in pai.iterfind("a:gradFill/a:gsLst/a:gs", _NS) if len(parada) and (c := _cor_do_no(parada[0], tema, mapa))]
    if paradas:
        return em_hexa(sum(em_rgb(c)[i] for c in paradas) / len(paradas) for i in range(3))
    imagem = pai.find("a:blipFill/a:blip", _NS)
    if imagem is None:
        imagem = pai.find("p:blipFill/a:blip", _NS)
    if imagem is not None and imagem.get(f"{{{_NS['r']}}}embed"):
        try:
            return _cor_da_imagem(parte.related_part(imagem.get(f"{{{_NS['r']}}}embed")).blob)
        except KeyError:
            return None
    return None


def _cor_da_forma_de_fundo(dono, largura: int, altura: int, tema: dict, mapa: dict) -> str | None:
    """A cor da forma do layout ou do mestre que cobre o slide inteiro, quando há uma.

    Muitos modelos fazem o fundo com uma imagem ou um retângulo sobre o
    slide, e não com o fundo do arquivo. Vale a forma que está por cima.
    """
    for forma in reversed(list(dono.shapes)):
        if forma.is_placeholder or not forma.width or not forma.height:
            continue
        direita = min(largura, (forma.left or 0) + forma.width)
        baixo = min(altura, (forma.top or 0) + forma.height)
        coberta = max(0, direita - max(0, forma.left or 0)) * max(0, baixo - max(0, forma.top or 0))
        if coberta < 0.85 * largura * altura:
            continue
        elemento = forma._element
        cor = _cor_do_preenchimento(elemento if _nome(elemento) == "pic" else elemento.find("p:spPr", _NS), dono.part, tema, mapa)
        if cor is None and elemento.find("p:spPr/a:noFill", _NS) is None:
            do_estilo = elemento.find("p:style/a:fillRef", _NS)
            if do_estilo is not None and do_estilo.get("idx", "0") != "0" and len(do_estilo):
                cor = _cor_do_no(do_estilo[0], tema, mapa)
        if cor:
            return cor
    return None


_FUNDOS: dict = {}


def cor_do_fundo(slide, largura: int, altura: int) -> str | None:
    """A cor que a audiência vê atrás do conteúdo do slide. None quando o modelo não permite saber.

    A ordem é a do desenho: a forma de fundo do layout, a do mestre, o
    fundo do layout e o fundo do mestre. Um modelo sem fundo declarado
    usa a primeira cor de fundo do tema.
    """
    layout = slide.slide_layout
    chave = (id(layout.part.package), str(layout.part.partname))
    if chave in _FUNDOS:
        return _FUNDOS[chave]
    mestre = layout.slide_master
    tema, mapa = _tema_e_mapa(layout)
    cor = _cor_da_forma_de_fundo(layout, largura, altura, tema, mapa)
    if cor is None and layout._element.get("showMasterSp", "1") not in ("0", "false"):
        cor = _cor_da_forma_de_fundo(mestre, largura, altura, tema, mapa)
    for dono in (layout, mestre):
        if cor is not None:
            break
        fundo = dono._element.find("p:cSld/p:bg", _NS)
        if fundo is None:
            continue
        cor = _cor_do_preenchimento(fundo.find("p:bgPr", _NS), dono.part, tema, mapa)
        referencia = fundo.find("p:bgRef", _NS)
        if cor is None and referencia is not None and len(referencia):
            cor = _cor_do_no(referencia[0], tema, mapa)
        if cor is None and (fundo.find("p:bgPr", _NS) is not None or referencia is not None):
            break  # há um fundo declarado e não deu para ler a cor: não adivinha
    else:
        if cor is None:
            cor = tema.get(mapa.get("bg1", "lt1")) or None
    _FUNDOS[chave] = cor if cor and re.fullmatch(r"[0-9A-F]{6}", cor) else None
    return _FUNDOS[chave]


def pintar(quadro, cor: str | None) -> None:
    """Dá a cor a todo o texto de um quadro. Sem cor, o texto fica com a do modelo."""
    if not cor:
        return
    from pptx.dml.color import RGBColor

    for paragrafo in quadro.paragraphs:
        for corrida in paragrafo.runs:
            corrida.font.color.rgb = RGBColor.from_string(cor)


# --- PowerPoint -----------------------------------------------------------

NOMES_DE_LAYOUT = {
    "capa": ["title slide", "slide de titulo", "diapositivo de titulo", "diapositiva de titulo", "capa", "cover", "portada"],
    "secao": ["section", "secao", "seccao", "seccion", "divisor", "divider"],
    "frase": ["quote", "citacao", "cita", "frase", "statement", "title only", "somente titulo", "so titulo", "solo el titulo"],
    "so_titulo": ["title only", "somente titulo", "so titulo", "solo el titulo", "apenas titulo"],
    "corpo": ["title and content", "titulo e conteudo", "titulo y objetos", "titulo y contenido"],
}


def grupo_do_tipo(tipo: str, tem_texto: bool, tem_visual: bool) -> str:
    if tipo == "capa":
        return "capa"
    if tipo in ("secao", "encerramento"):
        return "secao"
    if tipo in ("frase", "citacao"):
        return "frase"
    return "so_titulo" if tem_visual and not tem_texto else "corpo"


def todos_os_layouts(prs) -> list:
    """Os layouts de todos os slides mestres do modelo, na ordem em que o programa mostra."""
    return [layout for mestre in prs.slide_masters for layout in mestre.slide_layouts]


def escolher_layout(prs, tipo: str, pedido: str, tem_texto: bool, tem_visual: bool):
    from pptx.enum.shapes import PP_PLACEHOLDER as PH

    layouts = todos_os_layouts(prs)
    nomes: dict = {}
    for layout in layouts:
        nomes.setdefault(comum.normalizar(layout.name), layout)  # com nomes repetidos, vale o primeiro
    if pedido:
        if pedido.strip().isdigit() and 1 <= int(pedido) <= len(layouts):
            return layouts[int(pedido) - 1]
        if comum.normalizar(pedido) in nomes:
            return nomes[comum.normalizar(pedido)]
        avisos.append(f"O layout '{pedido}' não existe no modelo. Veja os nomes e os números com gerar.py --layouts.")
    grupo = grupo_do_tipo(tipo, tem_texto, tem_visual)
    for chave in NOMES_DE_LAYOUT[grupo]:
        for nome, layout in nomes.items():
            if re.search(rf"\b{re.escape(chave)}\b", nome):
                return layout

    def tipos(layout) -> set:
        return {p.placeholder_format.type for p in layout.placeholders}

    if grupo == "capa":
        candidatos = [l for l in layouts if PH.CENTER_TITLE in tipos(l) or PH.SUBTITLE in tipos(l)]
    elif grupo == "corpo":
        # O corpo pede um título e uma área só. Layout de capa ou de seção, pelo nome, fica de fora,
        # e entre os que sobram vence o de área de conteúdo e o de menos áreas.
        outros = [c for g in ("capa", "secao", "frase") for c in NOMES_DE_LAYOUT[g]]

        def de_outro_grupo(layout) -> bool:
            nome = comum.normalizar(layout.name)
            return any(re.search(rf"\b{re.escape(c)}\b", nome) for c in outros)

        def areas(layout) -> list:
            return [p.placeholder_format.type for p in layout.placeholders if p.placeholder_format.type in (PH.BODY, PH.OBJECT)]

        candidatos = [l for l in layouts if {PH.TITLE, PH.CENTER_TITLE} & tipos(l) and areas(l) and not de_outro_grupo(l)]
        candidatos.sort(key=lambda l: (PH.OBJECT not in areas(l), len(areas(l))))
    else:
        candidatos = [l for l in layouts if {PH.TITLE, PH.CENTER_TITLE} & tipos(l) and not {PH.BODY, PH.OBJECT} & tipos(l)]
    candidatos = candidatos or [l for l in layouts if {PH.TITLE, PH.CENTER_TITLE} & tipos(l)] or layouts
    return candidatos[0]


def escrever_trechos(paragrafo, texto: str) -> None:
    for parte, negrito, italico in trechos(texto):
        corrida = paragrafo.add_run()
        corrida.text = parte
        if negrito:
            corrida.font.bold = True
        if italico:
            corrida.font.italic = True


def numerar(paragrafo, recuo: bool) -> None:
    """Liga a numeração automática do parágrafo, que o PowerPoint conta sozinho a cada item."""
    from pptx.oxml.ns import qn

    propriedades = paragrafo._p.get_or_add_pPr()
    for antigo in propriedades.xpath("./a:buNone | ./a:buChar | ./a:buAutoNum | ./a:buBlip"):
        propriedades.remove(antigo)
    numeracao = propriedades.makeelement(qn("a:buAutoNum"), {"type": "arabicPeriod"})
    depois = propriedades.xpath("./a:tabLst | ./a:defRPr | ./a:extLst")
    if depois:
        depois[0].addprevious(numeracao)
    else:
        propriedades.append(numeracao)
    if recuo:  # a caixa de texto criada pelo gerador não tem o recuo de lista do modelo
        propriedades.set("marL", "342900")
        propriedades.set("indent", "-342900")


def escrever_texto(quadro, textos: list[dict], com_marcador: bool) -> None:
    """Põe parágrafos, listas e citações em um quadro de texto. 'com_marcador' vale para caixa sem marcador próprio."""
    primeiro = True
    for bloco in textos:
        if bloco["tipo"] == "lista":
            linhas = [(nivel, ("• " if com_marcador and not ordenada else "") + texto, ordenada) for nivel, ordenada, texto in bloco["itens"]]
        elif bloco["tipo"] == "citacao":
            linhas = [(0, f"*{plano(bloco['texto'])}*", False)]
        else:
            linhas = [(0, bloco["texto"], False)]
        for nivel, texto, ordenada in linhas:
            paragrafo = quadro.paragraphs[0] if primeiro else quadro.add_paragraph()
            primeiro = False
            paragrafo.level = nivel
            if ordenada:
                numerar(paragrafo, recuo=com_marcador)
            escrever_trechos(paragrafo, texto)


EMU_POR_PONTO = 12700


def linhas_de_texto(textos: list[dict], largura: int, corpo: int) -> int:
    """Quantas linhas o texto ocupa em uma caixa desta largura, com letra deste tamanho."""
    por_linha = max(12, int(largura / EMU_POR_PONTO / (corpo * 0.5)))
    total = 0
    for bloco in textos:
        itens = [i[2] for i in bloco["itens"]] if bloco["tipo"] == "lista" else [bloco["texto"]]
        total += sum(1 + len(plano(item)) // por_linha for item in itens)
    return total


def altura_do_texto(textos: list[dict], largura: int, corpo: int) -> int:
    return int((linhas_de_texto(textos, largura, corpo) * corpo * 1.4 + corpo) * EMU_POR_PONTO)


def fixar_tamanho(quadro, corpo: int) -> None:
    from pptx.util import Pt

    for paragrafo in quadro.paragraphs:
        for corrida in paragrafo.runs:
            corrida.font.size = Pt(corpo)


def acertar_posicao(slide, forma) -> None:
    """Um modelo exportado por outro programa pode repetir o número do campo. A posição herdada sai então
    do campo errado (a do título no corpo), e por isso ela é copiada do campo do layout que tem o mesmo tipo."""
    if forma is None:
        return
    iguais = [c for c in slide.slide_layout.placeholders if c.placeholder_format.idx == forma.placeholder_format.idx]
    if len(iguais) < 2:
        return
    do_tipo = [c for c in iguais if c.placeholder_format.type == forma.placeholder_format.type]
    if do_tipo and do_tipo[0].width and do_tipo[0].height:
        origem = do_tipo[0]
        forma.left, forma.top, forma.width, forma.height = origem.left, origem.top, origem.width, origem.height


def letra_do_titulo(slide) -> int:
    """O tamanho da letra do título, em pontos, lido do layout e do slide mestre."""
    from pptx.enum.shapes import PP_PLACEHOLDER as PH

    layout = slide.slide_layout
    mestre = layout.slide_master
    achados: list = []
    for dono in (layout, mestre):
        for campo in dono.placeholders:
            if campo.placeholder_format.type in (PH.TITLE, PH.CENTER_TITLE):
                achados += campo._element.xpath(".//a:lstStyle/a:lvl1pPr/a:defRPr/@sz")
                break
    achados += mestre._element.xpath("./p:txStyles/p:titleStyle/a:lvl1pPr/a:defRPr/@sz")
    return int(achados[0]) // 100 if achados else 44


def ajustar_titulo(slide, numero: int) -> None:
    """Título de ação costuma ter duas linhas. Quando ele não cabe no campo do layout, a letra diminui
    até 60% do tamanho do modelo. Se ainda assim não couber, fica o aviso para encurtar o título."""
    from pptx.util import Pt

    titulo = slide.shapes.title
    if titulo is None or not titulo.width or not titulo.height:
        return
    texto = titulo.text_frame.text
    do_modelo = letra_do_titulo(slide)

    def cabe(corpo: int) -> bool:
        por_linha = max(8, int(titulo.width / EMU_POR_PONTO / (corpo * 0.52)))
        linhas = -(-len(texto) // por_linha)
        return linhas * corpo * 1.2 * EMU_POR_PONTO <= titulo.height

    if cabe(do_modelo):
        return
    minimo = max(18, int(do_modelo * 0.6))
    corpo = next((c for c in range(do_modelo - 2, minimo - 1, -2) if cabe(c)), None)
    if corpo is None:
        corpo = minimo
        avisos.append(f"Página {numero}: o título não cabe no campo do layout '{slide.slide_layout.name}' nem com a letra reduzida. Encurte o título ou use um layout com mais espaço.")
    for paragrafo in titulo.text_frame.paragraphs:
        for corrida in paragrafo.runs:
            corrida.font.size = Pt(corpo)


def por_tabela(slide, linhas: list[list[str]], area, cores: dict, fundo: str | None = None, texto: str | None = None, pagina: int = 0) -> None:
    """Põe a tabela no slide. Em fundo escuro, as células ganham cores próprias, porque o estilo padrão é claro."""
    from pptx.dml.color import RGBColor
    from pptx.util import Pt

    colunas = max(len(l) for l in linhas)
    esquerda, topo, largura, altura = area
    forma = slide.shapes.add_table(len(linhas), colunas, esquerda, topo, largura, min(altura, int(altura * min(1.0, 0.12 * len(linhas) + 0.1))))
    corpo = 11 if len(linhas) > 7 or colunas > 5 else 13
    em_fundo_escuro = bool(fundo) and escuro(fundo)
    por_linha = max(4, int(largura / colunas / EMU_POR_PONTO / (corpo * 0.5)))
    necessaria = 0.0
    for r, linha in enumerate(linhas):
        celulas = [plano(linha[c]) if c < len(linha) else "" for c in range(colunas)]
        necessaria += max(1 + len(c) // por_linha for c in celulas) * corpo * 1.2 + 7.2  # 7,2 pt são as margens da célula
        if em_fundo_escuro:
            do_fundo = cores["destaque"] if r == 0 else misturar(fundo, "FFFFFF", 0.16 if r % 2 else 0.08)
            da_letra = texto_sobre(do_fundo) if r == 0 else (texto or TEXTO_CLARO)
        for c in range(colunas):
            celula = forma.table.cell(r, c)
            celula.text = celulas[c]
            if em_fundo_escuro:
                celula.fill.solid()
                celula.fill.fore_color.rgb = RGBColor.from_string(do_fundo)
            for paragrafo in celula.text_frame.paragraphs:
                for corrida in paragrafo.runs:
                    corrida.font.size = Pt(corpo)
                    if em_fundo_escuro:
                        corrida.font.color.rgb = RGBColor.from_string(da_letra)
    if necessaria * EMU_POR_PONTO > altura:
        avisos.append(
            f"Página {pagina}: a tabela de {len(linhas)} linhas não cabe na área do slide e passa da borda. "
            "Divida a tabela em duas páginas, corte linhas ou leve a base para uma planilha."
        )


def series_do_grafico(spec: dict, idioma: str) -> list[tuple[str, list, str]]:
    """(nome, valores, formato) de cada série de um bloco 'grafico'.

    Uma célula vazia é um ponto sem valor. Qualquer outra coisa que não
    seja número para a geração: um valor que some do gráfico sem aviso
    muda o que a página diz.
    """
    linhas = spec.get("linhas") or []
    onde = f" '{spec['titulo']}'" if spec.get("titulo") else ""
    resultado = []
    for n, nome in enumerate(linhas[0][1:], start=1):
        brutos = [l[n].strip() if n < len(l) else "" for l in linhas[1:]]
        decimal = decimal_da_coluna(brutos, idioma)
        valores, formatos = [], []
        for linha, bruto in zip(linhas[1:], brutos):
            if not bruto:
                valores.append(None)
                continue
            lido = ler_numero(bruto, decimal)
            if lido is None:
                raise SystemExit(
                    f"Gráfico{onde}: o valor '{bruto}' da linha '{linha[0]}', coluna '{nome}', não é um número. "
                    "Escreva só o número, com % ou com a moeda quando for o caso, ou deixe a célula vazia."
                )
            valores.append(lido[0])
            formatos.append(lido[1])
        if len({f.endswith("%") for f in formatos}) > 1:
            raise SystemExit(f"Gráfico{onde}: a coluna '{nome}' mistura percentual com número sem percentual. Escreva a coluna inteira de um jeito só.")
        resultado.append((nome, valores, max(formatos, key=len, default="")))
    return resultado


def cores_das_fatias(quantas: int, cores: dict) -> list[str]:
    """Uma cor por fatia: as cores registradas na marca quando bastam, ou tons da cor de destaque, do mais forte ao mais claro."""
    paleta = cores.get("paleta") or [cores["destaque"], cores["neutra"]]
    if len(paleta) >= quantas:
        return paleta[:quantas]
    return [misturar(cores["destaque"], "FFFFFF", 0.75 * n / max(1, quantas - 1)) for n in range(quantas)]


def por_grafico(slide, spec: dict, area, cores: dict, idioma: str = "pt", fundo: str | None = None, texto: str | None = None) -> None:
    """Põe o gráfico no slide. 'texto' é a cor dos rótulos, do eixo e da legenda quando o fundo pede uma cor própria."""
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
    from pptx.util import Pt

    linhas = spec.get("linhas") or []
    if len(linhas) < 2 or len(linhas[0]) < 2:
        raise SystemExit("Um bloco 'grafico' precisa de 'dados:' com uma linha de cabeçalho e ao menos uma de valores, separadas por '|'.")
    dados = CategoryChartData()
    dados.categories = [l[0] for l in linhas[1:]]
    series = linhas[0][1:]
    for nome, valores, formato in series_do_grafico(spec, idioma):
        dados.add_series(nome, valores, number_format=formato or "General")
    tipo = comum.normalizar(spec.get("tipo", "barras"))
    formas = {"barras": XL_CHART_TYPE.BAR_CLUSTERED, "colunas": XL_CHART_TYPE.COLUMN_CLUSTERED, "linhas": XL_CHART_TYPE.LINE_MARKERS, "pizza": XL_CHART_TYPE.PIE}
    if tipo not in formas:
        raise SystemExit(f"Tipo de gráfico '{spec.get('tipo')}' não existe. Use barras, colunas, linhas ou pizza.")
    esquerda, topo, largura, altura = area
    grafico = slide.shapes.add_chart(formas[tipo], esquerda, topo, largura, altura, dados).chart
    da_letra = RGBColor.from_string(texto) if texto else None
    grafico.font.size = Pt(12)
    if da_letra:
        grafico.font.color.rgb = da_letra
    grafico.has_title = bool(spec.get("titulo"))
    if grafico.has_title:
        grafico.chart_title.text_frame.text = spec["titulo"]
        pintar(grafico.chart_title.text_frame, texto)
    grafico.has_legend = len(series) > 1 or tipo == "pizza"
    if grafico.has_legend:
        grafico.legend.position = XL_LEGEND_POSITION.BOTTOM
        grafico.legend.include_in_layout = False
        if da_letra:
            grafico.legend.font.color.rgb = da_letra
    destaque, neutra = RGBColor.from_string(cores["destaque"]), RGBColor.from_string(cores["neutra"])
    alvo = comum.normalizar(spec.get("destaque", ""))
    area_do_grafico = grafico.plots[0]
    if tipo != "linhas":
        area_do_grafico.has_data_labels = True
        area_do_grafico.data_labels.font.size = Pt(11)
        if da_letra:
            area_do_grafico.data_labels.font.color.rgb = da_letra
        if tipo == "pizza":
            # O rótulo fica fora da fatia, sobre o fundo do slide, onde a cor do texto é conhecida.
            area_do_grafico.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    if tipo in ("barras", "colunas"):
        area_do_grafico.gap_width = 60
        grafico.value_axis.has_major_gridlines = False
        grafico.value_axis.visible = False
        if tipo == "barras":
            grafico.category_axis.reverse_order = True  # a primeira linha dos dados fica em cima
    if tipo != "pizza" and da_letra:
        for eixo in (grafico.category_axis, grafico.value_axis):
            eixo.tick_labels.font.color.rgb = da_letra
            eixo.format.line.color.rgb = da_letra
        if grafico.value_axis.has_major_gridlines:
            grafico.value_axis.major_gridlines.format.line.color.rgb = RGBColor.from_string(misturar(fundo or "000000", texto, 0.3))
    categorias = [comum.normalizar(l[0]) for l in linhas[1:]]
    for n, serie in enumerate(area_do_grafico.series):
        da_serie = alvo and comum.normalizar(series[n]) == alvo
        if tipo == "linhas":
            serie.format.line.color.rgb = destaque if (da_serie or (not alvo and n == 0) or len(series) == 1) else neutra
            serie.smooth = False
            continue
        if tipo == "pizza":
            # Com destaque, a fatia citada leva a cor e o resto fica em cinza. Sem destaque, cada fatia tem a sua cor.
            fatias = cores_das_fatias(len(categorias), cores)
            borda = RGBColor.from_string(fundo or "FFFFFF")
            for i, categoria in enumerate(categorias):
                ponto = serie.points[i]
                ponto.format.fill.solid()
                ponto.format.fill.fore_color.rgb = (destaque if categoria == alvo else neutra) if alvo else RGBColor.from_string(fatias[i])
                ponto.format.line.color.rgb = borda  # separa as fatias vizinhas
                ponto.format.line.width = Pt(1.5)
        elif len(series) == 1:
            # O destaque fica na categoria que o título cita. O resto fica em cinza.
            for i, categoria in enumerate(categorias):
                ponto = serie.points[i]
                ponto.format.fill.solid()
                ponto.format.fill.fore_color.rgb = destaque if (categoria == alvo or not alvo) else neutra
        else:
            serie.format.fill.solid()
            serie.format.fill.fore_color.rgb = destaque if (da_serie or (not alvo and n == 0)) else neutra


def por_imagem(slide, caminho: Path, area) -> None:
    esquerda, topo, largura, altura = area
    figura = slide.shapes.add_picture(str(caminho), esquerda, topo)
    escala = min(largura / figura.width, altura / figura.height)
    figura.width, figura.height = int(figura.width * escala), int(figura.height * escala)
    figura.left, figura.top = esquerda + (largura - figura.width) // 2, topo + (altura - figura.height) // 2


def caminho_de_imagem(pasta: Path, relativo: str) -> Path:
    for base in (pasta, comum.RAIZ):
        candidato = (base / relativo).resolve()
        if candidato.is_file():
            if not dentro_do_projeto(candidato):
                raise SystemExit(f"A imagem {relativo} fica fora da pasta do projeto. Copie a imagem para a pasta do entregável e cite a cópia.")
            return candidato
    raise SystemExit(f"Imagem não encontrada: {relativo} (procurada a partir de {comum.relativo(pasta)}).")


def gerar_pptx(pasta: Path, fonte: Path, modelo: Path | None, destino: Path, idioma: str, registro: dict, rascunho: bool) -> int:
    exigir("pptx")
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import PP_PLACEHOLDER as PH
    from pptx.enum.text import MSO_AUTO_SIZE
    from pptx.util import Pt

    prs = Presentation(str(modelo)) if modelo else Presentation()
    # As páginas de exemplo do modelo saem. Ficam os layouts.
    lista = prs.slides._sldIdLst
    for item in list(lista):
        prs.part.drop_rel(item.rId)
        lista.remove(item)
    # As seções do modelo citam as páginas que saíram. Ficando no arquivo, apontariam para slides que não existem.
    for extensao in prs.part._element.xpath("./p:extLst/p:ext"):
        if any(_nome(filho) == "sectionLst" for filho in extensao):
            pai = extensao.getparent()
            pai.remove(extensao)
            if not len(pai):
                pai.getparent().remove(pai)
    paginas = [p for p in comum.paginas(comum.ler(fonte)) if comum.MARCA not in p.titulo]
    if not paginas:
        raise SystemExit(f"{comum.relativo(fonte)} não tem páginas escritas.")
    largura, altura = prs.slide_width, prs.slide_height
    provas = evidencias()
    for pagina in paginas:
        tipo = comum.normalizar(pagina.meta.get("tipo", "texto"))
        conteudo = blocos(pagina.corpo, pasta)
        textos = [b for b in conteudo if b["tipo"] in ("paragrafo", "lista", "citacao", "titulo")]
        for b in textos:
            if b["tipo"] == "titulo":
                b.update(tipo="paragrafo", texto=f"**{plano(b['texto'])}**")
        visuais = [b for b in conteudo if b["tipo"] in ("tabela", "grafico", "imagem")]
        pedido = pagina.meta.get("layout", "") or registro["layouts"].get(tipo, "")
        slide = prs.slides.add_slide(escolher_layout(prs, tipo, pedido, bool(textos), bool(visuais)))
        # O texto que o gerador cria fora dos campos do modelo não herda a cor do modelo. Em fundo escuro ele
        # sairia preto, e por isso ganha uma cor que contrasta. A cor registrada na marca vence a escolha.
        fundo = cor_do_fundo(slide, largura, altura)
        da_letra = registro.get("texto") or (TEXTO_CLARO if fundo and escuro(fundo) else None)
        if slide.shapes.title is not None:
            acertar_posicao(slide, slide.shapes.title)
            slide.shapes.title.text_frame.text = plano(pagina.titulo)
            ajustar_titulo(slide, pagina.numero)
        else:
            avisos.append(f"Página {pagina.numero}: o layout '{slide.slide_layout.name}' não tem título. O título foi para uma caixa de texto.")
            caixa = slide.shapes.add_textbox(int(largura * 0.06), int(altura * 0.06), int(largura * 0.88), int(altura * 0.14))
            caixa.text_frame.word_wrap = True
            caixa.text_frame.text = plano(pagina.titulo)
            caixa.text_frame.paragraphs[0].runs[0].font.size = Pt(28)
            caixa.text_frame.paragraphs[0].runs[0].font.bold = True
            pintar(caixa.text_frame, da_letra)
        titulo = slide.shapes.title
        corpos = sorted(
            (p for p in slide.placeholders if p.placeholder_format.type in (PH.BODY, PH.OBJECT, PH.SUBTITLE) and p != titulo),
            key=lambda p: p.placeholder_format.idx,
        )
        corpo = corpos[0] if corpos else None
        acertar_posicao(slide, corpo)
        for sobra in corpos[1:]:
            sobra._element.getparent().remove(sobra._element)
        if corpo is not None and corpo.width and corpo.height:
            area = [corpo.left, corpo.top, corpo.width, corpo.height]
        else:
            topo = (titulo.top + titulo.height) if (titulo is not None and titulo.height and tipo != "capa") else int(altura * 0.24)
            topo = min(max(topo, int(altura * 0.2)), int(altura * 0.5))
            area = [int(largura * 0.06), topo + int(altura * 0.02), int(largura * 0.88), int(altura * 0.9) - topo]
        area_visual = list(area)
        tamanho = None
        if textos and visuais:
            # O texto fica em cima, no tamanho em que cabe em até 45% da área, e o visual ocupa o resto.
            tamanho = next((c for c in (20, 18, 16, 14) if altura_do_texto(textos, area[2], c) <= area[3] * 0.45), 12)
            fatia = min(int(area[3] * 0.5), max(int(area[3] * 0.12), altura_do_texto(textos, area[2], tamanho)))
            area_visual = [area[0], area[1] + fatia, area[2], area[3] - fatia]
            area = [area[0], area[1], area[2], fatia]
            if corpo is not None:
                corpo.left, corpo.top, corpo.width, corpo.height = area
        elif textos and tipo not in ("capa", "secao", "frase", "citacao", "encerramento") and altura_do_texto(textos, area[2], 16) > area[3]:
            avisos.append(f"Página {pagina.numero}: o texto não cabe na área do layout nem com letra pequena. Corte o texto ou leve parte para as notas.")
        if textos:
            if corpo is not None:
                quadro = corpo.text_frame
                escrever_texto(quadro, textos, com_marcador=False)
            else:
                caixa = slide.shapes.add_textbox(*area)
                quadro = caixa.text_frame
                quadro.word_wrap = True
                escrever_texto(quadro, textos, com_marcador=True)
                pintar(quadro, da_letra)
            if tamanho:
                fixar_tamanho(quadro, tamanho)
            elif corpo is not None and tipo not in ("capa", "secao", "frase", "citacao", "encerramento"):
                quadro.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        elif corpo is not None:
            corpo._element.getparent().remove(corpo._element)
        if visuais:
            vao = int(largura * 0.02)
            fatia = (area_visual[2] - vao * (len(visuais) - 1)) // len(visuais)
            for n, bloco in enumerate(visuais):
                parte = [area_visual[0] + n * (fatia + vao), area_visual[1], fatia, area_visual[3]]
                if bloco["tipo"] == "tabela":
                    por_tabela(slide, bloco["linhas"], parte, registro, fundo, da_letra, pagina.numero)
                elif bloco["tipo"] == "grafico":
                    por_grafico(slide, bloco["spec"], parte, registro, idioma, fundo, da_letra)
                else:
                    por_imagem(slide, caminho_de_imagem(pasta, bloco["caminho"]), parte)
        fonte_da_pagina = linha_de_fonte(pagina.meta.get("fonte", "") + " " + pagina.corpo, idioma, provas)
        if fonte_da_pagina:
            caixa = slide.shapes.add_textbox(int(largura * 0.06), int(altura * 0.925), int(largura * 0.7), int(altura * 0.05))
            caixa.text_frame.word_wrap = True
            caixa.text_frame.text = fonte_da_pagina
            caixa.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
            pintar(caixa.text_frame, da_letra)
        if rascunho:
            caixa = slide.shapes.add_textbox(int(largura * 0.8), int(altura * 0.01), int(largura * 0.19), int(altura * 0.05))
            caixa.text_frame.text = ROTULO_DE_RASCUNHO.get(idioma, "RASCUNHO")
            corrida = caixa.text_frame.paragraphs[0].runs[0]
            corrida.font.size, corrida.font.bold = Pt(11), True
            corrida.font.color.rgb = RGBColor.from_string(RASCUNHO_NO_ESCURO if fundo and escuro(fundo) else RASCUNHO_NO_CLARO)
        if pagina.notas.strip():
            quadro_de_notas = slide.notes_slide.notes_text_frame
            if quadro_de_notas is None:
                avisos.append(f"Página {pagina.numero}: o modelo não tem campo de notas, e as notas de quem apresenta ficaram fora do arquivo.")
            else:
                quadro_de_notas.text = plano(pagina.notas.strip())
    por_titulo_no_arquivo(prs, plano(paginas[0].titulo), neutro=not modelo)
    prs.save(str(destino))
    return len(paginas)


# --- Word -----------------------------------------------------------------


def gerar_docx(pasta: Path, fonte: Path, modelo: Path | None, destino: Path, idioma: str, registro: dict, rascunho: bool) -> int:
    exigir("docx")
    from docx import Document
    from docx.shared import Cm

    doc = Document(str(modelo)) if modelo else Document()
    corpo = doc.element.body
    for elemento in list(corpo):
        if not elemento.tag.endswith("}sectPr"):
            corpo.remove(elemento)  # o texto de exemplo do modelo sai; ficam os estilos, o cabeçalho e o rodapé
    _, texto = comum.cabecalho(comum.ler(fonte))

    from docx.enum.style import WD_STYLE_TYPE

    def estilo_de_paragrafo(nome: str) -> bool:
        try:
            return doc.styles[nome].type == WD_STYLE_TYPE.PARAGRAPH
        except KeyError:
            return False

    def com_estilo(funcao, estilos: list[str]):
        # O estilo é conferido antes: a biblioteca acrescenta o parágrafo e só depois procura o estilo,
        # e uma tentativa que falha deixaria um parágrafo a mais no documento.
        existe = next((e for e in estilos if estilo_de_paragrafo(e)), None)
        if estilos and existe is None:
            avisos.append(f"O modelo de Word não tem o estilo '{estilos[0]}'. O trecho saiu com o estilo padrão: confira o título, as listas e as citações.")
        return funcao(existe)

    def paragrafo(conteudo: str, estilos: list[str] | None = None, prefixo: str = ""):
        p = com_estilo(lambda e: doc.add_paragraph(style=e), estilos or [])
        if prefixo and p.style.name in ("Normal", "Body Text"):
            p.add_run(prefixo)
        for parte, negrito, italico in trechos(conteudo):
            corrida = p.add_run(parte)
            corrida.bold, corrida.italic = negrito or None, italico or None
        return p

    if rascunho:
        paragrafo(f"**{ROTULO_DE_RASCUNHO.get(idioma, 'RASCUNHO')}**")
    titulo_do_documento, quantos = "", 0
    for bloco in blocos(texto, pasta):
        quantos += 1
        tipo = bloco["tipo"]
        if tipo == "titulo":
            limpo = plano(bloco["texto"])
            if bloco["nivel"] == 1 and not titulo_do_documento:
                titulo_do_documento = limpo
                com_estilo(lambda e: doc.add_paragraph(limpo, style=e), ["Title", "Heading 1"])
            else:
                nivel = max(1, bloco["nivel"] - 1)
                com_estilo(lambda e: doc.add_paragraph(limpo, style=e), [f"Heading {nivel}"])
        elif tipo == "paragrafo":
            paragrafo(bloco["texto"])
        elif tipo == "citacao":
            paragrafo(f"*{plano(bloco['texto'])}*", ["Quote", "Intense Quote"])
        elif tipo == "lista":
            contagem: dict[int, int] = {}
            for nivel, ordenada, item in bloco["itens"]:
                base = "List Number" if ordenada else "List Bullet"
                contagem = {n: c for n, c in contagem.items() if n <= nivel}
                contagem[nivel] = contagem.get(nivel, 0) + 1
                # Sem o estilo de lista no modelo, o marcador ou o número vai escrito no texto.
                paragrafo(item, [base if nivel == 0 else f"{base} {nivel + 1}", base], prefixo=f"{contagem[nivel]}. " if ordenada else "• ")
        elif tipo in ("tabela", "grafico"):
            linhas = bloco["linhas"] if tipo == "tabela" else bloco["spec"].get("linhas", [])
            if tipo == "grafico":
                avisos.append("Um bloco 'grafico' entrou no Word como tabela. Para uma figura, gere a imagem do gráfico e cite com ![descrição](arquivo).")
                if bloco["spec"].get("titulo"):
                    paragrafo(f"**{bloco['spec']['titulo']}**")
            if not linhas:
                continue
            colunas = max(len(l) for l in linhas)
            tabela = doc.add_table(rows=len(linhas), cols=colunas)
            try:
                tabela.style = "Table Grid"
            except (KeyError, ValueError):
                pass
            # tabela.cell(r, c) refaz a grade a cada chamada. Em tabela grande, percorrer as linhas uma vez é muito mais rápido.
            for r, (linha, da_tabela) in enumerate(zip(linhas, tabela.rows)):
                for c, celula in enumerate(da_tabela.cells):
                    corrida = celula.paragraphs[0].add_run(plano(linha[c]) if c < len(linha) else "")
                    corrida.bold = True if r == 0 else None
            doc.add_paragraph()
        elif tipo == "imagem":
            secao = doc.sections[-1]
            util = secao.page_width - secao.left_margin - secao.right_margin
            doc.add_picture(str(caminho_de_imagem(pasta, bloco["caminho"])), width=min(util, Cm(16)))
            if bloco["alt"]:
                paragrafo(f"*{bloco['alt']}*", ["Caption"])
    citadas = []
    for ident in re.findall(r"\bE-\d+\b", texto):
        if ident not in citadas:
            citadas.append(ident)
    provas = evidencias()
    if citadas:
        com_estilo(lambda e: doc.add_paragraph(ROTULO_DE_FONTES.get(idioma, "Fontes"), style=e), ["Heading 1"])
        for ident in citadas:
            linha = provas.get(ident, {})
            detalhe = ", ".join(v for v in (linha.get("fonte", ""), linha.get("data", "")) if v)
            paragrafo(f"**{ident}**: {detalhe or '?'}")
    if titulo_do_documento:
        por_titulo_no_arquivo(doc, titulo_do_documento, neutro=not modelo)
    doc.save(str(destino))
    return quantos


# --- Excel ----------------------------------------------------------------


def nome_de_aba(nome: str, usados: set[str]) -> str:
    limpo = re.sub(r"[\[\]:*?/\\]", " ", plano(nome)).strip()[:31] or "Dados"
    base, n = limpo, 2
    while limpo.lower() in usados:
        limpo = f"{base[:28]} {n}"
        n += 1
    usados.add(limpo.lower())
    return limpo


def gerar_xlsx(pasta: Path, fonte: Path, modelo: Path | None, destino: Path, idioma: str, registro: dict, rascunho: bool) -> int:
    exigir("xlsx")
    from openpyxl import Workbook, load_workbook
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    from openpyxl.chart.series import DataPoint
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    if modelo:
        livro = load_workbook(str(modelo))
    else:
        livro = Workbook()
        livro.remove(livro.active)
    usados = {a.lower() for a in livro.sheetnames}
    _, texto = comum.cabecalho(comum.ler(fonte))
    mapa = comum.secoes(texto)
    negrito, cabecalho_cinza = Font(bold=True), PatternFill("solid", start_color="E3E7EB")

    def por_texto(celula, valor: str):
        """Grava o texto como texto. Um texto que começa por '=' não vira fórmula."""
        valor = str(valor or "").strip()
        celula.value = valor or None
        if valor:
            celula.data_type = "s"
        return celula

    def por_valor(celula, valor: str, decimal: str) -> None:
        """Número entra como número, no formato em que foi escrito. O resto entra como texto."""
        lido = ler_numero(valor, decimal)
        if lido is None:
            por_texto(celula, valor)
            return
        celula.value = lido[0]
        if lido[1]:
            celula.number_format = lido[1]

    def por_cabecalho(aba, linha: int, colunas: int) -> None:
        for c in range(1, colunas + 1):
            celula = aba.cell(row=linha, column=c)
            celula.font, celula.fill = negrito, cabecalho_cinza
            celula.alignment = Alignment(vertical="top", wrap_text=True)

    def ajustar_larguras(aba) -> None:
        for coluna in aba.columns:
            maior = max((len(str(c.value)) for c in coluna if c.value is not None), default=8)
            aba.column_dimensions[get_column_letter(coluna[0].column)].width = min(60, max(10, maior + 2))

    def por_tabela_md(aba, linhas: list[dict], colunas: list[str], inicio: int) -> int:
        for c, nome in enumerate(colunas, start=1):
            por_texto(aba.cell(row=inicio, column=c), nome)
        por_cabecalho(aba, inicio, len(colunas))
        for r, linha in enumerate(linhas, start=inicio + 1):
            for c, nome in enumerate(colunas, start=1):
                por_texto(aba.cell(row=r, column=c), plano(linha.get(comum.normalizar(nome), "")))
        return inicio + len(linhas) + 1

    # Aba de leitura: o que a planilha responde, e de onde vêm os dados.
    leitura = livro.create_sheet(nome_de_aba({"pt": "Leitura", "es": "Lectura", "en": "Read me"}.get(idioma, "Leitura"), usados), 0)
    meta, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
    por_texto(leitura["A1"], meta.get("titulo") or pasta.name)
    leitura["A1"].font = Font(bold=True, size=14)
    linha = 2
    if rascunho:
        leitura.cell(row=linha, column=1, value=ROTULO_DE_RASCUNHO.get(idioma, "RASCUNHO")).font = Font(bold=True, color="A3382C")
        linha += 1
    linha += 1
    perguntas = comum.achar_secao(mapa, "perguntas que a planilha responde") or ""
    for bloco in blocos(perguntas, pasta):
        for item in ([i[2] for i in bloco["itens"]] if bloco["tipo"] == "lista" else [bloco.get("texto", "")]):
            por_texto(leitura.cell(row=linha, column=1), plano(item)).alignment = Alignment(wrap_text=True, vertical="top")
            linha += 1
    abas_previstas = [l for l in comum.tabela(comum.achar_secao(mapa, "abas") or "") if l.get("aba") and comum.MARCA not in l.get("aba", "")]
    provas = evidencias()
    for prevista in abas_previstas:
        chave = next((k for k in prevista if k.startswith("origem")), None)
        if chave and prevista.get(chave):
            detalhe = linha_de_fonte(prevista[chave], idioma, provas)
            if detalhe:
                prevista[chave] = f"{prevista[chave]} ({detalhe.split(': ', 1)[1].rstrip('.')})"
    if abas_previstas:
        colunas = ["Aba", "O que contém"] + [c for c in ("Origem dos dados (E-nnn)", "Data dos dados") if comum.normalizar(c) in abas_previstas[0]]
        por_tabela_md(leitura, abas_previstas, colunas, linha + 1)
    leitura.column_dimensions["A"].width = 34
    for letra in "BCD":
        leitura.column_dimensions[letra].width = 44

    # Uma aba por arquivo de dados.
    pasta_de_dados = pasta / "dados"
    arquivos = {comum.normalizar(a.stem): a for a in sorted(pasta_de_dados.glob("*")) if a.suffix in (".csv", ".tsv")}
    ordem = []
    for prevista in abas_previstas:
        chave = comum.normalizar(plano(prevista["aba"]))
        if chave in arquivos:
            ordem.append((plano(prevista["aba"]), arquivos.pop(chave)))
        else:
            avisos.append(f"A aba '{plano(prevista['aba'])}' está na especificação e não há dados/{chave.replace(' ', '-')}.csv com esse nome.")
    for chave, arquivo in arquivos.items():
        avisos.append(f"dados/{arquivo.name} virou uma aba e não está na tabela 'Abas' de planilha.md.")
        ordem.append((arquivo.stem, arquivo))
    abas_de_dados = {}
    for nome, arquivo in ordem:
        linhas = ler_dados(arquivo)
        aba = livro.create_sheet(nome_de_aba(nome, usados))
        largura_dos_dados = max((len(l) for l in linhas), default=0)
        colunas_dos_dados = [[l[c] for l in linhas[1:] if c < len(l)] for c in range(largura_dos_dados)]
        decimais = [decimal_da_coluna(valores, idioma) for valores in colunas_dos_dados]
        # Uma coluna com um código de zero à esquerda, como CEP ou centro de custo, é de códigos: fica toda como texto.
        de_codigos = [any(re.fullmatch(r"0\d+", v.strip()) for v in valores) for valores in colunas_dos_dados]
        for r, valores in enumerate(linhas, start=1):
            for c, valor in enumerate(valores, start=1):
                if r == 1 or de_codigos[c - 1]:
                    por_texto(aba.cell(row=r, column=c), valor)
                else:
                    por_valor(aba.cell(row=r, column=c), valor, decimais[c - 1])
        if linhas:
            por_cabecalho(aba, 1, len(linhas[0]))
            aba.freeze_panes = "A2"
            aba.auto_filter.ref = aba.dimensions
        ajustar_larguras(aba)
        abas_de_dados[comum.normalizar(nome)] = (aba, linhas)

    # Dicionário de dados.
    dicionario = [l for l in comum.tabela(comum.achar_secao(mapa, "dicionario de dados") or "") if l.get("aba") and comum.MARCA not in l.get("aba", "")]
    if dicionario:
        aba = livro.create_sheet(nome_de_aba({"pt": "Dicionário", "es": "Diccionario", "en": "Dictionary"}.get(idioma, "Dicionário"), usados))
        por_tabela_md(aba, dicionario, ["Aba", "Coluna", "Definição", "Unidade", "Regra de cálculo"], 1)
        aba.freeze_panes = "A2"
        ajustar_larguras(aba)
    elif abas_de_dados:
        avisos.append("planilha.md não tem o dicionário de dados preenchido. Uma planilha de entrega diz o que é cada coluna.")

    # Gráficos nativos, a partir dos blocos 'grafico' da especificação.
    graficos = [b["spec"] for b in blocos(texto, pasta) if b["tipo"] == "grafico"]
    if graficos:
        painel = livro.create_sheet(nome_de_aba({"pt": "Gráficos", "es": "Gráficos", "en": "Charts"}.get(idioma, "Gráficos"), usados), 1)
        for n, spec in enumerate(graficos):
            alvo = abas_de_dados.get(comum.normalizar(spec.get("aba", "")))
            if alvo is None:
                raise SystemExit(f"O gráfico '{spec.get('titulo', n + 1)}' cita a aba '{spec.get('aba', '')}', que não tem dados. Em planilha, o bloco 'grafico' usa os campos aba, categorias e valores.")
            aba, linhas = alvo
            nomes = [comum.normalizar(c) for c in linhas[0]]

            def coluna(nome: str) -> int:
                if comum.normalizar(nome) not in nomes:
                    raise SystemExit(f"O gráfico '{spec.get('titulo', '')}' cita a coluna '{nome}', que não existe na aba '{spec.get('aba')}'.")
                return nomes.index(comum.normalizar(nome)) + 1

            tipo = comum.normalizar(spec.get("tipo", "colunas"))
            grafico = {"linhas": LineChart, "pizza": PieChart}.get(tipo, BarChart)()
            if tipo == "barras":
                grafico.type = "bar"
            grafico.title = spec.get("titulo") or None
            ultima = len(linhas)
            nomes_das_series = [v.strip() for v in spec.get("valores", "").split(",") if v.strip()]
            for nome in nomes_das_series:
                c = coluna(nome)
                grafico.add_data(Reference(aba, min_col=c, min_row=1, max_row=ultima), titles_from_data=True)
            coluna_das_categorias = coluna(spec.get("categorias", linhas[0][0]))
            grafico.set_categories(Reference(aba, min_col=coluna_das_categorias, min_row=2, max_row=ultima))
            # As cores seguem a marca, como no PowerPoint: o destaque na série ou na categoria citada, o resto em cinza.
            alvo_do_destaque = comum.normalizar(spec.get("destaque", ""))
            categorias = [comum.normalizar(l[coluna_das_categorias - 1]) if coluna_das_categorias - 1 < len(l) else "" for l in linhas[1:]]
            for s, serie in enumerate(grafico.series):
                da_serie = alvo_do_destaque and comum.normalizar(nomes_das_series[s]) == alvo_do_destaque
                cor = registro["destaque"] if (da_serie or (not alvo_do_destaque and s == 0) or len(nomes_das_series) == 1) else registro["neutra"]
                if tipo == "linhas":
                    serie.graphicalProperties.line.solidFill = cor
                    serie.smooth = False
                    continue
                serie.graphicalProperties.solidFill = cor
                if tipo == "pizza" or (len(nomes_das_series) == 1 and alvo_do_destaque in categorias):
                    fatias = cores_das_fatias(len(categorias), registro)
                    for i, categoria in enumerate(categorias):
                        ponto = DataPoint(idx=i)
                        if alvo_do_destaque:
                            ponto.graphicalProperties.solidFill = registro["destaque"] if categoria == alvo_do_destaque else registro["neutra"]
                        else:
                            ponto.graphicalProperties.solidFill = fatias[i]
                        if tipo == "pizza":
                            ponto.graphicalProperties.line.solidFill = "FFFFFF"
                        serie.dPt.append(ponto)
            grafico.width, grafico.height = 22, 11
            painel.add_chart(grafico, f"A{1 + n * 24}")
    if not livro.sheetnames:
        raise SystemExit("Nada a gerar: planilha.md não tem abas e a pasta dados/ está vazia.")
    livro.save(str(destino))
    return len(livro.sheetnames)


# --- PDF, imagens e comando -----------------------------------------------


def converter_para_pdf(arquivo: Path) -> Path | None:
    programa = shutil.which("soffice") or shutil.which("libreoffice")
    if not programa:
        avisos.append("O PDF não foi gerado: o LibreOffice (soffice) não está instalado. Exporte o PDF pelo aplicativo.")
        return None
    with tempfile.TemporaryDirectory() as perfil:
        comando = [programa, f"-env:UserInstallation={Path(perfil).resolve().as_uri()}", "--headless", "--convert-to", "pdf", "--outdir", str(arquivo.parent), str(arquivo)]
        try:
            saida = subprocess.run(comando, capture_output=True, text=True, timeout=240)
        except (OSError, subprocess.SubprocessError) as erro:
            avisos.append(f"O PDF não foi gerado: {erro}.")
            return None
    pdf = arquivo.with_suffix(".pdf")
    if not pdf.is_file():
        avisos.append("O PDF não foi gerado: " + (saida.stderr.strip().splitlines() or ["o LibreOffice não devolveu o arquivo"])[-1])
        return None
    return pdf


def gerar_imagens(pdf: Path) -> Path | None:
    programa = shutil.which("pdftoppm")
    if not programa:
        avisos.append("As imagens de conferência não foram geradas: o pdftoppm não está instalado. Abra o PDF e olhe página por página.")
        return None
    pasta = pdf.parent / "conferencia"
    pasta.mkdir(exist_ok=True)
    for antiga in pasta.glob(f"{pdf.stem}-*.png"):
        antiga.unlink()
    try:
        subprocess.run([programa, "-png", "-r", "60", str(pdf), str(pasta / pdf.stem)], capture_output=True, timeout=240)
    except (OSError, subprocess.SubprocessError) as erro:
        avisos.append(f"As imagens de conferência não foram geradas: {erro}. Abra o PDF e olhe página por página.")
        return None
    if not any(pasta.glob(f"{pdf.stem}-*.png")):
        avisos.append("As imagens de conferência não foram geradas: o pdftoppm não devolveu nenhuma página. Abra o PDF e olhe página por página.")
        return None
    return pasta


def listar_layouts(arquivo: str | None) -> int:
    exigir("pptx")
    from pptx import Presentation

    modelo = achar_modelo("pptx", arquivo, marca())
    prs = Presentation(str(modelo)) if modelo else Presentation()
    print(f"Layouts de {comum.relativo(modelo) if modelo else 'desenho neutro, sem modelo'}:")
    layouts = todos_os_layouts(prs)
    nomes = [layout.name for layout in layouts]
    for numero, layout in enumerate(layouts, 1):
        campos = ", ".join(f"{p.placeholder_format.type.name.lower()} ({p.name})" for p in layout.placeholders)
        print(f"  {numero}. {layout.name}: {campos or 'sem campos'}")
    if len(set(nomes)) < len(nomes):
        print("\nHá layouts com o mesmo nome. Para escolher um deles, use o número no lugar do nome.")
    print("\nPara fixar o layout de um tipo de página, ponha em _projeto/marca.md a seção 'Layouts do modelo', com a tabela 'Tipo de página | Layout'.")
    print("Para uma página só, use o campo 'layout' no comentário da página.")
    return 0


FONTES = {"pptx": "conteudo", "docx": "documento", "pdf": "documento", "xlsx": "planilha"}
GERADORES = {"pptx": gerar_pptx, "docx": gerar_docx, "xlsx": gerar_xlsx}


def main() -> int:
    analisador = argparse.ArgumentParser(description="Gera o arquivo final de um entregável.")
    analisador.add_argument("id", nargs="?", help="o entregável")
    analisador.add_argument("--formato", default="", help="pptx, docx, pdf ou xlsx (padrão: o do briefing)")
    analisador.add_argument("--idioma", default="", help="código do idioma da versão, como es ou en")
    analisador.add_argument("--modelo", default="", help="arquivo de modelo a usar")
    analisador.add_argument("--pdf", action="store_true", help="gera também o PDF")
    analisador.add_argument("--imagens", action="store_true", help="gera uma imagem por página, para conferir")
    analisador.add_argument("--rascunho", action="store_true", help="gera mesmo com erro nas checagens, com a marca de rascunho")
    analisador.add_argument("--layouts", nargs="?", const="", metavar="ARQUIVO", help="lista os layouts do modelo de apresentação")
    args = analisador.parse_args()

    if args.layouts is not None:
        return listar_layouts(args.layouts or args.modelo or None)
    if not args.id:
        analisador.error("diga o entregável: gerar.py ID")
    pasta = comum.BASE / args.id
    if pasta.parent != comum.BASE or args.id.startswith((".", "_")):
        raise SystemExit(f"'{args.id}' não é o nome de um entregável. Use o nome da pasta, sem barras.")
    if args.idioma and not re.fullmatch(r"[A-Za-z]{2}(?:-[A-Za-z]{2})?", args.idioma):
        raise SystemExit(f"'{args.idioma}' não é um código de idioma. Use es, en ou pt-BR.")
    if not (pasta / "briefing.md").is_file():
        raise SystemExit(f"Não existe o entregável '{args.id}'.")
    meta, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
    formato = comum.normalizar(args.formato or meta.get("formato", "")).split(" ")[0]
    if formato not in FONTES:
        raise SystemExit(f"Formato '{args.formato or meta.get('formato', '')}' não é gerado por este script. Use --formato pptx, docx, pdf ou xlsx. Peças em HTML ficam em interativos/ e já são o arquivo final.")
    faltas = comum.briefing_completo(pasta)
    if faltas:
        raise SystemExit("O gerador espera o briefing completo. Falta: " + ", ".join(faltas) + ".")
    if not comum.storyline_aprovada(pasta):
        raise SystemExit("O gerador espera a storyline aprovada pelo consultor (aprovada: sim em storyline.md).")
    principal = [i.strip() for i in meta.get("idiomas", "").split(",") if i.strip()][:1]
    idioma = (args.idioma or (principal[0] if principal else "pt"))[:2].lower()
    versao = bool(args.idioma) and not (principal and principal[0][:2].lower() == idioma)
    fonte = pasta / (f"{FONTES[formato]}.{args.idioma}.md" if versao else f"{FONTES[formato]}.md")
    if not fonte.is_file():
        raise SystemExit(f"A fonte {comum.relativo(fonte)} não existe. O formato {formato} é gerado a partir de {FONTES[formato]}.md.")
    erros = [a for a in validar.validar([pasta], gerais=False) if a.nivel == "erro"]
    if erros and not args.rascunho:
        for a in erros[:12]:
            print(a.formatar())
        raise SystemExit(f"\nArquivo não gerado: {len(erros)} erro(s) nas checagens. Corrija a fonte, ou use --rascunho para gerar com a marca de rascunho.")
    registro = marca()
    extensao = "docx" if formato == "pdf" else formato
    modelo = achar_modelo(extensao, args.modelo or None, registro)
    saida = pasta / "saida"
    saida.mkdir(exist_ok=True)
    nome = args.id + (f"-{args.idioma.lower()}" if versao else "") + ("-rascunho" if args.rascunho else "")
    destino = saida / f"{nome}.{extensao}"
    quantos = GERADORES[extensao](pasta, fonte, modelo, destino, idioma, registro, args.rascunho)
    unidade = {"pptx": "página(s)", "docx": "bloco(s)", "xlsx": "aba(s)"}[extensao]
    print(f"Gerado: {comum.relativo(destino)} ({quantos} {unidade}" + (f", sobre {modelo.name})" if modelo else ", desenho neutro)"))
    if formato == "pdf" or args.pdf or args.imagens:
        pdf = converter_para_pdf(destino)
        if pdf:
            print(f"Gerado: {comum.relativo(pdf)}")
            if args.imagens:
                imagens = gerar_imagens(pdf)
                if imagens:
                    print(f"Imagens para conferir: {comum.relativo(imagens)}/{pdf.stem}-N.png")
                if not (formato == "pdf" or args.pdf):
                    pdf.unlink()
    for aviso in dict.fromkeys(avisos):
        print(f"Aviso: {aviso}")
    print("Abra o arquivo e olhe página por página antes de entregar. Um problema visto no arquivo é corrigido na fonte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
