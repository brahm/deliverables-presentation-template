#!/usr/bin/env python3
"""O nível de governança do projeto, os materiais que ele emite, a linha de base e as versões.

Uso:
    governanca.py                          o nível e os materiais que o projeto emite
    governanca.py --sugerir [--semanas N] [--frentes N] [--pessoas N]
                  [--comite nenhum|sim|niveis] [--pagamento marco] [--beneficio]
                                           sugere um nível pelos sinais do projeto, com o motivo
    governanca.py --nivel enxuto|padrao|completo|personalizado
    governanca.py --tirar CODIGO --motivo TXT
    governanca.py --incluir CODIGO [--cadencia TXT] [--destinatario TXT]
    governanca.py --ajustar CODIGO [--cadencia TXT] [--destinatario TXT]
    governanca.py --sob-medida "NOME" --destinatario TXT --cadencia TXT --traz TXT [--fontes TXT]
    governanca.py --catalogo               todos os materiais, por nível
    governanca.py --linha-de-base [--motivo TXT] [--aprovada-por NOME]
    governanca.py --desvios                as datas de hoje contra a linha de base
    governanca.py --versao ENTREGAVEL --mudou TXT [--enviada-a NOME]
    governanca.py --aceite ENTREGAVEL --quem NOME [--ressalvas TXT]
    --hoje AAAA-MM-DD                      calcula como se fosse este dia

O nível só escolhe o que é emitido para pessoas lerem. Os registros de
_projeto/ são mantidos em qualquer nível, e por isso subir de nível é só
passar a emitir.
"""
from __future__ import annotations

import argparse
import datetime
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402
import rotina  # noqa: E402

CATALOGO = comum.HARNESS / "governanca" / "catalogo.tsv"
NIVEIS = ["enxuto", "padrao", "completo"]
NOMES = {"enxuto": "enxuto", "padrao": "padrão", "completo": "completo", "personalizado": "personalizado"}
MOMENTOS = [("inicio", "Início"), ("rotina", "Rotina"), ("entregaveis", "Entregáveis"), ("controle", "Controle compartilhado"), ("encerramento", "Encerramento")]
SEMPRE = "ações, riscos, issues, premissas, dependências, decisões, mudanças, versões, evidências, linha de base e lições"


# --- Nível e materiais ----------------------------------------------------


def catalogo() -> list[dict]:
    return comum.ler_tsv(CATALOGO)


def nivel_atual() -> str:
    """O nível gravado no brief: enxuto, padrao, completo, personalizado ou vazio."""
    meta, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    return comum.normalizar(meta.get("governanca", ""))


def materiais_do_nivel(nivel: str) -> list[dict]:
    """Os materiais do nível, somados aos dos níveis abaixo, sem os que um material mais completo substitui."""
    ate = NIVEIS.index(nivel)
    dentro = [m for m in catalogo() if m.get("nivel", "") in NIVEIS[: ate + 1]]
    trocados = {m.get("substitui", "") for m in dentro if m.get("substitui", "")}
    ordem = {chave: i for i, (chave, _) in enumerate(MOMENTOS)}
    return sorted((m for m in dentro if m["codigo"] not in trocados), key=lambda m: ordem.get(m.get("momento", ""), 9))


def mantidos() -> list[dict]:
    return [l for l in comum.ler_tsv(comum.PROJETO / "governanca.tsv") if comum.normalizar(l.get("situacao", "")) != "tirado"]


def gravar_campo_do_brief(campo: str, valor: str) -> None:
    brief = comum.PROJETO / "brief.md"
    linhas = comum.ler(brief).splitlines()
    if not linhas or linhas[0].strip() != "---":
        raise SystemExit("O brief do projeto ainda não existe. Rode preparar.py antes de definir a governança.")
    fim = next(i for i, l in enumerate(linhas[1:], start=1) if l.strip() == "---")
    for i in range(1, fim):
        if re.match(rf"^{campo}:", linhas[i]):
            linhas[i] = f"{campo}: {valor}"
            break
    else:
        antes = next((i for i in range(1, fim) if linhas[i].startswith("iniciado:")), fim)
        linhas.insert(antes, f"{campo}: {valor}")
    brief.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def linha_do_material(m: dict, origem: str) -> dict:
    return {"codigo": m["codigo"], "material": m.get("material", ""), "cadencia": m.get("cadencia", ""), "destinatario": m.get("destinatario", ""),
            "situacao": "mantido", "origem": origem, "traz": m.get("traz", ""), "fontes": m.get("fontes", "")}


