#!/usr/bin/env python3
"""A rotina diária do projeto: atas, material que chegou, prazos e avisos.

Uso:
    rotina.py                          mostra o resumo do dia, sem gravar nada
    rotina.py --abrir                  mostra o resumo e registra os avisos mostrados
    rotina.py --fechar "o que houve"   grava uma linha no diário do projeto
    rotina.py --ler ARQUIVO            texto de uma ata; na ata alterada, só a diferença
    rotina.py --ata [ARQUIVO] --data AAAA-MM-DD --reuniao NOME
              [--rito R] [--fonte F] [--participantes P] [--resultado TXT]
                                       registra a ata processada (sem ARQUIVO: relato de memória)
    rotina.py --sem-ata AAAA-MM-DD --rito R --motivo TXT
                                       a reunião não ocorreu ou ficou sem ata
    rotina.py --remarcar ID AAAA-MM-DD --motivo TXT [--quem NOME]
    rotina.py --concluir ID            a ação foi concluída
    rotina.py --andando ID             a ação está andando: registra o movimento de hoje
    rotina.py --dispensar ID --motivo TXT
    rotina.py --lista                  a lista do dia, em seis listas, com o que pede atenção primeiro
    rotina.py --lista --abrir          grava a lista em _projeto/afazeres.md e registra os avisos
    rotina.py --cobrado ID [--resposta aprovou|cobrei|nao-cobrei|dispensada] [--nota TXT]
                                       o follow-up de um item que espera o cliente
    rotina.py --respondida PERGUNTA    a pergunta da lista foi respondida hoje
    rotina.py --datas                  as datas deslocadas, para o status
    rotina.py --pausar AAAA-MM-DD      silencia os avisos até a retomada
    rotina.py --retomar
    --hoje AAAA-MM-DD                  calcula como se fosse este dia

Os avisos seguem o cronograma. Um item com prazo passa por três fases:
parece parado dentro do prazo (aviso leve, uma vez), prazo próximo e
vencido. O vencido pede resposta: concluído, nova data ou não é mais
necessário. Toda data nova guarda a anterior em _projeto/prazos.tsv.
ID é uma ação (T-nnn), um pedido de material (M-nnn), uma dependência
(DP-nnn) ou um entregável.
"""
from __future__ import annotations

import argparse
import datetime
import difflib
import hashlib
import html
import math
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402

ATAS = comum.BASE / "_atas"
ENTRADA = comum.INTAKE / "entrada"
COPIAS = ATAS / ".processadas"
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
PADROES = {
    "parado_fracao": 0.33, "parado_minimo": 2, "proximo_fracao": 0.2, "proximo_minimo": 1, "proximo_maximo": 5,
    "ata_depois_da_reuniao": 1, "propostas_sem_resposta": 3, "entrada_sem_classificar": 1, "projeto_sem_evento": 3,
    "cobrar_depois_de": 2, "dia_do_status": 5, "tolerancia_de_prazo": 5, "prazo_de_aprovacao": 5,
}
CICLOS = {"semanal": 7, "quinzenal": 14}


# --- Datas ------------------------------------------------------------------


def data(texto: str) -> datetime.date | None:
    try:
        return datetime.date.fromisoformat((texto or "").strip())
    except ValueError:
        return None


def uteis(inicio: datetime.date, fim: datetime.date) -> int:
    """Dias úteis depois de `inicio` até `fim`, de segunda a sexta. Negativo quando `fim` vem antes."""
    if fim < inicio:
        return -uteis(fim, inicio)
    semanas, resto = divmod((fim - inicio).days, 7)
    return semanas * 5 + sum(1 for d in range(1, resto + 1) if (inicio + datetime.timedelta(days=d)).weekday() < 5)


def dia_do_arquivo(arquivo: Path) -> datetime.date:
    return datetime.date.fromtimestamp(arquivo.stat().st_mtime)


# --- Registros em TSV -------------------------------------------------------


def garantir(nome: str) -> Path:
    """O registro do projeto, criado a partir do modelo quando ainda não existe."""
    alvo = comum.PROJETO / nome
    modelo = comum.MODELOS / "projeto" / nome
    if not alvo.exists() and modelo.is_file():
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(modelo, alvo)
    return alvo


def abrir_tsv(caminho: Path) -> tuple[list[str], list[str], list[dict]]:
    """Comentários, colunas e linhas de um registro, para gravar de volta sem perder nada."""
    if comum.ilegivel(caminho):
        raise SystemExit(
            f"{comum.relativo(caminho)} não pôde ser lido como texto. Nada foi gravado. "
            "Salve o registro em UTF-8, com as colunas separadas por tabulação, e rode de novo."
        )
    comentarios, colunas, linhas = [], [], []
    for linha in comum.ler(caminho).splitlines():
        if linha.startswith("#"):
            comentarios.append(linha)
        elif linha.strip() and not colunas:
            colunas = [c.strip() for c in linha.split("\t")]
        elif linha.strip():
            partes = linha.split("\t")
            linhas.append({c: (partes[i].strip() if i < len(partes) else "") for i, c in enumerate(colunas)})
    return comentarios, colunas, linhas


