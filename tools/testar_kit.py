#!/usr/bin/env python3
"""Testes do próprio kit. Só serve ao repositório do template.

Instala o harness em pastas temporárias e confere o instalador, as
skills, as checagens e os hooks. Cada checagem é provada dos dois lados:
passa em um exemplo bom e reprova no erro que ela existe para pegar.

Uso: python3 tools/testar_kit.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
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
    arquivos = [RAIZ / n for n in ("README.md", "INSTALL.md", "HISTORY.md", "AGENTS.md", "CLAUDE.md")]
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
    confere("acrescenta os cinco hooks", all(e in ajustes["hooks"] for e in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop")))
    confere("mantém a skill do projeto que tem o mesmo nome", (andamento / ".claude/skills/humanizar-texto/SKILL.md").read_text(encoding="utf-8") == "minha skill\n" and "não veio do kit" in saida.stdout, saida.stdout)
    confere("não toca na pasta de entregáveis que já existia", (andamento / "entregaveis/final/deck.pptx").read_text(encoding="utf-8") == "x" and "já existia" in saida.stdout)
    de_novo = instalar(andamento)
    confere("segunda instalação em projeto em andamento não muda nada", "Nada a fazer" in de_novo.stdout and (andamento / "AGENTS.md").read_text(encoding="utf-8").count("harness-de-entregaveis: inicio") == 1, de_novo.stdout)
    forcada = instalar(andamento, "--atualizar")
    confere("--atualizar não troca a skill do projeto", (andamento / ".claude/skills/humanizar-texto/SKILL.md").read_text(encoding="utf-8") == "minha skill\n", forcada.stdout)

    # Atualização: troca o que é do kit e preserva o que é do projeto.
    (vazio / "entregaveis/_harness/VERSAO").write_text("0.0.1\n", encoding="utf-8")
    (vazio / "entregaveis/_harness/REGRAS.md").write_text("regra velha\n", encoding="utf-8")
    skill = vazio / ".claude/skills/adiar-trabalho/SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8") + "\nlinha de versão antiga\n", encoding="utf-8")
    brief = vazio / "entregaveis/_projeto/brief.md"
    brief.write_text(brief.read_text(encoding="utf-8").replace("projeto: PREENCHER", "projeto: Meu projeto"), encoding="utf-8")
    sem_opcao = instalar(vazio)
    confere("sem --atualizar, avisa da versão diferente e não troca", "Use --atualizar" in sem_opcao.stdout and (vazio / "entregaveis/_harness/REGRAS.md").read_text(encoding="utf-8") == "regra velha\n", sem_opcao.stdout)
    atualizada = instalar(vazio, "--atualizar")
    confere("--atualizar troca o que é do kit", (vazio / "entregaveis/_harness/REGRAS.md").read_text(encoding="utf-8") == (HARNESS / "REGRAS.md").read_text(encoding="utf-8") and "linha de versão antiga" not in skill.read_text(encoding="utf-8"), atualizada.stdout + atualizada.stderr)
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
dono: Dona do projeto
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
aprovada_por: Dona do projeto
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
    com("storyline.md", ("aprovada: sim", "aprovada: nao"), "ERRO  [storyline]", "storyline: reprova conteúdo escrito sem aprovação do dono")
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
        f.write("| D-001 | 2026-11-20 | Deck de leitura em vez de projetado | O dono não disse | Vigente (assumida) |\n")
    estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto)
    confere("estado: conta as decisões assumidas à espera do dono", "Decisões assumidas à espera do dono: 1" in estado.stdout, estado.stdout)

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


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="kit-"))
    try:
        testar_skills()
        testar_referencias()
        testar_texto_do_kit()
        testar_instalador(tmp)
        testar_checagens(tmp)
        testar_hooks(tmp)
        testar_levantamento(tmp)
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