def definir(nivel: str) -> int:
    nivel = comum.normalizar(nivel)
    if nivel not in NIVEIS + ["personalizado"]:
        print("O nível é enxuto, padrao, completo ou personalizado.")
        return 2
    caminho = rotina.garantir("governanca.tsv")
    comentarios, colunas, linhas = rotina.abrir_tsv(caminho)
    if nivel == "personalizado":
        if not linhas:
            linhas = [linha_do_material(m, "nivel") for m in materiais_do_nivel("enxuto")]
    else:
        atuais = {l.get("codigo", ""): l for l in linhas}
        novas = [atuais.get(m["codigo"]) or linha_do_material(m, "nivel") for m in materiais_do_nivel(nivel)]
        codigos = {l["codigo"] for l in novas}
        # O que o consultor incluiu ou pediu sob medida não depende do nível e fica.
        novas += [l for l in linhas if l.get("codigo", "") not in codigos and comum.normalizar(l.get("origem", "")) != "nivel"]
        linhas = novas
    rotina.gravar_tsv(caminho, comentarios, colunas, linhas)
    gravar_campo_do_brief("governanca", nivel)
    print(f"Nível de governança gravado no brief: {NOMES[nivel]}. Registre a escolha com a skill registrar-decisao.\n")
    return listar()


def listar() -> int:
    nivel = nivel_atual()
    if not nivel:
        print("Nível de governança não definido. Rode governanca.py --sugerir e leve a sugestão ao consultor.")
        return 0
    print(f"Nível de governança: {NOMES.get(nivel, nivel)}.\n")
    linhas = comum.ler_tsv(comum.PROJETO / "governanca.tsv")
    ativos = [l for l in linhas if comum.normalizar(l.get("situacao", "")) != "tirado"]
    print("Materiais que o projeto emite:")
    print(tabela_de_materiais(ativos))
    tirados = [l for l in linhas if comum.normalizar(l.get("situacao", "")) == "tirado"]
    if tirados:
        print("\nTirados pelo consultor: " + ", ".join(f"{l.get('material', '')} [{l.get('codigo', '')}]" for l in tirados) + ".")
    print(f"\nMantidos sempre, como registro e sem material: {SEMPRE}.")
    print("Para mudar: --tirar, --incluir, --ajustar ou --sob-medida. O catálogo inteiro sai com --catalogo.")
    return 0


def tabela_de_materiais(materiais: list[dict]) -> str:
    if not materiais:
        return "  nenhum"
    largura = max(len(f"{m.get('material', '')} [{m.get('codigo', '')}]") for m in materiais)
    cad = max(len(m.get("cadencia", "")) for m in materiais)
    return "\n".join(
        f"  {i:2}. {(m.get('material', '') + ' [' + m.get('codigo', '') + ']').ljust(largura)}  {m.get('cadencia', '').ljust(cad)}  {m.get('destinatario', '')}".rstrip()
        for i, m in enumerate(materiais, start=1)
    )


def mostrar_catalogo() -> int:
    for nivel in NIVEIS:
        print(("O nível " + NOMES[nivel] + " emite:") if nivel == "enxuto" else f"\nO nível {NOMES[nivel]} acrescenta:")
        for chave, titulo in MOMENTOS:
            do_momento = [m for m in catalogo() if m.get("nivel", "") == nivel and m.get("momento", "") == chave]
            for m in do_momento:
                troca = f" Substitui [{m['substitui']}]." if m.get("substitui", "") else ""
                print(f"  {titulo}: {m.get('material', '')} [{m['codigo']}], {m.get('cadencia', '')}, para {m.get('destinatario', '')}.{troca}")
    print(f"\nEm qualquer nível o harness mantém como registro: {SEMPRE}.")
    return 0


