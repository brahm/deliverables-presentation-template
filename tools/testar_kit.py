#!/usr/bin/env python3
"""Testes do próprio kit. Só serve ao repositório do template.

Instala o harness em pastas temporárias e confere o instalador, as
skills, as checagens e os hooks. Cada checagem é provada dos dois lados:
passa em um exemplo bom e reprova no erro que ela existe para pegar.

Uso: python3 tools/testar_kit.py
"""
from __future__ import annotations

import ast
import datetime
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
HARNESS = RAIZ / "entregaveis" / "_harness"
PY = sys.executable

falhas: list[str] = []
total = 0


def confere(nome: str, condicao: bool, detalhe: str = "") -> None:
    global total
    total += 1
    if not condicao:
        falhas.append(nome + (f"\n      {detalhe.strip()[:600]}" if detalhe else ""))
        print(f"  FALHOU  {nome}")


def rodar(args: list, cwd: Path, entrada: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([str(a) for a in args], cwd=cwd, input=entrada, capture_output=True, text=True, timeout=120)


def instalar(destino: Path, *opcoes: str) -> subprocess.CompletedProcess:
    return rodar([PY, HARNESS / "scripts" / "instalar.py", "--destino", destino, *opcoes], RAIZ)


# --- Skills e documentos --------------------------------------------------


def testar_skills() -> None:
    print("Skills e regras")
    regras = (HARNESS / "REGRAS.md").read_text(encoding="utf-8")
    citadas = set(re.findall(r"\|\s*`([a-z-]+)`\s*\|", regras))
    pastas = {p.name for p in (RAIZ / ".claude" / "skills").iterdir() if p.is_dir()}
    confere("toda skill da tabela de momentos existe", citadas <= pastas, str(citadas - pastas))
    confere("toda skill do kit está na tabela de momentos", pastas <= citadas, str(pastas - citadas))
    for nome in sorted(pastas):
        texto = (RAIZ / ".claude" / "skills" / nome / "SKILL.md").read_text(encoding="utf-8")
        partes = texto.split("---\n")
        cabecalho = partes[1] if len(partes) > 2 and partes[0] == "" else ""
        campos = dict(re.findall(r"^(\w+): (.*)$", cabecalho, flags=re.MULTILINE))
        descricao = campos.get("description", "")
        confere(f"{nome}: o nome do cabeçalho é o da pasta", campos.get("name") == nome)
        confere(f"{nome}: a descrição começa por 'Use' e diz o momento", descricao.startswith("Use "))
        confere(f"{nome}: a descrição é um valor YAML simples", ": " not in descricao and " #" not in descricao and len(descricao) <= 1024, descricao)
        confere(f"{nome}: traz a marca de origem do kit", "origem: harness-de-entregaveis" in cabecalho)
        confere(f"{nome}: cabe em uma tela", len(texto.splitlines()) <= 90, f"{len(texto.splitlines())} linhas")


def testar_referencias() -> None:
    print("Referências entre arquivos")
    arquivos = [RAIZ / n for n in ("README.md", "INSTALL.md", "HISTORY.md", "AGENTS.md", "CLAUDE.md", "exemplo/LEIA-ME.md")]
    arquivos += sorted(HARNESS.rglob("*.md")) + sorted((RAIZ / ".claude" / "skills").rglob("*.md"))
    for arquivo in arquivos:
        if not arquivo.is_file():
            confere(f"{arquivo.relative_to(RAIZ)} existe", False)
            continue
        texto = arquivo.read_text(encoding="utf-8")
        for alvo in re.findall(r"\]\((?!https?:|#|mailto:)([^)#]+)(?:#[^)]*)?\)", texto):
            confere(f"{arquivo.relative_to(RAIZ)}: o link '{alvo}' existe", (arquivo.parent / alvo).exists())
        for alvo in re.findall(r"`(entregaveis/_harness/[\w./-]+|\.claude/skills/[a-z-]+/SKILL\.md|tools/[\w./-]+)`", texto):
            confere(f"{arquivo.relative_to(RAIZ)}: o caminho '{alvo}' existe", (RAIZ / alvo.rstrip("/")).exists())


def testar_texto_do_kit() -> None:
    """O kit segue as práticas de texto que cobra dos entregáveis."""
    print("Texto do próprio kit")
    sys.path.insert(0, str(HARNESS / "scripts"))
    import checagens  # noqa: PLC0415

    arquivos = [RAIZ / n for n in ("README.md", "INSTALL.md", "HISTORY.md")]
    arquivos += sorted(HARNESS.rglob("*.md")) + sorted((RAIZ / ".claude" / "skills").rglob("*.md"))
    for arquivo in arquivos:
        erros = [a for a in checagens.texto(arquivo, ["pt"]) if a.nivel == "erro"]
        confere(f"{arquivo.relative_to(RAIZ)}: sem vício de texto", not erros, "\n".join(a.formatar() for a in erros[:5]))


# --- Instalador -----------------------------------------------------------


def testar_instalador(tmp: Path) -> None:
    print("Instalador")
    vazio = tmp / "vazio"
    vazio.mkdir()
    (vazio / ".git").mkdir()
    simulacao = instalar(vazio, "--simular")
    confere("--simular não grava nada", simulacao.returncode == 0 and sorted(p.name for p in vazio.iterdir()) == [".git"], simulacao.stdout + simulacao.stderr)
    primeira = instalar(vazio, "--ci")
    confere("instala em pasta vazia", primeira.returncode == 0 and (vazio / "entregaveis/_harness/REGRAS.md").is_file(), primeira.stdout + primeira.stderr)
    confere("cria os registros do projeto", (vazio / "entregaveis/_projeto/brief.md").is_file() and (vazio / "entregaveis/_intake/materiais/.gitkeep").is_file())
    segunda = instalar(vazio, "--ci")
    confere("rodar de novo não muda nada", "Nada a fazer" in segunda.stdout, segunda.stdout)

    # A raiz do template é igual ao que o instalador põe em um projeto novo.
    for nome in ("AGENTS.md", "CLAUDE.md", ".claude/settings.json", ".gitignore", ".github/workflows/entregaveis.yml"):
        igual = (RAIZ / nome).is_file() and (RAIZ / nome).read_text(encoding="utf-8") == (vazio / nome).read_text(encoding="utf-8")
        confere(f"{nome} da raiz é igual ao de uma instalação nova", igual)
    json.loads((vazio / ".claude/settings.json").read_text(encoding="utf-8"))
    confere("a licença acompanha o harness", (HARNESS / "LICENCA.txt").read_text(encoding="utf-8") == (RAIZ / "LICENSE").read_text(encoding="utf-8"))

    # Projeto em andamento, com regras, hooks, skill e pasta de mesmo nome.
    andamento = tmp / "andamento"
    (andamento / ".claude/skills/humanizar-texto").mkdir(parents=True)
    (andamento / ".github").mkdir()
    (andamento / "entregaveis/final").mkdir(parents=True)
    (andamento / ".git").mkdir()
    (andamento / "AGENTS.md").write_text("# Meu projeto\n\nRegras minhas.\n", encoding="utf-8")
    (andamento / "CLAUDE.md").write_text("Regras do Claude daqui.\n", encoding="utf-8")
    (andamento / "GEMINI.md").write_text("# Gemini\n", encoding="utf-8")
    (andamento / ".github/copilot-instructions.md").write_text("Instruções do Copilot.\n", encoding="utf-8")
    (andamento / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    (andamento / ".claude/skills/humanizar-texto/SKILL.md").write_text("minha skill\n", encoding="utf-8")
    (andamento / "entregaveis/final/deck.pptx").write_text("x", encoding="utf-8")
    (andamento / ".claude/settings.json").write_text(json.dumps({
        "permissions": {"allow": ["Bash(npm test)"], "deny": ["Read(.env)"]},
        "hooks": {"PostToolUse": [{"matcher": "Write", "hooks": [{"type": "command", "command": "npm run lint"}]}]},
        "model": "opus",
    }), encoding="utf-8")
    saida = instalar(andamento)
    confere("instala em projeto em andamento", saida.returncode == 0, saida.stdout + saida.stderr)
    confere("mantém o texto do AGENTS.md do projeto", (andamento / "AGENTS.md").read_text(encoding="utf-8").startswith("# Meu projeto\n\nRegras minhas.\n"))
    confere("mantém o texto do CLAUDE.md do projeto", (andamento / "CLAUDE.md").read_text(encoding="utf-8").startswith("Regras do Claude daqui.\n"))
    for nome in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md", ".gitignore"):
        confere(f"{nome} recebe um bloco só", (andamento / nome).read_text(encoding="utf-8").count("harness-de-entregaveis: inicio") == 1)
    confere("não cria arquivo de agente que o projeto não usa", not (andamento / ".cursorrules").exists())
    ajustes = json.loads((andamento / ".claude/settings.json").read_text(encoding="utf-8"))
    comandos = [h["command"] for g in ajustes["hooks"]["PostToolUse"] for h in g["hooks"]]
    confere("mantém os hooks e os ajustes do projeto", "npm run lint" in comandos and ajustes["model"] == "opus" and ajustes["permissions"]["deny"] == ["Read(.env)"] and "Bash(npm test)" in ajustes["permissions"]["allow"])
    confere("acrescenta os seis hooks", all(e in ajustes["hooks"] for e in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop")) and sum(len(g["hooks"]) for grupos in ajustes["hooks"].values() for g in grupos if "_harness/hooks/" in g["hooks"][0]["command"]) == 6)
    confere("mantém a skill do projeto que tem o mesmo nome", (andamento / ".claude/skills/humanizar-texto/SKILL.md").read_text(encoding="utf-8") == "minha skill\n" and "não veio do kit" in saida.stdout, saida.stdout)
    confere("não toca na pasta de entregáveis que já existia", (andamento / "entregaveis/final/deck.pptx").read_text(encoding="utf-8") == "x" and "já existia" in saida.stdout)
    de_novo = instalar(andamento)
    confere("segunda instalação em projeto em andamento não muda nada", "Nada a fazer" in de_novo.stdout and (andamento / "AGENTS.md").read_text(encoding="utf-8").count("harness-de-entregaveis: inicio") == 1, de_novo.stdout)
    (andamento / ".claude/skills/relatar-ao-dono").mkdir()
    (andamento / ".claude/skills/relatar-ao-dono/SKILL.md").write_text("skill do projeto\n", encoding="utf-8")
    forcada = instalar(andamento, "--atualizar")
    confere("--atualizar não retira a skill do projeto que tem o nome antigo de uma do kit", (andamento / ".claude/skills/relatar-ao-dono/SKILL.md").is_file(), forcada.stdout)
    confere("--atualizar não troca a skill do projeto", (andamento / ".claude/skills/humanizar-texto/SKILL.md").read_text(encoding="utf-8") == "minha skill\n", forcada.stdout)

    # Atualização: troca o que é do kit e preserva o que é do projeto.
    (vazio / "entregaveis/_harness/VERSAO").write_text("0.0.1\n", encoding="utf-8")
    (vazio / "entregaveis/_harness/REGRAS.md").write_text("regra velha\n", encoding="utf-8")
    skill = vazio / ".claude/skills/adiar-trabalho/SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8") + "\nlinha de versão antiga\n", encoding="utf-8")
    brief = vazio / "entregaveis/_projeto/brief.md"
    brief.write_text(brief.read_text(encoding="utf-8").replace("projeto: PREENCHER", "projeto: Meu projeto"), encoding="utf-8")
    antiga = vazio / ".claude/skills/relatar-ao-dono"
    antiga.mkdir()
    (antiga / "SKILL.md").write_text("---\nname: relatar-ao-dono\nmetadata:\n  origem: harness-de-entregaveis\n---\n", encoding="utf-8")
    sem_opcao = instalar(vazio)
    confere("sem --atualizar, avisa da versão diferente e não troca", "Use --atualizar" in sem_opcao.stdout and (vazio / "entregaveis/_harness/REGRAS.md").read_text(encoding="utf-8") == "regra velha\n", sem_opcao.stdout)
    atualizada = instalar(vazio, "--atualizar")
    confere("--atualizar troca o que é do kit", (vazio / "entregaveis/_harness/REGRAS.md").read_text(encoding="utf-8") == (HARNESS / "REGRAS.md").read_text(encoding="utf-8") and "linha de versão antiga" not in skill.read_text(encoding="utf-8"), atualizada.stdout + atualizada.stderr)
    confere("--atualizar retira a skill do kit que mudou de nome", not antiga.exists() and (vazio / ".claude/skills/relatar-ao-consultor/SKILL.md").is_file() and "relatar-ao-consultor" in atualizada.stdout, atualizada.stdout)
    confere("--atualizar preserva os registros do projeto", "projeto: Meu projeto" in brief.read_text(encoding="utf-8"))

    # Outro nome de pasta.
    outra = tmp / "outra"
    outra.mkdir()
    (outra / ".git").mkdir()
    saida = instalar(outra, "--pasta", "consultoria", "--ci")
    confere("instala com outro nome de pasta", saida.returncode == 0 and (outra / "consultoria/_harness/REGRAS.md").is_file() and not (outra / "entregaveis").exists(), saida.stdout + saida.stderr)
    sobras = []
    for arquivo in outra.rglob("*"):
        if arquivo.is_file() and arquivo.suffix in {".md", ".json", ".yml"} or arquivo.name == ".gitignore":
            if "entregaveis/" in arquivo.read_text(encoding="utf-8"):
                sobras.append(str(arquivo.relative_to(outra)))
    confere("nenhuma instrução aponta para o nome antigo da pasta", not sobras, ", ".join(sobras[:8]))
    estado = rodar([PY, "consultoria/_harness/scripts/estado.py"], outra)
    confere("o estado roda com outro nome de pasta", estado.returncode == 0 and "não foi iniciado" in estado.stdout, estado.stdout + estado.stderr)


# --- Checagens ------------------------------------------------------------

BRIEF = """---
projeto: Diagnóstico de martech
cliente: Varejista Exemplo
tipo: assessment de martech e adtech
pacotes:
consultor: Consultora responsável
idioma_dos_relatorios: pt-BR
idiomas_dos_entregaveis: pt-BR, es, en
classificacao: restrito
marcacao_obrigatoria:
iniciado: sim
---
# Brief do projeto

## O que é o projeto

Um diagnóstico das plataformas de marketing de um varejista.

## A decisão que o projeto precisa provocar

A diretoria escolhe quais plataformas ficam.
"""

BRIEFING = """---
id: diag
titulo: Diagnóstico de martech
tipo: apresentacao
veiculo: projetado
formato: pptx
idiomas: pt-BR
duracao_min: 30
prazo:
origem:
estado: redacao
---
# Briefing do entregável

## Audiência

A diretora de marketing decide. Ela conhece as plataformas pelo nome e teme parar campanhas.

## De e para

| De | Para |
| --- | --- |
| Cada área compra a sua ferramenta | Um conjunto único, com dono |

## Grande ideia

A empresa paga por plataformas que se repetem e perde lançamentos por causa disso.

## Chamada para ação

| Ação | Dono | Prazo | Papel |
| --- | --- | --- | --- |
| Aprovar o desligamento de duas plataformas | Diretora de marketing | 2026-12-15 | libera recursos |

## Resistências

| Tipo | Resistência esperada | Como o material responde |
| --- | --- | --- |
| prática | Medo de parar campanhas | Plano de migração por ondas |
"""

STORYLINE = """---
aprovada: sim
aprovada_por: Consultora responsável
aprovada_em: 2026-11-20
---
# Storyline

## Abertura

| Elemento | Texto |
| --- | --- |
| Situação | A empresa cresceu comprando ferramentas por área |
| Complicação | As ferramentas se repetem |
| Pergunta | Quais ficam |
| Resposta | Ficam as que têm dono e uso |

## Resumo executivo

Duas plataformas fazem o mesmo trabalho. Desligar uma libera verba para o que falta.

## Sequência

| N | Seção | Título de ação | Tipo | Evidência |
| --- | --- | --- | --- | --- |
| 1 | | Diagnóstico de martech | capa | |
| 2 | Achados | Duas plataformas de e-mail fazem o mesmo trabalho | dados | E-001 |
| 3 | Pedido | A diretoria aprova o desligamento até dezembro | pedido | |

## Recursos planejados

Nenhum.
"""

CONTEUDO = """# Conteúdo

## 1. Diagnóstico de martech
<!-- tipo: capa; secao: ; fonte: ; recurso: -->

Para a diretoria de marketing.

## 2. Duas plataformas de e-mail fazem o mesmo trabalho
<!-- tipo: dados; secao: Achados; fonte: E-001; recurso: -->

Das 14 plataformas contratadas, duas enviam e-mail para a mesma base.

Notas: conte o caso da campanha de aniversário.

## 3. A diretoria aprova o desligamento até dezembro
<!-- tipo: pedido; secao: Pedido; fonte: nao-se-aplica; recurso: -->

A diretora de marketing aprova o plano de migração.
"""

REVISAO = """---
conteudo_revisado:
revisado_em:
---
# Revisão

| Critério | Veredito | Onde | Correção feita |
| --- | --- | --- | --- |
| A grande ideia aparece no resumo | passa | | |

## O que ficou pendente

Nada ficou pendente.
"""


def montar_exemplo(projeto: Path) -> Path:
    """Um projeto pequeno e correto, sobre o qual cada erro é plantado."""
    base = projeto / "entregaveis"
    (base / "_projeto/brief.md").write_text(BRIEF, encoding="utf-8")
    with (base / "_projeto/evidencias.tsv").open("a", encoding="utf-8") as f:
        f.write("E-001\tPlataformas contratadas\t14\tInventário de contratos\t2026-10-01\tfato\talta\tdiag\n")
    with (base / "_projeto/glossario.tsv").open("a", encoding="utf-8") as f:
        f.write("plataforma de dados de clientes\tBase única de clientes\tcustomer data platform\tpt\n")
    with (base / "_projeto/confidencial.tsv").open("a", encoding="utf-8") as f:
        f.write("Projeto Girassol\tcodinome de outro cliente\n")
    criado = rodar([PY, "entregaveis/_harness/scripts/preparar.py", "--entregavel", "diag", "--tipo", "apresentacao", "--veiculo", "projetado", "--formato", "pptx", "--idiomas", "pt-BR"], projeto)
    confere("preparar.py cria o entregável", criado.returncode == 0 and (base / "diag/conteudo.md").is_file() and not (base / "diag/documento.md").exists(), criado.stdout + criado.stderr)
    pasta = base / "diag"
    (pasta / "briefing.md").write_text(BRIEFING, encoding="utf-8")
    (pasta / "storyline.md").write_text(STORYLINE, encoding="utf-8")
    (pasta / "conteudo.md").write_text(CONTEUDO, encoding="utf-8")
    return pasta


def validar(projeto: Path, *opcoes: str) -> subprocess.CompletedProcess:
    return rodar([PY, "entregaveis/_harness/scripts/validar.py", *opcoes], projeto)


def testar_checagens(tmp: Path) -> None:
    print("Checagens")
    projeto = tmp / "checagens"
    projeto.mkdir()
    instalar(projeto)
    pasta = montar_exemplo(projeto)
    bom = validar(projeto)
    confere("o exemplo bom passa sem erro", bom.returncode == 0 and "ERRO" not in bom.stdout, bom.stdout + bom.stderr)

    def com(arquivo: str, trocar: tuple[str, str] | None, espera: str, nome: str, acrescentar: str = "", opcoes: tuple = (), deve_reprovar: bool = True) -> None:
        """Planta um erro, roda as checagens, confere o achado e desfaz."""
        alvo = pasta / arquivo
        existia = alvo.is_file()
        original = alvo.read_text(encoding="utf-8") if existia else ""
        texto = original
        if trocar:
            assert trocar[0] in texto, f"trecho não encontrado em {arquivo}: {trocar[0]}"
            texto = texto.replace(trocar[0], trocar[1])
        alvo.write_text(texto + acrescentar, encoding="utf-8")
        try:
            saida = validar(projeto, *opcoes)
            if deve_reprovar:
                confere(nome, saida.returncode == 1 and espera in saida.stdout, saida.stdout + saida.stderr)
            else:
                confere(nome, espera not in saida.stdout, saida.stdout + saida.stderr)
        finally:
            if existia:
                alvo.write_text(original, encoding="utf-8")
            else:
                alvo.unlink()

    pagina = lambda n, corpo, campos="tipo: texto; secao: Achados; fonte: nao-se-aplica; recurso: ": f"\n## {n}. A equipe de mídia aprova o plano em uma tela\n<!-- {campos} -->\n\n{corpo}\n"  # noqa: E731

    # Briefing
    com("briefing.md", ("A empresa paga por plataformas que se repetem e perde lançamentos por causa disso.", "PREENCHER"), "ERRO  [briefing]", "briefing: reprova grande ideia sem preencher")
    com("briefing.md", ("A empresa paga por plataformas que se repetem e perde lançamentos por causa disso.", "Arquitetura de martech"), "ERRO  [briefing]", "briefing: reprova grande ideia que é só um assunto")
    com("briefing.md", ("| Diretora de marketing | 2026-12-15 |", "| | |"), "ERRO  [briefing]", "briefing: reprova pedido sem dono e sem prazo")
    # Storyline
    com("conteudo.md", ("## 2. Duas plataformas de e-mail fazem o mesmo trabalho", "## 2. Contexto"), "ERRO  [storyline]", "storyline: reprova título que é rótulo")
    com("conteudo.md", ("## 2. Duas plataformas de e-mail fazem o mesmo trabalho", "## 2. O que encontramos nas plataformas de e-mail:"), "ERRO  [storyline]", "storyline: reprova título que termina em dois-pontos")
    com("conteudo.md", ("## 2. Duas plataformas de e-mail fazem o mesmo trabalho", "## 2. " + "As duas plataformas de e-mail fazem o mesmo trabalho para a mesma base de clientes e de leads todos os meses"), "ERRO  [storyline]", "storyline: reprova título acima do limite do veículo")
    com("storyline.md", ("aprovada: sim", "aprovada: nao"), "ERRO  [storyline]", "storyline: reprova conteúdo escrito sem aprovação do consultor")
    com("conteudo.md", ("tipo: pedido", "tipo: texto"), "ERRO  [storyline]", "storyline: reprova material sem página de pedido", opcoes=("--rigoroso",))
    # Densidade
    com("conteudo.md", None, "ERRO  [densidade]", "densidade: reprova página projetada com texto demais", acrescentar=pagina(4, " ".join(["A equipe revisa o plano."] * 30)))
    # Evidência
    com("conteudo.md", ("fonte: E-001", "fonte: "), "ERRO  [evidencia]", "evidência: reprova página de dados sem fonte")
    com("conteudo.md", ("fonte: E-001", "fonte: E-999"), "ERRO  [evidencia]", "evidência: reprova fonte que não está no registro")
    com("conteudo.md", None, "ERRO  [evidencia]", "evidência: reprova número sem fonte", acrescentar=pagina(4, "O custo subiu 18% no período.", "tipo: texto; secao: Achados; fonte: ; recurso: "))
    com("conteudo.md", None, "ERRO  [evidencia]", "evidência: reprova marca de rascunho na revisão", acrescentar=pagina(4, "Valor TBD pela equipe."), opcoes=("--rigoroso",))
    # Texto
    com("conteudo.md", None, "ERRO  [texto]", "texto: reprova travessão", acrescentar=pagina(4, "A equipe aprova — e segue."))
    com("conteudo.md", None, "ERRO  [texto]", "texto: reprova contraste vazio", acrescentar=pagina(4, "Não é apenas uma plataforma, é uma nova forma de trabalhar."))
    com("conteudo.md", None, "ERRO  [texto]", "texto: aceita contraste planejado e declarado", acrescentar=pagina(4, "Não é apenas uma plataforma, é uma nova forma de trabalhar.", "tipo: texto; secao: Achados; fonte: nao-se-aplica; recurso: contraste"), deve_reprovar=False)
    com("conteudo.md", None, "ERRO  [texto]", "texto: reprova aviso de importância", acrescentar=pagina(4, "Vale ressaltar que a equipe aprova o plano."))
    com("conteudo.md", None, "ERRO  [texto]", "texto: reprova autoridade sem nome", acrescentar=pagina(4, "Especialistas apontam que a equipe aprova o plano."))
    com("conteudo.md", None, "ERRO  [texto]", "texto: não examina expressão citada entre aspas", acrescentar=pagina(4, 'A equipe cortou a frase "vale ressaltar" do material.'), deve_reprovar=False)
    com("conteudo.es.md", None, "ERRO  [texto]", "texto: reprova vício em espanhol", acrescentar=CONTEUDO + pagina(4, "Cabe destacar que el equipo aprueba el plan."))
    com("conteudo.en.md", None, "ERRO  [texto]", "texto: reprova vício em inglês", acrescentar=CONTEUDO + pagina(4, "It is worth noting that the team approves the plan."))
    com("conteudo.es.md", None, "ERRO  [texto]", "texto: não aplica a lista de um idioma a outro", acrescentar=CONTEUDO + pagina(4, "It is worth noting that the team approves the plan."), deve_reprovar=False)
    # Termos
    com("conteudo.md", None, "ERRO  [termos]", "termos: reprova variante que o glossário manda evitar", acrescentar=pagina(4, "A customer data platform junta as bases."))
    # Estrutura
    com("conteudo.md", ("## 3. A diretoria", "## 5. A diretoria"), "ERRO  [estrutura]", "estrutura: reprova numeração quebrada")
    com("conteudo.md", ("tipo: dados; ", ""), "ERRO  [estrutura]", "estrutura: reprova página sem tipo")
    com("conteudo.md", None, "ERRO  [estrutura]", "estrutura: reprova referência a página que não existe", acrescentar=pagina(4, "O detalhe está na página 40."))
    # Confidencialidade
    com("conteudo.md", None, "ERRO  [confidencialidade]", "confidencialidade: reprova termo proibido", acrescentar=pagina(4, "O mesmo foi feito no Projeto Girassol."))
    com("conteudo.md", None, "ERRO  [confidencialidade]", "confidencialidade: reprova credencial", acrescentar=pagina(4, "A senha: abc12345xyz fica com a equipe."))

    # Marcação obrigatória
    brief = projeto / "entregaveis/_projeto/brief.md"
    brief.write_text(BRIEF.replace("marcacao_obrigatoria:", "marcacao_obrigatoria: Uso restrito"), encoding="utf-8")
    saida = validar(projeto, "--rigoroso")
    confere("confidencialidade: reprova falta da marcação obrigatória", saida.returncode == 1 and "ERRO  [confidencialidade]" in saida.stdout, saida.stdout)
    brief.write_text(BRIEF, encoding="utf-8")

    # Intake e projeto
    with (projeto / "entregaveis/_intake/registro.tsv").open("a", encoding="utf-8") as f:
        f.write("M-001\tModelo de apresentação\tmodelo\tcliente\t2026-11-01\t2026-11-05\tpedido\t\t\n")
    saida = validar(projeto)
    confere("intake: avisa de material pedido e não recebido", "AVISO [intake]" in saida.stdout and "M-001" in saida.stdout, saida.stdout)
    estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto)
    confere("estado: mostra o projeto, o entregável e o material pendente", estado.returncode == 0 and "diag" in estado.stdout and "Modelo de apresentação" in estado.stdout and "Decisões assumidas" not in estado.stdout, estado.stdout + estado.stderr)
    with (projeto / "entregaveis/_projeto/decisoes.md").open("a", encoding="utf-8") as f:
        f.write("| D-001 | 2026-11-20 | Deck de leitura em vez de projetado | O consultor não disse | Vigente (assumida) |\n")
    estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto)
    confere("estado: conta as decisões assumidas à espera do consultor", "Decisões assumidas à espera do consultor: 1" in estado.stdout, estado.stdout)

    # Revisão
    sem_rubrica = validar(projeto, "--carimbar", "diag")
    confere("revisão: não registra sem a rubrica preenchida", sem_rubrica.returncode == 1, sem_rubrica.stdout)
    (pasta / "revisao.md").write_text(REVISAO, encoding="utf-8")
    com_rubrica = validar(projeto, "--carimbar", "diag")
    confere("revisão: registra a versão revisada", com_rubrica.returncode == 0 and re.search(r"conteudo_revisado: \w{16}", (pasta / "revisao.md").read_text(encoding="utf-8")) is not None, com_rubrica.stdout + com_rubrica.stderr)


# --- Hooks ----------------------------------------------------------------


def testar_hooks(tmp: Path) -> None:
    print("Hooks")
    projeto = tmp / "hooks"
    projeto.mkdir()
    instalar(projeto)
    hooks = projeto / "entregaveis/_harness/hooks"

    def hook(nome: str, dados: dict) -> subprocess.CompletedProcess:
        return rodar([PY, hooks / nome], projeto, json.dumps({"cwd": str(projeto), **dados}))

    def gravacao(caminho: str, sessao: str = "s1") -> dict:
        return {"session_id": sessao, "tool_name": "Write", "tool_input": {"file_path": caminho}}

    inicio = hook("sessao.py", {"hook_event_name": "SessionStart"})
    confere("sessão: diz que o projeto não foi iniciado", inicio.returncode == 0 and "iniciar-projeto" in inicio.stdout, inicio.stdout + inicio.stderr)
    lembrete = hook("mensagem.py", {"prompt": "monte a apresentação da diretoria"})
    confere("mensagem: lembra de iniciar o projeto quando o pedido é de material", lembrete.returncode == 0 and "iniciar-projeto" in lembrete.stdout, lembrete.stdout)
    calado = hook("mensagem.py", {"prompt": "corrija o teste da API"})
    confere("mensagem: fica calada em pedido de outro assunto", calado.returncode == 0 and not calado.stdout.strip(), calado.stdout)

    pasta = montar_exemplo(projeto)
    ponto = hook("mensagem.py", {"prompt": "siga"})
    confere("mensagem: mostra o ponto atual em até três linhas", "diag" in ponto.stdout and len(ponto.stdout.strip().splitlines()) <= 4, ponto.stdout)

    # Antes de gravar
    confere("antes de gravar: deixa gravar página com briefing e storyline prontos", hook("antes_de_gravar.py", gravacao("entregaveis/diag/conteudo.md")).returncode == 0)
    (pasta / "storyline.md").write_text(STORYLINE.replace("aprovada: sim", "aprovada: nao"), encoding="utf-8")
    barrado = hook("antes_de_gravar.py", gravacao("entregaveis/diag/conteudo.md"))
    confere("antes de gravar: bloqueia página sem storyline aprovada", barrado.returncode == 2 and "storyline" in barrado.stderr, barrado.stderr)
    confere("antes de gravar: bloqueia arquivo de saída sem storyline aprovada", hook("antes_de_gravar.py", gravacao(str(pasta / "saida/deck.pptx"))).returncode == 2)
    confere("antes de gravar: deixa gravar a storyline", hook("antes_de_gravar.py", gravacao("entregaveis/diag/storyline.md")).returncode == 0)
    (pasta / "storyline.md").write_text(STORYLINE, encoding="utf-8")
    (pasta / "briefing.md").write_text(BRIEFING.replace("A empresa paga por plataformas que se repetem e perde lançamentos por causa disso.", "PREENCHER"), encoding="utf-8")
    barrado = hook("antes_de_gravar.py", gravacao("entregaveis/diag/conteudo.md"))
    confere("antes de gravar: bloqueia página com briefing incompleto", barrado.returncode == 2 and "briefing" in barrado.stderr, barrado.stderr)
    (pasta / "briefing.md").write_text(BRIEFING, encoding="utf-8")
    confere("antes de gravar: ignora arquivo fora da pasta de entregáveis", hook("antes_de_gravar.py", gravacao("src/app.py")).returncode == 0)
    confere("antes de gravar: bloqueia página em pasta sem briefing", hook("antes_de_gravar.py", gravacao("entregaveis/novo/conteudo.md")).returncode == 2)
    confere("antes de gravar: não barra pasta antiga do projeto", hook("antes_de_gravar.py", gravacao("entregaveis/final/saida/deck.pptx")).returncode == 0)
    confere("antes de gravar: entrada inválida não trava o trabalho", rodar([PY, hooks / "antes_de_gravar.py"], projeto, "isto não é json").returncode == 0)

    # Depois de gravar
    limpo = hook("depois_de_gravar.py", gravacao("entregaveis/diag/conteudo.md"))
    confere("depois de gravar: arquivo limpo passa", limpo.returncode == 0, limpo.stdout + limpo.stderr)
    (pasta / "conteudo.md").write_text(CONTEUDO + "\nA equipe aprova — e segue.\n", encoding="utf-8")
    sujo = hook("depois_de_gravar.py", gravacao("entregaveis/diag/conteudo.md"))
    confere("depois de gravar: devolve o vício de texto ao agente", sujo.returncode == 2 and "[texto]" in sujo.stderr, sujo.stdout + sujo.stderr)
    (pasta / "conteudo.md").write_text(CONTEUDO + "\nVeja o fluxo -> aprovação.\n", encoding="utf-8")
    aviso = hook("depois_de_gravar.py", gravacao("entregaveis/diag/conteudo.md"))
    confere("depois de gravar: aviso volta como contexto e não barra", aviso.returncode == 0 and "additionalContext" in aviso.stdout, aviso.stdout + aviso.stderr)
    (pasta / "conteudo.md").write_text(CONTEUDO, encoding="utf-8")

    # Fim do turno
    outra_sessao = hook("fim_do_turno.py", {"session_id": "s2"})
    confere("fim do turno: não cobra sessão que não alterou conteúdo", outra_sessao.returncode == 0, outra_sessao.stderr)
    cobrado = hook("fim_do_turno.py", {"session_id": "s1"})
    confere("fim do turno: bloqueia conteúdo alterado e sem revisão", cobrado.returncode == 2 and "revisar-entregavel" in cobrado.stderr, cobrado.stdout + cobrado.stderr)
    confere("fim do turno: cobra uma vez por versão", hook("fim_do_turno.py", {"session_id": "s1"}).returncode == 0)
    (pasta / "revisao.md").write_text(REVISAO, encoding="utf-8")
    carimbo = validar(projeto, "--carimbar", "diag")
    hook("depois_de_gravar.py", gravacao("entregaveis/diag/conteudo.md", "s3"))
    confere("fim do turno: libera depois da revisão registrada", carimbo.returncode == 0 and hook("fim_do_turno.py", {"session_id": "s3"}).returncode == 0, carimbo.stdout)
    (pasta / "conteudo.md").write_text(CONTEUDO.replace("aprova o plano de migração", "aprova o plano de migração por ondas"), encoding="utf-8")
    confere("fim do turno: volta a cobrar quando o conteúdo muda depois da revisão", hook("fim_do_turno.py", {"session_id": "s3"}).returncode == 2)


