#!/usr/bin/env python3
import urllib.request
from pathlib import Path

BASE_URL = (
    "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/"
    "f12cc2780a3440771933c495aa95849823ecd95a/actualizador.py"
)

REPLACEMENTS = {
    "https://nexgen999.github.io/PS5-Super-PLDMGR-Auto-Updater/json/PS5_Beta.json":
        "https://raw.githubusercontent.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater/main/json/PS5_Beta.json",
    "https://nexgen999.github.io/PS5-Super-PLDMGR-Auto-Updater/json/ps5_hen_loader.json":
        "https://raw.githubusercontent.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater/main/json/ps5_hen_loader.json",
}

def download_base():
    req = urllib.request.Request(
        BASE_URL,
        headers={
            "User-Agent": "HiddenKernel-Hotfix/1.0",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")

def main():
    source = download_base()

    for old, new in REPLACEMENTS.items():
        count = source.count(old)
        if count < 1:
            raise RuntimeError(f"No se encontró URL a corregir: {old}")
        source = source.replace(old, new)

    marker = "# HK-HOTFIX-NEXGEN-RAW-2026-09-25"
    if marker not in source:
        source = marker + "\n" + source

    target = Path(__file__)

    # Validar sintaxis antes de sustituir el archivo.
    compile(source, str(target), "exec")
    target.write_text(source, encoding="utf-8", newline="\n")

    print("Hotfix aplicado: catálogos Nexgen pasan a raw.githubusercontent.com.")
    print("Ejecutando actualizador completo corregido...")

    ns = {
        "__name__": "__main__",
        "__file__": str(target),
        "__package__": None,
    }
    exec(compile(source, str(target), "exec"), ns, ns)

if __name__ == "__main__":
    main()