def gravar_tsv(caminho: Path, comentarios: list[str], colunas: list[str], linhas: list[dict]) -> None:
    def limpo(valor) -> str:
        return re.sub(r"\s+", " ", str(valor or "")).strip()

    if not colunas:
        raise SystemExit(f"{comum.relativo(caminho)} está sem a linha de colunas. Nada foi gravado. Restaure o cabeçalho do registro e rode de novo.")
    corpo = ["\t".join(limpo(l.get(c, "")) for c in colunas) for l in linhas]
    comum.gravar(caminho, "\n".join(comentarios + ["\t".join(colunas)] + corpo) + "\n")


def proximo_id(linhas: list[dict], prefixo: str) -> str:
    numeros = [int(m.group(1)) for l in linhas if (m := re.fullmatch(rf"{prefixo}-(\d+)", l.get("id", "")))]
    return f"{prefixo}-{max(numeros, default=0) + 1:03d}"


def parametros() -> dict:
    valores: dict = dict(PADROES)
    valores["pausa_ate"] = None
    for linha in comum.ler_tsv(comum.PROJETO / "cadencias.tsv"):
        sinal, valor = linha.get("sinal", ""), linha.get("valor", "").replace(",", ".")
        if sinal == "pausa_ate":
            valores[sinal] = data(valor)
        elif sinal in PADROES:
            try:
                valores[sinal] = float(valor)
            except ValueError:
                pass
    return valores


# --- Itens com prazo --------------------------------------------------------


@dataclass
class Item:
    ident: str
    tipo: str
    texto: str
    dono: str
    inicio: datetime.date | None
    prazo: datetime.date
    movido: datetime.date | None
    base: bool = False
    etapas: int = 0  # etapas que faltam, em entregável


def inicio_da_fase() -> datetime.date | None:
    atual = str(comum.fase_atual())
    for linha in comum.tabela(comum.ler(comum.PROJETO / "fases.md")):
        if linha.get("fase", "").strip() == atual:
            return data(linha.get("inicio", ""))
    return None


def itens_com_prazo() -> list[Item]:
    itens: list[Item] = []
    # Uma data remarcada conta como movimento: o item não parece parado no dia em que o consultor respondeu.
    remarcado: dict[str, datetime.date] = {}
    for l in comum.ler_tsv(comum.PROJETO / "prazos.tsv"):
        dia = data(l.get("mudou_em", ""))
        if dia and dia > remarcado.get(l.get("item", ""), datetime.date.min):
            remarcado[l.get("item", "")] = dia

    def movimento(ident: str, movido: datetime.date | None) -> datetime.date | None:
        return max((d for d in (movido, remarcado.get(ident)) if d), default=None)

    for l in comum.ler_tsv(comum.PROJETO / "acoes.tsv"):
        prazo = data(l.get("prazo", ""))
        if comum.normalizar(l.get("estado", "")) == "aberta" and prazo:
            tipo = {"marco": "marco", "decisao": "decisão pedida", "aprovacao": "aprovação"}.get(comum.normalizar(l.get("tipo", "")), "ação")
            itens.append(Item(l.get("id", "?"), tipo, l.get("item", ""), l.get("dono", ""), data(l.get("inicio", "")), prazo,
                              data(l.get("movida_em", "")) or data(l.get("inicio", "")), comum.normalizar(l.get("base", "")) == "sim"))
    for l in comum.ler_tsv(comum.INTAKE / "registro.tsv"):
        prazo = data(l.get("prazo", ""))
        if comum.normalizar(l.get("estado", "")) in ("pedido", "em falta") and prazo:
            pedido = data(l.get("pedido_em", ""))
            itens.append(Item(l.get("id", "?"), "pedido de material", l.get("material", ""), l.get("pedido_a", ""), pedido, prazo, movimento(l.get("id", ""), pedido)))
    for l in comum.ler_tsv(comum.PROJETO / "dependencias.tsv"):
        prazo = data(l.get("prazo", ""))
        if comum.normalizar(l.get("estado", "")) == "aberta" and prazo:
            pedido = data(l.get("pedido_em", ""))
            itens.append(Item(l.get("id", "?"), "dependência", l.get("item", ""), l.get("de_quem", ""), pedido, prazo, movimento(l.get("id", ""), data(l.get("movida_em", "")) or pedido)))
    fase = inicio_da_fase()
    for pasta in comum.entregaveis():
        meta, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
        prazo = data(meta.get("prazo", ""))
        etapa = comum.etapa(meta)
        if not prazo or comum.ETAPAS[etapa] == "entregue":
            continue
        arquivos = [a for a in pasta.iterdir() if a.is_file()]
        movido = movimento(pasta.name, max((dia_do_arquivo(a) for a in arquivos), default=None))
        itens.append(Item(pasta.name, "entregável", meta.get("titulo", pasta.name), "", data(meta.get("inicio", "")) or fase, prazo, movido,
                          etapas=len(comum.ETAPAS) - 1 - etapa))
    return itens


