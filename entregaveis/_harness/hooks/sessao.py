#!/usr/bin/env python3
"""Hook de início de sessão: põe o estado do projeto no contexto do agente."""
from __future__ import annotations

import _base
import estado


def principal() -> int:
    print("\n".join(estado.linhas_de_estado()))
    return 0


if __name__ == "__main__":
    _base.protegido(principal)