def mudar_material(args) -> int:
    caminho = rotina.garantir("governanca.tsv")
    comentarios, colunas, linhas = rotina.abrir_tsv(caminho)
    if not nivel_atual():
        print("Defina o nível antes: governanca.py --nivel NIVEL.")
        return 2
    if args.sob_medida:
        if not (args.destinatario and args.cadencia and args.traz):
            print("Um material sob medida pede para quem é (--destinatario), com que frequência (--cadencia) e o que traz (--traz).")
            return 2
        numeros = [int(m.group(1)) for l in linhas if (m := re.fullmatch(r"SM-(\d+)", l.get("codigo", "")))]
        codigo = f"SM-{max(numeros, default=0) + 1:02d}"
        linhas.append({"codigo": codigo, "material": args.sob_medida, "cadencia": args.cadencia, "destinatario": args.destinatario,
                       "situacao": "mantido", "origem": "sob medida", "traz": args.traz, "fontes": args.fontes})
        print(f"{codigo} incluído: {args.sob_medida}, {args.cadencia}, para {args.destinatario}." + ("" if args.fontes else " Diga de quais registros ele sai (--ajustar com --fontes)."))
    else:
        codigo = args.tirar or args.incluir or args.ajustar
        linha = next((l for l in linhas if l.get("codigo", "") == codigo), None)
        if args.incluir and linha is None:
            modelo = next((m for m in catalogo() if m["codigo"] == codigo), None)
            if modelo is None:
                print(f"O catálogo não tem o material '{codigo}'. Veja os códigos com --catalogo, ou use --sob-medida para um material próprio.")
                return 1
            linha = linha_do_material(modelo, "incluido")
            linhas.append(linha)
        if linha is None:
            print(f"O projeto não emite o material '{codigo}'. Veja a lista com governanca.py.")
            return 1
        if args.tirar:
            if not args.motivo:
                print("Diga o motivo em uma linha (--motivo).")
                return 2
            linha["situacao"] = "tirado"
            linha["observacao"] = (linha.get("observacao", "") + f" Tirado em {args.dia}: {args.motivo}").strip()
            print(f"{linha.get('material', codigo)} deixa de ser emitido. O registro interno continua. Registre a dispensa com a skill registrar-dispensa.")
        else:
            linha["situacao"] = "mantido"
            for campo in ("cadencia", "destinatario", "traz", "fontes"):
                if getattr(args, campo):
                    linha[campo] = getattr(args, campo)
            print(f"{linha.get('material', codigo)} [{codigo}]: {linha.get('cadencia', '')}, para {linha.get('destinatario', '')}.")
    rotina.gravar_tsv(caminho, comentarios, colunas, linhas)
    return 0


# --- Sugestão de nível ----------------------------------------------------


def sinais_do_projeto(hoje: datetime.date) -> dict:
    """O que os registros deixam ler sobre o porte do projeto. O que não dá para ler fica None."""
    inicio = rotina.inicio_da_fase() or hoje
    prazos = []
    for pasta in comum.entregaveis():
        meta, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
        if dia := rotina.data(meta.get("prazo", "")):
            prazos.append(dia)
    pagamento = None
    for l in comum.ler_tsv(comum.PROJETO / "acoes.tsv"):
        # Só o marco conta na duração: uma tarefa de acompanhamento pode vencer meses depois da última entrega.
        marco = comum.normalizar(l.get("tipo", "")) == "marco"
        if marco and comum.normalizar(l.get("estado", "")) in ("aberta", "concluida") and (dia := rotina.data(l.get("prazo", ""))):
            prazos.append(dia)
            if "pagamento" in comum.normalizar(l.get("item", "")):
                pagamento = "marco"
    semanas = math.ceil((max(prazos) - inicio).days / 7) if prazos and max(prazos) > inicio else None
    _, corpo = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    previstos = [l for l in comum.tabela(comum.achar_secao(comum.secoes(corpo), "entregaveis previstos") or "") if l.get("id", "") and comum.MARCA not in l.get("id", "")]
    comite = "sim" if any("comite" in comum.normalizar(r.get("rito", "")) for r in rotina.ritos()) else None
    return {"semanas": semanas, "frentes": None, "pessoas": None, "entregaveis": max(len(comum.entregaveis()), len(previstos)) or None,
            "comite": comite, "pagamento": pagamento, "beneficio": None}