def preencher_interativo(html: str) -> str:
    """Troca as marcas e os exemplos de um modelo de HTML interativo por conteúdo de projeto."""
    html = re.sub(
        r"<!-- interativo.*?-->",
        "<!-- interativo\ntitulo: Caminho de uma campanha\nmensagem: A aprovação consome metade do prazo de uma campanha.\n"
        "apoia: página 2\nfontes: E-001\nidioma: pt-BR\n-->",
        html, count=1, flags=re.S,
    )
    html = html.replace("<title>PREENCHER</title>", "<title>Caminho de uma campanha</title>")
    html = html.replace("Fonte: PREENCHER, com a data do dado.", "Fonte: inventário de plataformas, março de 2026.")
    html = re.sub(r"PREENCHER[^<\n]*", "A aprovação consome metade do prazo de uma campanha.", html)
    return html.replace('"Exemplo: ', '"').replace('"Exemplo. ', '"').replace("Exemplo: ", "")


def testar_interativos(tmp: Path) -> None:
    print("HTML interativo")
    projeto = tmp / "interativos"
    projeto.mkdir()
    instalar(projeto)
    pasta = montar_exemplo(projeto)
    preparar = projeto / "entregaveis/_harness/scripts/preparar.py"
    modelos = sorted((HARNESS / "modelos/interativos").glob("*.html"))
    confere("há três modelos de HTML interativo", [m.stem for m in modelos] == ["camadas-3d", "fluxo", "simulador"], str(modelos))

    # Criação pelo preparar.py
    (pasta / "storyline.md").write_text(STORYLINE.replace("aprovada: sim", "aprovada: nao"), encoding="utf-8")
    recusa = rodar([PY, preparar, "--entregavel", "diag", "--interativo", "caminho", "--base", "fluxo"], projeto)
    confere("preparar: recusa a peça sem storyline aprovada", recusa.returncode != 0 and not (pasta / "interativos/caminho.html").exists(), recusa.stdout + recusa.stderr)
    (pasta / "storyline.md").write_text(STORYLINE, encoding="utf-8")
    for modelo in modelos:
        feito = rodar([PY, preparar, "--entregavel", "diag", "--interativo", f"peca-{modelo.stem}", "--base", modelo.stem], projeto)
        confere(f"preparar: cria a peça a partir de '{modelo.stem}'", feito.returncode == 0 and (pasta / f"interativos/peca-{modelo.stem}.html").is_file(), feito.stdout + feito.stderr)
    confere("preparar: recusa modelo que não existe", rodar([PY, preparar, "--entregavel", "diag", "--interativo", "x1", "--base", "nada"], projeto).returncode != 0)
    confere("preparar: não mexe no briefing ao criar a peça", (pasta / "briefing.md").read_text(encoding="utf-8") == BRIEFING)
    cru = validar(projeto, "--so", "interativo")
    confere("modelo recém-criado: só avisos enquanto está em redação", cru.returncode == 0 and "PREENCHER" in cru.stdout, cru.stdout[-600:])
    rigor = validar(projeto, "--so", "interativo", "--rigoroso")
    confere("modelo recém-criado: reprova na revisão por marca e dado de exemplo", rigor.returncode != 0 and "dado(s) de exemplo" in rigor.stdout, rigor.stdout[-600:])

    # Modelos preenchidos passam, inclusive na revisão
    for modelo in modelos:
        (pasta / f"interativos/peca-{modelo.stem}.html").write_text(preencher_interativo(modelo.read_text(encoding="utf-8")), encoding="utf-8")
    limpo = validar(projeto, "--so", "interativo", "--rigoroso")
    confere("modelos preenchidos passam na checagem rigorosa", limpo.returncode == 0 and "Nenhum erro e nenhum aviso" in limpo.stdout, limpo.stdout[-900:])
    for modelo in modelos:
        html = modelo.read_text(encoding="utf-8")
        confere(f"modelo '{modelo.stem}': sem endereço de rede", not re.search(r"https?://|//cdn|@import", html))

    # Arquivo único: cada tipo de recurso de fora reprova
    alvo = pasta / "interativos/peca-fluxo.html"
    bom = alvo.read_text(encoding="utf-8")

    def com(trecho: str, nome: str, espera: str = "arquivo único", antes: str = "</body>", deve_reprovar: bool = True) -> None:
        alvo.write_text(bom.replace(antes, trecho + antes, 1), encoding="utf-8")
        saida = validar(projeto, "--so", "interativo")
        ok = (saida.returncode != 0 and espera in saida.stdout) if deve_reprovar else saida.returncode == 0
        confere(nome, ok, saida.stdout[-500:])
        alvo.write_text(bom, encoding="utf-8")

    com('<script src="https://cdn.exemplo.com/grafico.js"></script>', "reprova script de fora")
    com('<script src="lib/grafico.js"></script>', "reprova script em pasta ao lado")
    com('<link rel="stylesheet" href="estilo.css">', "reprova folha de estilo de fora", antes="</head>")
    com('<img src="imagens/mapa.png" alt="Mapa">', "reprova imagem em pasta ao lado")
    com('<iframe src="https://exemplo.com/painel"></iframe>', "reprova quadro embutido")
    com("<style>@font-face { font-family: Marca; src: url(fontes/marca.woff2); }</style>", "reprova fonte em arquivo ao lado", antes="</head>")
    com('<style>@import "tema.css";</style>', "reprova importação de estilo", antes="</head>")
    com('<script>fetch("https://api.exemplo.com/dados").then(function () {});</script>', "reprova chamada de rede")
    com('<img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="Ponto">', "aceita imagem embutida no arquivo", deve_reprovar=False)
    com('<svg viewBox="0 0 10 10" role="img" aria-label="Marca"><defs><linearGradient id="g"></linearGradient></defs><rect width="10" height="10" fill="url(#g)"></rect></svg>', "aceita SVG desenhado no arquivo", deve_reprovar=False)

    # Estrutura e movimento
    alvo.write_text(bom.replace("prefers-reduced-motion", "prefers-outra-coisa"), encoding="utf-8")
    parado = validar(projeto, "--so", "interativo")
    confere("reprova animação sem movimento reduzido", parado.returncode != 0 and "prefers-reduced-motion" in parado.stdout, parado.stdout[-400:])
    alvo.write_text(bom.replace('<meta name="viewport" content="width=device-width, initial-scale=1">', ""), encoding="utf-8")
    confere("reprova arquivo sem viewport", validar(projeto, "--so", "interativo").returncode != 0)
    alvo.write_text(bom.replace("fontes: E-001", "fontes: E-777"), encoding="utf-8")
    perdida = validar(projeto, "--so", "interativo")
    confere("reprova evidência que não está no registro", perdida.returncode != 0 and "E-777" in perdida.stdout, perdida.stdout[-400:])
    alvo.write_text(bom.replace("</main>", "<p>A equipe aprova — e segue.</p></main>"), encoding="utf-8")
    vicio = validar(projeto, "--so", "interativo")
    confere("o texto visível da peça passa pelas checagens de texto", vicio.returncode != 0 and "[interativo]" in vicio.stdout, vicio.stdout[-400:])
    alvo.write_text(bom, encoding="utf-8")

    # Hooks
    hooks = projeto / "entregaveis/_harness/hooks"

    def hook(nome: str, caminho: str) -> subprocess.CompletedProcess:
        dados = {"cwd": str(projeto), "session_id": "i1", "tool_name": "Write", "tool_input": {"file_path": caminho}}
        return rodar([PY, hooks / nome], projeto, json.dumps(dados))

    confere("antes de gravar: deixa gravar a peça com storyline aprovada", hook("antes_de_gravar.py", "entregaveis/diag/interativos/peca-fluxo.html").returncode == 0)
    (pasta / "storyline.md").write_text(STORYLINE.replace("aprovada: sim", "aprovada: nao"), encoding="utf-8")
    confere("antes de gravar: bloqueia a peça sem storyline aprovada", hook("antes_de_gravar.py", "entregaveis/diag/interativos/peca-fluxo.html").returncode == 2)
    (pasta / "storyline.md").write_text(STORYLINE, encoding="utf-8")
    confere("depois de gravar: peça limpa passa", hook("depois_de_gravar.py", "entregaveis/diag/interativos/peca-fluxo.html").returncode == 0)
    alvo.write_text(bom.replace("</body>", '<script src="https://cdn.exemplo.com/grafico.js"></script></body>'), encoding="utf-8")
    devolvido = hook("depois_de_gravar.py", "entregaveis/diag/interativos/peca-fluxo.html")
    confere("depois de gravar: devolve o recurso de fora ao agente", devolvido.returncode == 2 and "arquivo único" in devolvido.stderr, devolvido.stdout + devolvido.stderr)
    alvo.write_text(bom, encoding="utf-8")

    # A revisão registrada vale para a versão da peça que foi revisada
    (pasta / "revisao.md").write_text(REVISAO, encoding="utf-8")
    validar(projeto, "--carimbar", "diag")
    codigo = "import sys; sys.path.insert(0, 'entregaveis/_harness/scripts'); import comum; print(comum.carimbo(comum.BASE / 'diag'))"
    antes = rodar([PY, "-c", codigo], projeto).stdout.strip()
    alvo.write_text(bom.replace("Caminho de uma campanha", "Caminho de uma campanha de mídia"), encoding="utf-8")
    depois = rodar([PY, "-c", codigo], projeto).stdout.strip()
    confere("o carimbo da revisão muda quando a peça muda", bool(antes) and antes != depois, f"{antes} {depois}")


DOMINIO = """---
estado: rascunho
calibrado_em: 2026-11-23
materiais: M-001
---
# Domínio do projeto

## Contexto e objetivo

A diretoria decide que plataformas ficam. Origem: brief.

## Métodos e frameworks

Inventário por função e por dono. Origem: M-001.
"""

REGRAS_DO_DOMINIO = (
    "id\ttipo\taplica\tonde\tpadrao\tmensagem\tnivel\torigem\n"
    "D-001\tjunto\t*\tconteudo\tnota de maturidade => crit[ée]rio\tToda nota de maturidade vem com o critério que a justifica.\terro\tM-001\n"
    "D-002\tproibido\tapresentacao\ttitulos\t\\bferramentas?\\b\tO projeto chama de plataforma, não de ferramenta.\terro\tM-001\n"
    "D-003\tobrigatorio\t*\tconteudo\tplataformas contratadas\tO material diz quantas plataformas estão contratadas.\terro\tM-001\n"
    "D-004\tordem\t*\tconteudo\tDiagn[óo]stico => desligamento\tO pedido de desligamento só vem depois do diagnóstico.\taviso\tM-001\n"
)

CASOS_DO_DOMINIO = (
    "checagem\tespera\ttexto\n"
    "D-001\tacusa\tA nota de maturidade da frente de dados é 2.\n"
    "D-001\tpassa\tA nota de maturidade da frente de dados é 2. O critério: não há identificador único.\n"
    "D-001\tacusa\tA nota de maturidade é 2.\\n\\nO critério está em outra página.\n"
    "D-002\tacusa\tTrês ferramentas fazem o mesmo trabalho\n"
    "D-002\tpassa\tTrês plataformas fazem o mesmo trabalho\n"
    "D-003\tacusa\tDuas enviam e-mail para a mesma base.\n"
    "D-003\tpassa\tDas 14 plataformas contratadas, duas enviam e-mail.\n"
    "D-004\tacusa\tA diretoria aprova o desligamento.\\n\\nDiagnóstico de martech.\n"
    "D-004\tpassa\tDiagnóstico de martech.\\n\\nA diretoria aprova o desligamento.\n"
)


def testar_dominio(tmp: Path) -> None:
    print("Domínio do projeto")
    modelos = HARNESS / "modelos/dominio"
    regras_do_modelo = [l for l in (modelos / "checagens.tsv").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    casos_do_modelo = [l for l in (modelos / "casos.tsv").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    confere("o template traz só o esqueleto: nenhuma regra e nenhum caso de domínio", len(regras_do_modelo) == 1 and len(casos_do_modelo) == 1, str(regras_do_modelo + casos_do_modelo))
    confere("o método do template está em branco", "PREENCHER" in (modelos / "dominio.md").read_text(encoding="utf-8") and "REGRAS = {}" in (modelos / "checagens_extra.py").read_text(encoding="utf-8"))
    na_raiz = RAIZ / "entregaveis/_dominio"
    confere("a raiz do template não tem domínio, registros nem materiais de projeto", not any((RAIZ / "entregaveis" / n).exists() for n in ("_dominio", "_projeto", "_intake")), str(na_raiz))

    projeto = tmp / "dominio"
    projeto.mkdir()
    instalar(projeto)
    dominio = projeto / "entregaveis/_dominio"
    script = projeto / "entregaveis/_harness/scripts/dominio.py"
    confere("a instalação cria _dominio com os cinco arquivos do esqueleto", sorted(a.name for a in dominio.iterdir()) == ["LEIA-ME.md", "casos.tsv", "checagens.tsv", "checagens_extra.py", "dominio.md"], str(list(dominio.iterdir())))
    vazio = rodar([PY, script], projeto)
    confere("sem regras, o teste do domínio passa e diz que não há regra", vazio.returncode == 0 and "nenhuma regra" in vazio.stdout, vazio.stdout + vazio.stderr)

    pasta = montar_exemplo(projeto)
    estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto)
    confere("o estado avisa que o domínio não foi calibrado", "calibrar-dominio" in estado.stdout, estado.stdout)
    aviso = validar(projeto, "--so", "dominio")
    confere("a validação avisa do domínio não calibrado, sem reprovar", aviso.returncode == 0 and "calibrar-dominio" in aviso.stdout, aviso.stdout)

    (dominio / "dominio.md").write_text(DOMINIO, encoding="utf-8")
    sem_regra = validar(projeto, "--so", "dominio")
    confere("domínio descrito e sem regra gera aviso", sem_regra.returncode == 0 and "nenhuma regra" in sem_regra.stdout, sem_regra.stdout)
    (dominio / "checagens.tsv").write_text(REGRAS_DO_DOMINIO, encoding="utf-8")
    sem_caso = rodar([PY, script], projeto)
    confere("regra sem caso de teste reprova", sem_caso.returncode == 1 and "falta caso de teste" in sem_caso.stdout and sem_caso.stdout.count("D-00") >= 4, sem_caso.stdout)
    confere("a validação do projeto reprova regra sem caso", validar(projeto, "--so", "dominio").returncode == 1)
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO, encoding="utf-8")
    provado = rodar([PY, script], projeto)
    confere("regras com os dois casos passam", provado.returncode == 0 and "4 regra(s) provada(s) em 9 caso(s)" in provado.stdout, provado.stdout + provado.stderr)
    lista = rodar([PY, script, "--listar"], projeto)
    confere("--listar mostra cada regra com os casos", lista.returncode == 0 and "D-001\tjunto" in lista.stdout and "3 caso(s)" in lista.stdout, lista.stdout)
    limpo = validar(projeto, "--so", "dominio")
    confere("o exemplo correto passa nas regras do domínio", limpo.returncode == 0 and "Nenhum erro e nenhum aviso" in limpo.stdout, limpo.stdout)
    confere("o estado para de avisar depois da calibração", "calibrar-dominio" not in rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout)

    def com(antes: str, depois: str, espera: str, nome: str, reprova: bool = True) -> None:
        (pasta / "conteudo.md").write_text(CONTEUDO.replace(antes, depois), encoding="utf-8")
        saida = validar(projeto, "--so", "dominio")
        confere(nome, (saida.returncode != 0) == reprova and espera in saida.stdout, saida.stdout[-500:])
        (pasta / "conteudo.md").write_text(CONTEUDO, encoding="utf-8")

    com("Para a diretoria de marketing.", "A nota de maturidade de dados é 2.", "D-001", "junto: acusa a nota sem o critério na mesma página")
    com("Para a diretoria de marketing.", "A nota de maturidade de dados é 2. O critério é a base única.", "Nenhum erro", "junto: aceita a nota com o critério", reprova=False)
    com("## 2. Duas plataformas de e-mail", "## 2. Duas ferramentas de e-mail", "D-002", "proibido: acusa o termo no título")
    com("Das 14 plataformas contratadas, duas", "Das 14 ferramentas contratadas, duas", "D-003", "proibido em títulos não olha o corpo, e obrigatório acusa a falta")
    com("## 1. Diagnóstico de martech", "## 1. Visão geral de martech", "D-004", "ordem: avisa do pedido antes do diagnóstico", reprova=False)
    (pasta / "briefing.md").write_text(BRIEFING.replace("tipo: apresentacao", "tipo: documento"), encoding="utf-8")
    com("## 2. Duas plataformas de e-mail", "## 2. Duas ferramentas de e-mail", "Nenhum erro", "aplica: a regra de apresentação não vale para outro tipo", reprova=False)
    (pasta / "briefing.md").write_text(BRIEFING, encoding="utf-8")

    # Regra com defeito e caso que contradiz a regra
    (dominio / "checagens.tsv").write_text(REGRAS_DO_DOMINIO + "D-005\tproibido\t*\ttudo\t(aberto\tNão feche.\terro\tM-001\nD-006\tsempre\t*\ttudo\tx\tTipo que não existe.\terro\tM-001\n", encoding="utf-8")
    defeito = rodar([PY, script], projeto)
    confere("expressão inválida e tipo desconhecido são apontados", defeito.returncode == 1 and "D-005: expressão inválida" in defeito.stdout and "D-006: tipo" in defeito.stdout, defeito.stdout)
    confere("regra com defeito não derruba a validação do entregável", validar(projeto, "diag", "--so", "dominio").returncode == 0)
    (dominio / "checagens.tsv").write_text(REGRAS_DO_DOMINIO, encoding="utf-8")
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO + "D-002\tpassa\tTrês ferramentas repetidas\nD-009\tacusa\tx\n", encoding="utf-8")
    contradiz = rodar([PY, script], projeto)
    confere("caso que contradiz a regra e caso de regra inexistente reprovam", contradiz.returncode == 1 and "esperava 'passa'" in contradiz.stdout and "'D-009' não existe" in contradiz.stdout, contradiz.stdout)
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO, encoding="utf-8")

    # Regra em Python
    (dominio / "checagens_extra.py").write_text(
        "import re\n\n\ndef parcelas(texto):\n    partes = [int(n) for n in re.findall(r'(\\d+)%', texto)]\n"
        "    if len(partes) > 1 and sum(partes) != 100:\n        return 'As parcelas não somam 100%.'\n    return None\n\n\nREGRAS = {'D-900': parcelas}\n",
        encoding="utf-8",
    )
    confere("regra em Python também exige os dois casos", rodar([PY, script], projeto).returncode == 1)
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO + "D-900\tacusa\tMídia paga 60% e mídia própria 30%.\nD-900\tpassa\tMídia paga 60% e mídia própria 40%.\n", encoding="utf-8")
    python_ok = rodar([PY, script], projeto)
    confere("regra em Python é provada pelos casos", python_ok.returncode == 0 and "5 regra(s)" in python_ok.stdout, python_ok.stdout + python_ok.stderr)
    com("Para a diretoria de marketing.", "Mídia paga leva 60% e mídia própria 30%.", "D-900", "regra em Python acusa no entregável")
    (dominio / "checagens_extra.py").write_text("REGRAS = {'D-900': lambda texto: 1 / 0}\nisto não é python\n", encoding="utf-8")
    quebrado = rodar([PY, script], projeto)
    confere("arquivo Python com defeito vira achado, sem derrubar o validador", quebrado.returncode == 1 and "não carrega" in quebrado.stdout and validar(projeto, "diag", "--so", "texto").returncode == 0, quebrado.stdout + quebrado.stderr)
    (dominio / "checagens_extra.py").write_text((modelos / "checagens_extra.py").read_text(encoding="utf-8"), encoding="utf-8")
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO, encoding="utf-8")

    # Hooks: o achado do domínio volta na gravação, e gravar uma regra roda os casos
    hooks = projeto / "entregaveis/_harness/hooks"

    def hook(nome: str, caminho: str) -> subprocess.CompletedProcess:
        dados = {"cwd": str(projeto), "session_id": "d1", "tool_name": "Write", "tool_input": {"file_path": caminho}}
        return rodar([PY, hooks / nome], projeto, json.dumps(dados))

    (pasta / "conteudo.md").write_text(CONTEUDO.replace("## 2. Duas plataformas de e-mail", "## 2. Duas ferramentas de e-mail"), encoding="utf-8")
    devolvido = hook("depois_de_gravar.py", "entregaveis/diag/conteudo.md")
    confere("depois de gravar: devolve o achado do domínio ao agente", devolvido.returncode == 2 and "[dominio]" in devolvido.stderr and "D-002" in devolvido.stderr, devolvido.stdout + devolvido.stderr)
    (pasta / "conteudo.md").write_text(CONTEUDO, encoding="utf-8")
    confere("depois de gravar: regras provadas passam", hook("depois_de_gravar.py", "entregaveis/_dominio/checagens.tsv").returncode == 0)
    (dominio / "casos.tsv").write_text("checagem\tespera\ttexto\n", encoding="utf-8")
    cobrado = hook("depois_de_gravar.py", "entregaveis/_dominio/checagens.tsv")
    confere("depois de gravar: regra sem caso volta ao agente", cobrado.returncode == 2 and "falta caso de teste" in cobrado.stderr, cobrado.stdout + cobrado.stderr)

    # Atualizar o kit não toca no domínio do projeto
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO, encoding="utf-8")
    instalar(projeto, "--atualizar")
    confere("--atualizar preserva o domínio do projeto", (dominio / "checagens.tsv").read_text(encoding="utf-8") == REGRAS_DO_DOMINIO and (dominio / "dominio.md").read_text(encoding="utf-8") == DOMINIO)


class _ServidorDeGit(http.server.BaseHTTPRequestHandler):
    """Responde como um servidor de git: um repositório aberto, um fechado e um que devolve uma página."""

    def do_GET(self):  # noqa: N802 - nome exigido pela biblioteca
        if self.path.startswith("/time/aberto.git/info/refs"):
            self.send_response(200)
            self.send_header("Content-Type", "application/x-git-upload-pack-advertisement")
            self.end_headers()
            self.wfile.write(b"001e# service=git-upload-pack\n0000")
        elif self.path.startswith("/time/pagina.git/info/refs"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html>entre</html>")
        else:
            self.send_response(401)
            self.end_headers()

    def log_message(self, *args):
        pass


def testar_repositorio(tmp: Path) -> None:
    print("Repositório local ou privado")
    if shutil.which("git") is None:
        print("  (sem git nesta máquina: testes do repositório pulados)")
        return
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _ServidorDeGit)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{servidor.server_address[1]}/time"
    try:
        projeto = tmp / "repositorio"
        projeto.mkdir()
        instalar(projeto)
        script = projeto / "entregaveis/_harness/scripts/repositorio.py"
        hooks = projeto / "entregaveis/_harness/hooks"

        def situacao() -> subprocess.CompletedProcess:
            return rodar([PY, script], projeto)

        def gravar(caminho: str) -> subprocess.CompletedProcess:
            dados = {"cwd": str(projeto), "session_id": "r1", "tool_name": "Write", "tool_input": {"file_path": caminho}}
            return rodar([PY, hooks / "antes_de_gravar.py"], projeto, json.dumps(dados))

        def comando(texto: str) -> subprocess.CompletedProcess:
            dados = {"cwd": str(projeto), "session_id": "r1", "tool_name": "Bash", "tool_input": {"command": texto}}
            return rodar([PY, hooks / "antes_de_comando.py"], projeto, json.dumps(dados))

        def remoto(url: str | None) -> None:
            rodar(["git", "remote", "remove", "origin"], projeto)
            if url:
                rodar(["git", "remote", "add", "origin", url], projeto)

        sem_git = situacao()
        confere("pasta sem git é aceita", sem_git.returncode == 0 and "Sem repositório remoto" in sem_git.stdout, sem_git.stdout + sem_git.stderr)
        rodar(["git", "init", "-q"], projeto)
        confere("git local sem remoto é aceito", situacao().returncode == 0 and gravar("entregaveis/_projeto/brief.md").returncode == 0)
        remoto("/srv/git/projeto.git")
        confere("remoto em disco conta como local", situacao().returncode == 0)

        # Remoto público
        remoto(f"{base}/aberto.git")
        publico = situacao()
        confere("remoto que entrega o clone sem credencial é público", publico.returncode == 1 and "PÚBLICO" in publico.stdout and "privado" in publico.stdout, publico.stdout + publico.stderr)
        barrado = gravar("entregaveis/_projeto/brief.md")
        confere("antes de gravar: bloqueia o brief em repositório público", barrado.returncode == 2 and "público" in barrado.stderr, barrado.stderr)
        confere("antes de gravar: bloqueia o domínio e o intake em repositório público", gravar("entregaveis/_dominio/dominio.md").returncode == 2 and gravar("entregaveis/_intake/registro.tsv").returncode == 2)
        confere("antes de gravar: bloqueia o briefing de um entregável novo", gravar("entregaveis/novo/briefing.md").returncode == 2)
        confere("antes de gravar: não barra o resto do repositório", gravar("src/app.py").returncode == 0 and gravar("entregaveis/_harness/REGRAS.md").returncode == 0 and gravar("README.md").returncode == 0)
        estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto)
        confere("o estado diz que o repositório é público", "PÚBLICO" in estado.stdout, estado.stdout)
        confere("antes de comando: sem projeto, o envio do template passa", comando("git push -u origin main").returncode == 0)
        confere("sem projeto, a validação não cobra o repositório", "[repositorio]" not in validar(projeto).stdout)
        negada = rodar([PY, script, "--confirmar", "é privado, pode seguir"], projeto)
        confere("um remoto público não aceita confirmação", negada.returncode == 1 and not (projeto / "entregaveis/_projeto/repositorio.tsv").exists(), negada.stdout)

        montar_exemplo(projeto)
        envio = comando("git add -A && git commit -m x && git push -u origin main")
        confere("antes de comando: com projeto, bloqueia o envio a repositório público", envio.returncode == 2 and "público" in envio.stderr, envio.stderr)
        confere("antes de comando: não olha os outros comandos", comando("git status").returncode == 0 and comando("python3 entregaveis/_harness/scripts/validar.py").returncode == 0)
        confere("antes de comando: bloqueia tornar o repositório público", comando("gh repo create cliente-x --public --source .").returncode == 2 and comando("gh repo edit --visibility public").returncode == 2)
        confere("antes de comando: deixa criar repositório privado", comando("gh repo create cliente-x --private --source .").returncode == 0)
        reprovado = validar(projeto, "--so", "repositorio")
        confere("com projeto, a validação reprova o repositório público", reprovado.returncode == 1 and "[repositorio]" in reprovado.stdout, reprovado.stdout)

        # Remoto privado
        remoto(f"{base}/fechado.git")
        privado = situacao()
        confere("remoto que pede identificação é privado", privado.returncode == 0 and "privado" in privado.stdout, privado.stdout + privado.stderr)
        confere("em repositório privado, a gravação e o envio passam", gravar("entregaveis/_projeto/brief.md").returncode == 0 and comando("git push origin main").returncode == 0 and validar(projeto, "--so", "repositorio").returncode == 0)

        # Remoto que não dá para verificar
        for nome, url in (("servidor que não responde", "http://127.0.0.1:1/time/sumido.git"), ("resposta que não é de git", f"{base}/pagina.git")):
            remoto(url)
            duvida = situacao()
            confere(f"{nome}: fica como não verificado e não é aceito", duvida.returncode == 1 and "não verificado" in duvida.stdout and "--confirmar" in duvida.stdout, duvida.stdout + duvida.stderr)
        confere("antes de gravar e antes de comando: bloqueiam o remoto não verificado", gravar("entregaveis/_projeto/brief.md").returncode == 2 and comando("git push").returncode == 2)
        confirmada = rodar([PY, script, "--confirmar", "sim, é o repositório privado do time"], projeto)
        registro = projeto / "entregaveis/_projeto/repositorio.tsv"
        confere("a confirmação do consultor fica registrada com as palavras dele", confirmada.returncode == 0 and "sim, é o repositório privado do time" in registro.read_text(encoding="utf-8"), confirmada.stdout + confirmada.stderr)
        confere("depois da confirmação, o remoto não verificado é aceito", situacao().returncode == 0 and gravar("entregaveis/_projeto/brief.md").returncode == 0 and comando("git push").returncode == 0)
        remoto(f"{base}/aberto.git")
        confere("a confirmação de um remoto não vale para outro", situacao().returncode == 1)

        codigo = (
            "import sys; sys.path.insert(0, 'entregaveis/_harness/scripts'); import repositorio as r; "
            "print(r.endereco('git@github.com:time/projeto.git'), r.endereco('ssh://git@git.exemplo.com:2222/time/projeto.git'), "
            "r.endereco('https://usuario@gitlab.com/grupo/sub/projeto.git'), r.endereco('../outro'), r.endereco('C:/git/projeto'))"
        )
        lidos = rodar([PY, "-c", codigo], projeto).stdout
        confere("lê endereços de remoto em ssh, https e disco", "('https', 'github.com', 'time/projeto') ('https', 'git.exemplo.com', 'time/projeto') ('https', 'gitlab.com', 'grupo/sub/projeto') None None" in lidos, lidos)
    finally:
        servidor.shutdown()


CONTEUDO_COM_VISUAIS = CONTEUDO.replace(
    "Das 14 plataformas contratadas, duas enviam e-mail para a mesma base.\n",
    """Das 14 plataformas contratadas, duas enviam e-mail para a mesma base.

- A plataforma A cobre **campanhas** e jornadas.
- A plataforma B cobre só campanhas.

```grafico
tipo: barras
destaque: E-mail
dados:
Função | Plataformas
E-mail | 2
Dados | 1
Mídia | 1
```
""",
).replace(
    "A diretora de marketing aprova o plano de migração.\n",
    """A diretora de marketing aprova o plano de migração.

| Quem | Faz o quê | Até quando |
| --- | --- | --- |
| Diretoria | Aprova o desligamento | Dezembro |
| Operações | Migra as jornadas | Fevereiro |
""",
)

DOCUMENTO = """# Diagnóstico de martech

A diretoria aprova o desligamento de uma plataforma de e-mail até dezembro.

## Duas plataformas fazem o mesmo trabalho

Das 14 plataformas contratadas, duas enviam e-mail para a mesma base [E-001].

- A plataforma A cobre **campanhas** e jornadas.
- A plataforma B cobre só campanhas.

| Função | Plataformas |
| --- | --- |
| E-mail | 2 |
| Dados | 1 |

## O pedido

1. A diretoria aprova o desligamento.
2. Operações migra as jornadas.
"""

PLANILHA = """# Planilha

## Perguntas que a planilha responde

- Que plataformas estão contratadas e quanto custam.

## Abas

| Aba | O que contém | Origem dos dados (E-nnn) | Data dos dados |
| --- | --- | --- | --- |
| Inventário | Uma linha por plataforma contratada | E-001 | 2026-10-01 |

## Dicionário de dados

| Aba | Coluna | Definição | Unidade | Regra de cálculo |
| --- | --- | --- | --- | --- |
| Inventário | Custo anual | Valor do contrato em doze meses | R$ | Soma das parcelas |

## Gráficos e análises

| Gráfico ou análise | Pergunta que responde | Achado que o título deve dizer |
| --- | --- | --- |
| Custo por plataforma | Onde está o gasto | A plataforma de dados custa mais que as duas de e-mail |

```grafico
aba: Inventário
tipo: colunas
titulo: A plataforma de dados custa mais que as duas de e-mail
categorias: Plataforma
valores: Custo anual
```
"""


def tem_pacote(nome: str) -> bool:
    try:
        __import__(nome)
        return True
    except ImportError:
        return False