def fase_do_item(item: Item, hoje: datetime.date, p: dict) -> tuple[str, str]:
    """A fase do aviso (vencido, proximo, parado ou vazio) e o que dizer dela."""
    if hoje > item.prazo:
        return "vencido", f"venceu em {item.prazo}, há {uteis(item.prazo, hoje)} dia(s) útil(eis)"
    restam = uteis(hoje, item.prazo)
    janela = uteis(item.inicio, item.prazo) if item.inicio and item.inicio < item.prazo else 0
    limiar = min(max(math.ceil(janela * p["proximo_fracao"]), p["proximo_minimo"]), p["proximo_maximo"]) if janela else max(p["proximo_minimo"], 2)
    quando = "vence hoje" if restam == 0 else f"vence em {item.prazo}, em {restam} dia(s) útil(eis)"
    if item.etapas and restam < item.etapas:
        return "proximo", f"{quando}, e faltam {item.etapas} etapa(s)"
    if restam <= limiar:
        return "proximo", quando
    if item.movido and item.movido <= hoje:
        parado = uteis(item.movido, hoje)
        if parado > max(math.ceil(janela * p["parado_fracao"]), p["parado_minimo"]):
            return "parado", f"sem movimento há {parado} dia(s) útil(eis), com prazo em {item.prazo}"
    return "", ""


def remarcacoes(ident: str) -> list[dict]:
    return [l for l in comum.ler_tsv(comum.PROJETO / "prazos.tsv") if l.get("item", "") == ident]


# --- Atas e entrada ---------------------------------------------------------


def arquivos_de(pasta: Path) -> list[Path]:
    if not pasta.is_dir():
        return []
    achados = []
    for arquivo in sorted(pasta.rglob("*")):
        partes = arquivo.relative_to(pasta).parts
        if arquivo.is_file() and not any(parte.startswith(".") for parte in partes) and arquivo.name != "LEIA-ME.md":
            achados.append(arquivo)
    return achados


def marca(arquivo: Path) -> str:
    return hashlib.sha256(arquivo.read_bytes()).hexdigest()[:16]


def atas_pendentes() -> tuple[list[Path], list[tuple[Path, dict]]]:
    """As atas novas e as que mudaram depois de processadas."""
    registradas = {l.get("arquivo", ""): l for l in comum.ler_tsv(comum.PROJETO / "reunioes.tsv") if l.get("arquivo", "")}
    novas, alteradas = [], []
    for arquivo in arquivos_de(ATAS):
        linha = registradas.get(arquivo.relative_to(ATAS).as_posix())
        if linha is None:
            novas.append(arquivo)
        elif linha.get("versao", "") != marca(arquivo):
            alteradas.append((arquivo, linha))
    return novas, alteradas


def ritos() -> list[dict]:
    return [l for l in comum.ler_tsv(comum.PROJETO / "ritos.tsv") if l.get("rito", "") and data(l.get("desde", ""))]