def nivel_pelos_sinais(s: dict) -> tuple[str, list[str]]:
    """O nível que os sinais pedem e os motivos, do mais forte para o mais fraco."""
    completo, padrao = [], []
    if s["semanas"] and s["semanas"] > 26:
        completo.append(f"dura {s['semanas']} semanas, mais de seis meses")
    if s["frentes"] and s["frentes"] > 4:
        completo.append(f"tem {s['frentes']} frentes")
    if s["comite"] == "niveis":
        completo.append("tem comitê em mais de um nível")
    if s["beneficio"]:
        completo.append("tem benefício comprometido")
    if s["semanas"] and s["semanas"] > 8:
        padrao.append(f"dura {s['semanas']} semanas, mais de oito")
    if s["frentes"] and s["frentes"] >= 2:
        padrao.append(f"tem {s['frentes']} frentes")
    if s["pessoas"] and s["pessoas"] > 3:
        padrao.append(f"tem {s['pessoas']} pessoas na equipe")
    if s["comite"] in ("sim", "niveis"):
        padrao.append("tem comitê formal")
    if s["pagamento"] == "marco":
        padrao.append("tem pagamento por marco")
    if completo:
        return "completo", completo
    if padrao:
        return "padrao", padrao
    return "enxuto", []


def sugerir(args, hoje: datetime.date) -> int:
    s = sinais_do_projeto(hoje)
    for campo in ("semanas", "frentes", "pessoas", "comite", "pagamento"):
        if getattr(args, campo) not in (None, ""):
            s[campo] = getattr(args, campo)
    if args.beneficio:
        s["beneficio"] = True
    nivel, motivos = nivel_pelos_sinais(s)
    lidos = []
    if s["semanas"]:
        lidos.append(f"{s['semanas']} semana(s)")
    if s["frentes"]:
        lidos.append(f"{s['frentes']} frente(s)")
    if s["entregaveis"]:
        lidos.append(f"{s['entregaveis']} entregável(is)")
    if s["pessoas"]:
        lidos.append(f"{s['pessoas']} pessoa(s)")
    if motivos:
        print(f"Nível sugerido: {NOMES[nivel]}. O projeto {' e '.join(motivos[:2])}.")
    else:
        print("Nível sugerido: enxuto. " + (f"O projeto tem {', '.join(lidos)}, e os registros não mostram comitê formal nem pagamento por marco." if lidos else "Nenhum sinal de porte pede mais do que o mínimo."))
    faltam = [nome for campo, nome in (("semanas", "a duração (--semanas)"), ("frentes", "o número de frentes (--frentes)"), ("pessoas", "o tamanho da equipe (--pessoas)"),
                                         ("comite", "se há comitê (--comite)"), ("pagamento", "se o pagamento é por marco (--pagamento marco)")) if not s[campo]]
    if faltam:
        print("Não deu para ler nos registros: " + ", ".join(faltam) + ". Pergunte ao consultor e rode de novo se a resposta mudar o porte.")
    print(f"\nMateriais do nível {NOMES[nivel]}:")
    print(tabela_de_materiais(materiais_do_nivel(nivel)))
    print(f"\nMantidos sempre, como registro e sem material: {SEMPRE}.")
    print("Pergunte ao consultor: enxuto, padrão, completo ou personalizado, e o que ele quer tirar, incluir ou pedir diferente. Grave com --nivel.")
    return 0


