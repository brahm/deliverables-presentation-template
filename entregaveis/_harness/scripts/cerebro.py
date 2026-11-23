#!/usr/bin/env python3
"""O segundo cérebro do projeto: notas em Markdown, um índice e um registro de atualizações.

Uso:
    cerebro.py                                  quantas notas há e o que falta absorver
    cerebro.py --buscar TERMO [TERMO...]        as notas e as linhas dos registros que falam dos termos
    cerebro.py --id E-008                       as notas que citam o id e a linha do registro
    cerebro.py --pendentes                      o que mudou no projeto e ainda não entrou em nota
    cerebro.py --nova PASTA "Título"            cria uma nota a partir do modelo
    cerebro.py --absorver ITENS --nota CAMINHO  marca os itens como absorvidos pelas notas, que precisam citar cada um
    cerebro.py --absorver ITENS --nada MOTIVO   marca os itens que não trazem conhecimento novo
    cerebro.py --mover NOTA PASTA               muda a nota de pasta e conserta as ligações
    cerebro.py --indice                         refaz o índice
    cerebro.py --conferir                       ligação quebrada, id que não existe, nota órfã, nota sem fonte

As notas ficam em entregaveis/_cerebro/, em quatro pastas: 1-projetos,
2-areas, 3-recursos e 4-arquivo. Os registros do projeto continuam
sendo a fonte dos dados: a nota cita o id e diz o que o dado significa.
Decisões, mudanças de data, cobranças e avisos não são copiados.
ITENS é uma lista de ids separados por vírgula, ou a palavra pendentes.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402
from comum import Achado  # noqa: E402

PASTA = comum.BASE / "_cerebro"
INDICE = PASTA / "indice.md"
REGISTRO = PASTA / "registro.md"
ABSORVIDO = PASTA / "absorvido.tsv"
MODELO_DE_NOTA = comum.MODELOS / "cerebro-nota" / "nota.md"

PASTAS = ("1-projetos", "2-areas", "3-recursos", "4-arquivo")
NOMES = {"1-projetos": "Projetos", "2-areas": "Áreas", "3-recursos": "Recursos", "4-arquivo": "Arquivo"}
EXPLICA = {
    "1-projetos": "O que tem prazo e fim: cada entregável em andamento e cada frente de trabalho.",
    "2-areas": "O que é acompanhado enquanto o projeto existir: o cliente, as pessoas, as plataformas, os processos e o contrato.",
    "3-recursos": "O que serve de consulta: métodos, conceitos, referências e o resumo de cada material recebido.",
    "4-arquivo": "O que deixou de estar ativo: entregável entregue, frente encerrada e fase anterior.",
}
# Colunas que mudam sem mudar o que se sabe. Ficam fora da marca de cada linha.
VOLATEIS = {"revisado_em", "movida_em", "processada_em", "onde_usada", "versao", "observacao", "arquivo", "caminho"}
# Registros lidos linha por linha, com a coluna que resume a linha.
POR_LINHA = (("evidencias.tsv", "afirmacao"), ("reunioes.tsv", "reuniao"), ("riscos.tsv", "risco"), ("premissas.tsv", "premissa"), ("issues.tsv", "problema"))
TABELAS = (("decisoes.md", "decisao"), ("licoes.md", "o que deu errado"))
ID = re.compile(r"\b(?:RS|PR|IS|DP|MU|SM|E|D|L|B|R|A|T|M)-\d{2,}\b")
LIGACAO = re.compile(r"\]\(([^)\s#]+)(#[^)\s]*)?\)")
LIMITE_DO_RESUMO = 5
TAMANHO_DE_COPIA = 60


@dataclass
class Fonte:
    """Um item do projeto que pode trazer conhecimento: uma linha de registro ou um arquivo."""

    ident: str
    origem: str
    texto: str
    marca: str


@dataclass
class Nota:
    caminho: Path
    rel: str
    meta: dict
    corpo: str
    texto: str
    citados: set = field(default_factory=set)


def _marca(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


def fontes() -> dict[str, Fonte]:
    """O que o projeto registrou e pode virar conhecimento, com a marca do conteúdo de cada item."""
    itens: dict[str, Fonte] = {}

    def linha(ident: str, origem: str, valores: dict, texto: str) -> None:
        base = "\t".join(f"{k}={v}" for k, v in sorted(valores.items()) if k not in VOLATEIS)
        if not ident or comum.MARCA in base:
            return
        itens[ident] = Fonte(ident, origem, texto, _marca(base))

    for nome, campo in POR_LINHA:
        for l in comum.ler_tsv(comum.PROJETO / nome):
            linha(l.get("id", ""), nome, l, l.get(campo, ""))
    for l in comum.ler_tsv(comum.INTAKE / "registro.tsv"):
        if comum.normalizar(l.get("estado", "")) == "recebido":  # um pedido ainda não ensina nada
            linha(l.get("id", ""), "registro.tsv do intake", l, l.get("material", ""))
    for nome, campo in TABELAS:
        for l in comum.tabela(comum.ler(comum.PROJETO / nome)):
            linha(l.get("id", ""), nome, l, l.get(campo, ""))

    def arquivo(ident: str, caminho: Path, texto: str, modelo: Path | None = None, aceita_marca: bool = False) -> None:
        _, corpo = comum.cabecalho(comum.ler(caminho))
        if not corpo.strip() or (comum.MARCA in corpo and not aceita_marca):
            return
        if modelo is not None and corpo.strip() == comum.cabecalho(comum.ler(modelo))[1].strip():
            return
        itens[ident] = Fonte(ident, ident, texto, _marca(corpo))

    meta, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    if comum.normalizar(meta.get("iniciado", "nao")) == "sim":
        arquivo("brief.md", comum.PROJETO / "brief.md", "Brief do projeto", aceita_marca=True)
    arquivo("audiencia.md", comum.PROJETO / "audiencia.md", "Audiência do projeto", comum.MODELOS / "projeto" / "audiencia.md")
    arquivo("dominio.md", comum.BASE / "_dominio" / "dominio.md", "Método e contexto do domínio", comum.MODELOS / "dominio" / "dominio.md")
    for pasta in comum.entregaveis():
        if not comum.briefing_completo(pasta):
            arquivo(f"{pasta.name}/briefing.md", pasta / "briefing.md", f"Briefing de {pasta.name}")
        if comum.storyline_aprovada(pasta):
            arquivo(f"{pasta.name}/storyline.md", pasta / "storyline.md", f"Storyline aprovada de {pasta.name}")
        arquivo(f"{pasta.name}/fechamento.md", pasta / "fechamento.md", f"Fechamento de {pasta.name}")
    return itens


def ids_do_projeto() -> set[str]:
    """Todo id que existe em algum registro, para conferir o que as notas citam."""
    achados: set[str] = set()
    arquivos = list(comum.PROJETO.glob("*.tsv")) + list(comum.PROJETO.glob("*.md")) + [comum.INTAKE / "registro.tsv", comum.BASE / "_dominio" / "checagens.tsv"]
    for arquivo in arquivos:
        for linha in comum.ler(arquivo).splitlines():
            if linha.startswith("#"):
                continue
            primeira = linha.strip("| \t").split("\t")[0].split("|")[0].strip()
            if ID.fullmatch(primeira):
                achados.add(primeira)
    return achados


def absorvidos() -> dict[str, dict]:
    return {l.get("item", ""): l for l in comum.ler_tsv(ABSORVIDO) if l.get("item", "")}


def pendentes() -> list[tuple[Fonte, str, str]]:
    """O que é novo ou mudou desde a última absorção: a fonte, a situação e as notas que a guardavam."""
    feitos = absorvidos()
    saida = []
    for ident, fonte in fontes().items():
        anterior = feitos.get(ident)
        if anterior is None:
            saida.append((fonte, "novo", ""))
        elif anterior.get("marca", "") != fonte.marca:
            saida.append((fonte, "mudou", anterior.get("notas", "")))
    return saida


def notas() -> list[Nota]:
    lista = []
    for pasta in PASTAS:
        for caminho in sorted((PASTA / pasta).rglob("*.md")):
            texto = comum.ler(caminho)
            meta, corpo = comum.cabecalho(texto)
            lista.append(Nota(caminho, caminho.relative_to(PASTA).as_posix(), meta, corpo, texto, set(ID.findall(texto))))
    return lista


def _cita(nota: Nota, ident: str) -> bool:
    if ID.fullmatch(ident):
        return ident in nota.citados
    return ident in nota.texto


def _resumo(nota: Nota) -> str:
    return comum.achar_secao(comum.secoes(nota.corpo), "em resumo") or ""


def _titulo(nota: Nota) -> str:
    return nota.meta.get("titulo", "") or nota.caminho.stem


# --- índice e registro ------------------------------------------------------

ONDE_ESTA_O_RESTO = (
    ("Uma decisão, com a data e o motivo", "_projeto/decisoes.md"),
    ("Um número ou um achado, com a fonte", "_projeto/evidencias.tsv"),
    ("Uma tarefa, um marco ou uma aprovação pedida", "_projeto/acoes.tsv"),
    ("A história de uma data que mudou", "_projeto/prazos.tsv"),
    ("Uma cobrança feita ao cliente", "_projeto/cobrancas.tsv"),
    ("Um risco, uma premissa, um problema ou uma dependência", "_projeto/riscos.tsv, premissas.tsv, issues.tsv e dependencias.tsv"),
    ("Uma reunião e o que saiu dela", "_projeto/reunioes.tsv"),
    ("Um material pedido ou recebido", "_intake/registro.tsv"),
    ("O que cada dia fechou", "_projeto/diario.md"),
)


def texto_do_indice() -> str:
    partes = [
        "# Índice do segundo cérebro",
        "",
        "Gerado pelo comando `cerebro.py --indice`. Para mudar uma linha, mude o cabeçalho da nota e gere de novo.",
        "",
    ]
    todas = notas()
    for pasta in PASTAS:
        partes += [f"## {NOMES[pasta]}", "", EXPLICA[pasta], ""]
        da_pasta = [n for n in todas if n.rel.startswith(pasta + "/")]
        for n in sorted(da_pasta, key=lambda n: comum.normalizar(_titulo(n))):
            resumo = n.meta.get("resumo", "").rstrip(".")
            fontes_ = n.meta.get("fontes", "")
            cauda = (f" Fontes: {fontes_}." if fontes_ else "") + (f" Atualizada em {n.meta['atualizada']}." if n.meta.get("atualizada") else "")
            partes.append(f"- [{_titulo(n)}]({n.rel}): {resumo or 'sem resumo'}.{cauda}")
        if not da_pasta:
            partes.append("Nenhuma nota.")
        partes.append("")
    partes += ["## Onde está o resto", "", "Os registros do projeto guardam os dados. As notas citam os ids e não repetem as linhas.", "",
               "| O que você procura | Onde está |", "| --- | --- |"]
    partes += [f"| {o} | `{onde}` |" for o, onde in ONDE_ESTA_O_RESTO]
    return "\n".join(partes) + "\n"


def refazer_indice() -> bool:
    texto = texto_do_indice()
    if comum.ler(INDICE) == texto:
        return False
    PASTA.mkdir(parents=True, exist_ok=True)
    INDICE.write_text(texto, encoding="utf-8")
    return True


def registrar(hoje: datetime.date, itens: str, destino: str, o_que: str) -> None:
    texto = comum.ler(REGISTRO) or "# Registro de atualizações do segundo cérebro\n\n"
    if not texto.endswith("\n"):
        texto += "\n"
    REGISTRO.write_text(texto + f"- {hoje} | {itens} | {destino} | {o_que}\n", encoding="utf-8")


def gravar_absorvidos(linhas: dict[str, dict]) -> None:
    comentario = [l for l in comum.ler(ABSORVIDO).splitlines() if l.startswith("#")]
    colunas = ["item", "marca", "absorvido_em", "notas"]
    corpo = ["\t".join(l.get(c, "") for c in colunas) for l in linhas.values()]
    ABSORVIDO.write_text("\n".join(comentario + ["\t".join(colunas)] + corpo) + "\n", encoding="utf-8")


# --- comandos ---------------------------------------------------------------

def _da_nota(caminho: str) -> Path | None:
    """A nota citada, por caminho a partir de _cerebro/ ou da raiz do projeto."""
    for base in (PASTA, comum.RAIZ, Path.cwd()):
        alvo = (base / caminho).resolve()
        if alvo.is_file() and PASTA.resolve() in alvo.parents and alvo.relative_to(PASTA.resolve()).parts[0] in PASTAS:
            return alvo
    return None


def _carimbar_nota(caminho: Path, hoje: datetime.date) -> None:
    texto = caminho.read_text(encoding="utf-8")
    if re.search(r"^atualizada:.*$", texto, flags=re.MULTILINE):
        novo = re.sub(r"^atualizada:.*$", f"atualizada: {hoje}", texto, count=1, flags=re.MULTILINE)
    elif texto.startswith("---\n") and "\n---" in texto[4:]:
        fim = texto.index("\n---", 4)
        novo = texto[:fim] + f"\natualizada: {hoje}" + texto[fim:]
    else:
        return
    if novo != texto:
        caminho.write_text(novo, encoding="utf-8")


def absorver(itens: str, caminhos: list[str], nada: str, o_que: str, hoje: datetime.date) -> int:
    conhecidas = fontes()
    if comum.normalizar(itens) == "pendentes":
        pedidos = [f.ident for f, _, _ in pendentes()]
        if not pedidos:
            print("Nada a absorver.")
            return 0
    else:
        pedidos = [i.strip() for i in itens.split(",") if i.strip()]
    estranhos = [i for i in pedidos if i not in conhecidas]
    if estranhos:
        print(f"Não é fonte do segundo cérebro: {', '.join(estranhos)}. Tarefas, datas, cobranças e avisos ficam nos registros. Veja as fontes com --pendentes.")
        return 2
    if bool(caminhos) == bool(nada):
        print("Diga --nota CAMINHO, com a nota que guarda o que os itens ensinam, ou --nada MOTIVO, quando eles não trazem conhecimento novo.")
        return 2
    destino = "nada"
    if caminhos:
        alvos = []
        for caminho in caminhos:
            alvo = _da_nota(caminho)
            if alvo is None:
                print(f"A nota {caminho} não existe em uma das pastas do segundo cérebro. Crie com --nova.")
                return 2
            alvos.append(alvo)
        escolhidas = [n for n in notas() if n.caminho.resolve() in alvos]
        por_preencher = [n.rel for n in escolhidas if comum.MARCA in n.texto]
        if por_preencher:
            print(f"A nota {', '.join(por_preencher)} ainda tem trechos por preencher. Escreva a nota antes de absorver. Nada foi gravado.")
            return 1
        sem_citacao = [i for i in pedidos if not any(_cita(n, i) for n in escolhidas)]
        if sem_citacao:
            print(f"Nenhuma das notas cita {', '.join(sem_citacao)}. A nota precisa trazer o id de cada item que absorve, para o conhecimento ter fonte. Nada foi gravado.")
            return 1
        for alvo in alvos:
            _carimbar_nota(alvo, hoje)
        destino = ", ".join(n.rel for n in escolhidas)
    linhas = absorvidos()
    for ident in pedidos:
        linhas[ident] = {"item": ident, "marca": conhecidas[ident].marca, "absorvido_em": str(hoje), "notas": destino}
    gravar_absorvidos(linhas)
    registrar(hoje, ", ".join(pedidos), destino, nada or o_que or "absorvido")
    refazer_indice()
    print(f"{len(pedidos)} item(ns) absorvido(s) em {destino}." if caminhos else f"{len(pedidos)} item(ns) marcado(s) sem conhecimento novo: {nada}.")
    resto = len(pendentes())
    if resto:
        print(f"Ainda há {resto} item(ns) a absorver. Veja com --pendentes.")
    return 0


def nova(pasta: str, titulo: str, resumo: str, hoje: datetime.date) -> int:
    pasta = next((p for p in PASTAS if comum.normalizar(pasta) in (comum.normalizar(p), comum.normalizar(p[2:]), p[0])), "")
    if not pasta:
        print(f"A pasta é uma de: {', '.join(PASTAS)}.")
        return 2
    nome = re.sub(r"\s+", "-", comum.normalizar(titulo))[:60].strip("-")
    if not nome:
        print("Diga o título da nota.")
        return 2
    alvo = PASTA / pasta / f"{nome}.md"
    repetida = next((n for n in notas() if n.caminho.stem == nome), None)
    if repetida is not None:
        print(f"Já existe a nota {repetida.rel}. Atualize essa nota em vez de criar outra.")
        return 1
    texto = comum.ler(MODELO_DE_NOTA)
    texto = texto.replace("titulo: " + comum.MARCA, f"titulo: {titulo}").replace("# " + comum.MARCA, f"# {titulo}").replace("atualizada:", f"atualizada: {hoje}", 1)
    if resumo:
        texto = texto.replace("resumo: " + comum.MARCA, f"resumo: {resumo}")
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(texto, encoding="utf-8")
    refazer_indice()
    print(f"Nota criada em {comum.relativo(alvo)}. Escreva o resumo, o que se sabe com o id de cada fonte e as ligações, e depois rode --absorver.")
    return 0


def _trocar_ligacoes(texto: str, de: Path, para: Path, velho: Path, novo: Path) -> str:
    """Refaz as ligações de um texto que estava em 'de' e passa a estar em 'para', quando 'velho' virou 'novo'."""
    def troca(m: re.Match) -> str:
        destino = m.group(1)
        if re.match(r"[a-z]+:", destino):
            return m.group(0)
        alvo = (de / destino).resolve()
        if alvo == velho.resolve():
            alvo = novo.resolve()
        elif de == para:
            return m.group(0)
        return "](" + Path(os.path.relpath(alvo, para)).as_posix() + (m.group(2) or "") + ")"
    return LIGACAO.sub(troca, texto)


def mover(caminho: str, pasta: str, hoje: datetime.date) -> int:
    origem = _da_nota(caminho)
    pasta = next((p for p in PASTAS if comum.normalizar(pasta) in (comum.normalizar(p), comum.normalizar(p[2:]), p[0])), "")
    if origem is None or not pasta:
        print(f"Diga uma nota que existe e uma das pastas: {', '.join(PASTAS)}.")
        return 2
    destino = (PASTA / pasta / origem.name).resolve()
    if destino == origem:
        print("A nota já está nessa pasta.")
        return 0
    if destino.exists():
        print(f"Já existe {comum.relativo(destino)}.")
        return 1
    velho, novo = origem.relative_to(PASTA.resolve()).as_posix(), destino.relative_to(PASTA.resolve()).as_posix()
    for nota in notas():
        atual = nota.caminho.resolve()
        para = destino.parent if atual == origem else atual.parent
        texto = _trocar_ligacoes(nota.texto, atual.parent, para, origem, destino)
        if texto != nota.texto:
            atual.write_text(texto, encoding="utf-8")
    destino.parent.mkdir(parents=True, exist_ok=True)
    origem.rename(destino)
    linhas = absorvidos()
    for l in linhas.values():
        l["notas"] = ", ".join(novo if n.strip() == velho else n.strip() for n in l.get("notas", "").split(","))
    gravar_absorvidos(linhas)
    registrar(hoje, velho, novo, "nota movida")
    refazer_indice()
    print(f"{velho} agora é {novo}. As ligações das outras notas foram refeitas.")
    return 0


# --- busca ------------------------------------------------------------------

def _termos(texto: list[str]) -> list[str]:
    return [t for t in comum.normalizar(" ".join(texto)).split() if t]


def buscar(termos: list[str], tudo: bool = False) -> int:
    alvo = _termos(termos)
    if not alvo:
        print("Diga o que buscar.")
        return 2
    achadas = []
    for n in notas():
        titulo, resumo, corpo = comum.normalizar(_titulo(n)), comum.normalizar(n.meta.get("resumo", "")), comum.normalizar(n.texto)
        if not all(t in corpo for t in alvo):
            continue
        pontos = sum(5 * (t in titulo) + 3 * (t in resumo) + min(corpo.count(t), 5) for t in alvo)
        achadas.append((pontos, n))
    achadas.sort(key=lambda par: (-par[0], par[1].rel))
    limite = None if tudo else 8
    if achadas:
        print(f"Notas ({len(achadas)}):")
    for _, n in achadas[:limite]:
        print(f"- {comum.relativo(n.caminho)} | {_titulo(n)}: {n.meta.get('resumo', '')}")
        mostradas = 0
        for numero, linha in enumerate(n.texto.splitlines(), start=1):
            if mostradas < 2 and not linha.startswith(("titulo:", "resumo:")) and any(t in comum.normalizar(linha) for t in alvo):
                print(f"    {numero}: {linha.strip()[:200]}")
                mostradas += 1
    linhas = _linhas_dos_registros(alvo)
    limite = None if tudo else 12
    if linhas:
        print(f"Registros ({len(linhas)}):")
        for linha in linhas[:limite]:
            print("- " + linha)
    if not achadas and not linhas:
        print(f"Nada no segundo cérebro nem nos registros sobre: {' '.join(termos)}.")
        return 1
    if not tudo and (len(achadas) > 8 or len(linhas) > 12):
        print("Há mais. Rode com --tudo ou junte um termo.")
    return 0


def _arquivos_de_registro() -> list[Path]:
    arquivos = sorted(comum.PROJETO.glob("*.tsv")) + sorted(comum.PROJETO.glob("*.md")) + [comum.INTAKE / "registro.tsv", comum.BASE / "_dominio" / "dominio.md", comum.BASE / "_dominio" / "checagens.tsv"]
    for pasta in comum.entregaveis():
        arquivos += [pasta / nome for nome in ("briefing.md", "storyline.md", "fechamento.md")]
    return [a for a in arquivos if a.is_file() and a.name not in ("alertas.tsv", "afazeres.md")]


def _linhas_dos_registros(alvo: list[str]) -> list[str]:
    saida = []
    for arquivo in _arquivos_de_registro():
        for numero, linha in enumerate(comum.ler(arquivo).splitlines(), start=1):
            if linha.startswith("#") or not all(t in comum.normalizar(linha) for t in alvo):
                continue
            celulas = [c.strip() for c in re.split(r"\t|\|", linha) if c.strip()]
            saida.append(f"{comum.relativo(arquivo)}:{numero}: " + " | ".join(celulas)[:240])
    return saida


def por_id(ident: str) -> int:
    citam = [n for n in notas() if _cita(n, ident)]
    linhas = _linhas_dos_registros([comum.normalizar(ident)]) if ID.fullmatch(ident) else []
    donas = [l for l in linhas if re.search(rf":\d+: {re.escape(ident)}\b", l)]
    for linha in donas or linhas[:3]:
        print("Registro: " + linha)
    for n in citam:
        print(f"Nota: {comum.relativo(n.caminho)} | {_titulo(n)}: {n.meta.get('resumo', '')}")
    if not citam:
        print(f"Nenhuma nota cita {ident}.")
    return 0 if citam or linhas else 1


# --- conferência ------------------------------------------------------------

def conferir(so: Path | None = None) -> list[Achado]:
    """O que tira a confiança no segundo cérebro. Tudo é aviso: nada aqui barra um entregável."""
    if not PASTA.is_dir():
        return []
    achados: list[Achado] = []
    todas = notas()
    conhecidos = ids_do_projeto()
    origens = fontes()
    apontadas: dict[Path, int] = {n.caminho.resolve(): 0 for n in todas}
    entregues = set()
    for pasta in comum.entregaveis():
        meta, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
        if comum.ETAPAS[comum.etapa(meta)] == "entregue":
            entregues.add(pasta.name)

    def aviso(nota: Nota, texto: str, linha: int = 0) -> None:
        achados.append(Achado("aviso", "cerebro", comum.relativo(nota.caminho), linha, texto))

    for n in todas:
        if comum.MARCA in n.texto:
            aviso(n, "A nota ainda tem trechos por preencher.")
        for campo in ("titulo", "resumo"):
            if not n.meta.get(campo, "").strip():
                aviso(n, f"Falta '{campo}' no cabeçalho. O índice usa esse campo.")
        if not n.meta.get("fontes", "").strip() and not n.citados:
            aviso(n, "A nota não cita nenhuma fonte. Ponha o id do registro, ou o arquivo, de onde vem o que ela diz.")
        resumo = [l for l in _resumo(n).splitlines() if l.strip()]
        if not resumo:
            aviso(n, "Falta a seção 'Em resumo', com o que se lê em trinta segundos.")
        elif len(resumo) > LIMITE_DO_RESUMO:
            aviso(n, f"A seção 'Em resumo' tem {len(resumo)} linhas. O limite é {LIMITE_DO_RESUMO}: destile.")
        for ident in sorted(n.citados - conhecidos):
            aviso(n, f"Cita {ident}, que não existe em nenhum registro.")
        for numero, linha in enumerate(n.texto.splitlines(), start=1):
            for m in LIGACAO.finditer(linha):
                if re.match(r"[a-z]+:", m.group(1)):
                    continue
                alvo = (n.caminho.parent / m.group(1)).resolve()
                if not alvo.exists():
                    aviso(n, f"A ligação para '{m.group(1)}' não leva a lugar nenhum.", numero)
                elif alvo in apontadas and alvo != n.caminho.resolve():
                    apontadas[alvo] += 1
        corpo = comum.normalizar(n.corpo)
        for fonte in origens.values():
            trecho = comum.normalizar(fonte.texto)
            if len(trecho) >= TAMANHO_DE_COPIA and trecho in corpo:
                aviso(n, f"Repete o texto de {fonte.ident}. Cite o id e diga o que o dado significa, sem copiar a linha do registro.")
        if n.rel.startswith("1-projetos/") and n.caminho.stem in entregues:
            aviso(n, f"O entregável {n.caminho.stem} foi entregue. Leve a nota ao arquivo com --mover.")
    if len(todas) >= 3:
        for n in todas:
            if apontadas[n.caminho.resolve()] == 0:
                aviso(n, "Nenhuma outra nota aponta para esta. Ligue a nota a pelo menos uma que trate de assunto vizinho.")
    if so is not None:
        return [a for a in achados if a.arquivo == comum.relativo(so)]
    if comum.ler(INDICE) != texto_do_indice():
        achados.append(Achado("aviso", "cerebro", comum.relativo(INDICE), 0, "O índice não reflete as notas. Rode cerebro.py --indice."))
    faltam = pendentes()
    if faltam:
        nomes = ", ".join(f.ident for f, _, _ in faltam[:6]) + ("..." if len(faltam) > 6 else "")
        achados.append(Achado("aviso", "cerebro", comum.relativo(ABSORVIDO), 0, f"{len(faltam)} item(ns) do projeto ainda fora do segundo cérebro ({nomes}). Aplique a skill manter-cerebro."))
    return achados


def texto_dos_pendentes(limite: int | None = None) -> list[str]:
    linhas = []
    faltam = pendentes()
    for fonte, situacao, antes in faltam[:limite]:
        cauda = f" Mudou desde a absorção em {antes}." if situacao == "mudou" and antes and antes != "nada" else (" Mudou desde a última leitura." if situacao == "mudou" else "")
        origem = "" if fonte.origem == fonte.ident else f" ({fonte.origem})"
        linhas.append(f"- {fonte.ident}{origem}: {fonte.texto[:110].rstrip('.')}.{cauda}")
    if limite is not None and len(faltam) > limite:
        linhas.append(f"... e mais {len(faltam) - limite}.")
    return linhas


def linha_de_estado() -> list[str]:
    """A linha do segundo cérebro no estado do projeto."""
    if not PASTA.is_dir():
        return []
    quantas, faltam = len(notas()), len(pendentes())
    if not quantas and not faltam:
        return []
    cauda = f", {faltam} item(ns) do projeto a absorver (skill manter-cerebro)" if faltam else ""
    return [f"Segundo cérebro: {quantas} nota(s){cauda}. Antes de escrever ou responder, busque com scripts/cerebro.py --buscar TERMO."]


def main() -> int:
    analisador = argparse.ArgumentParser(description="O segundo cérebro do projeto.")
    analisador.add_argument("--buscar", nargs="+", metavar="TERMO")
    analisador.add_argument("--tudo", action="store_true", help="mostra todos os resultados da busca")
    analisador.add_argument("--id", metavar="ID")
    analisador.add_argument("--pendentes", action="store_true")
    analisador.add_argument("--nova", nargs=2, metavar=("PASTA", "TITULO"))
    analisador.add_argument("--resumo", default="")
    analisador.add_argument("--absorver", metavar="ITENS")
    analisador.add_argument("--nota", action="append", default=[], metavar="CAMINHO")
    analisador.add_argument("--nada", default="", metavar="MOTIVO")
    analisador.add_argument("--o-que", default="", dest="o_que")
    analisador.add_argument("--mover", nargs=2, metavar=("NOTA", "PASTA"))
    analisador.add_argument("--indice", action="store_true")
    analisador.add_argument("--conferir", action="store_true")
    analisador.add_argument("--hoje", default="")
    args = analisador.parse_args()
    try:
        hoje = datetime.date.fromisoformat(args.hoje) if args.hoje else datetime.date.today()
    except ValueError:
        print("A data de --hoje é AAAA-MM-DD.")
        return 2

    if args.buscar:
        return buscar(args.buscar, args.tudo)
    if args.id:
        return por_id(args.id.strip())
    if not PASTA.is_dir():
        print("O segundo cérebro ainda não existe neste projeto. Rode scripts/preparar.py para criar a pasta.")
        return 2
    if args.nova:
        return nova(args.nova[0], args.nova[1].strip(), args.resumo.strip(), hoje)
    if args.absorver:
        return absorver(args.absorver, args.nota, args.nada.strip(), args.o_que.strip(), hoje)
    if args.mover:
        return mover(args.mover[0], args.mover[1], hoje)
    if args.indice:
        print("Índice refeito." if refazer_indice() else "O índice já estava em dia.")
        return 0
    if args.conferir:
        achados = conferir()
        for a in achados:
            print(a.formatar())
        print(f"{len(achados)} aviso(s)." if achados else "Segundo cérebro em ordem.")
        return 0
    if args.pendentes:
        linhas = texto_dos_pendentes()
        print(f"A absorver ({len(linhas)}):\n" + "\n".join(linhas) if linhas else "Nada a absorver.")
        return 0
    todas = notas()
    print(f"Segundo cérebro: {len(todas)} nota(s). " + ", ".join(f"{NOMES[p].lower()} {sum(n.rel.startswith(p + '/') for n in todas)}" for p in PASTAS) + ".")
    faltam = texto_dos_pendentes(8)
    if faltam:
        print(f"A absorver ({len(pendentes())}):\n" + "\n".join(faltam))
    ultimas = [l for l in comum.ler(REGISTRO).splitlines() if l.startswith("- ")][-5:]
    if ultimas:
        print("Últimas atualizações:\n" + "\n".join(ultimas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