def palpite(arquivo: Path) -> str:
    """A data e o rito que o nome do arquivo sugere."""
    nome = arquivo.stem
    dia = None
    if m := re.search(r"(20\d{2})[-_. ]?(\d{2})[-_. ]?(\d{2})", nome):
        dia = data(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
    elif m := re.search(r"(\d{2})[-_. ](\d{2})[-_. ](20\d{2})", nome):
        dia = data(f"{m.group(3)}-{m.group(2)}-{m.group(1)}")
    partes = [f"data {dia}"] if dia else []
    normal = comum.normalizar(nome)
    for rito in ritos():
        if comum.normalizar(rito["rito"]) in normal:
            partes.append(f"rito \"{rito['rito']}\"")
            break
    return f" (parece ser: {', '.join(partes)})" if partes else ""


def texto_de(arquivo: Path) -> str | None:
    """O texto de uma ata, nos formatos que a biblioteca padrão lê. None para os outros."""
    sufixo = arquivo.suffix.lower()
    if sufixo in (".txt", ".md"):
        try:
            return arquivo.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return arquivo.read_text(encoding="latin-1")
    if sufixo in (".vtt", ".srt"):
        linhas = []
        for linha in arquivo.read_text(encoding="utf-8", errors="replace").splitlines():
            linha = linha.strip()
            if not linha or linha == "WEBVTT" or "-->" in linha or linha.isdigit() or linha.startswith(("NOTE", "Kind:", "Language:")):
                continue
            linha = re.sub(r"<v ([^>]+)>", r"\1: ", linha)
            linhas.append(re.sub(r"<[^>]+>", "", linha))
        return "\n".join(linhas) + "\n"
    if sufixo == ".docx":
        try:
            with zipfile.ZipFile(arquivo) as pacote:
                xml = pacote.read("word/document.xml").decode("utf-8", errors="replace")
        except (zipfile.BadZipFile, KeyError):
            return None
        xml = re.sub(r"<w:tab\b[^>]*/>", "\t", xml)
        xml = re.sub(r"</w:p>", "\n", xml)
        return html.unescape(re.sub(r"<[^>]+>", "", xml))
    return None


def ler_ata(caminho: str) -> int:
    arquivo = Path(caminho)
    if not arquivo.is_file():
        arquivo = ATAS / caminho
    if not arquivo.is_file():
        print(f"Não achei a ata '{caminho}'. As atas ficam em {comum.relativo(ATAS)}/.")
        return 1
    texto = texto_de(arquivo)
    if texto is None:
        print(f"O formato de {arquivo.name} não é lido por este script. Abra o arquivo com as suas ferramentas e siga a skill processar-ata.")
        return 0
    try:
        nome = arquivo.resolve().relative_to(ATAS.resolve()).as_posix()
    except ValueError:
        nome = arquivo.name
    anterior = next((l for l in comum.ler_tsv(comum.PROJETO / "reunioes.tsv") if l.get("arquivo", "") == nome), None)
    copia = COPIAS / f"{anterior['id']}.txt" if anterior else None
    if anterior and copia and copia.is_file() and anterior.get("versao", "") != marca(arquivo):
        print(f"Ata alterada depois de processada ({anterior['id']}). Só a diferença:")
        antes, depois = copia.read_text(encoding="utf-8").splitlines(), texto.splitlines()
        for linha in difflib.ndiff(antes, depois):
            if linha.startswith(("+ ", "- ")):
                print(("ENTROU: " if linha[0] == "+" else "SAIU:   ") + linha[2:])
        return 0
    print(texto.rstrip())
    return 0


def registrar_ata(args, hoje: datetime.date) -> int:
    dia = data(args.data or "")
    if not dia or not args.reuniao:
        print("Diga a data (--data AAAA-MM-DD) e o nome da reunião (--reuniao).")
        return 2
    caminho = garantir("reunioes.tsv")
    comentarios, colunas, linhas = abrir_tsv(caminho)
    arquivo, nome, texto = None, "", None
    if args.ata:
        arquivo = Path(args.ata) if Path(args.ata).is_file() else ATAS / args.ata
        if not arquivo.is_file():
            print(f"Não achei a ata '{args.ata}'. As atas ficam em {comum.relativo(ATAS)}/.")
            return 1
        try:
            nome = arquivo.resolve().relative_to(ATAS.resolve()).as_posix()
        except ValueError:
            print(f"Salve a ata em {comum.relativo(ATAS)}/ antes de registrar. O controle parte dessa pasta.")
            return 1
        texto = texto_de(arquivo)
    linha = next((l for l in linhas if nome and l.get("arquivo", "") == nome), None)
    if linha is None:
        # Uma reunião já anotada como prevista ou sem ata, do mesmo rito e dia, recebe a ata.
        linha = next((l for l in linhas if not l.get("arquivo", "") and l.get("data", "") == str(dia) and args.rito and l.get("rito", "") == args.rito), None)
    if linha is None:
        linha = {"id": proximo_id(linhas, "A")}
        linhas.append(linha)
    linha.update({
        "data": str(dia), "reuniao": args.reuniao, "rito": args.rito or linha.get("rito", ""),
        "participantes": args.participantes or linha.get("participantes", ""),
        "fonte": args.fonte or ("relato de memória" if not arquivo else linha.get("fonte", "") or "ata salva na pasta"),
        "arquivo": nome, "versao": marca(arquivo) if arquivo else "",
        "situacao": "ata processada" if arquivo else "realizada",
        "resultado": args.resultado or linha.get("resultado", ""), "processada_em": str(hoje),
    })
    gravar_tsv(caminho, comentarios, colunas, linhas)
    if texto is not None:
        COPIAS.mkdir(parents=True, exist_ok=True)
        (COPIAS / f"{linha['id']}.txt").write_text(texto, encoding="utf-8")
    print(f"{linha['id']} registrada: {args.reuniao}, {dia}" + (f", arquivo {nome}" if nome else ", relato de memória") + ".")
    return 0


def registrar_sem_ata(args, hoje: datetime.date) -> int:
    dia = data(args.sem_ata)
    if not dia or not args.rito or not args.motivo:
        print("Diga a data, o rito (--rito) e o motivo (--motivo): a reunião não ocorreu, ou ocorreu e ficou sem ata.")
        return 2
    caminho = garantir("reunioes.tsv")
    comentarios, colunas, linhas = abrir_tsv(caminho)
    linha = {"id": proximo_id(linhas, "A"), "data": str(dia), "reuniao": args.rito, "rito": args.rito, "situacao": "sem ata", "resultado": args.motivo, "processada_em": str(hoje)}
    linhas.append(linha)
    gravar_tsv(caminho, comentarios, colunas, linhas)
    print(f"{linha['id']} registrada sem ata: {args.rito}, {dia}. Motivo: {args.motivo}.")
    return 0


# --- Respostas do consultor -------------------------------------------------


def localizar(ident: str) -> tuple[str, Path]:
    """De que registro é o item: 'acao', 'material', 'dependencia' ou 'entregavel'."""
    if re.fullmatch(r"T-\d+", ident):
        return "acao", comum.PROJETO / "acoes.tsv"
    if re.fullmatch(r"DP-\d+", ident):
        return "dependencia", comum.PROJETO / "dependencias.tsv"
    if re.fullmatch(r"M-\d+", ident):
        return "material", comum.INTAKE / "registro.tsv"
    if (comum.BASE / ident / "briefing.md").is_file() and not ident.startswith(("_", ".")):
        return "entregavel", comum.BASE / ident / "briefing.md"
    raise SystemExit(f"Não achei o item '{ident}'. Vale uma ação (T-nnn), um pedido de material (M-nnn), uma dependência (DP-nnn) ou a pasta de um entregável.")


def mudar_linha(caminho: Path, ident: str, mudancas: dict, acrescentar: str = "") -> dict:
    comentarios, colunas, linhas = abrir_tsv(caminho)
    linha = next((l for l in linhas if l.get("id", "") == ident), None)
    if linha is None:
        raise SystemExit(f"Não achei {ident} em {comum.relativo(caminho)}.")
    antes = dict(linha)
    linha.update({k: v for k, v in mudancas.items() if k in colunas})
    if acrescentar and "observacao" in colunas:
        linha["observacao"] = (linha.get("observacao", "") + " " + acrescentar).strip()
    gravar_tsv(caminho, comentarios, colunas, linhas)
    return antes


def remarcar(ident: str, nova: str, motivo: str, quem: str, hoje: datetime.date) -> int:
    dia = data(nova)
    if not dia or not motivo:
        print("Diga a data nova (AAAA-MM-DD) e o motivo em uma linha (--motivo). Não existe adiar sem data.")
        return 2
    onde, caminho = localizar(ident)
    base = False
    if onde == "entregavel":
        texto = comum.ler(caminho)
        meta, _ = comum.cabecalho(texto)
        anterior = meta.get("prazo", "")
        caminho.write_text(re.sub(r"^prazo:.*$", f"prazo: {dia}", texto, count=1, flags=re.MULTILINE), encoding="utf-8")
    else:
        antes = mudar_linha(caminho, ident, {"prazo": str(dia), "movida_em": str(hoje)})
        anterior = antes.get("prazo", "")
        base = comum.normalizar(antes.get("base", "")) == "sim"
    historico = garantir("prazos.tsv")
    comentarios, colunas, linhas = abrir_tsv(historico)
    do_item = [l for l in linhas if l.get("item", "") == ident]
    original = do_item[0].get("data_original", "") if do_item else anterior
    linhas.append({"item": ident, "data_original": original, "data_anterior": anterior, "data_nova": str(dia), "mudou_em": str(hoje), "quem": quem, "motivo": motivo})
    gravar_tsv(historico, comentarios, colunas, linhas)
    vezes = len(do_item) + 1
    print(f"{ident}: prazo de {anterior or 'sem data'} para {dia}. A data anterior ficou em {comum.relativo(historico)}. Remarcação número {vezes}.")
    if vezes == 2:
        print("Segunda remarcação do mesmo item: ela ganha destaque no status.")
    if vezes >= 3:
        print("Terceira remarcação ou mais: registre um risco em _projeto/riscos.tsv e pergunte ao consultor se é caso de escalar.")
    if base:
        print("Este prazo é da linha de base ou do contrato: a data nova pede o acordo do cliente. Abra a mudança em _projeto/mudancas.tsv, registre a decisão com a skill registrar-decisao e, com a mudança aprovada, grave a versão nova com governanca.py --linha-de-base.")
    return 0


def responder(ident: str, resposta: str, motivo: str, hoje: datetime.date) -> int:
    onde, caminho = localizar(ident)
    if resposta == "dispensar" and not motivo:
        print("Diga o motivo em uma linha (--motivo).")
        return 2
    if onde == "entregavel" or (onde == "material" and resposta != "dispensar"):
        print("Este comando vale para ações (T-nnn) e dependências (DP-nnn). Um material muda de estado com a skill receber-materiais, e um entregável com adiar-trabalho ou registrar-dispensa.")
        return 2
    if resposta in ("concluir", "andando") and onde == "acao":
        import afazeres

        presos = afazeres.espera_do_cliente(ident)
        if presos:
            # O trabalho que espera o cliente só segue com a confirmação dele.
            print(f"{ident} depende de " + ", ".join(f"{i.ident} ({i.tipo}, {i.dono or 'sem dono'})" for i in presos) + ", que ainda espera o cliente.")
            print("Confirme primeiro: rotina.py --cobrado ID --resposta aprovou quando o cliente respondeu, ou --resposta dispensada --motivo \"...\" quando não depende mais dele.")
            return 1
    if resposta == "concluir":
        mudar_linha(caminho, ident, {"estado": "atendida" if onde == "dependencia" else "concluida", "movida_em": str(hoje)})
        print(f"{ident} concluída em {hoje}.")
    elif resposta == "andando":
        mudar_linha(caminho, ident, {"movida_em": str(hoje)})
        print(f"{ident}: movimento registrado em {hoje}.")
    else:
        estado = "dispensado" if onde == "material" else "cancelada"
        mudar_linha(caminho, ident, {"estado": estado, "movida_em": str(hoje)}, f"Dispensado em {hoje}: {motivo}")
        print(f"{ident} dispensado. Os avisos ligados a ele param. Registre a decisão com a skill registrar-dispensa.")
    return 0


def pausar(ate: str | None) -> int:
    dia = data(ate) if ate else None
    if ate and not dia:
        print("Diga a data de retomada (AAAA-MM-DD).")
        return 2
    caminho = garantir("cadencias.tsv")
    comentarios, colunas, linhas = abrir_tsv(caminho)
    linha = next((l for l in linhas if l.get("sinal", "") == "pausa_ate"), None)
    if linha is None:
        linha = {"sinal": "pausa_ate", "observacao": "Data até a qual os avisos ficam em silêncio"}
        linhas.append(linha)
    linha["valor"] = str(dia) if dia else ""
    gravar_tsv(caminho, comentarios, colunas, linhas)
    print(f"Avisos em silêncio até {dia}." if dia else "Projeto retomado: os avisos voltaram.")
    return 0


def fechar(texto: str, hoje: datetime.date) -> int:
    caminho = garantir("diario.md")
    conteudo = comum.ler(caminho) or "# Diário do projeto\n\n| Data | O que aconteceu |\n| --- | --- |\n"
    texto = re.sub(r"\s+", " ", texto).replace("|", "/").strip()
    linhas = conteudo.rstrip("\n").splitlines()
    if linhas and linhas[-1].startswith(f"| {hoje} |"):
        linhas[-1] = linhas[-1].rstrip(" |") + f" {texto} |"
    else:
        linhas.append(f"| {hoje} | {texto} |")
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"Diário gravado em {comum.relativo(caminho)}.")
    return 0