def revisao(hoje: datetime.date) -> str:
    """Uma frase quando os sinais dos registros passam do nível atual. Vazio quando o nível serve."""
    atual = nivel_atual()
    if atual not in NIVEIS:
        return ""
    pedido, motivos = nivel_pelos_sinais(sinais_do_projeto(hoje))
    estouros = [d for d in desvios(hoje) if d[2]]
    if len(estouros) >= 2 and NIVEIS.index(pedido) <= NIVEIS.index(atual) < len(NIVEIS) - 1:
        pedido, motivos = NIVEIS[NIVEIS.index(atual) + 1], [f"passou da tolerância de prazo em {len(estouros)} itens"]
    if NIVEIS.index(pedido) > NIVEIS.index(atual):
        return f"O projeto {' e '.join(motivos[:2])}: os sinais pedem o nível {NOMES[pedido]}, e o atual é o {NOMES[atual]}."
    return ""


# --- Linha de base --------------------------------------------------------


def itens_da_base() -> list[dict]:
    """O que entra na fotografia: os entregáveis com prazo, os marcos e as ações com base: sim."""
    itens = []
    for pasta in comum.entregaveis():
        meta, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
        if rotina.data(meta.get("prazo", "")):
            itens.append({"item": pasta.name, "tipo": "entregavel", "descricao": meta.get("titulo", pasta.name), "data": meta["prazo"].strip(),
                          "aberto": comum.ETAPAS[comum.etapa(meta)] != "entregue"})
    for l in comum.ler_tsv(comum.PROJETO / "acoes.tsv"):
        estado, tipo = comum.normalizar(l.get("estado", "")), comum.normalizar(l.get("tipo", ""))
        if estado in ("aberta", "concluida") and rotina.data(l.get("prazo", "")) and (tipo == "marco" or comum.normalizar(l.get("base", "")) == "sim"):
            itens.append({"item": l.get("id", "?"), "tipo": "marco" if tipo == "marco" else "acao", "descricao": l.get("item", ""), "data": l["prazo"], "aberto": estado == "aberta"})
    return itens


def ultima_base() -> tuple[int, list[dict]]:
    linhas = comum.ler_tsv(comum.PROJETO / "linha-de-base.tsv")
    versoes = [int(l["versao"]) for l in linhas if l.get("versao", "").isdigit()]
    if not versoes:
        return 0, []
    return max(versoes), [l for l in linhas if l.get("versao", "") == str(max(versoes))]


def linha_de_base(motivo: str, por: str, hoje: datetime.date) -> int:
    itens = itens_da_base()
    if not itens:
        print("Nada a fotografar: nenhum entregável tem prazo no briefing e nenhuma ação é marco ou tem base: sim.")
        return 1
    versao, anterior = ultima_base()
    if anterior and {l["item"]: l.get("data_base", "") for l in anterior} == {i["item"]: i["data"] for i in itens}:
        print(f"A linha de base versão {versao} já traz estas datas. Nada foi gravado.")
        return 0
    if versao and not motivo:
        print("Uma versão nova da linha de base pede o motivo em uma linha (--motivo), em geral a mudança aprovada (MU-nnn).")
        return 2
    caminho = rotina.garantir("linha-de-base.tsv")
    comentarios, colunas, linhas = rotina.abrir_tsv(caminho)
    esforco = {l["item"]: l.get("esforco_base", "") for l in anterior}
    for i in itens:
        linhas.append({"versao": str(versao + 1), "item": i["item"], "tipo": i["tipo"], "descricao": i["descricao"], "data_base": i["data"],
                       "esforco_base": esforco.get(i["item"], ""), "aprovada_em": str(hoje), "aprovada_por": por, "motivo": motivo or "Plano inicial"})
    rotina.gravar_tsv(caminho, comentarios, colunas, linhas)
    print(f"Linha de base versão {versao + 1} gravada com {len(itens)} item(ns), em {comum.relativo(caminho)}." + (" A versão anterior continua no arquivo." if versao else ""))
    if not por:
        print("Falta quem aprovou. A linha de base vale quando o cliente aprova o plano: preencha aprovada_por quando ele confirmar.")
    return 0