def testar_gerador(tmp: Path) -> None:
    print("Gerador de arquivos")
    projeto = tmp / "gerador"
    projeto.mkdir()
    instalar(projeto)
    pasta = montar_exemplo(projeto)
    saida = pasta / "saida"
    materiais = projeto / "entregaveis/_intake/materiais"
    marca = projeto / "entregaveis/_projeto/marca.md"
    marca_em_branco = marca.read_text(encoding="utf-8")

    def gerar(*opcoes: str) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/gerar.py", *opcoes], projeto)

    (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")
    grande = CONTEUDO_COM_VISUAIS.replace("Mídia | 1\n", "".join(f"Função {n} | {n}\n" for n in range(40)))
    (pasta / "conteudo.md").write_text(grande, encoding="utf-8")
    confere("os dados de um bloco de gráfico não contam como texto da página", "[densidade]" not in validar(projeto, "diag").stdout)
    (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")
    confere("recusa formato que o script não gera", gerar("diag", "--formato", "html").returncode != 0)
    confere("recusa entregável que não existe", gerar("nada").returncode != 0)

    if not tem_pacote("pptx"):
        sem = gerar("diag")
        confere("sem o pacote, diz como instalar", sem.returncode != 0 and "pip install python-pptx" in sem.stdout + sem.stderr, sem.stdout + sem.stderr)
        print("  (python-pptx não está instalado: testes de PowerPoint pulados)")
    else:
        from pptx import Presentation
        from pptx.dml.color import RGBColor

        def textos(slide) -> str:
            return "\n".join(f.text_frame.text for f in slide.shapes if f.has_text_frame)

        (pasta / "storyline.md").write_text(STORYLINE.replace("aprovada: sim", "aprovada: nao"), encoding="utf-8")
        recusa = gerar("diag")
        confere("recusa gerar sem storyline aprovada", recusa.returncode != 0 and "storyline" in recusa.stdout + recusa.stderr and not saida.exists(), recusa.stdout + recusa.stderr)
        (pasta / "storyline.md").write_text(STORYLINE, encoding="utf-8")
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS + "\nA equipe aprova — e segue.\n", encoding="utf-8")
        reprovado = gerar("diag")
        confere("recusa gerar o que reprova nas checagens", reprovado.returncode != 0 and "[texto]" in reprovado.stdout and not (saida / "diag.pptx").exists(), reprovado.stdout + reprovado.stderr)
        rascunho = gerar("diag", "--rascunho")
        confere("--rascunho gera com a marca de rascunho em cada página", rascunho.returncode == 0 and all("RASCUNHO" in textos(s) for s in Presentation(str(saida / "diag-rascunho.pptx")).slides), rascunho.stdout + rascunho.stderr)
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")

        neutro = gerar("diag")
        confere("gera o PowerPoint e avisa que não há modelo", neutro.returncode == 0 and "desenho neutro" in neutro.stdout and (saida / "diag.pptx").is_file(), neutro.stdout + neutro.stderr)
        propriedades = Presentation(str(saida / "diag.pptx")).core_properties
        confere("no desenho neutro, o arquivo não leva o autor do arquivo de base da biblioteca", not propriedades.author and not propriedades.last_modified_by and not propriedades.comments, f"{propriedades.author!r} {propriedades.last_modified_by!r} {propriedades.comments!r}")
        slides = list(Presentation(str(saida / "diag.pptx")).slides)
        confere("uma página por slide, com o título de cada uma", [s.shapes.title.text_frame.text for s in slides] == ["Diagnóstico de martech", "Duas plataformas de e-mail fazem o mesmo trabalho", "A diretoria aprova o desligamento até dezembro"])
        confere("a capa leva o texto para o subtítulo", "Para a diretoria de marketing." in textos(slides[0]))
        confere("as notas vão para as notas de quem apresenta", "campanha de aniversário" in slides[1].notes_slide.notes_text_frame.text and "campanha de aniversário" not in textos(slides[1]))
        confere("a lista e o negrito chegam ao slide", "A plataforma B cobre só campanhas." in textos(slides[1]) and any(c.font.bold for f in slides[1].shapes if f.has_text_frame for par in f.text_frame.paragraphs for c in par.runs))
        graficos = [f.chart for f in slides[1].shapes if getattr(f, "has_chart", False)]
        confere("o bloco de gráfico vira gráfico nativo com os dados", len(graficos) == 1 and list(graficos[0].plots[0].categories) == ["E-mail", "Dados", "Mídia"] and list(graficos[0].plots[0].series[0].values) == [2, 1, 1])
        pontos = graficos[0].plots[0].series[0].points
        confere("o destaque fica na categoria citada e o resto em cinza", pontos[0].format.fill.fore_color.rgb == RGBColor.from_string("0B5CAD") and pontos[1].format.fill.fore_color.rgb == RGBColor.from_string("A9B3BD"))
        confere("a página que cita evidência ganha a linha de fonte", "Fonte: Inventário de contratos, 2026-10-01." in textos(slides[1]) and "Fonte:" not in textos(slides[2]))
        tabelas = [f.table for f in slides[2].shapes if getattr(f, "has_table", False)]
        confere("a tabela Markdown vira tabela", len(tabelas) == 1 and len(tabelas[0].rows) == 3 and tabelas[0].cell(2, 1).text == "Migra as jornadas")

        # Sobre um modelo: layouts com nome próprio e páginas de exemplo
        modelo = Presentation()
        for indice, nome in ((0, "Capa da casa"), (1, "Texto da casa"), (2, "Divisor da casa"), (5, "Só título da casa")):
            modelo.slide_layouts[indice].name = nome
        for _ in range(2):
            modelo.slides.add_slide(modelo.slide_layouts[1]).shapes.title.text_frame.text = "EXEMPLO DO MODELO"
        modelo.save(str(materiais / "modelo.pptx"))
        marca.write_text(
            marca_em_branco.replace("| Modelo de apresentação | | |", "| Modelo de apresentação | entregaveis/_intake/materiais/modelo.pptx | M-001 |")
            .replace("| Cores de destaque em gráficos | | |", "| Cores de destaque em gráficos | #C2410C e #D4D4D8 | M-001 |")
            .replace("| Tipo de página | Layout |\n| --- | --- |\n| | |", "| Tipo de página | Layout |\n| --- | --- |\n| pedido | Só título da casa |"),
            encoding="utf-8",
        )
        com_modelo = gerar("diag")
        slides = list(Presentation(str(saida / "diag.pptx")).slides)
        confere("gera sobre o modelo registrado na marca", com_modelo.returncode == 0 and "sobre modelo.pptx" in com_modelo.stdout and "desenho neutro" not in com_modelo.stdout, com_modelo.stdout + com_modelo.stderr)
        confere("as páginas de exemplo do modelo saem", len(slides) == 3 and not any("EXEMPLO DO MODELO" in textos(s) for s in slides))
        confere("o layout é escolhido pelo tipo de página e pela tabela da marca", [s.slide_layout.name for s in slides] == ["Capa da casa", "Texto da casa", "Só título da casa"], str([s.slide_layout.name for s in slides]))
        ponto = [f.chart for f in slides[1].shapes if getattr(f, "has_chart", False)][0].plots[0].series[0].points[0]
        confere("as cores do gráfico vêm da marca", ponto.format.fill.fore_color.rgb == RGBColor.from_string("C2410C"))
        lista = gerar("--layouts")
        confere("--layouts lista os layouts do modelo com os campos", lista.returncode == 0 and "Capa da casa: center_title" in lista.stdout, lista.stdout + lista.stderr)
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS.replace("<!-- tipo: capa; secao: ; fonte: ; recurso: -->", "<!-- tipo: capa; secao: ; fonte: ; recurso: ; layout: Divisor da casa -->"), encoding="utf-8")
        gerar("diag")
        confere("o campo layout da página vence a escolha automática", Presentation(str(saida / "diag.pptx")).slides[0].slide_layout.name == "Divisor da casa")
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")
        marca.write_text(marca_em_branco.replace("| Modelo de apresentação | | |", "| Modelo de apresentação | modelos/sumiu.pptx | M-001 |"), encoding="utf-8")
        sumido = gerar("diag")
        confere("modelo registrado e não encontrado é erro, não desenho neutro", sumido.returncode != 0 and "sumiu.pptx" in sumido.stdout + sumido.stderr)
        marca.write_text(marca_em_branco, encoding="utf-8")

        # Modelo exportado por outro programa: nomes e números de campo repetidos, propriedades ligadas fora do padrão
        import zipfile

        from pptx.util import Pt

        confere("o título que não cabe no campo tem a letra reduzida, e o que cabe fica como está",
                slides[0].shapes.title.text_frame.paragraphs[0].runs[0].font.size is None
                and (slides[1].shapes.title.text_frame.paragraphs[0].runs[0].font.size or Pt(99)) < Pt(44))
        estranho = Presentation()
        estranho.slide_layouts[0].name = estranho.slide_layouts[1].name = "Da casa"
        estranho.slide_layouts[1].placeholders[1]._element.ph.idx = 0
        estranho.save(str(tmp / "bruto.pptx"))
        padrao = b"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
        with zipfile.ZipFile(tmp / "bruto.pptx") as origem, zipfile.ZipFile(materiais / "estranho.pptx", "w", zipfile.ZIP_DEFLATED) as copia:
            for item in origem.infolist():
                dados = origem.read(item.filename)
                if item.filename == "_rels/.rels":
                    dados = dados.replace(padrao, padrao.replace(b"/package/", b"/officedocument/"))
                copia.writestr(item, dados)
        lista = gerar("--layouts", str(materiais / "estranho.pptx"))
        confere("--layouts numera os layouts e avisa dos nomes repetidos", "1. Da casa" in lista.stdout and "2. Da casa" in lista.stdout and "use o número" in lista.stdout, lista.stdout + lista.stderr)
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS.replace("<!-- tipo: capa; secao: ; fonte: ; recurso: -->", "<!-- tipo: capa; secao: ; fonte: ; recurso: ; layout: 6 -->"), encoding="utf-8")
        de_fora = gerar("diag", "--modelo", str(materiais / "estranho.pptx"))
        slides_de_fora = list(Presentation(str(saida / "diag.pptx")).slides)
        confere("o layout também é escolhido pelo número", de_fora.returncode == 0 and slides_de_fora[0].slide_layout.name == "Title Only", de_fora.stdout + de_fora.stderr)
        with zipfile.ZipFile(saida / "diag.pptx") as gerado:
            confere("as propriedades ligadas fora do padrão não são duplicadas", gerado.namelist().count("docProps/core.xml") == 1)
        campos = [f for f in slides_de_fora[1].placeholders]
        confere("com número de campo repetido, o corpo fica na posição do corpo, abaixo do título",
                len(campos) == 2 and campos[1].top >= campos[0].top + campos[0].height, str([(f.top, f.height) for f in campos]))
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")

        # Outro idioma
        (pasta / "conteudo.es.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")
        versao = gerar("diag", "--idioma", "es", "--rascunho")
        confere("--idioma gera a versão com o nome e o rótulo do idioma", versao.returncode == 0 and "Fuente: Inventário" in textos(Presentation(str(saida / "diag-es-rascunho.pptx")).slides[1]), versao.stdout + versao.stderr)
        (pasta / "conteudo.es.md").unlink()

        pdf = gerar("diag", "--pdf")
        confere("--pdf gera o PDF, ou diz por que não gerou", pdf.returncode == 0 and ((saida / "diag.pdf").is_file() or "PDF não foi gerado" in pdf.stdout), pdf.stdout + pdf.stderr)

    if not tem_pacote("docx"):
        print("  (python-docx não está instalado: testes de Word pulados)")
    else:
        from docx import Document

        (pasta / "documento.md").write_text(DOCUMENTO, encoding="utf-8")
        modelo = Document()
        modelo.add_paragraph("TEXTO DE EXEMPLO DO MODELO")
        modelo.sections[0].header.paragraphs[0].text = "Cabeçalho da casa"
        modelo.save(str(materiais / "modelo.docx"))
        marca.write_text(marca_em_branco.replace("| Modelo de documento | | |", "| Modelo de documento | entregaveis/_intake/materiais/modelo.docx | M-002 |"), encoding="utf-8")
        feito = gerar("diag", "--formato", "docx")
        confere("gera o Word sobre o modelo", feito.returncode == 0 and (saida / "diag.docx").is_file() and "sobre modelo.docx" in feito.stdout, feito.stdout + feito.stderr)
        doc = Document(str(saida / "diag.docx"))
        estilos = [(par.style.name, par.text) for par in doc.paragraphs if par.text.strip()]
        confere("título e seções usam os estilos do modelo", ("Title", "Diagnóstico de martech") in estilos and ("Heading 1", "O pedido") in estilos, str(estilos[:6]))
        confere("o texto de exemplo sai e o cabeçalho do modelo fica", not any("EXEMPLO" in texto for _, texto in estilos) and doc.sections[0].header.paragraphs[0].text == "Cabeçalho da casa")
        confere("listas e tabela chegam ao documento", ("List Bullet", "A plataforma B cobre só campanhas.") in estilos and ("List Number", "Operações migra as jornadas.") in estilos and len(doc.tables) == 1 and doc.tables[0].cell(1, 1).text == "2")
        confere("as evidências citadas formam a seção de fontes", ("Heading 1", "Fontes") in estilos and any(texto.startswith("E-001: Inventário de contratos") for _, texto in estilos))
        marca.write_text(marca_em_branco, encoding="utf-8")
        (pasta / "documento.md").unlink()

    if not tem_pacote("openpyxl"):
        print("  (openpyxl não está instalado: testes de Excel pulados)")
    else:
        from openpyxl import load_workbook

        (pasta / "planilha.md").write_text(PLANILHA, encoding="utf-8")
        (pasta / "dados").mkdir()
        (pasta / "dados/inventario.csv").write_text("Plataforma;Função;Custo anual;Usuários\nA;E-mail;120000;14\nB;E-mail;95000,50;6\nC;Dados;300000;22\n", encoding="utf-8")
        feito = gerar("diag", "--formato", "xlsx")
        confere("gera o Excel", feito.returncode == 0 and (saida / "diag.xlsx").is_file(), feito.stdout + feito.stderr)
        livro = load_workbook(str(saida / "diag.xlsx"))
        confere("a planilha tem leitura, gráficos, dados e dicionário", livro.sheetnames == ["Leitura", "Gráficos", "Inventário", "Dicionário"], str(livro.sheetnames))
        dados = livro["Inventário"]
        confere("os números entram como números, com a vírgula decimal lida", dados["C2"].value == 120000 and dados["C3"].value == 95000.5 and dados["A2"].value == "A")
        confere("a aba de dados tem cabeçalho fixo e filtro", dados.freeze_panes == "A2" and dados.auto_filter.ref == "A1:D4" and dados["A1"].font.bold)
        confere("a aba de leitura diz a pergunta e a origem dos dados", any("Que plataformas estão contratadas" in str(c.value) for c in livro["Leitura"]["A"]) and any("Inventário de contratos" in str(c.value) for linha in livro["Leitura"].iter_rows() for c in linha))
        confere("o gráfico é nativo e o dicionário traz a definição", len(livro["Gráficos"]._charts) == 1 and livro["Dicionário"]["C2"].value == "Valor do contrato em doze meses")
        (pasta / "planilha.md").write_text(PLANILHA.replace("valores: Custo anual", "valores: Custo mensal"), encoding="utf-8")
        errado = gerar("diag", "--formato", "xlsx")
        confere("gráfico que cita coluna inexistente é erro", errado.returncode != 0 and "Custo mensal" in errado.stdout + errado.stderr)


def testar_fases(tmp: Path) -> None:
    print("Fases do projeto")
    projeto = tmp / "fases"
    projeto.mkdir()
    instalar(projeto)
    base = projeto / "entregaveis"
    brief = base / "_projeto/brief.md"
    registro = base / "_projeto/fases.md"

    def fase(*opcoes: str) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/fase.py", *opcoes], projeto)

    cedo = fase("--nova", "--tipo", "mídia", "--origem", "vendida")
    confere("não abre fase em projeto que não foi iniciado", cedo.returncode != 0 and "iniciar-projeto" in cedo.stdout + cedo.stderr and not (base / "_projeto/fases").exists(), cedo.stdout + cedo.stderr)
    pasta = montar_exemplo(projeto)
    brief.write_text(BRIEF.replace("tipo: assessment de martech e adtech", "tipo: proposta") + "\n## Regra da casa\n\nSeção própria do projeto.\n", encoding="utf-8")
    antes = brief.read_text(encoding="utf-8")
    confere("um projeto sem o campo fase está na fase 1", "Fase 2" not in rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout)
    primeira = fase("--data", "2026-11-01")
    confere("registra a fase 1 com o tipo do brief", primeira.returncode == 0 and "| 1 | 2026-11-01 |  | proposta |" in registro.read_text(encoding="utf-8"), primeira.stdout + primeira.stderr)
    confere("não registra a fase 1 duas vezes", registro.read_text(encoding="utf-8").count("| 1 |") == 1 and fase().returncode == 0 and registro.read_text(encoding="utf-8").count("| 1 |") == 1)
    confere("recusa pacote que não existe", fase("--nova", "--tipo", "mídia", "--pacotes", "nao-existe", "--origem", "vendida").returncode != 0 and brief.read_text(encoding="utf-8") == antes)
    confere("pede o tipo e a origem da fase nova", fase("--nova", "--tipo", "mídia").returncode != 0 and brief.read_text(encoding="utf-8") == antes)
    simulada = fase("--nova", "--tipo", "assessment de martech e adtech", "--pacotes", "martech-adtech", "--origem", "proposta vendida", "--simular")
    confere("--simular mostra a mudança e não grava", simulada.returncode == 0 and "Nada foi gravado" in simulada.stdout and "diag" in simulada.stdout and brief.read_text(encoding="utf-8") == antes and not (base / "_projeto/fases").exists(), simulada.stdout + simulada.stderr)

    aberta = fase("--nova", "--tipo", "assessment de martech e adtech", "--pacotes", "martech-adtech", "--origem", "proposta vendida | em reunião", "--data", "2026-11-20")
    guarda = base / "_projeto/fases/fase-1"
    novo = brief.read_text(encoding="utf-8")
    meta = dict(l.split(":", 1) for l in novo.split("---")[1].strip().splitlines())
    confere("abre a fase nova", aberta.returncode == 0 and "Fase nova aberta" in aberta.stdout, aberta.stdout + aberta.stderr)
    confere("guarda o brief da fase encerrada, igual ao que era", (guarda / "brief.md").read_text(encoding="utf-8") == antes)
    confere("o brief passa a ser o da fase nova", meta["fase"].strip() == "2" and meta["tipo"].strip() == "assessment de martech e adtech" and meta["pacotes"].strip() == "martech-adtech" and meta["iniciado"].strip() == "sim", str(meta))
    confere("as seções da fase voltam ao modelo e as outras ficam", "Um diagnóstico das plataformas" not in novo and "A diretoria escolhe" not in novo and novo.count("PREENCHER") == 2 and "Seção própria do projeto." in novo, novo[-600:])
    linhas = registro.read_text(encoding="utf-8")
    confere("o registro fecha a fase 1 e abre a 2, sem quebrar a tabela", "| 1 | 2026-11-01 | 2026-11-20 | proposta |" in linhas and "| Encerrada |" in linhas and "| 2 | 2026-11-20 |  | assessment de martech e adtech | martech-adtech | proposta vendida / em reunião | Em andamento |" in linhas, linhas[-400:])
    passagem = (guarda / "passagem.md").read_text(encoding="utf-8")
    confere("a passagem nasce com as fases e os entregáveis em aberto", "da_fase: 1" in passagem and "para_a_fase: 2" in passagem and "| diag | " in passagem and "PREENCHER" in passagem, passagem[:300])
    confere("o pacote da fase nova é ativado", (projeto / ".claude/skills/pacote-martech-adtech/SKILL.md").is_file())
    confere("nada do que existia é apagado", (pasta / "conteudo.md").read_text(encoding="utf-8") == CONTEUDO and "E-001" in (base / "_projeto/evidencias.tsv").read_text(encoding="utf-8"))

    estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout
    confere("o estado mostra a fase, a passagem por escrever e o brief por fechar", "Fase 2 do projeto, aberta por: proposta vendida" in estado and "passagem da fase 1 para a 2" in estado and "brief da fase 2" in estado, estado)
    confere("o estado marca o entregável que veio da fase anterior", "- diag (fase 1, " in estado, estado)
    achados = validar(projeto).stdout
    confere("a validação cobra o brief e a passagem da fase nova", "[projeto]" in achados and "passagem da fase 1" in achados, achados)
    criado = rodar([PY, "entregaveis/_harness/scripts/preparar.py", "--entregavel", "relatorio", "--tipo", "documento", "--veiculo", "documento", "--formato", "docx"], projeto)
    confere("um entregável novo nasce na fase atual", criado.returncode == 0 and "fase: 2" in (base / "relatorio/briefing.md").read_text(encoding="utf-8"))
    (pasta / "briefing.md").write_text(BRIEFING.replace("estado: revisao", "estado: entregue").replace("estado: redacao", "estado: entregue"), encoding="utf-8")
    rodar([PY, "entregaveis/_harness/scripts/preparar.py", "--entregavel", "diag"], projeto)
    confere("preparar de novo um entregável antigo não troca a fase dele", "fase: 2" not in (pasta / "briefing.md").read_text(encoding="utf-8"))
    estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout
    confere("o entregue de fase anterior vira uma linha de história", "Entregues em fases anteriores: 1" in estado and "- diag (" not in estado, estado)

    # Com a passagem e o brief escritos, a fase está aberta de verdade
    (guarda / "passagem.md").write_text(re.sub(r"PREENCHER[^\n|]*", "Proposta vendida em reunião com a diretoria.", passagem), encoding="utf-8")
    brief.write_text(re.sub(r"PREENCHER[^\n|]*", "Assessment das plataformas de marketing.", novo), encoding="utf-8")
    estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout
    confere("com a passagem e o brief escritos, o estado só mostra a fase", "Fase 2 do projeto" in estado and "passagem da fase" not in estado and "brief da fase" not in estado, estado)
    terceira = fase("--nova", "--tipo", "processos agênticos", "--pacotes", "processos-agenticos", "--origem", "extensão contratada", "--data", "2026-12-10")
    linhas = registro.read_text(encoding="utf-8")
    confere("a extensão abre a fase 3 e guarda o brief da 2", terceira.returncode == 0 and (base / "_projeto/fases/fase-2/brief.md").is_file() and "Assessment das plataformas" in (base / "_projeto/fases/fase-2/brief.md").read_text(encoding="utf-8") and linhas.count("| Encerrada |") == 2 and "| 3 | 2026-12-10 |" in linhas, terceira.stdout + terceira.stderr)
    confere("o brief guardado da fase 1 não muda", (guarda / "brief.md").read_text(encoding="utf-8") == antes)
    mostra = fase()
    confere("mostra as três fases", mostra.stdout.count("Fase ") == 3 and "extensão contratada" in mostra.stdout, mostra.stdout)

    hooks = projeto / "entregaveis/_harness/hooks"
    aviso = rodar([PY, hooks / "mensagem.py"], projeto, json.dumps({"cwd": str(projeto), "prompt": "a proposta foi vendida, agora começa o assessment"}))
    confere("mensagem: avisa quando o pedido parece mudança de fase", "evoluir-projeto" in aviso.stdout and "registrar-decisao" in aviso.stdout, aviso.stdout)
    comum_ = rodar([PY, hooks / "mensagem.py"], projeto, json.dumps({"cwd": str(projeto), "prompt": "inclua uma página sobre mídia paga"}))
    confere("mensagem: não avisa de fase em pedido comum", "evoluir-projeto" not in comum_.stdout, comum_.stdout)


def testar_ambientes(tmp: Path) -> None:
    print("Outros ambientes")
    ambientes = HARNESS / "ambientes"
    instrucoes = (ambientes / "instrucoes.md").read_text(encoding="utf-8")
    conhecimento = sorted(a.name for a in (ambientes / "conhecimento").iterdir())
    confere("as instruções cabem no menor limite dos ambientes", len(instrucoes) <= 8000, f"{len(instrucoes)} caracteres")
    confere("os arquivos de conhecimento são .txt e cabem em um agente", all(n.endswith(".txt") for n in conhecimento) and len(conhecimento) <= 20, str(conhecimento))
    confere("o conjunto básico e um pacote cabem em cinco arquivos", len([n for n in conhecimento if not n.startswith("pacote-")]) == 4)
    pacotes = sorted(p.name for p in (HARNESS / "pacotes").iterdir() if (p / "PACOTE.md").is_file())
    confere("há um arquivo de conhecimento por pacote", [n for n in conhecimento if n.startswith("pacote-")] == [f"pacote-{p}.txt" for p in pacotes])
    procedimentos = (ambientes / "conhecimento/1-procedimentos.txt").read_text(encoding="utf-8")
    so_com_arquivos = {"adotar-projeto", "atualizar-harness", "usar-outro-ambiente"}
    for skill in sorted(p.name for p in (RAIZ / ".claude/skills").iterdir() if p.is_dir()):
        if skill in so_com_arquivos:
            confere(f"{skill}: fica fora dos procedimentos de outros ambientes", f"## {skill}\n" not in procedimentos)
        else:
            confere(f"{skill}: está nos procedimentos e nas instruções", f"## {skill}\n" in procedimentos and f"`{skill}`" in instrucoes)
    for nome in ("1-procedimentos", "2-metodo-e-texto", "3-formatos-e-visual", "4-modelos", "5-projeto", "pacote-NOME"):
        confere(f"as instruções dizem para que serve {nome}", f"`{nome}`" in instrucoes)
    em_dia = rodar([PY, "entregaveis/_harness/scripts/empacotar.py", "--conferir"], RAIZ)
    confere("os arquivos de conhecimento estão em dia com o método e as skills", em_dia.returncode == 0, em_dia.stdout + em_dia.stderr)

    projeto = tmp / "ambientes"
    projeto.mkdir()
    (projeto / ".git").mkdir()
    instalar(projeto)

    def empacotar(*opcoes: str) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/empacotar.py", *opcoes], projeto)

    confere("a cópia instalada também está em dia", empacotar("--conferir").returncode == 0)
    cedo = empacotar("--projeto")
    confere("não monta o pacote de um projeto que não foi iniciado", cedo.returncode != 0 and not (projeto / "entregaveis/_ambiente").exists(), cedo.stdout + cedo.stderr)
    pasta = montar_exemplo(projeto)
    rodar([PY, "entregaveis/_harness/scripts/preparar.py", "--pacote", "martech-adtech"], projeto)
    montado = empacotar("--projeto")
    saida = projeto / "entregaveis/_ambiente"
    nomes = sorted(a.name for a in saida.iterdir()) if saida.is_dir() else []
    confere("monta o pacote do projeto com as instruções, o método e o projeto", montado.returncode == 0 and {"instrucoes.txt", "1-procedimentos.txt", "2-metodo-e-texto.txt", "3-formatos-e-visual.txt", "4-modelos.txt", "5-projeto.txt"} <= set(nomes), montado.stdout + montado.stderr)
    confere("leva só os pacotes do projeto", [n for n in nomes if n.startswith("pacote-")] == ["pacote-martech-adtech.txt"], str(nomes))
    do_projeto = (saida / "5-projeto.txt").read_text(encoding="utf-8")
    confere("o arquivo do projeto traz o brief, as evidências e a storyline", "Varejista Exemplo" in do_projeto and "E-001" in do_projeto and "Duas plataformas de e-mail fazem o mesmo trabalho" in do_projeto)
    confere("a lista de nomes confidenciais fica de fora", "Projeto Girassol" not in "".join((saida / n).read_text(encoding="utf-8") for n in nomes))
    confere("avisa que o pacote leva material do projeto", "regras de material" in montado.stdout)
    confere("o pacote do projeto fica fora do git", "entregaveis/_ambiente/" in (projeto / ".gitignore").read_text(encoding="utf-8"))
    outra = tmp / "pacote-fora"
    outra.mkdir()
    (outra / "meu.txt").write_text("meu arquivo\n", encoding="utf-8")
    fora = empacotar("--projeto", "--saida", str(outra))
    confere("--saida grava em outra pasta sem apagar o que estava lá", fora.returncode == 0 and (outra / "5-projeto.txt").is_file() and (outra / "meu.txt").read_text(encoding="utf-8") == "meu arquivo\n", fora.stdout + fora.stderr)
    texto = projeto / "entregaveis/_harness/metodo/texto.md"
    texto.write_text(texto.read_text(encoding="utf-8") + "\nUma prática nova.\n", encoding="utf-8")
    atrasado = empacotar("--conferir")
    confere("acusa o arquivo de conhecimento fora de dia", atrasado.returncode == 1 and "2-metodo-e-texto.txt" in atrasado.stdout, atrasado.stdout + atrasado.stderr)
    refeito = empacotar()
    confere("refaz só o arquivo que mudou", refeito.returncode == 0 and "2-metodo-e-texto.txt" in refeito.stdout and "1-procedimentos.txt" not in refeito.stdout and empacotar("--conferir").returncode == 0, refeito.stdout + refeito.stderr)


