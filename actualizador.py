#!/usr/bin/env python3
import urllib.request
from pathlib import Path

BASE_URL = (
    "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/"
    "f12cc2780a3440771933c495aa95849823ecd95a/actualizador.py"
)

OLD_PREFIX = "https://nexgen999.github.io/PS5-Super-PLDMGR-Auto-Updater/"
NEW_PREFIX = (
    "https://raw.githubusercontent.com/"
    "nexgen999/PS5-Super-PLDMGR-Auto-Updater/main/"
)
MARKER = "# HK-HOTFIX-NEXGEN-RAW-2026-09-25-V2"

def download_base():
    req = urllib.request.Request(
        BASE_URL,
        headers={
            "User-Agent": "HiddenKernel-Hotfix/2.0",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")

def main():
    source = download_base()

    count = source.count(OLD_PREFIX)
    if count < 1:
        raise RuntimeError(
            f"No se encontró el prefijo Nexgen a corregir: {OLD_PREFIX}"
        )

    source = source.replace(OLD_PREFIX, NEW_PREFIX)

    if MARKER not in source:
        source = MARKER + "\n" + source

    target = Path(__file__)

    # Validar el actualizador completo antes de reemplazar el hotfix.
    compile(source, str(target), "exec")
    target.write_text(source, encoding="utf-8", newline="\n")

    print(f"Hotfix V2 aplicado: {count} URL(s) Nexgen corregidas.")
    print("Ejecutando actualizador completo corregido...")

    ns = {
        "__name__": "__main__",
        "__file__": str(target),
        "__package__": None,
    }
    exec(compile(source, str(target), "exec"), ns, ns)

if __name__ == "__main__":
    main()