def desvios(hoje: datetime.date) -> list[tuple[str, int, bool, str]]:
    """Cada item da linha de base contra a data de hoje: (item, dias úteis de desvio, acima da tolerância, texto)."""
    versao, base = ultima_base()
    if not base:
        return []
    tolerancia = rotina.parametros()["tolerancia_de_prazo"]
    atuais = {i["item"]: i for i in itens_da_base()}
    saida = []
    for l in base:
        ident, da_base = l["item"], rotina.data(l.get("data_base", ""))
        atual = atuais.get(ident)
        if not da_base:
            continue
        if atual is None:
            saida.append((ident, 0, False, f"{ident}: saiu do plano depois da linha de base versão {versao}"))
            continue
        prevista = rotina.data(atual["data"])
        desvio = rotina.uteis(da_base, prevista)
        if atual["aberto"] and hoje > prevista:
            desvio = rotina.uteis(da_base, hoje)  # vencido sem data nova: o desvio cresce a cada dia
        if desvio == 0:
            continue
        acima = desvio > tolerancia
        quanto = f"{desvio} dia(s) útil(eis) depois" if desvio > 0 else f"{-desvio} dia(s) útil(eis) antes"
        saida.append((ident, desvio, acima, f"{ident}: linha de base {da_base}, hoje {prevista if hoje <= prevista or not atual['aberto'] else 'vencido sem data nova'}, {quanto}"
                      + (f". ACIMA DA TOLERÂNCIA de {int(tolerancia)} dia(s)" if acima else "")))
    for ident, atual in atuais.items():
        if ident not in {l["item"] for l in base}:
            saida.append((ident, 0, False, f"{ident}: entrou no plano depois da linha de base versão {versao}"))
    return saida


def mostrar_desvios(hoje: datetime.date) -> int:
    versao, base = ultima_base()
    if not base:
        print("O projeto ainda não tem linha de base. Grave com governanca.py --linha-de-base quando o plano for aprovado.")
        return 0
    achados = desvios(hoje)
    if not achados:
        print(f"Nenhum desvio contra a linha de base versão {versao}.")
        return 0
    print(f"Desvios contra a linha de base versão {versao}:")
    print("\n".join(f"- {texto}" for _, _, _, texto in achados))
    if any(acima for _, _, acima, _ in achados):
        print("Desvio acima da tolerância não é do consultor sozinho: leve ao patrocinador com o que causou, o impacto e as opções.")
    return 0


# --- Versões e aceite -----------------------------------------------------


def pasta_do_entregavel(ident: str) -> Path:
    pasta = comum.BASE / ident
    if ident.startswith(("_", ".")) or not (pasta / "briefing.md").is_file():
        raise SystemExit(f"Não achei o entregável '{ident}'. Vale o nome da pasta dele.")
    return pasta


def registrar_versao(ident: str, mudou: str, enviada_a: str, hoje: datetime.date) -> int:
    pasta = pasta_do_entregavel(ident)
    if not mudou:
        print("Diga em uma linha o que mudou nesta versão (--mudou).")
        return 2
    caminho = rotina.garantir("versoes.tsv")
    comentarios, colunas, linhas = rotina.abrir_tsv(caminho)
    numero = len([l for l in linhas if l.get("entregavel", "") == ident]) + 1
    linhas.append({"entregavel": ident, "versao": f"v{numero}", "data": str(hoje), "marca": comum.carimbo(pasta), "o_que_mudou": mudou, "enviada_a": enviada_a})
    rotina.gravar_tsv(caminho, comentarios, colunas, linhas)
    print(f"{ident} v{numero} registrada em {hoje}" + (f", enviada a {enviada_a}" if enviada_a else "") + ".")
    return 0