def datas_deslocadas() -> list[str]:
    por_item: dict[str, list[dict]] = {}
    for linha in comum.ler_tsv(comum.PROJETO / "prazos.tsv"):
        por_item.setdefault(linha.get("item", ""), []).append(linha)
    saida = []
    for ident, mudancas in por_item.items():
        original, ultima = data(mudancas[0].get("data_original", "")), mudancas[-1]
        nova = data(ultima.get("data_nova", ""))
        desloc = f"{(nova - original).days} dia(s) de deslocamento" if original and nova else "deslocamento sem data original"
        destaque = " ATENÇÃO: " if len(mudancas) >= 2 else " "
        saida.append(f"-{destaque}{ident}: original {original or '?'}, anterior {ultima.get('data_anterior', '?')}, nova {nova or '?'}, {len(mudancas)} remarcação(ões), {desloc}. Motivo: {ultima.get('motivo', '')}")
    return saida


# --- Resumo do dia ----------------------------------------------------------


def avisos_de_cadencia(hoje: datetime.date, p: dict, tem_aberto: bool) -> list[tuple[str, str]]:
    avisos: list[tuple[str, str]] = []
    reunioes = comum.ler_tsv(comum.PROJETO / "reunioes.tsv")
    for rito in ritos():
        desde, ate = data(rito["desde"]), data(rito.get("ate", ""))
        cadencia = comum.normalizar(rito.get("cadencia", ""))
        ocorrencias, dia, passo = [], desde, 0
        while dia <= hoje and (not ate or dia <= ate) and passo < 600:
            ocorrencias.append(dia)
            passo += 1
            if cadencia == "mensal":
                mes = desde.month - 1 + passo
                ultimo = [31, 29 if (desde.year + mes // 12) % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes % 12]
                dia = datetime.date(desde.year + mes // 12, mes % 12 + 1, min(desde.day, ultimo))
            elif cadencia in CICLOS:
                dia = desde + datetime.timedelta(days=CICLOS[cadencia] * passo)
            else:
                break
        meio = (15 if cadencia == "mensal" else CICLOS.get(cadencia, 7) // 2) or 3
        do_rito = [data(l.get("data", "")) for l in reunioes if l.get("rito", "") == rito["rito"]]
        # Só conta a ocorrência cuja ata já devia ter chegado: a reunião de hoje ainda está no prazo.
        devidas = [o for o in ocorrencias if uteis(o, hoje) > p["ata_depois_da_reuniao"]][-2:]
        faltas = [o for o in devidas if not any(d and abs((d - o).days) <= meio for d in do_rito)]
        if len(faltas) == 2:
            avisos.append((f"rito:{rito['rito']}", f"O rito \"{rito['rito']}\" está sem ata há dois ciclos ({faltas[0]} e {faltas[1]}). As atas não estão sendo feitas, ou o rito mudou?"))
        elif faltas and faltas[0] == devidas[-1]:
            avisos.append((f"rito:{rito['rito']}:{faltas[0]}", f"A reunião \"{rito['rito']}\" de {faltas[0]} não tem ata. Ela ocorreu? Salve a ata na pasta, conte o que houve ou registre com --sem-ata."))
    velhas = [l.get("id", "?") for l in comum.ler_tsv(comum.PROJETO / "acoes.tsv")
              if comum.normalizar(l.get("estado", "")) == "proposta" and (d := data(l.get("movida_em", "")) or data(l.get("inicio", ""))) and uteis(d, hoje) > p["propostas_sem_resposta"]]
    velhas += [l.get("id", "?") for l in comum.ler_tsv(comum.PROJETO / "riscos.tsv")
               if comum.normalizar(l.get("estado", "")) == "proposto" and (d := data(l.get("revisado_em", ""))) and uteis(d, hoje) > p["propostas_sem_resposta"]]
    if velhas:
        avisos.append(("propostas", f"Propostas à espera do sim do consultor há mais de {int(p['propostas_sem_resposta'])} dias úteis: {', '.join(velhas)}."))
    esquecidos = [a.name for a in arquivos_de(ENTRADA) if uteis(dia_do_arquivo(a), hoje) > p["entrada_sem_classificar"]]
    if esquecidos:
        avisos.append(("entrada", f"Arquivos na pasta de entrada sem classificar: {', '.join(esquecidos[:5])}. Aplique a skill incorporar-material."))
    if tem_aberto:
        fontes = [a for a in comum.PROJETO.glob("*") if a.is_file()] + [comum.INTAKE / "registro.tsv"] + arquivos_de(ATAS)
        for pasta in comum.entregaveis():
            fontes += [a for a in pasta.iterdir() if a.is_file()]
        ultimo = max((dia_do_arquivo(a) for a in fontes if a.is_file()), default=None)
        if ultimo and uteis(ultimo, hoje) > p["projeto_sem_evento"]:
            avisos.append(("silencio", f"O projeto não registra nada há {uteis(ultimo, hoje)} dias úteis. Ele está pausado? Se estiver, rode --pausar com a data de retomada."))
    return avisos


def resumo(hoje: datetime.date) -> dict:
    """As seções do resumo do dia. Cada entrada é (chave do aviso, texto)."""
    p = parametros()
    secoes: dict[str, list[tuple[str, str]]] = {"pausa": [], "chegou": [], "sim": [], "vencido": [], "proximo": [], "parado": [], "cadencia": []}
    novas, alteradas = atas_pendentes()
    secoes["chegou"] += [(f"ata:{a.name}", f"Ata nova: {a.relative_to(ATAS).as_posix()}{palpite(a)}") for a in novas]
    secoes["chegou"] += [(f"ata:{a.name}", f"Ata alterada depois de processada ({l.get('id', '?')}): {a.relative_to(ATAS).as_posix()}") for a, l in alteradas]
    secoes["chegou"] += [(f"entrada:{a.name}", f"Na pasta de entrada, sem classificar: {a.relative_to(ENTRADA).as_posix()}") for a in arquivos_de(ENTRADA)]
    for l in comum.ler_tsv(comum.PROJETO / "acoes.tsv"):
        if comum.normalizar(l.get("estado", "")) == "proposta":
            secoes["sim"].append((l.get("id", "?"), f"{l.get('id', '?')} (proposta, origem {l.get('origem', '?') or '?'}): {l.get('item', '')}. Dono: {l.get('dono', '') or 'a definir'}. Prazo: {l.get('prazo', '') or 'a definir'}"))
    for l in comum.ler_tsv(comum.PROJETO / "riscos.tsv"):
        if comum.normalizar(l.get("estado", "")) == "proposto":
            secoes["sim"].append((l.get("id", "?"), f"{l.get('id', '?')} (risco proposto, origem {l.get('origem', '?') or '?'}): {l.get('risco', '')}"))
    if p["pausa_ate"] and p["pausa_ate"] >= hoje:
        secoes["pausa"].append(("pausa", f"Projeto em pausa até {p['pausa_ate']}: os avisos de prazo e de cadência estão em silêncio."))
        return secoes
    mostrados = {(l.get("item", ""), l.get("fase", "")): l for l in comum.ler_tsv(comum.PROJETO / "alertas.tsv")}
    itens = itens_com_prazo()
    for item in itens:
        fase, detalhe = fase_do_item(item, hoje, p)
        if not fase:
            continue
        anterior = mostrados.get((item.ident, fase))
        if fase == "parado" and anterior and anterior.get("primeiro_aviso", "") != str(hoje):
            continue  # o aviso leve é dado uma única vez
        texto = f"{item.ident} ({item.tipo}): {item.texto}" + (f". Dono: {item.dono}" if item.dono else "") + f". {detalhe[0].upper()}{detalhe[1:]}"
        mudancas = remarcacoes(item.ident)
        if mudancas:
            texto += f". Remarcado {len(mudancas)} vez(es), a partir de {mudancas[0].get('data_original', '?')}"
        if fase == "vencido" and anterior and int(anterior.get("vezes", "0") or 0) >= 2 and anterior.get("ultimo_aviso", "") != str(hoje):
            texto += ". Terceiro aviso sem resposta: registre como risco em _projeto/riscos.tsv"
        if item.base and fase != "parado":
            texto += ". Prazo da linha de base ou do contrato"
        secoes[fase].append((item.ident, texto))
    abertos = bool(itens) or any(comum.ETAPAS[comum.etapa(comum.cabecalho(comum.ler(pa / "briefing.md"))[0])] != "entregue" for pa in comum.entregaveis())
    secoes["cadencia"] = avisos_de_cadencia(hoje, p, abertos)
    return secoes


TITULOS = [
    ("pausa", ""),
    ("chegou", "Chegou:"),
    ("sim", "Espera o seu sim:"),
    ("vencido", "Vencidos, com resposta obrigatória (concluído, nova data ou não é mais necessário):"),
    ("proximo", "Prazo próximo:"),
    ("parado", "Parece parado, mas está no prazo (aviso dado uma vez):"),
    ("cadencia", "Cadência:"),
]


def texto_do_resumo(hoje: datetime.date, secoes: dict) -> str:
    linhas = [f"Resumo do dia, {hoje} ({DIAS[hoje.weekday()]})"]
    for chave, titulo in TITULOS:
        if secoes[chave]:
            linhas += ([titulo] if titulo else []) + [f"- {texto}" for _, texto in secoes[chave]]
    if len(linhas) == 1:
        linhas.append("Nada chegou e nenhum prazo pede atenção hoje.")
    return "\n".join(linhas)


def registrar_avisos(hoje: datetime.date, secoes: dict) -> None:
    """Guarda quais avisos foram mostrados, para o aviso leve não se repetir e o vencido subir de nível."""
    caminho = garantir("alertas.tsv")
    comentarios, colunas, linhas = abrir_tsv(caminho)
    if not colunas:
        return
    for fase in ("vencido", "proximo", "parado", "cadencia"):
        for chave, _ in secoes[fase]:
            linha = next((l for l in linhas if l.get("item", "") == chave and l.get("fase", "") == fase), None)
            if linha is None:
                linhas.append({"item": chave, "fase": fase, "primeiro_aviso": str(hoje), "ultimo_aviso": str(hoje), "vezes": "1"})
            elif linha.get("ultimo_aviso", "") != str(hoje):
                linha.update({"ultimo_aviso": str(hoje), "vezes": str(int(linha.get("vezes", "0") or 0) + 1)})
    gravar_tsv(caminho, comentarios, colunas, linhas)


def linha_de_estado() -> list[str]:
    """Uma linha para o estado do projeto, só quando há algo a tratar."""
    try:
        secoes = resumo(datetime.date.today())
    except Exception:  # noqa: BLE001 - o estado nunca deixa de sair por causa desta linha
        return []
    if secoes["pausa"]:
        return [secoes["pausa"][0][1]]
    nomes = [("chegou", "arquivo(s) novo(s) em atas e entrada"), ("sim", "proposta(s) à espera do sim"), ("vencido", "vencido(s) sem resposta"),
             ("proximo", "com prazo próximo"), ("parado", "parecendo parado(s)"), ("cadencia", "aviso(s) de cadência")]
    partes = [f"{len(secoes[c])} {nome}" for c, nome in nomes if secoes[c]]
    return ["Rotina do dia: " + ", ".join(partes) + ". Aplique a skill rotina-diaria (scripts/rotina.py --lista --abrir)."] if partes else []


def main() -> int:
    analisador = argparse.ArgumentParser(description="A rotina diária do projeto: atas, entrada, prazos e avisos.")
    analisador.add_argument("--abrir", action="store_true", help="mostra o resumo e registra os avisos mostrados")
    analisador.add_argument("--fechar", metavar="TEXTO", help="grava uma linha no diário do projeto")
    analisador.add_argument("--ler", metavar="ARQUIVO", help="texto de uma ata, ou só a diferença da ata alterada")
    analisador.add_argument("--ata", nargs="?", const="", metavar="ARQUIVO", help="registra a ata processada")
    analisador.add_argument("--sem-ata", dest="sem_ata", metavar="DATA", help="a reunião não ocorreu ou ficou sem ata")
    analisador.add_argument("--data", default="")
    analisador.add_argument("--reuniao", default="")
    analisador.add_argument("--rito", default="")
    analisador.add_argument("--fonte", default="")
    analisador.add_argument("--participantes", default="")
    analisador.add_argument("--resultado", default="")
    analisador.add_argument("--remarcar", nargs=2, metavar=("ID", "DATA"))
    analisador.add_argument("--concluir", metavar="ID")
    analisador.add_argument("--andando", metavar="ID")
    analisador.add_argument("--dispensar", metavar="ID")
    analisador.add_argument("--motivo", default="")
    analisador.add_argument("--quem", default="consultor")
    analisador.add_argument("--lista", action="store_true", help="a lista do dia, em seis listas")
    analisador.add_argument("--cobrado", metavar="ID", help="o follow-up de um item que espera o cliente")
    analisador.add_argument("--resposta", default="", help="aprovou, cobrei, nao-cobrei ou dispensada")
    analisador.add_argument("--nota", default="")
    analisador.add_argument("--respondida", metavar="PERGUNTA", help="a pergunta da lista foi respondida hoje")
    analisador.add_argument("--datas", action="store_true", help="as datas deslocadas, para o status")
    analisador.add_argument("--pausar", metavar="DATA")
    analisador.add_argument("--retomar", action="store_true")
    analisador.add_argument("--hoje", default="", help="calcula como se fosse este dia")
    args = analisador.parse_args()
    hoje = data(args.hoje) or datetime.date.today()

    if args.ler:
        return ler_ata(args.ler)
    if args.ata is not None:
        return registrar_ata(args, hoje)
    if args.sem_ata:
        return registrar_sem_ata(args, hoje)
    if args.cobrado or args.respondida or args.lista:
        import afazeres

        if args.cobrado:
            return afazeres.cobrado(args.cobrado, args.resposta, args.nota, args.motivo, args.quem, hoje)
        if args.respondida:
            return afazeres.responder_pergunta(args.respondida, hoje)
        lista = afazeres.montar(hoje)
        print(afazeres.texto_da_lista(hoje, lista))
        if args.abrir:
            registrar_avisos(hoje, resumo(hoje))
            print(f"\nLista gravada em {comum.relativo(afazeres.gravar(hoje, lista))}.")
        return 0
    if args.remarcar:
        return remarcar(args.remarcar[0], args.remarcar[1], args.motivo, args.quem, hoje)
    for resposta in ("concluir", "andando", "dispensar"):
        if getattr(args, resposta):
            return responder(getattr(args, resposta), resposta, args.motivo, hoje)
    if args.pausar or args.retomar:
        return pausar(args.pausar)
    if args.fechar:
        return fechar(args.fechar, hoje)
    if args.datas:
        linhas = datas_deslocadas()
        print("Datas deslocadas:\n" + "\n".join(linhas) if linhas else "Nenhuma data foi remarcada.")
        return 0
    secoes = resumo(hoje)
    print(texto_do_resumo(hoje, secoes))
    if args.abrir:
        registrar_avisos(hoje, secoes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