def testar_pacotes(tmp: Path) -> None:
    print("Pacotes")
    pacotes = sorted(p for p in (HARNESS / "pacotes").iterdir() if p.is_dir())
    confere("há ao menos um pacote", bool(pacotes))
    leia_me = (HARNESS / "pacotes" / "LEIA-ME.md").read_text(encoding="utf-8")
    for pacote in pacotes:
        nome = pacote.name
        for arquivo in ("PACOTE.md", "skill/SKILL.md"):
            confere(f"{nome}: tem {arquivo}", (pacote / arquivo).is_file())
        de_metodo = [a for a in ("pedido-de-dados.tsv", "entrevistas.md", "glossario.tsv") if (pacote / a).is_file()]
        confere(f"{nome}: traz os três arquivos de conteúdo, ou só os controles de governança", len(de_metodo) == 3 or (not de_metodo and (pacote / "controles.tsv").is_file()), str(de_metodo))
        confere(f"{nome}: está na lista de pacotes disponíveis", f"`{nome}`" in leia_me)
        skill = (pacote / "skill/SKILL.md").read_text(encoding="utf-8")
        cabecalho = skill.split("---\n")[1]
        campos = dict(re.findall(r"^(\w+): (.*)$", cabecalho, flags=re.MULTILINE))
        descricao = campos.get("description", "")
        confere(f"{nome}: a skill se chama pacote-{nome}", campos.get("name") == f"pacote-{nome}")
        confere(f"{nome}: a descrição da skill começa por 'Use' e é um valor YAML simples", descricao.startswith("Use ") and ": " not in descricao and " #" not in descricao and len(descricao) <= 1024)
        confere(f"{nome}: a skill traz a marca de origem do kit", "origem: harness-de-entregaveis" in cabecalho)
        titulos = set(re.findall(r"^#{2,3} (.+)$", (pacote / "PACOTE.md").read_text(encoding="utf-8"), flags=re.MULTILINE))
        for secao in re.findall(r'"([^"]+)"', " ".join(skill.split())):
            confere(f"{nome}: a seção '{secao}' citada na skill existe em PACOTE.md", secao in titulos)
        for arquivo, colunas, minimo in (("pedido-de-dados.tsv", 5, 5), ("glossario.tsv", 4, 5), ("controles.tsv", 6, 2)):
            if not (pacote / arquivo).is_file():
                continue
            linhas = [l for l in (pacote / arquivo).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
            tortas = [l for l in linhas if len(l.split("\t")) != colunas]
            confere(f"{nome}: {arquivo} tem {colunas} colunas em toda linha", len(linhas) > minimo and not tortas, "\n".join(tortas[:3]))
        if (pacote / "pedido-de-dados.tsv").is_file():
            prioridades = {l.split("\t")[4] for l in (pacote / "pedido-de-dados.tsv").read_text(encoding="utf-8").splitlines()[4:] if "\t" in l}
            confere(f"{nome}: as prioridades do pedido de dados são as três previstas", prioridades <= {"essencial", "importante", "complementar"}, str(prioridades))
        if (pacote / "controles.tsv").is_file():
            linhas = [l.split("\t") for l in (pacote / "controles.tsv").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")][1:]
            confere(f"{nome}: todo controle vale sempre ou em uma condição escrita, antes de uma etapa que existe", all((l[2] == "sempre" or l[2].startswith("quando ")) and l[3] in ("storyline", "storyboard", "redacao", "revisao", "envio") for l in linhas), str([l[:4] for l in linhas]))
            confere(f"{nome}: todo controle diz o que registra e que evidência o fecha", all(l[1] and l[4] and l[5] for l in linhas))
            guia = (pacote / "PACOTE.md").read_text(encoding="utf-8")
            confere(f"{nome}: PACOTE.md apresenta cada controle pelo nome", "## Controles de governança" in guia and all(f"| {l[1]} |" in guia for l in linhas), str([l[1] for l in linhas if f"| {l[1]} |" not in guia]))
            confere(f"{nome}: a skill do pacote manda conferir os controles", "--controles" in skill and "--cumprido" in skill)

    todos_os_codigos = [l.split("\t")[0] for a in sorted((HARNESS / "pacotes").glob("*/controles.tsv")) for l in a.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")][0:]
    todos_os_codigos = [c for c in todos_os_codigos if c != "codigo"]
    confere("nenhum código de controle se repete entre os pacotes", len(todos_os_codigos) == len(set(todos_os_codigos)) and len(todos_os_codigos) >= 10, str(todos_os_codigos))
    so_governanca = HARNESS / "pacotes" / "processos-midia"
    texto_do_pacote = (so_governanca / "PACOTE.md").read_text(encoding="utf-8")
    confere("o pacote de processos de mídia traz só governança", not any((so_governanca / a).exists() for a in ("pedido-de-dados.tsv", "entrevistas.md", "glossario.tsv")) and "## Frameworks" not in texto_do_pacote and "## Esqueletos" not in texto_do_pacote and "## O que este pacote não traz" in texto_do_pacote)

    projeto = tmp / "pacotes"
    projeto.mkdir()
    instalar(projeto, "--pasta", "consultoria")
    preparar = [PY, "consultoria/_harness/scripts/preparar.py"]
    inexistente = rodar(preparar + ["--pacote", "nao-existe"], projeto)
    confere("ativar pacote que não existe falha e lista os disponíveis", inexistente.returncode != 0 and "martech-adtech" in inexistente.stdout + inexistente.stderr, inexistente.stdout + inexistente.stderr)
    ativacao = rodar(preparar + ["--pacote", "martech-adtech"], projeto)
    skill = projeto / ".claude/skills/pacote-martech-adtech/SKILL.md"
    confere("ativar o pacote copia a skill", ativacao.returncode == 0 and skill.is_file(), ativacao.stdout + ativacao.stderr)
    confere("a skill ativada aponta para a pasta deste projeto", skill.is_file() and "consultoria/_harness/pacotes/martech-adtech/" in skill.read_text(encoding="utf-8") and "entregaveis/" not in skill.read_text(encoding="utf-8"))
    glossario = (projeto / "consultoria/_projeto/glossario.tsv").read_text(encoding="utf-8")
    confere("ativar o pacote soma os termos ao glossário", "\nCDP\t" in glossario and "\nDSP\t" in glossario)
    confere("ativar o pacote preenche o campo do brief", "pacotes: martech-adtech\n" in (projeto / "consultoria/_projeto/brief.md").read_text(encoding="utf-8"))
    rodar(preparar + ["--pacote", "martech-adtech"], projeto)
    depois = (projeto / "consultoria/_projeto/glossario.tsv").read_text(encoding="utf-8")
    confere("ativar de novo não repete termos nem o nome no brief", depois == glossario and "pacotes: martech-adtech\n" in (projeto / "consultoria/_projeto/brief.md").read_text(encoding="utf-8"))
    estado = rodar([PY, "consultoria/_harness/scripts/validar.py"], projeto)
    confere("as checagens rodam com o pacote ativo", estado.returncode == 0, estado.stdout + estado.stderr)
    skill.write_text(skill.read_text(encoding="utf-8") + "\nlinha de versão antiga\n", encoding="utf-8")
    instalar(projeto, "--pasta", "consultoria", "--atualizar")
    confere("--atualizar renova a skill do pacote ativado", "linha de versão antiga" not in skill.read_text(encoding="utf-8"))
    todos = tmp / "todos-os-pacotes"
    todos.mkdir()
    instalar(todos)
    for pacote in pacotes:
        rodar([PY, "entregaveis/_harness/scripts/preparar.py", "--pacote", pacote.name], todos)
    ativos = (todos / "entregaveis/_projeto/brief.md").read_text(encoding="utf-8")
    confere("um projeto pode ativar todos os pacotes", all((todos / f".claude/skills/pacote-{p.name}/SKILL.md").is_file() and p.name in ativos for p in pacotes), ativos[:300])
    chaves = [tuple(l.split("\t")[i] for i in (0, 3)) for l in (todos / "entregaveis/_projeto/glossario.tsv").read_text(encoding="utf-8").splitlines() if "\t" in l and not l.startswith("#")]
    confere("pacotes somados não repetem termos no glossário", len(chaves) == len({(t.lower(), i) for t, i in chaves}), str([c for c in chaves if chaves.count(c) > 1][:5]))
    testar_controles(tmp)
    sem_pacote = tmp / "sem-pacote"
    sem_pacote.mkdir()
    instalar(sem_pacote)
    confere("a skill de pacote não é instalada em projeto que não o ativou", not (sem_pacote / ".claude/skills/pacote-martech-adtech").exists())


def testar_controles(tmp: Path) -> None:
    """Os controles de governança que um pacote traz: situação, portão, lista do dia, checagem e envio."""
    projeto = tmp / "controles"
    projeto.mkdir()
    (projeto / ".git").mkdir()
    instalar(projeto)
    base = projeto / "entregaveis"
    reg = base / "_projeto"
    montar_exemplo(projeto)
    hoje = "2026-03-02"

    def gov(*args) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/governanca.py", *args, "--hoje", hoje], projeto)

    def lista() -> str:
        return rodar([PY, "entregaveis/_harness/scripts/rotina.py", "--lista", "--hoje", hoje], projeto).stdout

    def estado() -> str:
        return rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout

    def etapa(nome: str) -> None:
        briefing = base / "diag/briefing.md"
        briefing.write_text(re.sub(r"^estado: .*$", f"estado: {nome}", briefing.read_text(encoding="utf-8"), flags=re.MULTILINE), encoding="utf-8")

    def linha_de(ident: str) -> str:
        return next((l for l in (reg / "controles.tsv").read_text(encoding="utf-8").splitlines() if l.startswith(ident + "\t")), "")

    def checagem() -> subprocess.CompletedProcess:
        return validar(projeto, "--so", "governanca")

    gov("--nivel", "enxuto")
    sem = gov("--controles")
    confere("sem pacote ativo, não há controle e o estado não fala deles", "Nenhum pacote ativo traz controles" in sem.stdout and "Controles do tipo de projeto" not in estado() and "Controle do tipo de projeto" not in lista(), sem.stdout)
    rodar([PY, "entregaveis/_harness/scripts/preparar.py", "--pacote", "treinamento"], projeto)
    confere("pacote sem controles não cria controle", "Nenhum pacote ativo traz controles" in gov("--controles").stdout and "treinamento" in gov("--controles").stdout)
    etapa("briefing")
    ativado = rodar([PY, "entregaveis/_harness/scripts/preparar.py", "--pacote", "processos-midia"], projeto)
    confere("ativar o pacote só de governança copia a skill, avisa dos controles e não mexe no glossário", ativado.returncode == 0 and (projeto / ".claude/skills/pacote-processos-midia/SKILL.md").is_file() and "6 controle(s) de governança" in ativado.stdout and "termos do pacote" not in ativado.stdout and "treinamento, processos-midia" in (reg / "brief.md").read_text(encoding="utf-8"), ativado.stdout + ativado.stderr)
    todos = gov("--controles").stdout
    confere("a lista mostra os seis controles, quatro pendentes e dois a confirmar", todos.count("Situação: pendente.") == 4 and todos.count("Situação: a confirmar.") == 2 and "taxonomia-e-metricas (processos-midia)" in todos and "Fecha com: Decisão registrada (D-nnn)" in todos, todos)
    confere("o estado conta os controles pendentes e os que falta confirmar", "Controles do tipo de projeto: 6, com 4 pendente(s) e 2 a confirmar" in estado(), estado())

    # O condicional é perguntado; o pendente só quando o entregável chega à etapa.
    no_briefing = lista()
    confere("a lista do dia pergunta pelo controle condicional", "Plano e registro de entrevistas e workshops [entrevistas-e-workshops]. Ele vale quando o levantamento ouve pessoas de mais de uma área" in no_briefing and "Vale neste projeto?" in no_briefing, no_briefing)
    confere("antes da etapa, o controle pendente não é cobrado", "sem evidência" not in no_briefing and "Controle do tipo de projeto" not in checagem().stdout and checagem().returncode == 0, no_briefing + checagem().stdout)
    etapa("storyline")
    na_storyline = lista()
    confere("na etapa, o controle pendente é cobrado, com o que o fecha", "Controle do tipo de projeto sem evidência: Taxonomia de campanhas e dicionário de métricas aprovados [taxonomia-e-metricas]" in na_storyline and "diag já chegou lá" in na_storyline and "papeis-e-niveis-de-servico" not in na_storyline, na_storyline)
    aviso = checagem()
    confere("checagem: controle pendente na etapa é aviso, e não erro", aviso.returncode == 0 and "AVISO" in aviso.stdout and "taxonomia-e-metricas" in aviso.stdout and "entrevistas-e-workshops" not in aviso.stdout, aviso.stdout)

    trocar_fase = (reg / "brief.md").read_text(encoding="utf-8")
    (reg / "brief.md").write_text(trocar_fase.replace("iniciado: sim", "fase: 2\niniciado: sim", 1), encoding="utf-8")
    confere("entregável de fase anterior não cobra controle", "sem evidência" not in lista() and "Vale neste projeto?" in lista(), lista())
    (reg / "brief.md").write_text(trocar_fase, encoding="utf-8")

    # As respostas.
    confere("controle que os pacotes ativos não trazem é recusado", gov("--controle", "criterios-de-avaliacao", "--pendente").returncode == 1 and "Os pacotes ativos não trazem o controle 'criterios-de-avaliacao'" in gov("--controle", "criterios-de-avaliacao", "--pendente").stdout and not linha_de("criterios-de-avaliacao"))
    confere("a resposta é uma só", gov("--controle", "taxonomia-e-metricas").returncode == 2 and gov("--controle", "taxonomia-e-metricas", "--pendente", "--nao-se-aplica", "--motivo", "x").returncode == 2)
    confere("cumprido pede a evidência e quem confirmou", gov("--controle", "taxonomia-e-metricas", "--cumprido", "--quem", "Gerente de mídia").returncode == 2 and gov("--controle", "taxonomia-e-metricas", "--cumprido", "--evidencia", "D-004").returncode == 2 and not linha_de("taxonomia-e-metricas"))
    cumprido = gov("--controle", "taxonomia-e-metricas", "--cumprido", "--evidencia", "D-004", "--quem", "Gerente de mídia")
    confere("o controle cumprido guarda a evidência, quem confirmou e a data", cumprido.returncode == 0 and linha_de("taxonomia-e-metricas") == f"taxonomia-e-metricas\tcumprido\tD-004\tGerente de mídia\t{hoje}\t", linha_de("taxonomia-e-metricas"))
    confere("controle cumprido sai da lista do dia e da checagem", "taxonomia-e-metricas" not in lista() and "taxonomia-e-metricas" not in checagem().stdout and "com 3 pendente(s) e 2 a confirmar" in estado())
    confere("não se aplica pede o motivo", gov("--controle", "impacto-da-mudanca", "--nao-se-aplica").returncode == 2 and not linha_de("impacto-da-mudanca"))
    dispensado = gov("--controle", "impacto-da-mudanca", "--nao-se-aplica", "--motivo", "O processo novo não muda o trabalho de ninguém")
    confere("o controle que não se aplica sai da lista, com o motivo guardado", dispensado.returncode == 0 and "impacto-da-mudanca\tnao se aplica\t" in linha_de("impacto-da-mudanca") and "não muda o trabalho de ninguém" in linha_de("impacto-da-mudanca") and "impacto-da-mudanca" not in lista() and "registrar-dispensa" in dispensado.stdout)
    gov("--controle", "entrevistas-e-workshops", "--pendente")
    confere("o condicional que vale passa a pendente e é cobrado na etapa", "entrevistas-e-workshops\tpendente\t" in linha_de("entrevistas-e-workshops") and "Controle do tipo de projeto sem evidência: Plano e registro de entrevistas e workshops" in lista() and "Vale neste projeto?" not in lista(), lista())
    gov("--controle", "taxonomia-e-metricas", "--pendente")
    confere("reabrir um controle cumprido apaga a evidência antiga", linha_de("taxonomia-e-metricas") == "taxonomia-e-metricas\tpendente\t\t\t\t" and "taxonomia-e-metricas" in lista(), linha_de("taxonomia-e-metricas"))
    gov("--controle", "taxonomia-e-metricas", "--cumprido", "--evidencia", "D-004", "--quem", "Gerente de mídia")
    gov("--controle", "entrevistas-e-workshops", "--cumprido", "--evidencia", "A-001, A-002", "--quem", "Consultora")

    # Os portões seguintes e o envio.
    etapa("redacao")
    confere("controle de revisão não é cobrado na redação", "papeis-e-niveis-de-servico" not in lista())
    etapa("revisao")
    na_revisao = lista()
    confere("controles de revisão são cobrados na revisão, e o de envio ainda não", "papeis-e-niveis-de-servico" in na_revisao and "alcadas-de-autorizacao" in na_revisao and "validacao-com-donos-dos-processos" not in na_revisao, na_revisao)
    envio = gov("--versao", "diag", "--mudou", "Versão para os donos", "--enviada-a", "Gerente de mídia")
    confere("o envio com controle sem evidência é registrado com o aviso", envio.returncode == 0 and "diag v1 registrada" in envio.stdout and "ATENÇÃO: o envio saiu com controle do tipo de projeto sem evidência" in envio.stdout and "[validacao-com-donos-dos-processos]" in envio.stdout and "[taxonomia-e-metricas]" not in envio.stdout and "[impacto-da-mudanca]" not in envio.stdout, envio.stdout)
    confere("depois do envio, o controle de envio é cobrado", "validacao-com-donos-dos-processos" in lista() and "validacao-com-donos-dos-processos" in checagem().stdout)
    for codigo in ("papeis-e-niveis-de-servico", "alcadas-de-autorizacao", "validacao-com-donos-dos-processos"):
        gov("--controle", codigo, "--cumprido", "--evidencia", "A-003", "--quem", "Gerente de mídia")
    limpo = gov("--versao", "diag", "--mudou", "Versão final", "--enviada-a", "Gerente de mídia")
    confere("com tudo cumprido ou dispensado, o envio sai sem aviso e nada é cobrado", "ATENÇÃO" not in limpo.stdout and "Controle do tipo de projeto" not in lista() and "Controle do tipo de projeto" not in checagem().stdout and checagem().returncode == 0 and "com 0 pendente(s) e 0 a confirmar" in estado(), limpo.stdout + checagem().stdout)

    # A checagem do registro.
    original = (reg / "controles.tsv").read_text(encoding="utf-8")
    for linha, espera, nome in (("inventado\tpendente\t\t\t\t", "O controle 'inventado' não existe em nenhum pacote", "controle fora dos pacotes é erro"),
                                ("rastreabilidade\tfeito\t\t\t\t", "rastreabilidade: a situação 'feito' não existe", "situação fora da lista é erro"),
                                ("rastreabilidade\tcumprido\t\t\t\t", "rastreabilidade: controle cumprido sem evidência", "cumprido sem evidência é erro")):
        (reg / "controles.tsv").write_text(original + linha + "\n", encoding="utf-8")
        saida = checagem()
        confere(f"checagem: {nome}", saida.returncode != 0 and espera in saida.stdout, saida.stdout)
    (reg / "controles.tsv").write_text(original, encoding="utf-8")

    # O assessment de martech e adtech e o pacote para outros ambientes.
    rodar([PY, "entregaveis/_harness/scripts/preparar.py", "--pacote", "martech-adtech"], projeto)
    soma = gov("--controles").stdout
    confere("os controles dos pacotes ativos se somam", "criterios-de-avaliacao (martech-adtech)" in soma and "validacao-com-donos-das-plataformas (martech-adtech)" in soma and "taxonomia-e-metricas (processos-midia)" in soma and soma.count("Situação:") == 10, soma)
    pacote = rodar([PY, "entregaveis/_harness/scripts/empacotar.py", "--projeto"], projeto)
    ambiente = base / "_ambiente"
    confere("o pacote para outros ambientes leva os controles e as respostas do projeto", pacote.returncode == 0 and "## Controles de governança" in (ambiente / "pacote-processos-midia.txt").read_text(encoding="utf-8") and "alcadas-de-autorizacao\tAlçadas" in (ambiente / "pacote-processos-midia.txt").read_text(encoding="utf-8") and "### controles.tsv" in (ambiente / "5-projeto.txt").read_text(encoding="utf-8") and "taxonomia-e-metricas\tcumprido\tD-004" in (ambiente / "5-projeto.txt").read_text(encoding="utf-8"), pacote.stdout + pacote.stderr)


def testar_levantamento(tmp: Path) -> None:
    print("Levantamento de projeto existente")
    projeto = tmp / "levantar"
    (projeto / "docs").mkdir(parents=True)
    (projeto / "docs/modelo-da-marca.potx").write_text("x", encoding="utf-8")
    (projeto / "docs/proposta.docx").write_text("x", encoding="utf-8")
    (projeto / "AGENTS.md").write_text("Regras.\n", encoding="utf-8")
    instalar(projeto)
    saida = rodar([PY, "entregaveis/_harness/scripts/levantar.py"], projeto)
    confere("levantar.py lista o que o projeto já tem", saida.returncode == 0 and "proposta.docx" in saida.stdout and "AGENTS.md" in saida.stdout, saida.stdout + saida.stderr)


# --- Atas, prazos e rotina diária -----------------------------------------


def dia_util(inicio: datetime.date, n: int) -> datetime.date:
    """O dia que fica n dias úteis depois de `inicio` (antes, quando n é negativo)."""
    dia, passo = inicio, 1 if n >= 0 else -1
    while n:
        dia += datetime.timedelta(days=passo)
        if dia.weekday() < 5:
            n -= passo
    return dia


def testar_rotina(tmp: Path) -> None:
    print("Atas, prazos e rotina diária")
    projeto = tmp / "rotina"
    projeto.mkdir()
    (projeto / ".git").mkdir()
    instalar(projeto)
    base = projeto / "entregaveis"
    reg = base / "_projeto"
    confere("a instalação cria a pasta de atas e a pasta de entrada", (base / "_atas/LEIA-ME.md").is_file() and (base / "_intake/entrada/.gitkeep").is_file())
    confere("a instalação cria os registros do dia a dia", all((reg / n).is_file() for n in ("acoes.tsv", "reunioes.tsv", "ritos.tsv", "riscos.tsv", "prazos.tsv", "cadencias.tsv", "alertas.tsv", "diario.md")))
    ignorados = (projeto / ".gitignore").read_text(encoding="utf-8")
    confere("as atas e a pasta de entrada ficam fora do git", "entregaveis/_atas/*" in ignorados and "entregaveis/_intake/entrada/*" in ignorados and "!entregaveis/_atas/LEIA-ME.md" in ignorados)
    pasta = montar_exemplo(projeto)

    def rotina(*args) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/rotina.py", *args], projeto)

    def secao(saida: str, titulo: str) -> str:
        """As linhas de uma seção do resumo."""
        dentro, linhas = False, []
        for linha in saida.splitlines():
            if not linha.startswith("- "):
                dentro = linha.startswith(titulo)
            elif dentro:
                linhas.append(linha)
        return "\n".join(linhas)

    def acao(*campos) -> None:
        with (reg / "acoes.tsv").open("a", encoding="utf-8") as f:
            f.write("\t".join(str(c) for c in campos) + "\n")

    def linha_de(arquivo: Path, ident: str) -> str:
        return next((l for l in arquivo.read_text(encoding="utf-8").splitlines() if l.startswith(ident + "\t")), "")

    # O dia de referência é um dia útil. Os arquivos do teste têm a data de hoje, e a rotina olha essa data.
    a = dia_util(datetime.date.today(), 0) if datetime.date.today().weekday() < 5 else dia_util(datetime.date.today(), 1)
    vazio = rotina("--hoje", a)
    confere("projeto sem prazo nem ata: nada a tratar", vazio.returncode == 0 and "Nada chegou e nenhum prazo pede atenção hoje" in vazio.stdout, vazio.stdout + vazio.stderr)

    # As três fases, pelo cronograma. Janela de 20 dias úteis: parado depois de 7, próximo com 4 ou menos.
    acao("T-001", "tarefa", "Enviar o inventário de contratos", "Compras do cliente", "cliente", dia_util(a, -10), dia_util(a, 10), "nao", "aberta", "consultor", dia_util(a, -10), "")
    acao("T-002", "tarefa", "Marcar as entrevistas", "Consultora", "consultoria", dia_util(a, -10), dia_util(a, 10), "nao", "aberta", "consultor", dia_util(a, -1), "")
    parado = rotina("--abrir", "--hoje", a)
    confere("fase 1: item sem movimento dentro do prazo recebe o aviso leve", "T-001" in secao(parado.stdout, "Parece parado") and "T-001" not in secao(parado.stdout, "Vencidos") and "T-001" not in secao(parado.stdout, "Prazo próximo"), parado.stdout + parado.stderr)
    confere("fase 1: item que andou ontem não recebe aviso", "T-002" not in parado.stdout, parado.stdout)
    confere("o aviso mostrado fica em alertas.tsv", linha_de(reg / "alertas.tsv", "T-001").split("\t")[1:2] == ["parado"], (reg / "alertas.tsv").read_text(encoding="utf-8"))
    de_novo = rotina("--abrir", "--hoje", dia_util(a, 1))
    confere("fase 1: o aviso leve é dado uma vez só", "T-001" not in de_novo.stdout, de_novo.stdout)
    proximo = rotina("--hoje", dia_util(a, 6))
    confere("fase 2: prazo próximo avisa quando resta um quinto da janela", "T-001" in secao(proximo.stdout, "Prazo próximo") and "em 4 dia(s) útil(eis)" in proximo.stdout, proximo.stdout)
    confere("fase 2: com cinco dias úteis de folga ainda não avisa", "T-001" not in secao(rotina("--hoje", dia_util(a, 5)).stdout, "Prazo próximo"))
    vencido = rotina("--hoje", dia_util(a, 11))
    confere("fase 3: prazo vencido pede uma das três respostas", "T-001" in secao(vencido.stdout, "Vencidos") and "concluído, nova data ou não é mais necessário" in vencido.stdout, vencido.stdout)
    confere("fase 3: no dia do prazo o item ainda não está vencido", "T-001" not in secao(rotina("--hoje", dia_util(a, 10)).stdout, "Vencidos"))
    for passo in (11, 12):
        rotina("--abrir", "--hoje", dia_util(a, passo))
    terceiro = rotina("--hoje", dia_util(a, 13))
    confere("fase 3: o terceiro aviso sem resposta sugere o risco", "Terceiro aviso sem resposta" in secao(terceiro.stdout, "Vencidos"), terceiro.stdout)

    # As respostas: nova data com histórico, concluído e não é mais necessário.
    acao("T-003", "tarefa", "Aprovar o roteiro das entrevistas", "Diretora de marketing", "cliente", dia_util(a, -8), dia_util(a, -3), "nao", "aberta", "consultor", dia_util(a, -8), "")
    original = str(dia_util(a, -3))
    aviso = validar(projeto, "--so", "prazos")
    confere("checagem de prazos: avisa do item vencido sem resposta", "T-003" in aviso.stdout and "venceu em" in aviso.stdout and "ERRO" not in aviso.stdout, aviso.stdout)
    confere("o estado mostra a linha da rotina do dia", "Rotina do dia:" in rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout)
    sem_motivo = rotina("--remarcar", "T-003", dia_util(a, 5))
    confere("nova data sem motivo é recusada", sem_motivo.returncode == 2 and original in linha_de(reg / "acoes.tsv", "T-003"), sem_motivo.stdout)
    sem_data = rotina("--remarcar", "T-003", "depois", "--motivo", "A diretora está de férias")
    confere("não existe adiar sem data", sem_data.returncode == 2 and "Não existe adiar sem data" in sem_data.stdout, sem_data.stdout)
    primeira = rotina("--remarcar", "T-003", dia_util(a, 5), "--motivo", "A diretora está de férias", "--quem", "Consultora", "--hoje", a)
    historico = linha_de(reg / "prazos.tsv", "T-003").split("\t")
    confere("nova data: a anterior fica no histórico, com quem mudou e o motivo", primeira.returncode == 0 and historico[1:7] == [original, original, str(dia_util(a, 5)), str(a), "Consultora", "A diretora está de férias"], str(historico))
    confere("nova data: o registro de ações recebe o prazo novo", str(dia_util(a, 5)) in linha_de(reg / "acoes.tsv", "T-003"))
    confere("nova data: o item sai dos vencidos e da checagem", "T-003" not in validar(projeto, "--so", "prazos").stdout and "T-003" not in secao(rotina("--hoje", a).stdout, "Vencidos"))
    segunda = rotina("--remarcar", "T-003", dia_util(a, 8), "--motivo", "O roteiro mudou", "--hoje", dia_util(a, 4))
    confere("segunda remarcação do mesmo item ganha destaque", "Segunda remarcação" in segunda.stdout and "ATENÇÃO" in rotina("--datas").stdout, segunda.stdout)
    terceira = rotina("--remarcar", "T-003", dia_util(a, 12), "--motivo", "Falta a aprovação do jurídico", "--hoje", dia_util(a, 7))
    confere("terceira remarcação vira risco", "Terceira remarcação" in terceira.stdout and "riscos.tsv" in terceira.stdout, terceira.stdout)
    datas = rotina("--datas").stdout
    linhas_do_item = [l for l in (reg / "prazos.tsv").read_text(encoding="utf-8").splitlines() if l.startswith("T-003\t")]
    confere("o histórico guarda toda mudança e mantém a data original", len(linhas_do_item) == 3 and all(l.split("\t")[1] == original for l in linhas_do_item) and f"original {original}" in datas and "3 remarcação(ões)" in datas, datas)
    confere("o resumo diz quantas vezes o item foi remarcado", "Remarcado 3 vez(es)" in rotina("--hoje", dia_util(a, 13)).stdout)
    acao("T-004", "marco", "Entrega do relatório final", "Consultora", "consultoria", dia_util(a, -5), dia_util(a, 15), "sim", "aberta", "consultor", a, "")
    de_base = rotina("--remarcar", "T-004", dia_util(a, 20), "--motivo", "O cliente pediu mais uma área", "--hoje", a)
    confere("data de base: a mudança pede o acordo do cliente", "acordo do cliente" in de_base.stdout and "acordo do cliente" not in primeira.stdout, de_base.stdout)
    concluida = rotina("--concluir", "T-001", "--hoje", dia_util(a, 11))
    confere("concluído: o item sai dos avisos e fica no registro", concluida.returncode == 0 and "\tconcluida\t" in linha_de(reg / "acoes.tsv", "T-001") and "T-001" not in rotina("--hoje", dia_util(a, 13)).stdout, concluida.stdout)
    sem_porque = rotina("--dispensar", "T-002")
    confere("dispensa sem motivo é recusada", sem_porque.returncode == 2 and "\taberta\t" in linha_de(reg / "acoes.tsv", "T-002"), sem_porque.stdout)
    dispensada = rotina("--dispensar", "T-002", "--motivo", "O cliente já tinha as entrevistas gravadas", "--hoje", a)
    confere("não é mais necessário: o item é cancelado com o motivo e não é apagado", dispensada.returncode == 0 and "\tcancelada\t" in linha_de(reg / "acoes.tsv", "T-002") and "O cliente já tinha as entrevistas gravadas" in linha_de(reg / "acoes.tsv", "T-002"), dispensada.stdout)
    confere("não é mais necessário: os avisos do item param", "T-002" not in rotina("--hoje", dia_util(a, 30)).stdout)
    confere("item que não existe: o comando diz o que vale", rotina("--concluir", "T-999").returncode != 0 and rotina("--remarcar", "X-1", dia_util(a, 3), "--motivo", "teste").returncode != 0)

    # Pedido de material e entregável também têm prazo.
    with (base / "_intake/registro.tsv").open("a", encoding="utf-8") as f:
        f.write(f"M-001\tRelatórios de uso\tdados\tTecnologia do cliente\t{dia_util(a, -10)}\t{dia_util(a, -2)}\tpedido\t\t\n")
    material = rotina("--hoje", a)
    confere("pedido de material vencido entra nos vencidos", "M-001 (pedido de material)" in secao(material.stdout, "Vencidos"), material.stdout)
    confere("material não é concluído pela rotina", rotina("--concluir", "M-001").returncode == 2)
    rotina("--dispensar", "M-001", "--motivo", "O cliente desistiu da análise de uso", "--hoje", a)
    confere("material dispensado sai dos avisos", "\tdispensado\t" in linha_de(base / "_intake/registro.tsv", "M-001") and "M-001" not in rotina("--hoje", a).stdout)
    with (base / "_intake/registro.tsv").open("a", encoding="utf-8") as f:
        f.write(f"M-002\tLista de usuários\tdados\tTecnologia do cliente\t{dia_util(a, -15)}\t{dia_util(a, -1)}\tem falta\t\t\n")
    rotina("--remarcar", "M-002", dia_util(a, 20), "--motivo", "O cliente pediu mais um mês", "--hoje", a)
    remarcado = rotina("--hoje", a)
    confere("material remarcado: a data nova vai ao registro e conta como movimento", str(dia_util(a, 20)) in linha_de(base / "_intake/registro.tsv", "M-002") and "M-002" not in remarcado.stdout, remarcado.stdout)
    confere("material remarcado: volta a parecer parado se ninguém mexe", "M-002" in secao(rotina("--hoje", dia_util(a, 13)).stdout, "Parece parado"))
    briefing = pasta / "briefing.md"
    briefing.write_text(briefing.read_text(encoding="utf-8").replace("prazo:\n", f"prazo: {dia_util(a, 1)}\n", 1), encoding="utf-8")
    apertado = rotina("--hoje", a)
    confere("entregável: avisa quando as etapas que faltam não cabem no prazo", "diag (entregável)" in secao(apertado.stdout, "Prazo próximo") and "faltam 2 etapa(s)" in apertado.stdout, apertado.stdout)
    rotina("--remarcar", "diag", dia_util(a, 15), "--motivo", "A reunião da diretoria mudou de data", "--hoje", a)
    confere("entregável: a data nova vai ao briefing e ao histórico", f"prazo: {dia_util(a, 15)}" in briefing.read_text(encoding="utf-8") and linha_de(reg / "prazos.tsv", "diag").split("\t")[2] == str(dia_util(a, 1)) and "diag" not in rotina("--hoje", a).stdout)

    # Atas: a pasta manda. Nova, processada, alterada.
    semana_passada = a - datetime.timedelta(days=7)
    with (reg / "ritos.tsv").open("a", encoding="utf-8") as f:
        f.write(f"Comitê semanal\tsemanal\t{a - datetime.timedelta(days=14)}\t\tConsultora, diretora de marketing\t\n")
    ata = base / "_atas" / f"{semana_passada} comite semanal.md"
    ata.write_text("# Comitê semanal\n\nA diretora aprovou o roteiro.\nO inventário chega na sexta.\n", encoding="utf-8")
    chegou = rotina("--hoje", a)
    confere("ata nova na pasta aparece no resumo, com a data e o rito do nome", f"Ata nova: {ata.name}" in secao(chegou.stdout, "Chegou") and f"data {semana_passada}" in chegou.stdout and 'rito "Comitê semanal"' in chegou.stdout, chegou.stdout)
    confere("o guia da pasta de atas não conta como ata", "LEIA-ME" not in chegou.stdout)
    confere("o estado conta a ata nova", "arquivo(s) novo(s) em atas e entrada" in rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout)
    lida = rotina("--ler", ata.name)
    confere("--ler devolve o texto da ata", lida.returncode == 0 and "A diretora aprovou o roteiro." in lida.stdout, lida.stdout + lida.stderr)
    registrada = rotina("--ata", ata.name, "--data", semana_passada, "--reuniao", "Comitê semanal", "--rito", "Comitê semanal", "--resultado", "1 decisão, 1 ação", "--hoje", a)
    da_ata = linha_de(reg / "reunioes.tsv", "A-001")
    confere("ata processada entra em reunioes.tsv com o arquivo e a marca", registrada.returncode == 0 and ata.name in da_ata and "ata processada" in da_ata and "1 decisão, 1 ação" in da_ata, registrada.stdout + da_ata)
    confere("ata processada sai do resumo", "Ata" not in rotina("--hoje", a).stdout)
    ata.write_text(ata.read_text(encoding="utf-8") + "O jurídico pediu para ver o contrato.\n", encoding="utf-8")
    alterada = rotina("--hoje", a)
    confere("ata alterada depois de processada volta ao resumo", "Ata alterada depois de processada (A-001)" in alterada.stdout, alterada.stdout)
    diferenca = rotina("--ler", ata.name)
    confere("ata alterada: --ler mostra só a diferença", "ENTROU: O jurídico pediu para ver o contrato." in diferenca.stdout and "A diretora aprovou o roteiro." not in diferenca.stdout, diferenca.stdout)
    rotina("--ata", ata.name, "--data", semana_passada, "--reuniao", "Comitê semanal", "--rito", "Comitê semanal", "--hoje", a)
    confere("ata alterada e reprocessada não cria outra reunião", "Ata" not in rotina("--hoje", a).stdout and not linha_de(reg / "reunioes.tsv", "A-002"))
    fora = projeto / "ata-solta.md"
    fora.write_text("Ata fora da pasta.\n", encoding="utf-8")
    confere("ata fora da pasta de atas é recusada", rotina("--ata", str(fora), "--data", a, "--reuniao", "Avulsa").returncode == 1)
    confere("ata sem data ou sem nome de reunião é recusada", rotina("--ata", ata.name, "--reuniao", "Comitê").returncode == 2)
    legenda = base / "_atas" / "gravacao.vtt"
    legenda.write_text("WEBVTT\n\n1\n00:00:01.000 --> 00:00:04.000\n<v Diretora>O prazo fica para março.</v>\n", encoding="utf-8")
    da_legenda = rotina("--ler", "gravacao.vtt").stdout
    confere("legenda de gravação: sai o texto, sem os tempos", "Diretora: O prazo fica para março." in da_legenda and "-->" not in da_legenda, da_legenda)
    with zipfile.ZipFile(base / "_atas" / "ata.docx", "w") as pacote:
        pacote.writestr("word/document.xml", "<w:document><w:body><w:p><w:r><w:t>Decidido: sai a plataforma B.</w:t></w:r></w:p></w:body></w:document>")
    confere("ata em Word é lida sem pacote extra", "Decidido: sai a plataforma B." in rotina("--ler", "ata.docx").stdout)
    (base / "_atas" / "audio.m4a").write_bytes(b"\x00\x01")
    confere("formato que o script não lê: manda abrir com as ferramentas do agente", "não é lido por este script" in rotina("--ler", "audio.m4a").stdout)
    for nome in ("gravacao.vtt", "ata.docx", "audio.m4a"):
        (base / "_atas" / nome).unlink()
    relato = rotina("--ata", "--data", a, "--reuniao", "Conversa com a diretora financeira", "--hoje", a)
    confere("reunião sem ata entra como relato de memória", relato.returncode == 0 and "relato de memória" in linha_de(reg / "reunioes.tsv", "A-002") and "realizada" in linha_de(reg / "reunioes.tsv", "A-002"), relato.stdout)

    # Cadência: rito sem ata, propostas paradas, entrada esquecida, pausa.
    um_ciclo = rotina("--hoje", dia_util(a, 2))
    confere("rito: a reunião sem ata é cobrada depois de um dia útil", f'A reunião "Comitê semanal" de {a} não tem ata' in secao(um_ciclo.stdout, "Cadência"), um_ciclo.stdout)
    confere("rito: no dia da reunião a ata ainda não é cobrada", "Comitê semanal" not in secao(rotina("--hoje", a).stdout, "Cadência"))
    dois_ciclos = rotina("--hoje", dia_util(a, 7))
    confere("rito: dois ciclos sem ata viram outra pergunta", "sem ata há dois ciclos" in secao(dois_ciclos.stdout, "Cadência"), dois_ciclos.stdout)
    sem_ata = rotina("--sem-ata", a, "--rito", "Comitê semanal", "--motivo", "A reunião foi cancelada pelo cliente", "--hoje", dia_util(a, 2))
    confere("rito: a reunião registrada sem ata deixa de ser cobrada", sem_ata.returncode == 0 and "sem ata" in linha_de(reg / "reunioes.tsv", "A-003") and "Comitê semanal" not in secao(rotina("--hoje", dia_util(a, 2)).stdout, "Cadência"), sem_ata.stdout)
    acao("T-005", "tarefa", "Rever o contrato da plataforma B", "", "cliente", dia_util(a, -5), "", "nao", "proposta", "A-001", dia_util(a, -5), "O jurídico pediu para ver o contrato")
    proposta = rotina("--hoje", a)
    confere("proposta de ata espera o sim do consultor", "T-005 (proposta, origem A-001)" in secao(proposta.stdout, "Espera o seu sim") and "T-005" in secao(proposta.stdout, "Cadência"), proposta.stdout)
    confere("proposta não gera aviso de prazo nem de checagem", "T-005" not in validar(projeto, "--so", "prazos").stdout)
    entrada = base / "_intake/entrada/custos.xlsx"
    entrada.write_bytes(b"planilha")
    confere("arquivo na pasta de entrada aparece no resumo", "Na pasta de entrada, sem classificar: custos.xlsx" in secao(rotina("--hoje", a).stdout, "Chegou"))
    confere("arquivo esquecido na pasta de entrada vira aviso de cadência", "custos.xlsx" in secao(rotina("--hoje", dia_util(a, 3)).stdout, "Cadência") and "custos.xlsx" not in secao(rotina("--hoje", a).stdout, "Cadência"))
    entrada.unlink()
    confere("projeto sem registro novo há dias pergunta pela pausa", "Ele está pausado?" in rotina("--hoje", dia_util(a, 6)).stdout and "Ele está pausado?" not in rotina("--hoje", a).stdout)
    acao("T-006", "tarefa", "Enviar a lista de usuários", "Tecnologia do cliente", "cliente", dia_util(a, -9), dia_util(a, -4), "nao", "aberta", "consultor", dia_util(a, -9), "")
    confere("antes da pausa, o vencido aparece", "T-006" in secao(rotina("--hoje", a).stdout, "Vencidos") and "T-006" in validar(projeto, "--so", "prazos").stdout)
    rotina("--pausar", dia_util(a, 20))
    pausado = rotina("--hoje", a)
    confere("pausa: os avisos de prazo e de cadência ficam em silêncio", "Projeto em pausa até" in pausado.stdout and "Vencidos" not in pausado.stdout and "Cadência" not in pausado.stdout, pausado.stdout)
    confere("pausa: a checagem de prazos e o estado também calam", "T-006" not in validar(projeto, "--so", "prazos").stdout and "Projeto em pausa até" in rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout)
    confere("pausa: acaba sozinha na data de retomada", "T-006" in secao(rotina("--hoje", dia_util(a, 21)).stdout, "Vencidos"))
    rotina("--retomar")
    confere("retomada: os avisos voltam", "T-006" in secao(rotina("--hoje", a).stdout, "Vencidos"))
    (reg / "cadencias.tsv").write_text((reg / "cadencias.tsv").read_text(encoding="utf-8").replace("proximo_maximo\t5", "proximo_maximo\t8").replace("proximo_fracao\t0.2", "proximo_fracao\t0.5"), encoding="utf-8")
    confere("os limites dos avisos são do projeto", "T-004" in secao(rotina("--hoje", dia_util(a, 12)).stdout, "Prazo próximo"))

    # Diário.
    rotina("--fechar", "Ata do comitê processada. Falta a resposta sobre T-006.", "--hoje", a)
    rotina("--fechar", "O cliente confirmou a reunião de quinta.", "--hoje", a)
    diario = (reg / "diario.md").read_text(encoding="utf-8")
    confere("o diário grava uma linha por dia", diario.count(f"| {a} |") == 1 and "Ata do comitê processada." in diario and "O cliente confirmou a reunião de quinta." in diario, diario)

    # A checagem acusa o registro malformado.
    acao("T-007", "tarefa", "Item com estado errado", "Consultora", "consultoria", a, dia_util(a, 5), "nao", "em andamento", "consultor", a, "")
    acao("T-008", "tarefa", "Item com data errada", "Consultora", "consultoria", a, "15/12/2026", "nao", "aberta", "consultor", a, "")
    acao("T-009", "tarefa", "Item sem dono", "", "consultoria", a, dia_util(a, 5), "nao", "aberta", "consultor", a, "")
    acao("T-010", "tarefa", "Item sem prazo", "Consultora", "consultoria", a, "", "nao", "aberta", "consultor", a, "")
    errado = validar(projeto, "--so", "prazos")
    confere("checagem de prazos: estado que não existe é erro", errado.returncode != 0 and "T-007: o estado 'em andamento' não existe" in errado.stdout, errado.stdout)
    confere("checagem de prazos: data fora do formato é erro", "T-008: o campo 'prazo' precisa de uma data" in errado.stdout)
    confere("checagem de prazos: ação aberta sem dono ou sem prazo é aviso", "T-009 está aberta sem dono" in errado.stdout and "T-010 está aberta sem prazo" in errado.stdout)
    confere("a rotina não quebra com registro malformado", rotina("--hoje", a).returncode == 0)

    # O hook de mensagem lembra a skill do momento.
    hooks = base / "_harness/hooks"

    def mensagem(texto: str) -> str:
        return rodar([PY, hooks / "mensagem.py"], projeto, json.dumps({"cwd": str(projeto), "prompt": texto})).stdout

    confere("mensagem: dispensa lembra a skill registrar-dispensa", "registrar-dispensa" in mensagem("o relatório de uso não é mais necessário, o cliente desistiu") or "registrar-dispensa" in mensagem("a análise de subuso não vai mais ser feita"))
    confere("mensagem: ata lembra a skill processar-ata", "processar-ata" in mensagem("salvei a ata da reunião de ontem na pasta"))
    comum_ = mensagem("inclua uma página sobre mídia paga")
    confere("mensagem: pedido comum não lembra ata nem dispensa", "processar-ata" not in comum_ and "registrar-dispensa" not in comum_, comum_)

    # Atas no git são erro de confidencialidade.
    if shutil.which("git") is not None:
        shutil.rmtree(projeto / ".git")
        rodar(["git", "init", "-q"], projeto)
        limpo = validar(projeto, "--so", "confidencialidade")
        confere("ata fora do git: a checagem passa", "ata ou transcrição" not in limpo.stdout, limpo.stdout)
        rodar(["git", "add", "-f", str(ata)], projeto)
        versionada = validar(projeto, "--so", "confidencialidade")
        confere("ata no git: a checagem acusa", versionada.returncode != 0 and "de ata ou transcrição estão no git" in versionada.stdout, versionada.stdout)
        ignorada = rodar(["git", "check-ignore", "-q", str(base / "_intake/entrada/custos.xlsx")], projeto)
        confere("o git ignora o que está na pasta de entrada e nas atas", ignorada.returncode == 0 and rodar(["git", "check-ignore", "-q", str(base / "_atas/LEIA-ME.md")], projeto).returncode != 0)

    # Um projeto de versão anterior recebe os registros novos na atualização, sem perder os que já tem.
    antigo = tmp / "rotina-antigo"
    antigo.mkdir()
    instalar(antigo)
    for nome in ("acoes.tsv", "prazos.tsv", "reunioes.tsv", "cadencias.tsv"):
        (antigo / "entregaveis/_projeto" / nome).unlink()
    shutil.rmtree(antigo / "entregaveis/_atas")
    (antigo / "entregaveis/_projeto/riscos.tsv").write_text((antigo / "entregaveis/_projeto/riscos.tsv").read_text(encoding="utf-8") + "RS-001\tO cliente troca de diretor\t\t\tConsultora\taberto\tconsultor\t\n", encoding="utf-8")
    (antigo / "entregaveis/_harness/VERSAO").write_text("0.7.1\n", encoding="utf-8")
    atualizado = instalar(antigo, "--atualizar")
    confere("--atualizar cria os registros e a pasta de atas que a versão nova trouxe", atualizado.returncode == 0 and all((antigo / "entregaveis/_projeto" / n).is_file() for n in ("acoes.tsv", "prazos.tsv", "reunioes.tsv", "cadencias.tsv")) and (antigo / "entregaveis/_atas/LEIA-ME.md").is_file(), atualizado.stdout + atualizado.stderr)
    confere("--atualizar não toca no registro que o projeto já tinha", "RS-001" in (antigo / "entregaveis/_projeto/riscos.tsv").read_text(encoding="utf-8"))


# --- Governança e lista do dia --------------------------------------------


def testar_governanca(tmp: Path) -> None:
    print("Governança por nível e lista do dia")
    modelos = HARNESS / "modelos" / "projeto"
    catalogo = [dict(zip(l0.split("\t"), l.split("\t"))) for l0, *resto in [[l for l in (HARNESS / "governanca/catalogo.tsv").read_text(encoding="utf-8").splitlines() if not l.startswith("#")]] for l in resto]
    codigos = {m["codigo"]: m for m in catalogo}
    niveis = ["enxuto", "padrao", "completo"]
    confere("catálogo: todo material tem nível, momento, cadência, destinatário, conteúdo e fontes", all(m["nivel"] in niveis and m["momento"] in ("inicio", "rotina", "entregaveis", "controle", "encerramento") and m["cadencia"] and m["destinatario"] and m["traz"] and m["fontes"] for m in catalogo))
    confere("catálogo: o nível enxuto emite sete materiais", sum(1 for m in catalogo if m["nivel"] == "enxuto") == 7)
    confere("catálogo: um material só substitui outro de nível mais baixo", all(m["substitui"] in codigos and niveis.index(codigos[m["substitui"]]["nivel"]) < niveis.index(m["nivel"]) for m in catalogo if m["substitui"]))
    fontes = {f for m in catalogo for f in re.findall(r"[a-z-]+\.(?:tsv|md)", m["fontes"])}
    fora = {f for f in fontes if not (modelos / f).is_file() and f not in ("registro.tsv", "briefing.md", "afazeres.md")}
    confere("catálogo: toda fonte citada é um registro que existe", not fora, str(fora))

    projeto = tmp / "governanca"
    projeto.mkdir()
    (projeto / ".git").mkdir()
    instalar(projeto)
    base = projeto / "entregaveis"
    reg = base / "_projeto"
    novos = ("premissas.tsv", "issues.tsv", "dependencias.tsv", "mudancas.tsv", "papeis.tsv", "linha-de-base.tsv", "versoes.tsv", "esforco.tsv", "cobrancas.tsv", "perguntas.tsv", "governanca.tsv")
    confere("a instalação cria os registros de governança", all((reg / n).is_file() for n in novos), str([n for n in novos if not (reg / n).is_file()]))
    montar_exemplo(projeto)

    def gov(*args) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/governanca.py", *args], projeto)

    def rotina(*args) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/rotina.py", *args], projeto)

    def estado() -> str:
        return rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout

    def acrescentar(arquivo: Path, *campos) -> None:
        with arquivo.open("a", encoding="utf-8") as f:
            f.write("\t".join(str(c) for c in campos) + "\n")

    def linha_de(arquivo: Path, ident: str) -> str:
        return next((l for l in arquivo.read_text(encoding="utf-8").splitlines() if l.startswith(ident + "\t")), "")

    def trocar(arquivo: Path, antes: str, depois: str) -> None:
        texto = arquivo.read_text(encoding="utf-8")
        assert antes in texto, antes
        arquivo.write_text(texto.replace(antes, depois, 1), encoding="utf-8")

    def bloco(saida: str, titulo: str) -> str:
        """As linhas de uma lista da lista do dia, até a linha em branco."""
        dentro, linhas = False, []
        for linha in saida.splitlines():
            if linha.startswith(titulo):
                dentro = True
            elif dentro and not linha.strip():
                break
            elif dentro:
                linhas.append(linha)
        return "\n".join(linhas)

    def lista(dia, *args) -> str:
        return rotina("--lista", "--hoje", dia, *args).stdout

    a = dia_util(datetime.date.today(), 0) if datetime.date.today().weekday() < 5 else dia_util(datetime.date.today(), 1)
    brief = reg / "brief.md"

    # O nível: sugestão pelo porte, com os dois lados de cada limite.
    confere("sem nível, o estado manda definir a governança", "Nível de governança não definido" in estado(), estado())
    confere("sem nível, a checagem de governança não avisa nada", "Nenhum erro e nenhum aviso" in validar(projeto, "--so", "governanca").stdout)

    def sugere(*args) -> str:
        saida = gov("--sugerir", "--hoje", a, *args).stdout
        return (re.search(r"Nível sugerido: (\w+)", saida) or [None, saida])[1]

    pequeno = gov("--sugerir", "--hoje", a)
    confere("sugestão: projeto sem sinal de porte fica no enxuto, com sete materiais", "Nível sugerido: enxuto" in pequeno.stdout and len(re.findall(r"^\s+\d+\. ", pequeno.stdout, flags=re.MULTILINE)) == 7 and "Mantidos sempre" in pequeno.stdout, pequeno.stdout + pequeno.stderr)
    confere("sugestão: diz o que não deu para ler nos registros", "--frentes" in pequeno.stdout and "--pessoas" in pequeno.stdout)
    confere("sugestão: não grava nada", "governanca:" not in brief.read_text(encoding="utf-8") and not linha_de(reg / "governanca.tsv", "abertura"))
    confere("sugestão: mais de oito semanas pede o padrão, e oito não", sugere("--semanas", "9") == "padrão" and sugere("--semanas", "8") == "enxuto")
    confere("sugestão: duas frentes pedem o padrão, e uma não", sugere("--frentes", "2") == "padrão" and sugere("--frentes", "1") == "enxuto")
    confere("sugestão: mais de três pessoas pedem o padrão", sugere("--pessoas", "4") == "padrão" and sugere("--pessoas", "3") == "enxuto")
    confere("sugestão: comitê formal ou pagamento por marco pedem o padrão", sugere("--comite", "sim") == "padrão" and sugere("--pagamento", "marco") == "padrão" and sugere("--comite", "nenhum", "--pagamento", "outro") == "enxuto")
    confere("sugestão: mais de seis meses pede o completo, e seis meses não", sugere("--semanas", "27") == "completo" and sugere("--semanas", "26") == "padrão")
    confere("sugestão: mais de quatro frentes pedem o completo", sugere("--frentes", "5") == "completo" and sugere("--frentes", "4") == "padrão")
    confere("sugestão: comitê em níveis ou benefício comprometido pedem o completo", sugere("--comite", "niveis") == "completo" and sugere("--beneficio") == "completo")
    acrescentar(reg / "ritos.tsv", "Comitê mensal", "mensal", a + datetime.timedelta(days=200), "", "Diretoria", "")
    confere("sugestão: lê o comitê no registro de ritos", sugere() == "padrão" and "comitê formal" in gov("--sugerir", "--hoje", a).stdout)
    trocar(reg / "ritos.tsv", "Comitê mensal", "Reunião mensal")
    trocar(base / "diag/briefing.md", "prazo:", f"prazo: {a + datetime.timedelta(days=100)}")
    longo = gov("--sugerir", "--hoje", a)
    confere("sugestão: lê a duração nos prazos dos entregáveis", "Nível sugerido: padrão" in longo.stdout and "15 semanas" in longo.stdout, longo.stdout)
    trocar(base / "diag/briefing.md", f"prazo: {a + datetime.timedelta(days=100)}", "prazo:")
    longe = a + datetime.timedelta(days=90)
    acrescentar(reg / "acoes.tsv", "T-080", "tarefa", "Acompanhar a renovação", "Consultora", "consultoria", a, longe, "nao", "aberta", "consultor", a, "", "", "")
    confere("sugestão: uma tarefa de acompanhamento não estica a duração do projeto", sugere() == "enxuto", gov("--sugerir", "--hoje", a).stdout)
    trocar(reg / "acoes.tsv", "T-080\ttarefa", "T-080\tmarco")
    confere("sugestão: um marco conta na duração", sugere() == "padrão" and "13 semanas" in gov("--sugerir", "--hoje", a).stdout, gov("--sugerir", "--hoje", a).stdout)
    trocar(reg / "acoes.tsv", "Acompanhar a renovação", "Pagamento da segunda parcela")
    confere("sugestão: lê o pagamento por marco no registro de ações", "tem pagamento por marco" in gov("--sugerir", "--hoje", a).stdout)
    (reg / "acoes.tsv").write_text("".join(l for l in (reg / "acoes.tsv").read_text(encoding="utf-8").splitlines(keepends=True) if not l.startswith("T-080\t")), encoding="utf-8")

    # A escolha do consultor.
    confere("nível que não existe é recusado e nada é gravado", gov("--nivel", "medio").returncode == 2 and "governanca:" not in brief.read_text(encoding="utf-8"))
    confere("um material só muda depois de o nível existir", gov("--incluir", "pauta").returncode == 2)
    enxuto = gov("--nivel", "enxuto")
    cabecalho = brief.read_text(encoding="utf-8").split("---")[1]
    confere("o nível vai para o cabeçalho do brief, mesmo em brief de versão anterior", enxuto.returncode == 0 and "governanca: enxuto\niniciado: sim" in cabecalho, cabecalho)
    confere("o estado mostra o nível e quantos materiais são emitidos", "Governança: nível enxuto, 7 material(is) emitido(s)" in estado(), estado())
    confere("--tirar pede o motivo", gov("--tirar", "status-semanal").returncode == 2 and "mantido" in linha_de(reg / "governanca.tsv", "status-semanal"))
    tirado = gov("--tirar", "status-semanal", "--motivo", "O cliente tem o próprio status")
    confere("--tirar: o material deixa de ser emitido e fica registrado", tirado.returncode == 0 and "tirado" in linha_de(reg / "governanca.tsv", "status-semanal") and "7 material" not in estado() and "6 material(is)" in estado() and "Tirados pelo consultor: Status semanal" in gov().stdout)
    confere("--incluir traz um material do catálogo", gov("--incluir", "pauta").returncode == 0 and "incluido" in linha_de(reg / "governanca.tsv", "pauta"))
    confere("--incluir recusa o que não está no catálogo", gov("--incluir", "relatorio-magico").returncode == 1)
    confere("material sob medida pede destinatário, cadência e conteúdo", gov("--sob-medida", "Resumo para o conselho", "--cadencia", "trimestral").returncode == 2 and "SM-01" not in (reg / "governanca.tsv").read_text(encoding="utf-8"))
    medida = gov("--sob-medida", "Resumo para o conselho", "--cadencia", "trimestral", "--destinatario", "conselho", "--traz", "três linhas", "--fontes", "acoes.tsv")
    confere("material sob medida entra na lista com código próprio", medida.returncode == 0 and "sob medida" in linha_de(reg / "governanca.tsv", "SM-01"), medida.stdout + medida.stderr)
    gov("--ajustar", "aceite", "--destinatario", "Diretora de marketing")
    confere("--ajustar muda cadência e destinatário", "Diretora de marketing" in linha_de(reg / "governanca.tsv", "aceite"))
    padrao = gov("--nivel", "padrao")
    tabela = (reg / "governanca.tsv").read_text(encoding="utf-8")
    confere("subir de nível: o material mais completo troca o mais leve", padrao.returncode == 0 and linha_de(reg / "governanca.tsv", "termo-de-abertura") and not linha_de(reg / "governanca.tsv", "abertura") and not linha_de(reg / "governanca.tsv", "nota-de-reuniao"), tabela)
    confere("subir de nível: o tirado, o incluído e o sob medida ficam como o consultor deixou", "tirado" in linha_de(reg / "governanca.tsv", "status-semanal") and linha_de(reg / "governanca.tsv", "SM-01") and "incluido" in linha_de(reg / "governanca.tsv", "pauta"))
    confere("o brief mostra o nível novo, uma vez só", brief.read_text(encoding="utf-8").count("governanca:") == 1 and "governanca: padrao" in brief.read_text(encoding="utf-8"))
    gov("--nivel", "enxuto")
    confere("descer de nível: voltam os materiais leves e sai o que era do nível de cima", linha_de(reg / "governanca.tsv", "abertura") and not linha_de(reg / "governanca.tsv", "termo-de-abertura") and not linha_de(reg / "governanca.tsv", "raci") and linha_de(reg / "governanca.tsv", "pauta") and linha_de(reg / "governanca.tsv", "SM-01"))
    confere("o nível completo soma os materiais dos três níveis", gov("--nivel", "completo").returncode == 0 and linha_de(reg / "governanca.tsv", "matriz-de-riscos") and linha_de(reg / "governanca.tsv", "raci"))
    gov("--nivel", "enxuto")
    cat = gov("--catalogo").stdout
    confere("--catalogo mostra os três níveis", all(t in cat for t in ("O nível enxuto emite", "O nível padrão acrescenta", "O nível completo acrescenta", "[matriz-de-riscos]")), cat)
    confere("com nível definido, entregável sem aprovador é aviso", "'diag' não tem quem aprova" in validar(projeto, "--so", "governanca").stdout)
    acrescentar(reg / "papeis.tsv", "diag", "Consultora", "Diretora de marketing", "", "", "3", "")
    confere("com o aprovador registrado, o aviso some", "Nenhum erro e nenhum aviso" in validar(projeto, "--so", "governanca").stdout, validar(projeto, "--so", "governanca").stdout)
    trocar(brief, "governanca: enxuto", "governanca: medio")
    confere("checagem: nível fora da lista é erro", validar(projeto, "--so", "governanca").returncode != 0 and "'medio' não existe" in validar(projeto, "--so", "governanca").stdout)
    trocar(brief, "governanca: medio", "governanca: enxuto")

    # A lista do dia. Janelas em dias úteis a partir do dia de referência.
    def acao(ident, tipo, item, dono, lado, inicio, prazo, depende="", entregavel="", estado_="aberta", base_="nao") -> None:
        acrescentar(reg / "acoes.tsv", ident, tipo, item, dono, lado, dia_util(a, inicio), dia_util(a, prazo), base_, estado_, "consultor", dia_util(a, inicio), "", depende, entregavel)

    vazia = lista(a)
    confere("lista sem item aberto: só as perguntas do dia", "Atenção primeiro" not in vazia and "Próximas ações (1)" in vazia and "[reuniao]" in vazia, vazia)
    acao("T-001", "aprovacao", "Aprovar os critérios do diagnóstico", "Diretora de marketing", "cliente", -8, 10)
    acao("T-002", "tarefa", "Aplicar os critérios às plataformas", "Consultora", "consultoria", -1, 12, depende="T-001")
    acao("T-003", "tarefa", "Enviar a agenda das entrevistas", "Consultora", "consultoria", -6, -1)
    acao("T-004", "tarefa", "Montar o roteiro de entrevistas", "Consultora", "consultoria", -1, 15)
    acao("T-005", "tarefa", "Revisar o inventário", "Consultora", "consultoria", -10, 2)
    acao("T-006", "tarefa", "Entrevistar os donos das plataformas", "Consultora", "consultoria", -1, 20)
    acao("T-007", "tarefa", "Escrever o parecer", "Consultora", "consultoria", -1, 14, depende="T-001")
    acrescentar(reg / "riscos.tsv", "RS-001", "Os donos das plataformas não têm agenda", "Férias", "Atraso", "Consultora", "aberto", "consultor", a, "alta", "alta", "T-006", "Agendar cedo")
    acrescentar(reg / "riscos.tsv", "RS-002", "O roteiro fica longo", "Escopo", "Cansaço", "Consultora", "aberto", "consultor", a, "baixa", "alta", "T-004", "")
    acrescentar(base / "_intake/registro.tsv", "M-001", "Relatórios de uso", "dados", "Gerente de marketing", dia_util(a, -8), dia_util(a, 5), "pedido", "", "")
    acrescentar(reg / "dependencias.tsv", "DP-001", "Acesso ao painel de mídia", "Agência", "terceiro", dia_util(a, -1), dia_util(a, 8), "diag", "aberta", "consultor", dia_util(a, -1), "")
    do_dia = lista(a)
    proximas, aguardando, topo, confirmar = bloco(do_dia, "Próximas ações"), bloco(do_dia, "Aguardando o cliente"), bloco(do_dia, "Atenção primeiro"), bloco(do_dia, "Confirmar")
    confere("lista: o que é do cliente ou de terceiro fica em Aguardando o cliente", all(i in aguardando for i in ("T-001", "M-001", "DP-001")) and "T-001 (" not in proximas and "M-001" not in proximas, do_dia)
    confere("lista: o que não espera ninguém fica nas próximas ações", all(f"{i} (" in proximas for i in ("T-003", "T-004", "T-005", "T-006")), proximas)
    confere("lista: trabalho que depende do cliente sai das próximas ações", "T-002 (" not in proximas and "T-007 (" not in proximas and "diag (" not in proximas, proximas)
    confere("lista: quem espera mostra o que trava", "Trava: T-002, T-007" in aguardando and "Trava: diag" in aguardando, aguardando)
    ordem = re.findall(r"^\d\. (\S+) ", topo, flags=re.MULTILINE)
    confere("destaque: vencido primeiro, depois o risco alto e o que trava mais", ordem == ["T-003", "T-006", "T-001"], topo)
    confere("destaque: cada item diz por que subiu", "está vencido e sem data nova" in topo and "ameaçado por um risco de exposição alta" in topo and "trava 2 item(ns)" in topo, topo)
    confere("destaque: no máximo três, mesmo com mais candidatos", len(ordem) == 3 and "DP-001" not in topo and "T-005" not in topo)
    confere("destaque: risco de exposição baixa não sobe o item", "T-004" not in topo and "Risco de exposição alta" not in next(l for l in proximas.splitlines() if "T-004 (" in l))
    confere("confirmar: vencido pede uma das três respostas", "T-003" in confirmar and "Concluído, nova data ou não é mais necessário?" in confirmar, confirmar)
    confere("confirmar: follow-up do que espera o cliente há mais de dois dias úteis", "T-001 (aprovação, Diretora de marketing): você já fez o follow-up" in confirmar and "M-001 (pedido de material" in confirmar, confirmar)
    confere("confirmar: quem espera há pouco ainda não gera pergunta", "DP-001 (dependência" not in confirmar)
    confere("confirmar: o item parado que já tem a pergunta do follow-up não aparece duas vezes", confirmar.count("T-001") == 1 and "Sem movimento há 8 dia(s)" in aguardando, confirmar)
    confere("a lista nunca pergunta por horas", "oras trabalhadas" not in do_dia and "[horas]" not in do_dia)
    confere("--lista sozinha não grava nada", not (reg / "afazeres.md").exists() and not linha_de(reg / "alertas.tsv", "T-003"))
    aberta = rotina("--lista", "--abrir", "--hoje", a)
    gravada = (reg / "afazeres.md").read_text(encoding="utf-8") if (reg / "afazeres.md").is_file() else ""
    confere("--lista --abrir grava a lista e registra os avisos", aberta.returncode == 0 and "- [ ] T-004 (ação)" in gravada and "Atenção primeiro" in gravada and linha_de(reg / "alertas.tsv", "T-003"), gravada)

    # O trabalho que depende do cliente só segue com a confirmação.
    recusa = rotina("--concluir", "T-002", "--hoje", a)
    confere("concluir trabalho que espera o cliente é recusado", recusa.returncode == 1 and "ainda espera o cliente" in recusa.stdout and "\taberta\t" in linha_de(reg / "acoes.tsv", "T-002"), recusa.stdout)
    confere("andar com trabalho que espera o cliente também é recusado", rotina("--andando", "T-007", "--hoje", a).returncode == 1)
    confere("trabalho que não espera ninguém anda normalmente", rotina("--andando", "T-004", "--hoje", a).returncode == 0)
    confere("--cobrado só vale para o que espera o cliente", rotina("--cobrado", "T-004", "--hoje", a).returncode == 1 and rotina("--cobrado", "T-001", "--resposta", "talvez", "--hoje", a).returncode == 2)
    fatos = rotina("--cobrado", "T-001", "--resposta", "nao-cobrei", "--hoje", a)
    confere("ainda não cobrei: dá os fatos para a mensagem e não registra cobrança", fatos.returncode == 0 and "Redija a mensagem de cobrança de T-001" in fatos.stdout and "T-002, T-007" in fatos.stdout and not linha_de(reg / "cobrancas.tsv", "T-001"), fatos.stdout)
    cobrei = rotina("--cobrado", "T-001", "--hoje", a, "--nota", "Mensagem enviada")
    confere("cobrei hoje: a cobrança fica registrada com a data", cobrei.returncode == 0 and f"T-001\t{a}\tconsultor\tcobrado\tMensagem enviada" in (reg / "cobrancas.tsv").read_text(encoding="utf-8"), cobrei.stdout + cobrei.stderr)
    depois = lista(dia_util(a, 2))
    confere("depois da cobrança, a pergunta some e a lista mostra a data e a contagem", "T-001 (aprovação, Diretora" not in bloco(depois, "Confirmar") and f"Última cobrança: {a}, 1 feita(s)" in bloco(depois, "Aguardando o cliente"), depois)
    confere("passado o limite sem resposta, a pergunta do follow-up volta", "T-001 (aprovação, Diretora" in bloco(lista(dia_util(a, 3)), "Confirmar"))
    confere("o limite da cobrança é do projeto", "T-001 (aprovação, Diretora" in bloco(lista(dia_util(a, 2)), "Confirmar") if trocar(reg / "cadencias.tsv", "cobrar_depois_de\t2", "cobrar_depois_de\t1") is None else False)
    trocar(reg / "cadencias.tsv", "cobrar_depois_de\t1", "cobrar_depois_de\t2")
    acrescentar(reg / "cobrancas.tsv", "M-001", a, "consultor", "aprovou", "Resposta antiga, de um pedido reaberto")
    confere("só a cobrança conta como cobrança: a resposta do cliente não entra na contagem", "Nenhuma cobrança registrada" in next(l for l in bloco(lista(a), "Aguardando o cliente").splitlines() if "M-001 (" in l))
    material = rotina("--cobrado", "M-001", "--resposta", "aprovou", "--hoje", a)
    confere("material que chegou segue a skill de materiais, e não o follow-up", "receber-materiais" in material.stdout and "\tpedido\t" in linha_de(base / "_intake/registro.tsv", "M-001"))
    remarcada = rotina("--remarcar", "DP-001", dia_util(a, 9), "--motivo", "A agência pediu mais um dia", "--hoje", a)
    confere("dependência tem prazo, e o prazo muda guardando o anterior", remarcada.returncode == 0 and str(dia_util(a, 9)) in linha_de(reg / "dependencias.tsv", "DP-001") and f"DP-001\t{dia_util(a, 8)}" in (reg / "prazos.tsv").read_text(encoding="utf-8"), remarcada.stdout + remarcada.stderr)
    confere("dispensar a espera pede o motivo", rotina("--cobrado", "DP-001", "--resposta", "dispensada", "--hoje", a).returncode == 2 and "\taberta\t" in linha_de(reg / "dependencias.tsv", "DP-001"))
    dispensada = rotina("--cobrado", "DP-001", "--resposta", "dispensada", "--motivo", "O painel não será usado", "--hoje", a)
    confere("não depende mais: a dependência é cancelada e o entregável volta às próximas ações", dispensada.returncode == 0 and "\tcancelada\t" in linha_de(reg / "dependencias.tsv", "DP-001") and "diag (entregável)" in bloco(lista(a), "Próximas ações"), dispensada.stdout)
    aprovou = rotina("--cobrado", "T-001", "--resposta", "aprovou", "--hoje", dia_util(a, 1))
    confere("aprovou: o item fecha e o comando diz o que volta às próximas ações", aprovou.returncode == 0 and "\tconcluida\t" in linha_de(reg / "acoes.tsv", "T-001") and "Voltam às próximas ações: T-002, T-007" in aprovou.stdout, aprovou.stdout + aprovou.stderr)
    confere("com a confirmação, o trabalho volta à lista e pode ser concluído", "T-002 (" in bloco(lista(dia_util(a, 1)), "Próximas ações") and rotina("--concluir", "T-002", "--hoje", dia_util(a, 1)).returncode == 0)

    # Sem vencido e sem item que trava, sobem o prazo com menos folga e a espera mais longa.
    rotina("--concluir", "T-003", "--hoje", a)
    trocar(reg / "riscos.tsv", "Consultora\taberto\tconsultor\t" + str(a) + "\talta\talta", "Consultora\tfechado\tconsultor\t" + str(a) + "\talta\talta")
    calmo = bloco(lista(a), "Atenção primeiro")
    ordem = re.findall(r"^\d\. (\S+) ", calmo, flags=re.MULTILINE)
    confere("destaque: sem vencido nem trava, sobem o prazo próximo e a espera sem cobrança, nesta ordem", ordem == ["T-005", "M-001"] and "folga de 2 dia(s)" in calmo and "espera o cliente há 8 dia(s) útil(eis) sem cobrança" in calmo, calmo)
    confere("risco fechado deixa de subir o item", "T-006" not in calmo)
    trocar(reg / "acoes.tsv", "Entrevistar os donos das plataformas", "Entrevistar os donos de cada plataforma")
    texto_acoes = (reg / "acoes.tsv").read_text(encoding="utf-8").splitlines()
    (reg / "acoes.tsv").write_text("\n".join(l + "diag" if l.startswith("T-006\t") else l for l in texto_acoes) + "\n", encoding="utf-8")
    serve = lista(a)
    confere("ação que serve a um entregável sobe por ele, sem tirá-lo das próximas ações", "Trava: diag" in next(l for l in bloco(serve, "Próximas ações").splitlines() if "T-006 (" in l) and "diag (entregável)" in bloco(serve, "Próximas ações") and re.findall(r"^1\. (\S+) ", bloco(serve, "Atenção primeiro"), flags=re.MULTILINE) == ["T-006"], serve)
    acrescentar(reg / "dependencias.tsv", "DP-002", "Liberação do jurídico", "Jurídico do cliente", "cliente", dia_util(a, -6), dia_util(a, -1), "", "aberta", "consultor", dia_util(a, -6), "")
    confere("dependência vencida pede resposta como qualquer item com prazo", "DP-002 (dependência)" in bloco(lista(a), "Confirmar") and "DP-002" in bloco(lista(a), "Atenção primeiro"), lista(a))
    confere("dependência atendida sai da lista", rotina("--concluir", "DP-002", "--hoje", a).returncode == 0 and "\tatendida\t" in linha_de(reg / "dependencias.tsv", "DP-002") and "DP-002" not in lista(a))

    # Agenda, pausa e algum dia.
    acrescentar(reg / "ritos.tsv", "Ponto semanal", "semanal", a - datetime.timedelta(days=7), "", "Consultora, gerente", "")
    confere("agenda: a reunião do rito aparece no dia dela, e só nele", "Reunião: Ponto semanal" in bloco(lista(a), "Agenda do dia") and "Ponto semanal" not in bloco(lista(dia_util(a, 1)), "Agenda do dia"))
    confere("agenda: o que vence hoje aparece", "Vence hoje: T-005" in bloco(lista(dia_util(a, 2)), "Agenda do dia") and "Vence hoje" not in lista(a))
    acrescentar(reg / "adiados.tsv", "B-001", "Análise de subuso", "Falta o relatório", "depois do diagnóstico", "aberto")
    confere("algum dia: os adiados ficam em uma linha, fora da vista", "Algum dia: 1 item(ns) adiado(s)" in lista(a) and "Análise de subuso" not in bloco(lista(a), "Próximas ações"))
    rotina("--pausar", dia_util(a, 5), "--hoje", a)
    pausada = lista(a)
    confere("pausa: a lista avisa e não destaca nada", "em pausa até" in pausada and "Atenção primeiro" not in pausada and "Aguardando o cliente" not in pausada, pausada)
    rotina("--retomar")

    # Perguntas por frequência.
    confere("pergunta diária aparece com a chave", "[reuniao]" in lista(a) and "[dispensa]" in lista(a))
    respondida = rotina("--respondida", "reuniao,dispensa", "--hoje", a)
    confere("pergunta diária respondida some no dia e volta no dia seguinte", respondida.returncode == 0 and "[reuniao]" not in lista(a) and "[reuniao]" in lista(dia_util(a, 1)))
    confere("--respondida recusa pergunta que não existe", rotina("--respondida", "almoco", "--hoje", a).returncode == 1)
    rodar([PY, "entregaveis/_harness/scripts/fase.py"], projeto)
    quinta = a + datetime.timedelta(days=1)
    while quinta.weekday() != 3:
        quinta += datetime.timedelta(days=1)
    confere("pergunta semanal aparece na véspera do status, e não antes", "[riscos]" in lista(quinta) and "RS-002" in lista(quinta) and "[riscos]" not in lista(quinta - datetime.timedelta(days=1)), lista(quinta))
    confere("pergunta semanal sem assunto não aparece", "[premissas]" not in lista(quinta) and "[retorno]" not in lista(quinta) and "[algum_dia]" in lista(quinta))
    acrescentar(reg / "premissas.tsv", "PR-001", "O cliente mantém os dois contratos até março", "Proposta", "Diretora financeira", dia_util(a, 10), "a confirmar", "O parecer muda", "diag", "")
    confere("pergunta semanal com assunto aparece, com os itens", "[premissas]" in lista(quinta) and "PR-001: O cliente mantém" in lista(quinta))
    rotina("--respondida", "riscos", "--hoje", quinta)
    confere("pergunta semanal respondida só volta na véspera seguinte", "[riscos]" not in lista(quinta + datetime.timedelta(days=1)) and "[riscos]" not in lista(quinta + datetime.timedelta(days=6)) and "[riscos]" in lista(quinta + datetime.timedelta(days=7)))
    trocar(reg / "cadencias.tsv", "dia_do_status\t5", "dia_do_status\t1")
    confere("o dia do status é do projeto: com status na segunda, a véspera é a sexta", "[riscos]" in lista(quinta + datetime.timedelta(days=1)))
    trocar(reg / "cadencias.tsv", "dia_do_status\t1", "dia_do_status\t5")
    trocar(reg / "perguntas.tsv", "premissas\tsemanal", "premissas\tnunca")
    confere("a frequência de cada pergunta é do projeto", "[premissas]" not in lista(quinta))
    confere("pergunta de marco não aparece antes de um marco", "[satisfacao]" not in lista(quinta))

    # Versões e aceite.
    confere("aceite sem versão registrada é recusado", gov("--aceite", "diag", "--quem", "Diretora de marketing", "--hoje", a).returncode == 1)
    confere("versão pede o que mudou", gov("--versao", "diag", "--hoje", a).returncode == 2 and not linha_de(reg / "versoes.tsv", "diag"))
    versao = gov("--versao", "diag", "--mudou", "Primeira versão completa", "--enviada-a", "Diretora de marketing", "--hoje", a)
    confere("versão registrada com número, data, marca do conteúdo e destinatário", versao.returncode == 0 and re.search(rf"^diag\tv1\t{a}\t[0-9a-f]{{16}}\tPrimeira versão completa\tDiretora de marketing", (reg / "versoes.tsv").read_text(encoding="utf-8"), flags=re.MULTILINE) is not None, versao.stdout + versao.stderr)
    confere("versão enviada sem aceite vira pergunta semanal de retorno", "[retorno]" in lista(quinta) and "diag v1, enviada a Diretora de marketing" in lista(quinta))
    confere("aceite pede quem aceitou", gov("--aceite", "diag", "--hoje", a).returncode == 2)
    aceite = gov("--aceite", "diag", "--quem", "Diretora de marketing", "--ressalvas", "Rever a página 4", "--hoje", a)
    confere("aceite registrado na última versão, com quem, quando e as ressalvas", aceite.returncode == 0 and f"Diretora de marketing, {a}; ressalvas: Rever a página 4" in linha_de(reg / "versoes.tsv", "diag"), aceite.stdout)
    confere("versão de entregável que não existe é recusada", gov("--versao", "fantasma", "--mudou", "x").returncode != 0)
    confere("depois do aceite, aparecem as perguntas de marco e some a de retorno", "[satisfacao]" in lista(quinta) and "[materiais]" in lista(quinta) and "[retorno]" not in lista(quinta))
    rotina("--respondida", "satisfacao", "--hoje", quinta)
    confere("pergunta de marco respondida não volta sem marco novo", "[satisfacao]" not in lista(quinta + datetime.timedelta(days=14)) and "[beneficio]" in lista(quinta + datetime.timedelta(days=14)))

    # Linha de base e desvios.
    confere("linha de base sem nada com prazo é recusada", gov("--linha-de-base", "--hoje", a).returncode == 1 and not linha_de(reg / "linha-de-base.tsv", "1"))
    acao("T-010", "marco", "Entrega do diagnóstico", "Consultora", "consultoria", -1, 20, base_="sim")
    acao("T-011", "marco", "Apresentação à diretoria", "Consultora", "consultoria", -1, 30)
    trocar(base / "diag/briefing.md", "prazo:", f"prazo: {dia_util(a, 20)}")
    primeira = gov("--linha-de-base", "--aprovada-por", "Diretora de marketing", "--hoje", a)
    arquivo_base = reg / "linha-de-base.tsv"
    confere("linha de base: fotografa os entregáveis com prazo e os marcos", primeira.returncode == 0 and all(f"1\t{i}\t" in arquivo_base.read_text(encoding="utf-8") for i in ("diag", "T-010", "T-011")) and "1\tT-004" not in arquivo_base.read_text(encoding="utf-8"), arquivo_base.read_text(encoding="utf-8"))
    confere("sem mudança, a linha de base não é regravada nem acusa desvio", "já traz estas datas" in gov("--linha-de-base", "--hoje", a).stdout and arquivo_base.read_text(encoding="utf-8").count("\n1\t") == 3 and "Nenhum desvio" in gov("--desvios", "--hoje", a).stdout)
    rotina("--remarcar", "T-010", dia_util(a, 25), "--motivo", "O cliente pediu mais uma semana", "--hoje", a)
    dentro = gov("--desvios", "--hoje", a).stdout
    confere("desvio dentro da tolerância é mostrado sem alarme", "T-010: linha de base" in dentro and "5 dia(s) útil(eis) depois" in dentro and "ACIMA DA TOLERÂNCIA" not in dentro, dentro)
    rotina("--remarcar", "T-010", dia_util(a, 26), "--motivo", "Mais um dia", "--hoje", a)
    acima = gov("--desvios", "--hoje", a).stdout
    confere("desvio acima da tolerância é marcado e sobe ao patrocinador", "6 dia(s) útil(eis) depois. ACIMA DA TOLERÂNCIA de 5 dia(s)" in acima and "patrocinador" in acima, acima)
    confere("item vencido sem data nova desvia mais a cada dia", "T-011: linha de base" in gov("--desvios", "--hoje", dia_util(a, 33)).stdout and "vencido sem data nova, 3 dia(s) útil(eis) depois" in gov("--desvios", "--hoje", dia_util(a, 33)).stdout, gov("--desvios", "--hoje", dia_util(a, 33)).stdout)
    confere("um desvio acima da tolerância ainda não pede outro nível", "[nivel]" not in lista(quinta))
    rotina("--remarcar", "diag", dia_util(a, 28), "--motivo", "Depende do marco", "--hoje", a)
    confere("dois desvios acima da tolerância viram a pergunta de subir o nível", "[nivel]" in lista(quinta) and "passou da tolerância de prazo em 2 itens" in lista(quinta), lista(quinta))
    confere("versão nova da linha de base pede o motivo", gov("--linha-de-base", "--hoje", a).returncode == 2 and "\n2\t" not in arquivo_base.read_text(encoding="utf-8"))
    confere("linha de base que cita mudança sem aprovação é recusada", gov("--linha-de-base", "--motivo", "MU-001", "--hoje", a).returncode == 1 and "\n2\t" not in arquivo_base.read_text(encoding="utf-8"))
    acrescentar(reg / "mudancas.tsv", "MU-001", "Mais uma semana para o diagnóstico", "Diretora de marketing", a, "6 dias úteis", "nenhum", "nenhum", "aprovada", "Diretora de marketing", a, "consultor", "")
    segunda = gov("--linha-de-base", "--motivo", "MU-001", "--aprovada-por", "Diretora de marketing", "--hoje", a)
    confere("versão nova guarda a anterior e zera os desvios", segunda.returncode == 0 and arquivo_base.read_text(encoding="utf-8").count("\n1\t") == 3 and arquivo_base.read_text(encoding="utf-8").count("\n2\t") == 3 and "Nenhum desvio" in gov("--desvios", "--hoje", a).stdout)

    # A checagem dos registros de governança.
    def planta(arquivo: Path, campos: tuple, espera: str, nome: str, erro: bool) -> None:
        original = arquivo.read_text(encoding="utf-8")
        acrescentar(arquivo, *campos)
        saida = validar(projeto, "--so", "governanca")
        confere(nome, espera in saida.stdout and (saida.returncode != 0) == erro, saida.stdout)
        arquivo.write_text(original, encoding="utf-8")

    limpo = validar(projeto, "--so", "governanca")
    confere("os registros de governança corretos passam sem aviso", "Nenhum erro e nenhum aviso" in limpo.stdout, limpo.stdout)
    planta(reg / "premissas.tsv", ("PR-009", "x", "", "", "", "talvez", "", "", ""), "PR-009: o estado 'talvez' não existe", "checagem: estado de premissa fora da lista é erro", True)
    planta(reg / "mudancas.tsv", ("MU-009", "x", "", "", "", "", "", "feita", "", "", "", ""), "MU-009: o estado 'feita' não existe", "checagem: estado de mudança fora da lista é erro", True)
    planta(reg / "riscos.tsv", ("RS-009", "x", "", "", "", "aberto", "", "", "altíssima", "alta", "", ""), "RS-009: 'probabilidade' é alta, media ou baixa", "checagem: probabilidade fora da escala é erro", True)
    planta(reg / "governanca.tsv", ("inventado", "x", "", "", "mantido", "nivel", "", "", ""), "'inventado' não está no catálogo", "checagem: material fora do catálogo é erro", True)
    planta(reg / "acoes.tsv", ("T-090", "tarefa", "x", "Consultora", "consultoria", a, dia_util(a, 9), "nao", "aberta", "consultor", a, "", "T-999", ""), "T-090: o campo 'depende_de' cita T-999", "checagem: dependência de item que não existe é aviso", False)
    planta(reg / "riscos.tsv", ("RS-008", "x", "", "", "", "aberto", "", "", "alta", "alta", "T-998", ""), "RS-008: o campo 'ameaca' cita T-998", "checagem: risco que ameaça item que não existe é aviso", False)
    planta(reg / "acoes.tsv", ("T-091", "tarefa", "x", "Consultora", "consultoria", a, dia_util(a, 9), "nao", "concluida", "consultor", a, "", "M-001", ""), "T-091 foi concluída, mas dependia de M-001", "checagem: trabalho concluído à frente do cliente é aviso", False)

    # O pacote para outros ambientes leva os registros de governança.
    pacote = rodar([PY, "entregaveis/_harness/scripts/empacotar.py", "--projeto"], projeto)
    do_projeto = (base / "_ambiente/5-projeto.txt").read_text(encoding="utf-8") if (base / "_ambiente/5-projeto.txt").is_file() else ""
    confere("o pacote do projeto leva o nível, os papéis e as cobranças", pacote.returncode == 0 and all(f"### {n}" in do_projeto for n in ("governanca.tsv", "papeis.tsv", "cobrancas.tsv", "linha-de-base.tsv")) and "Diretora de marketing" in do_projeto, pacote.stdout + pacote.stderr)

    # O hook de mensagem lembra o registro do follow-up.
    def mensagem(texto: str) -> str:
        return rodar([PY, base / "_harness/hooks/mensagem.py"], projeto, json.dumps({"cwd": str(projeto), "prompt": texto})).stdout

    confere("mensagem: resposta do cliente lembra o registro do follow-up", "--cobrado" in mensagem("a diretora de marketing aprovou os critérios ontem") and "--cobrado" in mensagem("já cobrei o relatório de uso"))
    confere("mensagem: pedido comum não lembra o follow-up", "--cobrado" not in mensagem("inclua uma página sobre mídia paga"))

    # Um projeto de versão anterior recebe as colunas e os sinais novos, sem perder nada.
    antigo = tmp / "governanca-antigo"
    antigo.mkdir()
    instalar(antigo)
    ant = antigo / "entregaveis/_projeto"
    for nome in ("perguntas.tsv", "papeis.tsv", "linha-de-base.tsv"):
        (ant / nome).unlink()
    (ant / "acoes.tsv").write_text("# Ações\nid\ttipo\titem\tdono\tlado\tinicio\tprazo\tbase\testado\torigem\tmovida_em\tobservacao\nT-001\ttarefa\tItem antigo\tConsultora\tconsultoria\t2026-01-05\t2026-01-30\tnao\taberta\tconsultor\t2026-01-05\tNota antiga\n", encoding="utf-8")
    (ant / "cadencias.tsv").write_text("sinal\tvalor\tobservacao\nparado_minimo\t4\tAjuste do projeto\npausa_ate\t\t\n", encoding="utf-8")
    (antigo / "entregaveis/_harness/VERSAO").write_text("0.8.0\n", encoding="utf-8")
    atualizado = instalar(antigo, "--atualizar")
    acoes = (ant / "acoes.tsv").read_text(encoding="utf-8")
    cadencias = (ant / "cadencias.tsv").read_text(encoding="utf-8")
    confere("--atualizar acrescenta as colunas novas no fim e mantém as linhas", atualizado.returncode == 0 and "\tobservacao\tdepende_de\tentregavel\n" in acoes and "T-001\ttarefa\tItem antigo" in acoes and "Nota antiga\n" in acoes, acoes + atualizado.stderr)
    confere("--atualizar acrescenta os sinais novos e mantém o valor que o projeto ajustou", "cobrar_depois_de\t2" in cadencias and "dia_do_status\t5" in cadencias and "parado_minimo\t4\tAjuste do projeto" in cadencias and cadencias.count("parado_minimo") == 1, cadencias)
    confere("--atualizar cria os registros de governança que faltavam", all((ant / n).is_file() for n in ("perguntas.tsv", "papeis.tsv", "linha-de-base.tsv")))
    instalar(antigo, "--atualizar")
    confere("atualizar de novo não duplica coluna nem sinal", (ant / "acoes.tsv").read_text(encoding="utf-8").count("depende_de") == 1 and (ant / "cadencias.tsv").read_text(encoding="utf-8").count("cobrar_depois_de") == 1)
    confere("a lista do dia lê o registro de versão anterior", "T-001 (ação): Item antigo" in rodar([PY, "entregaveis/_harness/scripts/rotina.py", "--lista"], antigo).stdout)


# --- Materiais emitidos, ciclo de aprovação e ciclo de mudança ---------------


def testar_emissao(tmp: Path) -> None:
    print("Materiais emitidos, aprovação e mudança")
    projeto = tmp / "emissao"
    projeto.mkdir()
    (projeto / ".git").mkdir()
    instalar(projeto)
    base = projeto / "entregaveis"
    reg = base / "_projeto"
    montar_exemplo(projeto)
    d0 = datetime.date(2026, 3, 2)  # uma segunda-feira

    def d(n: int) -> datetime.date:
        return dia_util(d0, n)

    def gov(*args, hoje=d0) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/governanca.py", *args, "--hoje", hoje], projeto)

    def rotina(*args, hoje=d0) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/rotina.py", *args, "--hoje", hoje], projeto)

    def em(*args, hoje=d0) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/emitir.py", *args, "--hoje", hoje], projeto)

    def status(*args, hoje=d0) -> str:
        return em("status-semanal", *args, hoje=hoje).stdout

    def secao(texto: str, titulo: str) -> str:
        """O corpo de uma seção do material, até o próximo título."""
        partes = re.split(r"^## ", texto, flags=re.MULTILINE)
        return next((parte for parte in partes if parte.startswith(titulo)), "")

    def acrescentar(arquivo: Path, *campos) -> None:
        with arquivo.open("a", encoding="utf-8") as f:
            f.write("\t".join(str(c) for c in campos) + "\n")

    def linha_de(arquivo: Path, ident: str) -> str:
        return next((l for l in arquivo.read_text(encoding="utf-8").splitlines() if l.startswith(ident + "\t")), "")

    def trocar(arquivo: Path, antes: str, depois: str) -> None:
        texto = arquivo.read_text(encoding="utf-8")
        assert antes in texto, antes
        arquivo.write_text(texto.replace(antes, depois, 1), encoding="utf-8")

    def acao(ident, tipo, item, dono, lado, inicio, prazo, estado_="aberta", base_="nao", entregavel="", movida=None) -> None:
        acrescentar(reg / "acoes.tsv", ident, tipo, item, dono, lado, d(inicio), d(prazo), base_, estado_, "consultor", d(inicio if movida is None else movida), "", "", entregavel)

    def cor(*args, hoje=d0) -> str:
        return (re.search(r"\*\*Semáforo: (\w+)\.\*\*", status(*args, hoje=hoje)) or [None, "?"])[1]

    gov("--nivel", "enxuto")
    confere("a instalação cria o registro dos materiais emitidos", (reg / "emitidos.tsv").is_file() and "prazo_de_aprovacao\t5" in (reg / "cadencias.tsv").read_text(encoding="utf-8"))
    lista_de_materiais = em().stdout
    confere("emitir.py sem argumento lista o que monta e o que está na lista do projeto", "status-semanal: Status semanal de uma página. Na lista do projeto" in lista_de_materiais and "pauta: Pauta e pré-leitura. Fora da lista do projeto" in lista_de_materiais, lista_de_materiais)

    # O status de um projeto sem nada aberto.
    vazio = em("status-semanal")
    confere("status sem nada aberto: verde, com o aviso de que falta a linha de base", vazio.returncode == 0 and cor() == "verde" and "ainda não tem linha de base, e por isso o desvio de prazo não foi medido" in vazio.stdout and "Diagnóstico de martech, Varejista Exemplo" in vazio.stdout, vazio.stdout + vazio.stderr)
    confere("status: seção sem dado diz que não há, e seção opcional não sai", "Nenhuma decisão pendente." in secao(vazio.stdout, "Decisões pedidas") and "## Datas deslocadas" not in vazio.stdout and "## Esforço" not in vazio.stdout)
    confere("status: o rascunho diz quem envia e não é gravado sem --gravar", "Quem revisa e envia é o consultor" in vazio.stdout and not (reg / "emitidos").exists())

    # O semáforo, com os dois lados de cada regra.
    acrescentar(reg / "riscos.tsv", "RS-001", "A base de clientes atrasa", "", "", "Consultora", "proposto", "A-001", d0, "alta", "alta", "", "")
    confere("semáforo: risco ainda proposto não muda a cor", cor() == "verde")
    trocar(reg / "riscos.tsv", "\tproposto\t", "\taberto\t")
    confere("semáforo: risco de exposição alta deixa amarelo, com o motivo", cor() == "amarelo" and "RS-001: risco de exposição alta" in status(), status())
    trocar(reg / "riscos.tsv", "alta\talta", "media\tmedia")
    confere("semáforo: risco de exposição média não muda a cor", cor() == "verde")
    acao("T-001", "tarefa", "Mapear os contratos", "Consultora", "consultoria", -5, -1)
    confere("semáforo: item vencido sem data nova deixa amarelo", cor() == "amarelo" and f"T-001 (ação): venceu em {d(-1)}" in status(), status())
    confere("semáforo: o mesmo item, na véspera do prazo, não muda a cor", cor(hoje=d(-2)) == "verde")
    rotina("--concluir", "T-001")
    confere("semáforo: item concluído volta ao verde", cor() == "verde", status())
    acrescentar(reg / "issues.tsv", "IS-001", "O acesso ao painel caiu", "Para a coleta", "TI do cliente", "Reabrir o acesso", d(3), "nao", "aberta", "consultor", "", "")
    confere("semáforo: issue aberta sem escalada não deixa vermelho", cor() == "verde")
    trocar(reg / "issues.tsv", "\tnao\taberta", "\tsim\taberta")
    confere("semáforo: issue escalada deixa vermelho", cor() == "vermelho" and "IS-001: issue escalada" in status(), status())
    trocar(reg / "issues.tsv", "\tsim\taberta", "\tsim\tresolvida")
    confere("semáforo: issue resolvida não conta", cor() == "verde")
    trocar(base / "diag/briefing.md", "prazo:", f"prazo: {d(20)}")
    acao("T-002", "marco", "Apresentação à diretoria", "Consultora", "consultoria", 0, 30)
    gov("--linha-de-base", "--aprovada-por", "Diretora de marketing")
    confere("semáforo: com linha de base e sem desvio, verde sem ressalva", cor() == "verde" and "ainda não tem linha de base" not in status() and "Nenhum desvio contra a linha de base" in status(), status())
    rotina("--remarcar", "T-002", d(35), "--motivo", "O cliente pediu uma semana")
    dentro = status()
    confere("semáforo: desvio dentro da tolerância deixa amarelo", cor() == "amarelo" and "T-002: linha de base" in dentro and "5 dia(s) útil(eis) depois" in dentro, dentro)
    confere("status: a data mudada entra em datas deslocadas e na tabela de marcos", "T-002: original" in secao(dentro, "Datas deslocadas") and f"| T-002: Apresentação à diretoria | {d(30)} | {d(35)} | no prazo, 5 dia(s) útil(eis) depois |" in secao(dentro, "Marcos"), dentro)
    rotina("--remarcar", "T-002", d(36), "--motivo", "Mais um dia")
    confere("semáforo: desvio acima da tolerância deixa vermelho", cor() == "vermelho" and "ACIMA DA TOLERÂNCIA" in status(), status())

    # A cor do consultor.
    confere("a cor trocada pede a justificativa", em("status-semanal", "--cor", "amarelo").returncode == 2)
    trocado = status("--cor", "amarelo", "--motivo", "O comitê já aprovou a data nova")
    confere("a cor do consultor aparece com o motivo e com a cor da regra", "**Semáforo: amarelo.** Definido pelo consultor: O comitê já aprovou a data nova" in trocado and "Pela regra, a cor seria vermelho" in trocado and "ACIMA DA TOLERÂNCIA" in trocado, trocado)
    confere("a cor igual à da regra não vira cor do consultor", "Definido pelo consultor" not in status("--cor", "vermelho", "--motivo", "Confirmo"))

    # Feito, a fazer e o período entre uma emissão e a seguinte.
    feito = secao(status(), "Feito no período")
    confere("status: a ação concluída no período entra em feito", "T-001: Mapear os contratos, concluído em " + str(d0) in feito, feito)
    confere("status: sem emissão anterior, o período é de sete dias", f"Período de {d0 - datetime.timedelta(days=6)} a {d0}" in status() and "T-001" not in secao(status(hoje=d(6)), "Feito no período"))
    acao("T-003", "tarefa", "Entrevistar os donos das plataformas", "Consultora", "consultoria", 0, 4)
    acao("T-004", "tarefa", "Montar o anexo de custos", "Consultora", "consultoria", 0, 18)
    acao("T-005", "tarefa", "Enviar os relatórios de uso", "Gerente de marketing", "cliente", 0, 3)
    afazer = secao(status(), "A fazer na próxima semana")
    confere("status: a fazer traz o que vence em sete dias e o entregável aberto", "T-003 (ação)" in afazer and "diag (entregável)" in afazer and "T-004" not in afazer and "T-005" not in afazer, afazer)
    rotina("--cobrado", "T-005", hoje=d(1))
    pend = secao(status(hoje=d(4)), "Pendências do cliente")
    confere("status: a pendência do cliente traz o dono, o atraso e as cobranças", "T-005 (ação): Enviar os relatórios de uso. Com: Gerente de marketing" in pend and "vencido há 1 dia(s) útil(eis)" in pend and f"Cobranças: 1, a última em {d(1)}" in pend and "T-003" not in pend, pend)
    gravado = em("status-semanal", "--gravar", hoje=d(4))
    arquivo = reg / "emitidos" / f"{d(4)}-status-semanal.md"
    confere("--gravar grava o rascunho e registra a emissão", gravado.returncode == 0 and arquivo.is_file() and arquivo.read_text(encoding="utf-8") == gravado.stdout and f"{d(4)}\tstatus-semanal\t\tentregaveis/_projeto/emitidos/{d(4)}-status-semanal.md\trascunho" in (reg / "emitidos.tsv").read_text(encoding="utf-8"), gravado.stdout + gravado.stderr)
    confere("--gravar: o rodapé fica fora do rascunho e manda humanizar", "Rascunho gravado em" in gravado.stderr and "humanizar-texto" in gravado.stderr and "Rascunho gravado em" not in gravado.stdout)
    em("status-semanal", "--gravar", hoje=d(4))
    confere("gravar de novo no mesmo dia não duplica a emissão", (reg / "emitidos.tsv").read_text(encoding="utf-8").count("\tstatus-semanal\t") == 1)
    rotina("--concluir", "T-003", hoje=d(6))
    seguinte = status(hoje=d(8))
    confere("o status seguinte conta o período a partir da última emissão", f"Período de {d(4) + datetime.timedelta(days=1)} a {d(8)}" in seguinte and "T-003: Entrevistar" in secao(seguinte, "Feito no período") and "T-001" not in secao(seguinte, "Feito no período"), seguinte)
    confere("a emissão do próprio dia não encurta o período", f"Período de {d0 - datetime.timedelta(days=2)} a {d(4)}" in status(hoje=d(4)), status(hoje=d(4)))

    # Riscos, decisões, esforço.
    trocar(reg / "riscos.tsv", "media\tmedia", "alta\talta")
    acrescentar(reg / "riscos.tsv", "RS-002", "A diretora sai de férias", "", "", "Consultora", "aberto", "consultor", d0, "alta", "media", "", "Antecipar a aprovação")
    acrescentar(reg / "riscos.tsv", "RS-003", "O contrato muda de dono", "", "", "Consultora", "aberto", "consultor", d0, "media", "media", "", "")
    acrescentar(reg / "riscos.tsv", "RS-004", "O fornecedor demora", "", "", "Consultora", "aberto", "consultor", d0, "baixa", "baixa", "", "")
    riscos = secao(status(), "Riscos e issues")
    confere("status: só os três riscos de maior exposição, do maior para o menor", riscos.index("RS-001") < riscos.index("RS-002") < riscos.index("RS-003") and "RS-004" not in riscos and "Resposta: Antecipar a aprovação" in riscos, riscos)
    confere("status: risco sem resposta sai marcado para completar", "RS-003 (risco, media/media): O contrato muda de dono. Resposta: PREENCHER" in riscos and "ponto(s) marcado(s) com PREENCHER" in em("status-semanal").stderr)
    acao("T-006", "decisao", "Escolher entre renovar ou trocar a plataforma de e-mail", "Diretora de marketing", "cliente", 0, 8)
    acao("T-007", "decisao", "Decisão ainda em proposta", "Diretora de marketing", "cliente", 0, 8, estado_="proposta")
    pedidas = secao(status(), "Decisões pedidas")
    confere("status: a decisão pedida aparece com quem decide e até quando", f"T-006: Escolher entre renovar ou trocar a plataforma de e-mail. Quem decide: Diretora de marketing. Até: {d(8)}" in pedidas and "T-007" not in pedidas, pedidas)
    acrescentar(reg / "esforco.tsv", d0, "Consultora", "", "diag", "12,5", "")
    confere("status: o esforço só aparece quando há lançamento", "Esforço lançado: 12.5 hora(s)" in secao(status(), "Esforço"), status())

    # O status executivo e a pauta.
    acrescentar(reg / "reunioes.tsv", "A-001", d0, "Reunião de acompanhamento", "", "Consultora", "anotação", "", "", "realizada", "2 ações", d0)
    confere("status: a reunião realizada no período entra em feito", f"Reunião de {d0}: Reunião de acompanhamento, 2 ações" in secao(status(), "Feito no período"), status())
    executivo = em("status-executivo")
    confere("status executivo: responde às cinco perguntas", all(f"## {n}. " in executivo.stdout for n in range(1, 6)) and "**Semáforo: vermelho.**" in executivo.stdout and "| T-002: Apresentação à diretoria" in executivo.stdout, executivo.stdout)
    confere("status executivo: opções, recomendação e prognóstico ficam para o consultor", "T-006: Escolher entre renovar" in secao(executivo.stdout, "5. O que precisa ser decidido") and "Opções e recomendação: PREENCHER" in executivo.stdout and "Leitura do consultor sobre a data final e o que a sustenta: PREENCHER" in executivo.stdout)
    confere("material fora da lista do nível sai com o aviso de como incluir", "governanca.py --incluir status-executivo" in executivo.stderr and "--incluir" not in em("status-semanal").stderr)
    confere("status executivo: reunião não é entrega", "Reunião de" not in secao(executivo.stdout, "2. O que foi entregue") and "T-001: Mapear os contratos" in secao(executivo.stdout, "2. O que foi entregue"))
    acrescentar(reg / "ritos.tsv", "Comitê quinzenal", "quinzenal", d0, "", "Consultora, diretora de marketing", "")
    sem_reuniao = em("pauta")
    confere("pauta sem reunião é recusada e lista as reuniões que se repetem", sem_reuniao.returncode == 2 and "Comitê quinzenal" in sem_reuniao.stdout)
    pauta = em("pauta", "--reuniao", "comite quinzenal", "--data", d(2))
    confere("pauta: participantes do rito, data e decisões esperadas", pauta.returncode == 0 and "# Pauta: Comitê quinzenal" in pauta.stdout and f"Reunião de {d(2)}" in pauta.stdout and "Participantes: Consultora, diretora de marketing." in pauta.stdout and "T-006" in secao(pauta.stdout, "Decisões esperadas"), pauta.stdout)
    confere("pauta: cinco blocos com tempo, preenchidos com os itens abertos", all(f"({m} min)" in pauta.stdout for m in (5, 10, 15)) and len(re.findall(r"^## .*\(\d+ min\)$", pauta.stdout, flags=re.MULTILINE)) == 5 and "RS-001" in secao(pauta.stdout, "Riscos, issues e dependências") and "T-004: Montar o anexo" in secao(pauta.stdout, "Ações e responsáveis"), pauta.stdout)
    confere("pauta: o objetivo fica para o consultor e o último status é material de leitura", "Objetivo: PREENCHER" in pauta.stdout and f"Último status: entregaveis/_projeto/emitidos/{d(4)}-status-semanal.md" in secao(pauta.stdout, "Material de leitura"), pauta.stdout)
    livre = em("pauta", "--reuniao", "Conversa com a diretora financeira")
    confere("pauta de reunião fora dos ritos marca os participantes para completar", "# Pauta: Conversa com a diretora financeira" in livre.stdout and "Participantes: PREENCHER." in livre.stdout)
    gov("--incluir", "pauta")
    confere("material incluído na lista sai sem o aviso", "--incluir" not in em("pauta", "--reuniao", "Comitê quinzenal").stderr)
    gravada = em("pauta", "--reuniao", "Comitê quinzenal", "--gravar")
    confere("pauta gravada leva a reunião no nome do arquivo", (reg / "emitidos" / f"{d0}-pauta-comite-quinzenal.md").is_file() and "\tpauta\tComitê quinzenal\t" in (reg / "emitidos.tsv").read_text(encoding="utf-8"), gravada.stderr)

    # O ciclo de aprovação: o envio abre, o silêncio não aceita e o aceite fecha.
    confere("nota de entrega e aceite pedem o entregável", em("nota-de-entrega").returncode == 2 and em("aceite").returncode == 2)
    sem_versao = em("aceite", "diag")
    confere("aceite de entregável sem versão diz como registrar o envio", sem_versao.returncode != 0 and "--versao diag" in sem_versao.stderr, sem_versao.stdout + sem_versao.stderr)
    acrescentar(reg / "versoes.tsv", "diag", "v1", d0, "abc", "Primeira versão", "Diretora de marketing", "")
    antiga = secao(status(), "Pendências do cliente")
    confere("status: envio antigo sem aceite e sem aprovação aberta entra nas pendências", f"diag v1: enviada a Diretora de marketing em {d0}, sem aceite registrado. Resposta esperada até {d(5)}" in antiga, antiga)
    (reg / "versoes.tsv").write_text("\n".join((reg / "versoes.tsv").read_text(encoding="utf-8").splitlines()[:-1]) + "\n", encoding="utf-8")
    interna = gov("--versao", "diag", "--mudou", "Rascunho interno")
    confere("versão sem envio não abre aprovação", interna.returncode == 0 and "Aprovação" not in interna.stdout and "\taprovacao\tAprovar diag" not in (reg / "acoes.tsv").read_text(encoding="utf-8"))
    envio = gov("--versao", "diag", "--mudou", "Versão para a diretoria", "--enviada-a", "Gerente de marketing")
    primeira = linha_de(reg / "acoes.tsv", "T-008")
    confere("o envio abre a aprovação do cliente, com o prazo padrão quando nada foi combinado", envio.returncode == 0 and f"T-008\taprovacao\tAprovar diag v2\tGerente de marketing\tcliente\t{d0}\t{d(5)}\tnao\taberta\tenvio" in primeira and primeira.endswith("\tdiag") and "silêncio não vale como aceite" in envio.stdout, envio.stdout + primeira)
    acrescentar(reg / "papeis.tsv", "diag", "Consultora", "Diretora de marketing", "", "", "3", "")
    reenvio = gov("--versao", "diag", "--mudou", "Ajustes pedidos", "--enviada-a", "Gerente de marketing", hoje=d(1))
    segunda = linha_de(reg / "acoes.tsv", "T-009")
    confere("o envio seguinte troca a aprovação e usa o aprovador e o prazo combinados", "\tcancelada\t" in linha_de(reg / "acoes.tsv", "T-008") and f"T-009\taprovacao\tAprovar diag v3\tDiretora de marketing\tcliente\t{d(1)}\t{d(4)}\t" in segunda and "\taberta\t" in segunda, reenvio.stdout + segunda)
    trocar(reg / "cadencias.tsv", "prazo_de_aprovacao\t5", "prazo_de_aprovacao\t2")
    trocar(reg / "papeis.tsv", "\t3\t", "\t\t")
    confere("o prazo padrão de resposta é do projeto", f"Resposta até {d(3)}, 2 dia(s) útil(eis) depois do envio" in em("nota-de-entrega", "diag", hoje=d(1)).stdout)
    trocar(reg / "papeis.tsv", "Diretora de marketing\t\t\t\t", "Diretora de marketing\t\t\t3\t")
    nota = em("nota-de-entrega", "diag", hoje=d(1))
    confere("nota de entrega: versão, o que mudou, aprovador e data de resposta", "diag, versão v3" in nota.stdout and "O que mudou nesta versão: Ajustes pedidos" in nota.stdout and "Quem aprova: Diretora de marketing." in nota.stdout and f"Resposta até {d(4)}, 3 dia(s) útil(eis) depois do envio" in nota.stdout and "silêncio não vale como aceite" in nota.stdout, nota.stdout)
    aguardando = rotina("--lista", hoje=d(2)).stdout
    confere("a aprovação aberta entra em aguardando o cliente na lista do dia", "T-009 (aprovação): Aprovar diag v3" in aguardando[aguardando.find("Aguardando o cliente"):], aguardando)
    no_prazo = em("ciclo-de-aprovacao", hoje=d(3)).stdout
    confere("ciclo de aprovação: dentro do prazo, aguardando", f"| diag | Diretora de marketing | 3 dia(s) útil(eis) | v3, {d(1)} | aguardando a resposta até {d(4)}. Cobranças: 0 (T-009) |" in no_prazo, no_prazo)
    rotina("--cobrado", "T-009", hoje=d(5))
    vencido = em("ciclo-de-aprovacao", hoje=d(6)).stdout
    confere("ciclo de aprovação: depois do prazo, o silêncio não vale como aceite e a cobrança é contada", f"sem resposta, vencido em {d(4)}, há 2 dia(s) útil(eis). O silêncio não vale como aceite. Cobranças: 1 (T-009)" in vencido, vencido)
    confere("a aprovação vencida entra no status como pendência do cliente", "T-009 (aprovação): Aprovar diag v3. Com: Diretora de marketing" in secao(status(hoje=d(6)), "Pendências do cliente") and "diag v3: enviada" not in status(hoje=d(6)))
    pedido = em("aceite", "diag", hoje=d(2))
    confere("antes do aceite, o material é o pedido, com a data de resposta", "# Pedido de aceite: Diagnóstico de martech" in pedido.stdout and f"Pedimos a confirmação até {d(4)}" in pedido.stdout and "O aceite ainda não foi registrado" in pedido.stdout and "Aceite registrado" not in pedido.stdout, pedido.stdout)
    gov("--incluir", "termo-de-aceite")
    termo = em("termo-de-aceite", "diag", hoje=d(2))
    confere("com o termo de aceite na lista, o pedido vira termo formal", "# Termo de aceite: Diagnóstico de martech" in termo.stdout and "( ) Aceito com ressalvas" in termo.stdout and "Nome: Diretora de marketing" in termo.stdout and "Pedimos a confirmação" not in termo.stdout, termo.stdout)
    gov("--tirar", "termo-de-aceite", "--motivo", "Uma mensagem basta")
    aceite = gov("--aceite", "diag", "--quem", "Diretora de marketing", "--ressalvas", "Falta o anexo de custos", hoje=d(6))
    confere("o aceite fecha a aprovação aberta", aceite.returncode == 0 and "A aprovação T-009 foi fechada" in aceite.stdout and "\tconcluida\t" in linha_de(reg / "acoes.tsv", "T-009") and f"Aceite de Diretora de marketing em {d(6)}" in linha_de(reg / "acoes.tsv", "T-009"), aceite.stdout)
    confirmacao = em("aceite", "diag", hoje=d(6))
    confere("depois do aceite, o material é a confirmação, com quem aceitou e as ressalvas", "# Confirmação de aceite: Diagnóstico de martech" in confirmacao.stdout and f"Aceite registrado: Diretora de marketing, {d(6)}; ressalvas: Falta o anexo de custos." in confirmacao.stdout and "Pedimos a confirmação" not in confirmacao.stdout, confirmacao.stdout)
    confere("sem marco de pagamento ligado, a confirmação não fala de faturamento", "Aviso de faturamento" not in confirmacao.stdout)
    acao("T-010", "marco", "Pagamento da segunda parcela", "Financeiro", "cliente", 0, 12, entregavel="outro")
    confere("marco de pagamento de outro entregável não entra", "Aviso de faturamento" not in em("aceite", "diag", hoje=d(6)).stdout)
    acao("T-011", "marco", "Pagamento da primeira parcela", "Financeiro", "cliente", 0, 12, entregavel="diag")
    faturar = em("aceite", "diag", hoje=d(6)).stdout
    confere("com marco de pagamento ligado, a confirmação leva o aviso de faturamento", "O aceite cumpre a condição do marco T-011: Pagamento da primeira parcela." in secao(faturar, "Aviso de faturamento"), faturar)
    confere("ciclo de aprovação: o envio aceito aparece como aceito", "| aceito: Diretora de marketing" in em("ciclo-de-aprovacao", hoje=d(7)).stdout)
    gov("--versao", "diag", "--mudou", "Com o anexo", "--enviada-a", "Diretora de marketing", hoje=d(7))
    acao("T-013", "tarefa", "Enviar o logotipo para a capa", "Gerente de marketing", "cliente", 0, 12, entregavel="diag")
    respondeu = rotina("--cobrado", "T-012", "--resposta", "aprovou", hoje=d(8))
    confere("a resposta do cliente a uma aprovação lembra o registro do aceite", "governanca.py --aceite diag" in respondeu.stdout and "--aceite" not in rotina("--cobrado", "T-013", "--resposta", "aprovou", hoje=d(8)).stdout, respondeu.stdout)

    # O ciclo de mudança: pedido, impacto e decisão.
    mud = reg / "mudancas.tsv"
    confere("mudança sem solicitante é recusada", gov("--mudanca", "Incluir o custo por loja").returncode == 2 and not linha_de(mud, "MU-001"))
    aberta = gov("--mudanca", "Incluir o custo por loja", "--solicitante", "Diretora financeira", "--origem", "A-002")
    confere("a mudança nasce como proposta, com quem pediu, a data e a origem", aberta.returncode == 0 and f"MU-001\tIncluir o custo por loja\tDiretora financeira\t{d0}\t\t\t\tproposta\t\t\tA-002" in linha_de(mud, "MU-001") and "Nenhum trabalho deste pedido começa antes da decisão" in aberta.stdout, aberta.stdout + linha_de(mud, "MU-001"))
    proposta = em("mudanca", "MU-001")
    confere("solicitação de mudança ainda sem análise diz o que falta", "# Solicitação de mudança MU-001" in proposta.stdout and "Prazo: Ainda não analisado" in proposta.stdout and "( ) Aprovada" in proposta.stdout, proposta.stdout)
    confere("solicitação de mudança que não existe é recusada", em("mudanca", "MU-099").returncode != 0 and "Não achei a mudança 'MU-099'" in em("mudanca", "MU-099").stderr and em("mudanca").returncode == 2)
    confere("mudança proposta não entra nas decisões pedidas", "MU-001" not in status())
    confere("aprovar sem impacto medido é recusado", gov("--decidir", "MU-001", "--decisao", "aprovada", "--quem", "Diretora de marketing").returncode == 1 and "\tproposta\t" in linha_de(mud, "MU-001"))
    confere("analisar pede ao menos um impacto", gov("--analisar", "MU-001").returncode == 2 and "\tproposta\t" in linha_de(mud, "MU-001"))
    parcial = gov("--analisar", "MU-001", "--impacto-prazo", "5 dias úteis no diagnóstico")
    confere("análise parcial fica em análise e diz o que falta", "\tem analise\t" in linha_de(mud, "MU-001") and "Falta medir o impacto em esforço, escopo" in parcial.stdout and gov("--decidir", "MU-001", "--decisao", "aprovada", "--quem", "Diretora de marketing").returncode == 1, parcial.stdout)
    completa = gov("--analisar", "MU-001", "--impacto-esforco", "16 horas", "--impacto-escopo", "Uma página a mais")
    confere("análise completa mantém o que já estava e aponta a solicitação", "5 dias úteis no diagnóstico\t16 horas\tUma página a mais\tem analise" in linha_de(mud, "MU-001") and "emitir.py mudanca MU-001" in completa.stdout, linha_de(mud, "MU-001"))
    confere("mudança em análise entra nas decisões pedidas do status, com o impacto", "MU-001: mudança pedida por Diretora financeira, Incluir o custo por loja. Impacto: prazo 5 dias úteis no diagnóstico; esforço 16 horas; escopo Uma página a mais" in secao(status(), "Decisões pedidas"), status())
    confere("decidir pede quem decidiu e uma decisão válida", gov("--decidir", "MU-001", "--decisao", "aprovada").returncode == 2 and gov("--decidir", "MU-001", "--decisao", "talvez", "--quem", "Diretora de marketing").returncode == 2 and "\tem analise\t" in linha_de(mud, "MU-001"))
    rotina("--remarcar", "diag", d(25), "--motivo", "MU-001")
    base_tsv = reg / "linha-de-base.tsv"
    confere("linha de base que cita mudança ainda sem decisão é recusada", gov("--linha-de-base", "--motivo", "MU-001").returncode == 1 and "\n2\t" not in base_tsv.read_text(encoding="utf-8"))
    aprovada = gov("--decidir", "MU-001", "--decisao", "aprovada", "--quem", "Diretora de marketing", hoje=d(1))
    confere("a aprovação grava quem decidiu e quando, e manda levar ao plano", aprovada.returncode == 0 and f"\taprovada\tDiretora de marketing\t{d(1)}\t" in linha_de(mud, "MU-001") and "rotina.py --remarcar" in aprovada.stdout and '--linha-de-base --motivo "MU-001"' in aprovada.stdout and "aditivos" not in aprovada.stdout, aprovada.stdout)
    confere("mudança decidida não é decidida nem analisada de novo", gov("--decidir", "MU-001", "--decisao", "rejeitada", "--quem", "X", "--motivo", "Y").returncode == 1 and gov("--analisar", "MU-001", "--impacto-prazo", "nenhum").returncode == 1 and "\taprovada\t" in linha_de(mud, "MU-001"))
    confere("com a mudança aprovada, a linha de base nova é gravada", gov("--linha-de-base", "--motivo", "MU-001", "--aprovada-por", "Diretora de marketing", hoje=d(1)).returncode == 0 and "\n2\t" in base_tsv.read_text(encoding="utf-8") and "\tMU-001\n" in base_tsv.read_text(encoding="utf-8"))
    decidida = em("mudanca", "MU-001", hoje=d(2)).stdout
    confere("solicitação decidida mostra a decisão e a linha de base de referência", f"Aprovada em {d(1)}. Diretora de marketing" in secao(decidida, "Decisão") and "( ) Aprovada" not in decidida and "Referência: linha de base versão 2." in decidida, decidida)
    confere("status executivo: a mudança decidida entra em mudanças e esforço", "MU-001 (aprovada em " + str(d(1)) in secao(em("status-executivo", hoje=d(2)).stdout, "Mudanças e esforço"))
    gov("--mudanca", "Refazer o inventário por país", "--solicitante", "Diretor de tecnologia")
    confere("rejeitar pede o motivo", gov("--decidir", "MU-002", "--decisao", "rejeitada", "--quem", "Diretora de marketing").returncode == 2 and "\tproposta\t" in linha_de(mud, "MU-002"))
    rejeitada = gov("--decidir", "MU-002", "--decisao", "rejeitada", "--quem", "Diretora de marketing", "--motivo", "Fora do contrato", hoje=d(2))
    adiado = linha_de(reg / "adiados.tsv", "B-001")
    confere("a mudança rejeitada fica guardada nos adiados", rejeitada.returncode == 0 and "\trejeitada\tDiretora de marketing: Fora do contrato\t" in linha_de(mud, "MU-002") and f"B-001\tRefazer o inventário por país\tMudança MU-002 rejeitada em {d(2)}: Fora do contrato\t" in adiado and adiado.endswith("\taberto") and "B-001" in rejeitada.stdout, rejeitada.stdout + adiado)
    confere("a mudança aprovada não vai para os adiados", "MU-001" not in (reg / "adiados.tsv").read_text(encoding="utf-8"))
    gov("--incluir", "aditivos")
    gov("--mudanca", "Sessão extra de repasse", "--solicitante", "Diretora de marketing")
    gov("--analisar", "MU-003", "--impacto-prazo", "nenhum", "--impacto-esforco", "4 horas", "--impacto-escopo", "Uma sessão")
    confere("com o registro de aditivos na lista, a aprovação lembra o aditivo", "registro de aditivos" in gov("--decidir", "MU-003", "--decisao", "aprovada", "--quem", "Diretora de marketing").stdout)
    confere("os registros de governança continuam passando na checagem", "erro" not in validar(projeto, "--so", "governanca").stdout.lower().replace("nenhum erro", ""), validar(projeto, "--so", "governanca").stdout)

    # O dia do status na lista do dia.
    sexta, quinta = d0 + datetime.timedelta(days=11), d0 + datetime.timedelta(days=10)
    confere("no dia do status, a agenda lembra o status semanal", "Dia do status semanal" in rotina("--lista", hoje=sexta).stdout and "Dia do status semanal" not in rotina("--lista", hoje=quinta).stdout, rotina("--lista", hoje=sexta).stdout)
    em("status-semanal", "--gravar", hoje=sexta)
    confere("com o status do dia já montado, a agenda não repete", "Dia do status semanal" not in rotina("--lista", hoje=sexta).stdout and "Dia do status semanal" in rotina("--lista", hoje=sexta + datetime.timedelta(days=7)).stdout)
    gov("--tirar", "status-semanal", "--motivo", "O cliente tem o próprio status")
    confere("sem o status semanal na lista do projeto, a agenda não lembra", "Dia do status semanal" not in rotina("--lista", hoje=sexta + datetime.timedelta(days=7)).stdout)

    # Um projeto de versão anterior recebe o registro e o sinal novos.
    antigo = tmp / "emissao-antigo"
    antigo.mkdir()
    instalar(antigo)
    ant = antigo / "entregaveis/_projeto"
    (ant / "emitidos.tsv").unlink()
    (ant / "cadencias.tsv").write_text("".join(l for l in (ant / "cadencias.tsv").read_text(encoding="utf-8").splitlines(keepends=True) if not l.startswith("prazo_de_aprovacao")), encoding="utf-8")
    (antigo / "entregaveis/_harness/VERSAO").write_text("0.10.0\n", encoding="utf-8")
    padrao = rodar([PY, "-c", "import sys; sys.path.insert(0, 'entregaveis/_harness/scripts'); import rotina; print(rotina.parametros()['prazo_de_aprovacao'])"], antigo)
    confere("sem o sinal no projeto, o prazo de aprovação é de cinco dias úteis", padrao.stdout.strip() == "5", padrao.stdout + padrao.stderr)
    atualizado = instalar(antigo, "--atualizar")
    confere("--atualizar cria o registro de emitidos e acrescenta o prazo de aprovação", atualizado.returncode == 0 and (ant / "emitidos.tsv").is_file() and "prazo_de_aprovacao\t5" in (ant / "cadencias.tsv").read_text(encoding="utf-8"), atualizado.stdout + atualizado.stderr)


# --- Segundo cérebro --------------------------------------------------------


def testar_cerebro(tmp: Path) -> None:
    print("Segundo cérebro do projeto")
    confere("o template não traz segundo cérebro de projeto nenhum", not (RAIZ / "entregaveis/_cerebro").exists())
    projeto = tmp / "cerebro"
    projeto.mkdir()
    (projeto / ".git").mkdir()
    instalar(projeto)
    base = projeto / "entregaveis"
    reg = base / "_projeto"
    pasta = base / "_cerebro"
    hoje = "2026-11-10"

    def cer(*args) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/cerebro.py", *args], projeto)

    def a_absorver() -> set:
        return set(re.findall(r"^- (\S+?)(?: \(|:)", cer("--pendentes").stdout, flags=re.MULTILINE))

    def estado() -> str:
        return rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout

    def avisos() -> str:
        return cer("--conferir").stdout

    def acrescentar(arquivo: Path, *campos) -> None:
        with arquivo.open("a", encoding="utf-8") as f:
            f.write("\t".join(str(c) for c in campos) + "\n")

    def trocar(arquivo: Path, antes: str, depois: str) -> None:
        texto = arquivo.read_text(encoding="utf-8")
        assert antes in texto, antes
        arquivo.write_text(texto.replace(antes, depois, 1), encoding="utf-8")

    def nota(caminho: str, titulo: str, sabemos: str, ligacoes: str = "", resumo: str = "O que importa sobre o assunto.", fontes: str = "E-001") -> Path:
        alvo = pasta / caminho
        alvo.write_text(f"---\ntitulo: {titulo}\nresumo: Resumo de {titulo.lower()}.\nfontes: {fontes}\natualizada:\n---\n# {titulo}\n\n## Em resumo\n\n{resumo}\n\n"
                        f"## O que sabemos\n\n{sabemos}\n\n## Em aberto\n\n- Nada.\n\n## Ligações\n\n{ligacoes}\n", encoding="utf-8")
        return alvo

    confere("a instalação cria as quatro pastas, o índice, o registro e o controle", all((pasta / n).exists() for n in ("1-projetos", "2-areas", "3-recursos", "4-arquivo", "indice.md", "registro.md", "absorvido.tsv", "LEIA-ME.md")))
    confere("projeto que não começou não tem nada a absorver", "Nada a absorver" in cer("--pendentes").stdout and "Segundo cérebro" not in estado())
    confere("projeto que não começou não recebe aviso do segundo cérebro", "[cerebro]" not in validar(projeto, "--so", "cerebro").stdout)

    montar_exemplo(projeto)
    confere("as fontes são a evidência, o brief, o briefing completo e a storyline aprovada", a_absorver() == {"E-001", "brief.md", "diag/briefing.md", "diag/storyline.md"}, cer("--pendentes").stdout)
    confere("o estado conta as notas e o que falta absorver", "Segundo cérebro: 0 nota(s), 4 item(ns) do projeto a absorver" in estado(), estado())
    trocar(base / "diag/storyline.md", "aprovada: sim", "aprovada: nao")
    confere("storyline sem aprovação ainda não é fonte", "diag/storyline.md" not in a_absorver())
    trocar(base / "diag/storyline.md", "aprovada: nao", "aprovada: sim")
    (base / "diag/fechamento.md").write_text("# Fechamento\n\nPREENCHER: o que a audiência decidiu.\n", encoding="utf-8")
    confere("arquivo com trecho por preencher ainda não é fonte", "diag/fechamento.md" not in a_absorver())
    (base / "diag/fechamento.md").write_text("# Fechamento\n\nA diretoria aprovou o pedido.\n", encoding="utf-8")
    confere("o fechamento escrito é fonte", "diag/fechamento.md" in a_absorver())
    (base / "diag/fechamento.md").unlink()

    # O que entra e o que fica só nos registros.
    acrescentar(base / "_intake/registro.tsv", "M-050", "Relatório de uso", "dados", "Cliente", "2026-11-01", "2026-11-20", "pedido", "", "")
    acrescentar(base / "_intake/registro.tsv", "M-051", "Contratos das plataformas", "dados", "Cliente", "2026-11-01", "2026-11-20", "recebido", "", "")
    confere("material recebido é fonte, e material só pedido não", "M-051" in a_absorver() and "M-050" not in a_absorver())
    acrescentar(reg / "acoes.tsv", "T-070", "tarefa", "Cobrar o inventário", "Consultora", "consultoria", "2026-11-03", "2026-11-20", "nao", "aberta", "consultor", "2026-11-03", "", "", "")
    acrescentar(reg / "prazos.tsv", "T-070", "2026-11-18", "2026-11-18", "2026-11-20", "2026-11-05", "consultor", "Férias do cliente")
    acrescentar(reg / "cobrancas.tsv", "T-070", "2026-11-06", "consultor", "cobrado", "")
    confere("tarefa, mudança de data e cobrança não são fonte", not ({"T-070"} & a_absorver()) and len(a_absorver()) == 5, cer("--pendentes").stdout)
    recusa = cer("--absorver", "T-070", "--nada", "teste")
    confere("absorver uma tarefa é recusado, com o motivo", recusa.returncode == 2 and "Não é fonte" in recusa.stdout and "T-070" in recusa.stdout, recusa.stdout)
    acrescentar(reg / "riscos.tsv", "RS-001", "O inventário atrasa", "Depende de uma pessoa", "A leitura sai sem custo", "Consultora", "aberto", "consultor", "2026-11-03", "media", "alta", "", "Cobrar toda semana")
    with (reg / "decisoes.md").open("a", encoding="utf-8") as f:
        f.write("| D-001 | 2026-11-03 | A leitura executiva é projetada em reunião | Palavras da consultora | Vigente |\n")
    confere("risco e decisão são fontes", {"RS-001", "D-001"} <= a_absorver(), cer("--pendentes").stdout)

    # Criar uma nota.
    criada = cer("--nova", "2", "Plataformas do cliente", "--resumo", "O que o cliente contrata.", "--hoje", hoje)
    alvo = pasta / "2-areas/plataformas-do-cliente.md"
    confere("--nova cria a nota na pasta, com o título, o resumo e a data", criada.returncode == 0 and alvo.is_file() and "titulo: Plataformas do cliente" in alvo.read_text(encoding="utf-8") and "resumo: O que o cliente contrata." in alvo.read_text(encoding="utf-8") and f"atualizada: {hoje}" in alvo.read_text(encoding="utf-8"), criada.stdout + criada.stderr)
    confere("--nova recusa a nota repetida e a pasta que não existe", cer("--nova", "3-recursos", "Plataformas do cliente").returncode == 1 and cer("--nova", "9", "Outra").returncode == 2 and not (pasta / "3-recursos/plataformas-do-cliente.md").exists())
    confere("nota por preencher é avisada", "plataformas-do-cliente.md: A nota ainda tem trechos por preencher" in avisos(), avisos())

    # Absorver.
    confere("absorver pede a nota ou o motivo, e não os dois", cer("--absorver", "E-001").returncode == 2 and cer("--absorver", "E-001", "--nota", "2-areas/plataformas-do-cliente.md", "--nada", "x").returncode == 2)
    confere("absorver em nota que não existe é recusado", cer("--absorver", "E-001", "--nota", "2-areas/nao-existe.md").returncode == 2)
    crua = cer("--absorver", "E-001", "--nota", "2-areas/plataformas-do-cliente.md", "--hoje", hoje)
    confere("a nota por preencher não absorve", crua.returncode == 1 and "ainda tem trechos por preencher" in crua.stdout and "E-001" in a_absorver(), crua.stdout)
    nota("2-areas/plataformas-do-cliente.md", "Plataformas do cliente", "- Os contratos chegaram em novembro (M-051).", fontes="M-051")
    sem_id = cer("--absorver", "E-001,M-051", "--nota", "2-areas/plataformas-do-cliente.md", "--hoje", hoje)
    confere("a nota que não cita o item não absorve, e nada é gravado", sem_id.returncode == 1 and "Nenhuma das notas cita E-001" in sem_id.stdout and "\t" + hoje not in (pasta / "absorvido.tsv").read_text(encoding="utf-8") and {"E-001", "M-051"} <= a_absorver(), sem_id.stdout)
    nota("2-areas/plataformas-do-cliente.md", "Plataformas do cliente", "- O inventário fechou em 14 plataformas (E-001).\n- Os contratos chegaram em novembro e a avaliação usou o roteiro da consultora (M-051).")
    feito = cer("--absorver", "E-001,M-051", "--nota", "2-areas/plataformas-do-cliente.md", "--o-que", "Inventário e contratos", "--hoje", hoje)
    controle = (pasta / "absorvido.tsv").read_text(encoding="utf-8")
    confere("absorver marca os itens com a nota e a data", feito.returncode == 0 and re.search(rf"^E-001\t\w+\t{hoje}\t2-areas/plataformas-do-cliente.md$", controle, flags=re.MULTILINE) is not None and "M-051\t" in controle, feito.stdout + controle)
    confere("absorver escreve a linha no registro de atualizações", f"- {hoje} | E-001, M-051 | 2-areas/plataformas-do-cliente.md | Inventário e contratos" in (pasta / "registro.md").read_text(encoding="utf-8"))
    confere("absorver data a nota e refaz o índice", f"atualizada: {hoje}" in alvo.read_text(encoding="utf-8") and "- [Plataformas do cliente](2-areas/plataformas-do-cliente.md): Resumo de plataformas do cliente. Fontes: E-001." in (pasta / "indice.md").read_text(encoding="utf-8"), (pasta / "indice.md").read_text(encoding="utf-8"))
    confere("o item absorvido sai da lista", not ({"E-001", "M-051"} & a_absorver()) and "Ainda há 5 item(ns)" in feito.stdout, feito.stdout)
    nada = cer("--absorver", "D-001", "--nada", "Decisão de forma, sem conhecimento novo", "--hoje", hoje)
    confere("o item que não ensina sai com o motivo no registro", nada.returncode == 0 and "D-001" not in a_absorver() and f"- {hoje} | D-001 | nada | Decisão de forma, sem conhecimento novo" in (pasta / "registro.md").read_text(encoding="utf-8"), nada.stdout)

    # O que muda volta à lista.
    trocar(reg / "evidencias.tsv", "\talta\tdiag", "\talta\tdiag, status")
    confere("coluna que não muda o que se sabe não devolve o item", "E-001" not in a_absorver())
    trocar(reg / "evidencias.tsv", "Plataformas contratadas\t14", "Plataformas contratadas\t15")
    mudou = cer("--pendentes").stdout
    confere("o item que mudou volta, com a nota que o guardava", "- E-001 (evidencias.tsv)" in mudou and "Mudou desde a absorção em 2-areas/plataformas-do-cliente.md" in mudou, mudou)
    trocar(alvo, "14 plataformas", "15 plataformas")
    cer("--absorver", "E-001", "--nota", "2-areas/plataformas-do-cliente.md", "--hoje", hoje)
    nota("4-arquivo/diag.md", "Diagnóstico de martech", "- O pedido e a audiência estão no [briefing](../../diag/briefing.md).\n- A sequência aprovada está na [storyline](../../diag/storyline.md).", fontes="diag/briefing.md, diag/storyline.md")
    cer("--absorver", "diag/briefing.md,diag/storyline.md", "--nota", "4-arquivo/diag.md", "--hoje", hoje)
    trocar(base / "diag/briefing.md", "estado: redacao", "estado: revisao")
    confere("a etapa do entregável não devolve o briefing", "diag/briefing.md" not in a_absorver(), cer("--pendentes").stdout)
    with (base / "diag/briefing.md").open("a", encoding="utf-8") as f:
        f.write("\nA diretoria pediu o custo por loja.\n")
    confere("o briefing que mudou no texto volta à lista", "diag/briefing.md" in a_absorver())
    varios = cer("--absorver", "pendentes", "--nota", "4-arquivo/diag.md", "--hoje", hoje)
    confere("absorver os pendentes em nota que não cita todos é recusado, com a lista", varios.returncode == 1 and "brief.md" in varios.stdout and "RS-001" in varios.stdout and "RS-001" in a_absorver(), varios.stdout)
    confere("absorver os pendentes com motivo esvazia a lista", cer("--absorver", "pendentes", "--nada", "Semeadura do teste", "--hoje", hoje).returncode == 0 and "Nada a absorver" in cer("--pendentes").stdout and "Nada a absorver" in cer("--absorver", "pendentes", "--nada", "x").stdout)
    confere("sem pendência, o estado só conta as notas", "Segundo cérebro: 2 nota(s). Antes de escrever" in estado(), estado())

    # Busca.
    nota("3-recursos/metodo.md", "Método de avaliação", "- A repetição de plataformas é medida por capacidade (E-001).\n- Plataformas contratadas entram no inventário, com ou sem uso.", "- [Plataformas do cliente](../2-areas/plataformas-do-cliente.md): o resultado.")
    busca = cer("--buscar", "PLATAFORMAS")
    ordem = re.findall(r"^- (entregaveis/_cerebro/\S+)", busca.stdout, flags=re.MULTILINE)
    confere("a busca ignora maiúscula e põe o título antes do corpo", busca.returncode == 0 and ordem[:2] == ["entregaveis/_cerebro/2-areas/plataformas-do-cliente.md", "entregaveis/_cerebro/3-recursos/metodo.md"], busca.stdout)
    pelo_titulo = re.findall(r"^- (entregaveis/_cerebro/\S+)", cer("--buscar", "avaliacao").stdout, flags=re.MULTILINE)
    confere("a busca põe a nota que traz o termo no título antes da que só cita", pelo_titulo == ["entregaveis/_cerebro/3-recursos/metodo.md", "entregaveis/_cerebro/2-areas/plataformas-do-cliente.md"], str(pelo_titulo))
    confere("a busca ignora acento e mostra a linha da nota", "metodo.md" in cer("--buscar", "repeticao").stdout and re.search(r"^\s+\d+: - A repetição", cer("--buscar", "repeticao").stdout, flags=re.MULTILINE) is not None, cer("--buscar", "repeticao").stdout)
    confere("a busca traz as linhas dos registros", "Registros (" in busca.stdout and "entregaveis/_projeto/evidencias.tsv:" in busca.stdout and "E-001 | Plataformas contratadas | 15" in busca.stdout, busca.stdout)
    confere("a busca acha a tarefa no registro, que não é nota", "acoes.tsv" in cer("--buscar", "cobrar", "inventario").stdout and "Notas (" not in cer("--buscar", "cobrar", "inventario").stdout)
    confere("a busca exige todos os termos", "metodo.md" in cer("--buscar", "repetição", "capacidade").stdout and "metodo.md" not in cer("--buscar", "repetição", "contratos").stdout)
    vazio = cer("--buscar", "girafa")
    confere("a busca sem resultado diz que não há nada", vazio.returncode == 1 and "Nada no segundo cérebro nem nos registros" in vazio.stdout)
    por_id = cer("--id", "E-001")
    confere("--id mostra a linha do registro e as notas que citam", "Registro: entregaveis/_projeto/evidencias.tsv" in por_id.stdout and por_id.stdout.count("Nota: ") == 2, por_id.stdout)
    confere("--id diz quando nenhuma nota cita", "Nenhuma nota cita RS-001" in cer("--id", "RS-001").stdout)

    # Conferência.
    trocar(pasta / "4-arquivo/diag.md", "## Ligações\n\n", "## Ligações\n\n- [Método de avaliação](../3-recursos/metodo.md): como foi medido.\n")
    trocar(alvo, "## Ligações\n\n", "## Ligações\n\n- [Diagnóstico de martech](../4-arquivo/diag.md): o entregável.\n")
    cer("--indice")
    confere("notas ligadas, com fonte e resumo curto passam, e um trecho curto igual ao do registro não é cópia", "Segundo cérebro em ordem" in avisos(), avisos())
    confere("a checagem do segundo cérebro entra no validar", "Nenhum erro e nenhum aviso" in validar(projeto, "--so", "cerebro").stdout)

    def acusa(arquivo: Path, antes: str, depois: str, espera: str, nome: str) -> None:
        original = arquivo.read_text(encoding="utf-8")
        assert antes in original, antes
        arquivo.write_text(original.replace(antes, depois, 1), encoding="utf-8")
        saida = avisos()
        arquivo.write_text(original, encoding="utf-8")
        confere(nome, espera in saida and espera not in avisos(), saida)

    acusa(alvo, "(../4-arquivo/diag.md)", "(../4-arquivo/sumiu.md)", "A ligação para '../4-arquivo/sumiu.md' não leva a lugar nenhum", "conferência: ligação quebrada")
    acusa(alvo, "(M-051)", "(M-051, E-999)", "Cita E-999, que não existe em nenhum registro", "conferência: id que não existe")
    acusa(pasta / "4-arquivo/diag.md", "fontes: diag/briefing.md, diag/storyline.md", "fontes:", "A nota não cita nenhuma fonte", "conferência: nota sem fonte")
    acusa(alvo, "O que importa sobre o assunto.", "Um.\nDois.\nTrês.\nQuatro.\nCinco.\nSeis.", "A seção 'Em resumo' tem 6 linhas", "conferência: resumo longo")
    cinco = alvo.read_text(encoding="utf-8")
    alvo.write_text(cinco.replace("O que importa sobre o assunto.", "Um.\nDois.\nTrês.\nQuatro.\nCinco."), encoding="utf-8")
    confere("conferência: cinco linhas de resumo cabem", "A seção 'Em resumo' tem" not in avisos(), avisos())
    alvo.write_text(cinco, encoding="utf-8")
    acusa(alvo, "## Em resumo", "## Síntese", "Falta a seção 'Em resumo'", "conferência: nota sem resumo")
    acusa(alvo, "titulo: Plataformas do cliente", "titulo:", "Falta 'titulo' no cabeçalho", "conferência: nota sem título")
    acusa(pasta / "3-recursos/metodo.md", "- [Plataformas do cliente](../2-areas/plataformas-do-cliente.md): o resultado.", "", "plataformas-do-cliente.md: Nenhuma outra nota aponta para esta", "conferência: nota órfã")
    acrescentar(reg / "evidencias.tsv", "E-002", "Custo anual das três plataformas que repetem uma capacidade atendida por outra", "R$ 1,9 milhão", "Contratos", "2026-11-04", "fato", "alta", "diag")
    acusa(alvo, "- O inventário fechou", "- Custo anual das três plataformas que repetem uma capacidade atendida por outra: R$ 1,9 milhão (E-002).\n- O inventário fechou", "Repete o texto de E-002", "conferência: nota que copia a linha do registro")
    trocar(alvo, "- O inventário fechou", "- A repetição custa caro e abre a conversa com o financeiro (E-002).\n- O inventário fechou")
    confere("conferência: citar o id e dizer o que significa não é cópia", "Repete o texto" not in avisos(), avisos())
    confere("conferência: avisa do que o projeto registrou e nenhuma nota guarda", "1 item(ns) do projeto ainda fora do segundo cérebro (E-002)" in avisos() and "AVISO [cerebro]" in validar(projeto, "--so", "cerebro").stdout and validar(projeto, "--so", "cerebro").returncode == 0, avisos())
    cer("--absorver", "E-002", "--nota", "2-areas/plataformas-do-cliente.md", "--hoje", hoje)
    trocar(alvo, "resumo: Resumo de plataformas do cliente.", "resumo: O que o cliente contrata e quanto custa.")
    confere("conferência: índice que não reflete as notas", "O índice não reflete as notas" in avisos() and "Índice refeito" in cer("--indice").stdout and "O índice não reflete" not in avisos() and "já estava em dia" in cer("--indice").stdout)
    nota("1-projetos/diag.md", "Entregável diag", "- Em produção (E-001).", "- [Método de avaliação](../3-recursos/metodo.md): o método.")
    trocar(pasta / "3-recursos/metodo.md", "## Ligações\n\n", "## Ligações\n\n- [Entregável diag](../1-projetos/diag.md): onde é usado.\n")
    confere("conferência: nota de entregável em andamento fica nos projetos", "foi entregue" not in avisos(), avisos())
    trocar(base / "diag/briefing.md", "estado: revisao", "estado: entregue")
    confere("conferência: nota de entregável entregue vai ao arquivo", "1-projetos/diag.md: O entregável diag foi entregue. Leve a nota ao arquivo" in avisos(), avisos())

    # Mover.
    (pasta / "4-arquivo/diag.md").rename(pasta / "4-arquivo/diagnostico.md")
    trocar(alvo, "(../4-arquivo/diag.md)", "(../4-arquivo/diagnostico.md)")
    trocar(pasta / "4-arquivo/diagnostico.md", "(../3-recursos/metodo.md)", "(./../3-recursos/metodo.md)")
    (pasta / "1-projetos/frente").mkdir()
    nota("1-projetos/frente/funda.md", "Nota funda", "- Em produção (E-001).", "- [Método de avaliação](../../3-recursos/metodo.md): o método.")
    funda = cer("--mover", "1-projetos/frente/funda.md", "arquivo", "--hoje", hoje)
    confere("--mover refaz as ligações de uma nota que muda de profundidade", funda.returncode == 0 and "(../3-recursos/metodo.md)" in (pasta / "4-arquivo/funda.md").read_text(encoding="utf-8"), funda.stdout + funda.stderr)
    confere("--mover não reescreve a ligação que não aponta para a nota movida", "(./../3-recursos/metodo.md)" in (pasta / "4-arquivo/diagnostico.md").read_text(encoding="utf-8"))
    (pasta / "4-arquivo/funda.md").unlink()
    cer("--indice")
    movida = cer("--mover", "1-projetos/diag.md", "arquivo", "--hoje", hoje)
    destino = pasta / "4-arquivo/diag.md"
    confere("--mover leva a nota à outra pasta", movida.returncode == 0 and destino.is_file() and not (pasta / "1-projetos/diag.md").exists(), movida.stdout + movida.stderr)
    confere("--mover refaz a ligação de quem apontava para a nota", "(../4-arquivo/diag.md)" in (pasta / "3-recursos/metodo.md").read_text(encoding="utf-8"))
    confere("--mover refaz as ligações da nota movida", "(../3-recursos/metodo.md)" in destino.read_text(encoding="utf-8") and "não leva a lugar nenhum" not in avisos(), avisos())
    confere("--mover escreve no registro e refaz o índice", f"- {hoje} | 1-projetos/diag.md | 4-arquivo/diag.md | nota movida" in (pasta / "registro.md").read_text(encoding="utf-8") and "(4-arquivo/diag.md)" in (pasta / "indice.md").read_text(encoding="utf-8"))
    cer("--mover", "2-areas/plataformas-do-cliente.md", "3-recursos", "--hoje", hoje)
    alvo = pasta / "3-recursos/plataformas-do-cliente.md"
    confere("--mover corrige o caminho da nota no controle do que foi absorvido", "\t3-recursos/plataformas-do-cliente.md" in (pasta / "absorvido.tsv").read_text(encoding="utf-8") and "2-areas/plataformas-do-cliente.md" not in (pasta / "absorvido.tsv").read_text(encoding="utf-8"))
    (pasta / "1-projetos/metodo.md").write_text("# Outra\n", encoding="utf-8")
    ocupado = cer("--mover", "3-recursos/metodo.md", "projetos")
    confere("--mover recusa o destino ocupado e a pasta que não existe", ocupado.returncode == 1 and (pasta / "3-recursos/metodo.md").is_file() and (pasta / "1-projetos/metodo.md").read_text(encoding="utf-8") == "# Outra\n" and cer("--mover", "3-recursos/metodo.md", "9").returncode == 2 and cer("--mover", "3-recursos/nao-existe.md", "arquivo").returncode == 2, ocupado.stdout)
    (pasta / "1-projetos/metodo.md").unlink()

    # Gatilhos: gravação, começo e fim do turno.
    hooks = base / "_harness/hooks"

    def hook(nome: str, dados: dict) -> subprocess.CompletedProcess:
        return rodar([PY, hooks / nome], projeto, json.dumps({"cwd": str(projeto), **dados}))

    def gravacao(caminho: str, sessao: str) -> dict:
        return {"session_id": sessao, "tool_name": "Write", "tool_input": {"file_path": caminho}}

    def contexto(caminho: str, sessao: str) -> str:
        """O que o hook de depois da gravação devolve ao agente como contexto."""
        saida = hook("depois_de_gravar.py", gravacao(caminho, sessao))
        assert saida.returncode == 0, saida.stderr
        return json.loads(saida.stdout)["hookSpecificOutput"]["additionalContext"] if saida.stdout.strip() else ""

    cer("--absorver", "pendentes", "--nada", "Antes dos gatilhos", "--hoje", hoje)
    confere("gravação sem nada novo não lembra o segundo cérebro", "Segundo cérebro" not in contexto("entregaveis/_projeto/evidencias.tsv", "c1"))
    hook("mensagem.py", {"session_id": "c1", "prompt": "registre o achado"})
    calado = hook("fim_do_turno.py", {"session_id": "c1"})
    confere("fim do turno: turno que não registrou nada segue", calado.returncode == 0, calado.stderr)
    acrescentar(reg / "evidencias.tsv", "E-003", "Tempo do carrinho abandonado até a campanha", "2 dias", "Medição", "2026-11-05", "fato", "alta", "diag")
    lembrete = contexto("entregaveis/_projeto/evidencias.tsv", "c1")
    confere("gravação de registro com item novo lembra o segundo cérebro", "Segundo cérebro: 1 item(ns) a absorver (E-003)" in lembrete and "manter-cerebro" in lembrete, lembrete)
    confere("o lembrete da gravação não se repete para o mesmo item", "Segundo cérebro" not in contexto("entregaveis/_projeto/evidencias.tsv", "c1"))
    confere("gravação fora do projeto não lembra nada", contexto("README.md", "c9") == "")
    cobrado = hook("fim_do_turno.py", {"session_id": "c1"})
    confere("fim do turno: cobra o que o turno registrou e nenhuma nota guarda", cobrado.returncode == 2 and "1 item(ns) que o segundo cérebro ainda não guarda (E-003)" in cobrado.stderr and "manter-cerebro" in cobrado.stderr, cobrado.stdout + cobrado.stderr)
    confere("fim do turno: cobra uma vez por item", hook("fim_do_turno.py", {"session_id": "c1"}).returncode == 0)
    hook("mensagem.py", {"session_id": "c2", "prompt": "siga"})
    confere("fim do turno: o que já estava pendente antes do turno não segura o turno", hook("fim_do_turno.py", {"session_id": "c2"}).returncode == 0)
    acrescentar(reg / "evidencias.tsv", "E-004", "Nota de maturidade em dados", "2 em 5", "Entrevistas", "2026-11-05", "fato", "alta", "diag")
    confere("fim do turno: não cobra de novo quando o hook já segurou o turno", hook("fim_do_turno.py", {"session_id": "c2", "stop_hook_active": True}).returncode == 0)
    confere("fim do turno: sem o retrato do começo do turno, não cobra", hook("fim_do_turno.py", {"session_id": "c3"}).returncode == 0)
    confere("fim do turno: com o retrato, cobra o item novo", hook("fim_do_turno.py", {"session_id": "c2"}).returncode == 2)
    trocar(alvo, "- O inventário fechou", "- O carrinho demora dois dias e a maturidade é baixa (E-003, E-004).\n- O inventário fechou")
    cer("--absorver", "E-003,E-004", "--nota", "3-recursos/plataformas-do-cliente.md", "--hoje", hoje)
    hook("mensagem.py", {"session_id": "c4", "prompt": "siga"})
    acrescentar(reg / "evidencias.tsv", "E-005", "Contratos que vencem em março", "2", "Contratos", "2026-11-05", "fato", "alta", "diag")
    trocar(alvo, "(E-003, E-004)", "(E-003, E-004). Dois contratos vencem em março (E-005)")
    cer("--absorver", "E-005", "--nota", "3-recursos/plataformas-do-cliente.md", "--hoje", hoje)
    confere("fim do turno: o que foi absorvido no próprio turno não é cobrado", hook("fim_do_turno.py", {"session_id": "c4"}).returncode == 0)
    limpa = contexto("entregaveis/_cerebro/3-recursos/plataformas-do-cliente.md", "c4")
    confere("gravação de nota em ordem não devolve aviso", limpa == "", limpa)
    trocar(alvo, "(E-005)", "(E-005, E-888)")
    trocar(pasta / "3-recursos/metodo.md", "(E-001)", "(E-001, E-777)")
    devolvida = contexto("entregaveis/_cerebro/3-recursos/plataformas-do-cliente.md", "c4")
    confere("gravação de nota com id que não existe devolve o aviso na hora, e só o da nota gravada", "Segundo cérebro, nesta nota" in devolvida and "E-888" in devolvida and "E-777" not in devolvida, devolvida)
    trocar(alvo, "(E-005, E-888)", "(E-005)")
    trocar(pasta / "3-recursos/metodo.md", "(E-001, E-777)", "(E-001)")
    area = rodar([PY, "-c", "import sys; sys.path.insert(0, 'entregaveis/_harness/hooks'); import _base, comum; print(_base.area_de_projeto(comum.BASE / '_cerebro/2-areas/x.md'), _base.area_de_projeto(comum.BASE / '_harness/kit.md'))"], projeto)
    confere("a trava do repositório público vale para as notas", area.stdout.split() == ["True", "False"], area.stdout + area.stderr)

    # Lista do dia, pacote para outros ambientes e atualização.
    def lista() -> str:
        return rodar([PY, "entregaveis/_harness/scripts/rotina.py", "--lista", "--hoje", hoje], projeto).stdout

    confere("lista do dia: sem pendência, o segundo cérebro não aparece", "Segundo cérebro" not in lista(), lista())
    acrescentar(reg / "evidencias.tsv", "E-006", "Custo evitado por ano", "R$ 1,2 milhão", "Contratos", "2026-11-06", "fato", "alta", "diag")
    confere("lista do dia: o que falta absorver entra na caixa de entrada", "Segundo cérebro: 1 item(ns) do projeto ainda fora das notas (E-006)" in lista() and "Caixa de entrada" in lista(), lista())
    pacote = rodar([PY, "entregaveis/_harness/scripts/empacotar.py", "--projeto"], projeto)
    do_projeto = (base / "_ambiente/5-projeto.txt").read_text(encoding="utf-8") if (base / "_ambiente/5-projeto.txt").is_file() else ""
    confere("o pacote do projeto leva o índice e as notas", pacote.returncode == 0 and "## Segundo cérebro" in do_projeto and "### 3-recursos/plataformas-do-cliente.md" in do_projeto and "O carrinho demora dois dias" in do_projeto and "# Índice do segundo cérebro" in do_projeto, pacote.stdout + pacote.stderr)
    conhecimento = HARNESS / "ambientes" / "conhecimento"
    em_dia = rodar([PY, HARNESS / "scripts" / "empacotar.py", "--conferir"], RAIZ)
    confere("os outros ambientes recebem o método e o modelo de nota", "em dia" in em_dia.stdout and "Segundo cérebro do projeto" in (conhecimento / "2-metodo-e-texto.txt").read_text(encoding="utf-8") and "Nota do segundo cérebro" in (conhecimento / "4-modelos.txt").read_text(encoding="utf-8") and "manter-cerebro" in (conhecimento / "1-procedimentos.txt").read_text(encoding="utf-8"))
    antes = {a.relative_to(pasta).as_posix(): a.read_text(encoding="utf-8") for a in sorted(pasta.rglob("*")) if a.is_file()}
    atualizado = instalar(projeto, "--atualizar")
    depois = {a.relative_to(pasta).as_posix(): a.read_text(encoding="utf-8") for a in sorted(pasta.rglob("*")) if a.is_file()}
    confere("--atualizar não toca nas notas, no índice nem no controle", atualizado.returncode == 0 and antes == depois, str(set(antes) ^ set(depois)))

    antigo = tmp / "cerebro-antigo"
    antigo.mkdir()
    instalar(antigo)
    montar_exemplo(antigo)
    shutil.rmtree(antigo / "entregaveis/_cerebro")
    sem_pasta = rodar([PY, "entregaveis/_harness/scripts/estado.py"], antigo)
    confere("projeto de versão anterior, sem a pasta, segue sem erro e sem a linha", sem_pasta.returncode == 0 and "Segundo cérebro" not in sem_pasta.stdout and rodar([PY, "entregaveis/_harness/scripts/cerebro.py", "--pendentes"], antigo).returncode == 2, sem_pasta.stdout + sem_pasta.stderr)
    confere("a busca funciona nos registros mesmo sem a pasta", "evidencias.tsv" in rodar([PY, "entregaveis/_harness/scripts/cerebro.py", "--buscar", "plataformas"], antigo).stdout)
    instalar(antigo, "--atualizar")
    com_pasta = rodar([PY, "entregaveis/_harness/scripts/estado.py"], antigo)
    confere("--atualizar cria o segundo cérebro em projeto de versão anterior", (antigo / "entregaveis/_cerebro/indice.md").is_file() and "Segundo cérebro: 0 nota(s), 4 item(ns)" in com_pasta.stdout, com_pasta.stdout)
    rodar([PY, "entregaveis/_harness/scripts/empacotar.py", "--projeto"], antigo)
    confere("o pacote de um projeto sem notas não traz a seção do segundo cérebro", "## Registros do projeto" in (antigo / "entregaveis/_ambiente/5-projeto.txt").read_text(encoding="utf-8") and "## Segundo cérebro" not in (antigo / "entregaveis/_ambiente/5-projeto.txt").read_text(encoding="utf-8"))
    (antigo / "wiki").mkdir()
    (antigo / "wiki/notas-do-projeto.md").write_text("x", encoding="utf-8")
    levantado = rodar([PY, "entregaveis/_harness/scripts/levantar.py"], antigo)
    confere("o levantamento aponta uma base de conhecimento que o projeto já tem", "Possíveis bases de conhecimento" in levantado.stdout and "notas-do-projeto.md" in levantado.stdout, levantado.stdout)
    vazio_ = tmp / "cerebro-vazio"
    vazio_.mkdir()
    instalar(vazio_)
    linha = rodar([PY, "-c", "import sys; sys.path.insert(0, 'entregaveis/_harness/scripts'); import cerebro; print(cerebro.linha_de_estado())"], vazio_)
    confere("sem nota e sem nada a absorver, o estado não ganha a linha", linha.stdout.strip() == "[]", linha.stdout + linha.stderr)
    tem = "import sys; sys.path.insert(0, 'entregaveis/_harness/scripts'); import repositorio; print(repositorio.tem_projeto())"
    sem_nota = rodar([PY, "-c", tem], vazio_).stdout.strip()
    (vazio_ / "entregaveis/_cerebro/2-areas/cliente.md").write_text("# Cliente\n", encoding="utf-8")
    confere("uma nota já conta como conteúdo de projeto para a trava do repositório", sem_nota == "False" and rodar([PY, "-c", tem], vazio_).stdout.strip() == "True", sem_nota)


# --- Conferência do ambiente ----------------------------------------------


def testar_ambiente(tmp: Path) -> None:
    print("Conferência do ambiente")
    script = HARNESS / "scripts" / "ambiente.py"
    fonte = script.read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    novidades = [type(no).__name__ for no in ast.walk(arvore) if isinstance(no, (ast.JoinedStr, ast.NamedExpr, ast.AnnAssign, ast.Match if hasattr(ast, "Match") else ast.NamedExpr))]
    anotadas = [no.name for no in ast.walk(arvore) if isinstance(no, ast.FunctionDef) and (no.returns or any(a.annotation for a in no.args.args))]
    confere("ambiente.py roda em Python antigo para conseguir avisar da versão", not novidades and not anotadas and "from __future__" not in fonte and "pathlib" not in fonte, str(novidades + anotadas))

    def ambiente(*args, caminho: str | None = None, sem_pacotes: bool = False) -> subprocess.CompletedProcess:
        variaveis = dict(os.environ)
        if caminho is not None:
            variaveis["PATH"] = caminho
        return subprocess.run([PY, *(["-S"] if sem_pacotes else []), str(script), *args], capture_output=True, text=True, timeout=120, env=variaveis)

    aqui = ambiente()
    tem_python3 = shutil.which("python3") is not None
    confere("lista o que a máquina tem", "Ambiente desta máquina" in aqui.stdout and "Python " in aqui.stdout and "LibreOffice" in aqui.stdout, aqui.stdout + aqui.stderr)
    if tem_python3:
        confere("com o essencial pronto, sai com zero", aqui.returncode == 0 and "[essencial]" not in aqui.stdout, aqui.stdout)
    sem_nada = tmp / "caminho-vazio"
    sem_nada.mkdir()
    falta = ambiente(caminho=str(sem_nada))
    confere("sem o comando python3, acusa o essencial e sai com erro", falta.returncode == 1 and "[essencial]" in falta.stdout and "Falta o essencial" in falta.stdout, falta.stdout + falta.stderr)
    confere("cada falta vem com o comando que resolve", "Como resolver o que falta:" in falta.stdout and "1. Comando python3" in falta.stdout and "Git\n" in falta.stdout, falta.stdout)
    confere("oferece o agente ou o passo a passo, e o caminho sem instalação", "com o seu sim, ou você roda um a um" in falta.stdout and "ambientes/LEIA-ME.md" in falta.stdout, falta.stdout)
    sem_pacotes = ambiente(sem_pacotes=True)
    confere("pacote do gerador em falta não é essencial e traz o pip", "FALTA  python-pptx" in sem_pacotes.stdout and "pip install python-pptx" in sem_pacotes.stdout and "ambiente.py --instalar" in sem_pacotes.stdout and (sem_pacotes.returncode == 0 or not tem_python3), sem_pacotes.stdout)
    if tem_python3:
        confere("sem os pacotes, diz que o essencial está pronto", "O essencial está pronto" in sem_pacotes.stdout)
    if all(tem_pacote(p) for p in ("pptx", "docx", "openpyxl")):
        confere("--instalar não faz nada quando os pacotes já estão", "já estão instalados" in ambiente("--instalar").stdout)

    # As instruções de cada sistema.
    codigo = (
        "import sys; sys.path.insert(0, sys.argv[1]); import ambiente as a\n"
        "a.platform.system = lambda: sys.argv[2]; a.shutil.which = lambda c: None\n"
        "print(a.relatorio(a.conferir())); print(a.faltas_em_uma_linha())\n"
    )
    por_sistema = {s: rodar([PY, "-c", codigo, script.parent, s], RAIZ).stdout for s in ("Windows", "Darwin", "Linux", "FreeBSD")}
    confere("Windows: instruções com a loja e o winget", "(Windows)" in por_sistema["Windows"] and "Microsoft Store" in por_sistema["Windows"] and "winget install Git.Git" in por_sistema["Windows"] and "winget install TheDocumentFoundation.LibreOffice" in por_sistema["Windows"], por_sistema["Windows"])
    confere("macOS: instruções com o Homebrew", "(macOS)" in por_sistema["Darwin"] and "brew install python" in por_sistema["Darwin"] and "brew install --cask libreoffice" in por_sistema["Darwin"] and "winget" not in por_sistema["Darwin"], por_sistema["Darwin"])
    confere("Linux: instruções com apt e dnf", "sudo apt install python3" in por_sistema["Linux"] and "sudo dnf install git" in por_sistema["Linux"], por_sistema["Linux"])
    confere("sistema desconhecido recebe as instruções de Linux", "sudo apt install python3" in por_sistema["FreeBSD"], por_sistema["FreeBSD"])
    confere("a linha do instalador nomeia as faltas", "Nesta máquina falta: Comando python3, Git" in por_sistema["Linux"] and "Falta o essencial." in por_sistema["Linux"], por_sistema["Linux"][-400:])

    # O instalador confere a máquina e avisa.
    destino = tmp / "ambiente-instalado"
    destino.mkdir()
    saida = subprocess.run([PY, str(HARNESS / "scripts" / "instalar.py"), "--destino", str(destino)], capture_output=True, text=True, timeout=120, env={**os.environ, "PATH": str(sem_nada)})
    confere("o instalador avisa do que falta na máquina e aponta o script", saida.returncode == 0 and "Nesta máquina falta" in saida.stdout and "entregaveis/_harness/scripts/ambiente.py" in saida.stdout, saida.stdout + saida.stderr)
    confere("a instalação termina mesmo com a máquina incompleta", (destino / "entregaveis/_harness/REGRAS.md").is_file() and (destino / "entregaveis/_projeto/brief.md").is_file())
    if tem_python3 and shutil.which("git") and all(tem_pacote(p) for p in ("pptx", "docx", "openpyxl")) and (shutil.which("soffice") or shutil.which("libreoffice")) and shutil.which("pdftoppm"):
        completo = tmp / "ambiente-completo"
        completo.mkdir()
        confere("com a máquina pronta, o instalador não avisa de nada", "Nesta máquina falta" not in instalar(completo).stdout)

    # As skills, as regras e os outros ambientes começam pela conferência.
    for skill in ("iniciar-projeto", "adotar-projeto"):
        texto = re.sub(r"\s+", " ", (RAIZ / ".claude" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8"))
        confere(f"{skill}: confere a máquina e oferece instalar ou repassar os passos", "scripts/ambiente.py" in texto and "passo a passo" in texto)
    instrucoes = (HARNESS / "ambientes" / "instrucoes.md").read_text(encoding="utf-8")
    confere("as instruções dos outros ambientes mandam conferir o ambiente", "## Confira o ambiente" in instrucoes)
    guia = (HARNESS / "ambientes" / "LEIA-ME.md").read_text(encoding="utf-8")
    confere("o guia dos ambientes cobre quem só tem o Copilot web", "### Só o Copilot web, sem instalar nada" in guia and "## Conferir o ambiente" in guia)
    confere("o INSTALL manda conferir a máquina antes de instalar", "scripts/ambiente.py" in (RAIZ / "INSTALL.md").read_text(encoding="utf-8"))


# --- Exemplo completo -----------------------------------------------------


def testar_exemplo(tmp: Path) -> None:
    """O exemplo de exemplo/ abre em uma instalação limpa e passa no harness de hoje."""
    print("Exemplo completo")
    origem = RAIZ / "exemplo"
    projeto = tmp / "exemplo-aberto"
    aberto = rodar([PY, str(RAIZ / "tools" / "abrir_exemplo.py"), str(projeto)], RAIZ)
    confere("abrir_exemplo.py abre o exemplo em uma pasta nova", aberto.returncode == 0 and "Lojas Exemplo" in aberto.stdout, aberto.stdout + aberto.stderr)
    confere("abrir_exemplo.py recusa uma pasta com arquivos", rodar([PY, str(RAIZ / "tools" / "abrir_exemplo.py"), str(projeto)], RAIZ).returncode == 2)
    confere("abrir_exemplo.py recusa uma pasta dentro do template", rodar([PY, str(RAIZ / "tools" / "abrir_exemplo.py"), str(RAIZ / "exemplo-aberto")], RAIZ).returncode == 2 and not (RAIZ / "exemplo-aberto").exists())
    confere("o pacote do brief do exemplo foi ativado", (projeto / ".claude/skills/pacote-martech-adtech/SKILL.md").is_file())

    rigor = validar(projeto, "--rigoroso")
    confere("o exemplo passa nas checagens rigorosas sem erro", rigor.returncode == 0 and "ERRO" not in rigor.stdout, rigor.stdout)
    dominio = rodar([PY, "entregaveis/_harness/scripts/dominio.py"], projeto)
    confere("as regras do domínio do exemplo estão provadas", dominio.returncode == 0 and "3 regra(s) provada(s)" in dominio.stdout, dominio.stdout)
    em_dia = rodar([PY, "-c", "import sys; sys.path.insert(0, 'entregaveis/_harness/scripts'); import comum, validar; print(validar.revisao_em_dia(comum.BASE / 'leitura-executiva'))"], projeto)
    confere("a revisão registrada no exemplo é a do conteúdo atual", em_dia.stdout.strip() == "True", em_dia.stdout + em_dia.stderr)
    estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto)
    confere("o estado mostra o material em falta, a decisão assumida e o item adiado", all(t in estado.stdout for t in ("Materiais pendentes: 1", "Decisões assumidas à espera do consultor: 1", "Itens adiados em aberto: 1")), estado.stdout)

    do_dia = rodar([PY, "entregaveis/_harness/scripts/rotina.py", "--hoje", "2026-11-27"], projeto)
    confere("a rotina do exemplo mostra a tarefa que vence e o pedido remarcado", "T-003" in do_dia.stdout and "Prazo próximo" in do_dia.stdout and "M-007" in do_dia.stdout and "Remarcado 1 vez(es), a partir de 2026-10-09" in do_dia.stdout, do_dia.stdout + do_dia.stderr)
    deslocadas = rodar([PY, "entregaveis/_harness/scripts/rotina.py", "--datas"], projeto)
    confere("o exemplo guarda a data original do pedido remarcado", "M-007: original 2026-10-09" in deslocadas.stdout and "nova 2026-12-04" in deslocadas.stdout, deslocadas.stdout)
    confere("o estado do exemplo mostra o nível de governança", "Governança: nível enxuto, 7 material(is)" in estado.stdout, estado.stdout)
    lista = rodar([PY, "entregaveis/_harness/scripts/rotina.py", "--lista", "--hoje", "2026-11-27"], projeto)
    topo = re.findall(r"^\d\. (\S+)", lista.stdout, flags=re.MULTILINE)
    confere("a lista do exemplo sobe o item ameaçado por risco, depois os dois prazos próximos", topo == ["T-002", "T-003", "M-007"] and "Risco de exposição alta: RS-001" in lista.stdout, lista.stdout + lista.stderr)
    confere("a lista do exemplo mostra a cobrança feita e pergunta pelo follow-up", "Última cobrança: 2026-11-20, 1 feita(s)" in lista.stdout and "T-001 (ação, Diretor de tecnologia): você já fez o follow-up" in lista.stdout, lista.stdout)
    confere("a lista do exemplo não pede outro nível de governança", "[nivel]" not in lista.stdout and "[premissas]" in lista.stdout, lista.stdout)
    desvios = rodar([PY, "entregaveis/_harness/scripts/governanca.py", "--desvios", "--hoje", "2026-11-27"], projeto)
    confere("o exemplo está dentro da linha de base", "Nenhum desvio contra a linha de base versão 1" in desvios.stdout, desvios.stdout + desvios.stderr)
    marca = rodar([PY, "-c", "import sys; sys.path.insert(0, 'entregaveis/_harness/scripts'); import comum; print(comum.carimbo(comum.BASE / 'leitura-executiva'))"], projeto)
    confere("a versão registrada no exemplo é a do conteúdo atual", marca.stdout.strip() and marca.stdout.strip() in (projeto / "entregaveis/_projeto/versoes.tsv").read_text(encoding="utf-8"), marca.stdout + marca.stderr)
    guardado = (origem / "entregaveis/_projeto/emitidos/2026-11-20-status-semanal.md").read_text(encoding="utf-8")
    refeito = rodar([PY, "entregaveis/_harness/scripts/emitir.py", "status-semanal", "--hoje", "2026-11-20"], projeto)
    confere("o status semanal guardado no exemplo é o que os registros de hoje produzem", refeito.stdout == guardado and "**Semáforo: amarelo.**" in guardado and "leitura-executiva v1: enviada a Diretoria da Lojas Exemplo em 2026-11-05, sem aceite registrado" in guardado, refeito.stdout + refeito.stderr)
    confere("o exemplo registra a emissão do status", "2026-11-20\tstatus-semanal\t\tentregaveis/_projeto/emitidos/2026-11-20-status-semanal.md\trascunho" in (origem / "entregaveis/_projeto/emitidos.tsv").read_text(encoding="utf-8"))
    controles = rodar([PY, "entregaveis/_harness/scripts/governanca.py", "--controles"], projeto)
    confere("o exemplo mostra os quatro controles do assessment cumpridos, com a evidência", controles.stdout.count("Situação: cumprido, por Consultora responsável") == 4 and "Evidência: E-001 a E-008." in controles.stdout and "Controles do tipo de projeto: 4, com 0 pendente(s) e 0 a confirmar" in estado.stdout and "Controle do tipo de projeto" not in lista.stdout, controles.stdout + estado.stdout)
    cerebro = [PY, "entregaveis/_harness/scripts/cerebro.py"]
    confere("o estado do exemplo conta as seis notas, sem nada a absorver", "Segundo cérebro: 6 nota(s). Antes de escrever" in estado.stdout, estado.stdout)
    confere("o segundo cérebro do exemplo absorveu tudo o que o projeto registrou", "Nada a absorver" in rodar(cerebro + ["--pendentes"], projeto).stdout, rodar(cerebro + ["--pendentes"], projeto).stdout)
    confere("o segundo cérebro do exemplo passa na conferência", "Segundo cérebro em ordem" in rodar(cerebro + ["--conferir"], projeto).stdout, rodar(cerebro + ["--conferir"], projeto).stdout)
    multa = rodar(cerebro + ["--buscar", "multa"], projeto)
    confere("a busca do exemplo traz a nota, a evidência e a lição", "1-projetos/saida-das-duas-plataformas-de-marco.md" in multa.stdout and "E-008" in multa.stdout and "L-002" in multa.stdout, multa.stdout)
    registro = (projeto / "entregaveis/_cerebro/registro.md").read_text(encoding="utf-8")
    confere("o exemplo mostra a decisão que não virou nota", "| D-010 | nada |" in registro and "D-010" not in "".join(a.read_text(encoding="utf-8") for a in (projeto / "entregaveis/_cerebro").glob("[1-4]-*/*.md")), registro)
    reunioes = (projeto / "entregaveis/_projeto/reunioes.tsv").read_text(encoding="utf-8")
    origens = {l.split("\t")[9] for l in (projeto / "entregaveis/_projeto/acoes.tsv").read_text(encoding="utf-8").splitlines() if l.startswith("T-")}
    confere("toda tarefa do exemplo aponta para uma reunião registrada", origens == {"A-001"} and "\nA-001\t2026-11-05\t" in reunioes, str(origens))

    marcados = [str(a.relative_to(origem)) for a in sorted(origem.rglob("*")) if a.suffix in (".md", ".tsv") and "PREENCHER" in a.read_text(encoding="utf-8")]
    confere("nenhum arquivo do exemplo ficou com marca de preenchimento", not marcados, str(marcados))
    guia = (origem / "LEIA-ME.md").read_text(encoding="utf-8")
    quebrados = [alvo for alvo in re.findall(r"\]\((?!https?:|#)([^)#]+)\)", guia) if not (origem / alvo).exists()]
    confere("todo link do guia do exemplo existe", not quebrados, str(quebrados))
    sys.path.insert(0, str(HARNESS / "scripts"))
    import checagens  # noqa: PLC0415

    for arquivo in sorted(origem.rglob("*.md")):
        erros = [a for a in checagens.texto(arquivo, ["pt"]) if a.nivel == "erro"]
        confere(f"exemplo/{arquivo.relative_to(origem)}: sem vício de texto", not erros, "\n".join(a.formatar() for a in erros[:5]))

    # O exemplo reprova no erro que o guia convida a provocar.
    conteudo = projeto / "entregaveis/leitura-executiva/conteudo.md"
    original = conteudo.read_text(encoding="utf-8")
    titulos = re.findall(r"^## \d+\. (.+)$", original, flags=re.MULTILINE)
    conteudo.write_text(original.replace("## 4. " + titulos[3], "## 4. Investimento"), encoding="utf-8")
    com_rotulo = validar(projeto, "leitura-executiva")
    confere("um título trocado por rótulo reprova o exemplo", com_rotulo.returncode != 0 and "é um rótulo" in com_rotulo.stdout, com_rotulo.stdout)
    conteudo.write_text(original, encoding="utf-8")

    if not tem_pacote("pptx"):
        print("  (python-pptx não está instalado: geração do exemplo pulada)")
        return
    from pptx import Presentation  # noqa: PLC0415

    gerado = rodar([PY, "entregaveis/_harness/scripts/gerar.py", "leitura-executiva"], projeto)
    arquivo = projeto / "entregaveis/leitura-executiva/saida/leitura-executiva.pptx"
    confere("o gerador produz o arquivo do exemplo", gerado.returncode == 0 and arquivo.is_file(), gerado.stdout + gerado.stderr)
    if arquivo.is_file():
        confere("o arquivo gerado tem uma página por título", [s.shapes.title.text_frame.text for s in Presentation(str(arquivo)).slides] == [re.sub(r"[*_`]", "", t) for t in titulos])
    guardado = [s.shapes.title.text_frame.text for s in Presentation(str(origem / "resultado" / "leitura-executiva.pptx")).slides]
    confere("o arquivo guardado em exemplo/resultado tem os títulos do conteúdo atual", guardado == titulos, str(guardado))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="kit-"))
    try:
        testar_skills()
        testar_referencias()
        testar_texto_do_kit()
        testar_instalador(tmp)
        testar_checagens(tmp)
        testar_hooks(tmp)
        testar_interativos(tmp)
        testar_dominio(tmp)
        testar_repositorio(tmp)
        testar_gerador(tmp)
        testar_fases(tmp)
        testar_ambientes(tmp)
        testar_pacotes(tmp)
        testar_levantamento(tmp)
        testar_rotina(tmp)
        testar_governanca(tmp)
        testar_emissao(tmp)
        testar_cerebro(tmp)
        testar_ambiente(tmp)
        testar_exemplo(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print()
    if falhas:
        print(f"{len(falhas)} de {total} conferências falharam:")
        for f in falhas:
            print(f"  - {f}")
        return 1
    print(f"Tudo certo: {total} conferências passaram.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