def registrar_aceite(ident: str, quem: str, ressalvas: str, hoje: datetime.date) -> int:
    pasta_do_entregavel(ident)
    if not quem:
        print("Diga quem aceitou (--quem). O aceite vem do cliente, e não do consultor.")
        return 2
    caminho = rotina.garantir("versoes.tsv")
    comentarios, colunas, linhas = rotina.abrir_tsv(caminho)
    do_item = [l for l in linhas if l.get("entregavel", "") == ident]
    if not do_item:
        print(f"{ident} ainda não tem versão registrada. Registre a versão enviada com --versao antes do aceite.")
        return 1
    do_item[-1]["aceite"] = f"{quem}, {hoje}; " + (f"ressalvas: {ressalvas}" if ressalvas else "sem ressalvas")
    rotina.gravar_tsv(caminho, comentarios, colunas, linhas)
    print(f"Aceite de {ident} {do_item[-1].get('versao', '')} registrado: {quem}, {hoje}. Guarde a mensagem ou a ata em que o cliente aceitou.")
    return 0


def linha_de_estado() -> list[str]:
    """A linha de governança do estado do projeto."""
    nivel = nivel_atual()
    if not nivel:
        return ["Nível de governança não definido: aplique a skill definir-governanca."]
    return [f"Governança: nível {NOMES.get(nivel, nivel)}, {len(mantidos())} material(is) emitido(s). A lista sai com scripts/governanca.py."]


def main() -> int:
    analisador = argparse.ArgumentParser(description="O nível de governança, os materiais, a linha de base e as versões.")
    analisador.add_argument("--sugerir", action="store_true")
    analisador.add_argument("--semanas", type=int)
    analisador.add_argument("--frentes", type=int)
    analisador.add_argument("--pessoas", type=int)
    analisador.add_argument("--comite", choices=["nenhum", "sim", "niveis"])
    analisador.add_argument("--pagamento", choices=["marco", "outro"])
    analisador.add_argument("--beneficio", action="store_true")
    analisador.add_argument("--nivel")
    analisador.add_argument("--tirar", metavar="CODIGO")
    analisador.add_argument("--incluir", metavar="CODIGO")
    analisador.add_argument("--ajustar", metavar="CODIGO")
    analisador.add_argument("--sob-medida", dest="sob_medida", metavar="NOME")
    analisador.add_argument("--cadencia", default="")
    analisador.add_argument("--destinatario", default="")
    analisador.add_argument("--traz", default="")
    analisador.add_argument("--fontes", default="")
    analisador.add_argument("--motivo", default="")
    analisador.add_argument("--catalogo", action="store_true")
    analisador.add_argument("--linha-de-base", dest="linha_de_base", action="store_true")
    analisador.add_argument("--aprovada-por", dest="aprovada_por", default="")
    analisador.add_argument("--desvios", action="store_true")
    analisador.add_argument("--versao", metavar="ENTREGAVEL")
    analisador.add_argument("--mudou", default="")
    analisador.add_argument("--enviada-a", dest="enviada_a", default="")
    analisador.add_argument("--aceite", metavar="ENTREGAVEL")
    analisador.add_argument("--quem", default="")
    analisador.add_argument("--ressalvas", default="")
    analisador.add_argument("--hoje", default="", help="calcula como se fosse este dia")
    args = analisador.parse_args()
    hoje = rotina.data(args.hoje) or datetime.date.today()
    args.dia = hoje

    if args.sugerir:
        return sugerir(args, hoje)
    if args.nivel:
        return definir(args.nivel)
    if args.tirar or args.incluir or args.ajustar or args.sob_medida:
        return mudar_material(args)
    if args.catalogo:
        return mostrar_catalogo()
    if args.linha_de_base:
        return linha_de_base(args.motivo, args.aprovada_por, hoje)
    if args.desvios:
        return mostrar_desvios(hoje)
    if args.versao:
        return registrar_versao(args.versao, args.mudou, args.enviada_a, hoje)
    if args.aceite:
        return registrar_aceite(args.aceite, args.quem, args.ressalvas, hoje)
    return listar()


if __name__ == "__main__":
    sys.exit(main())
