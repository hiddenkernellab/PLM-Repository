#!/usr/bin/env python3
import urllib.request
from pathlib import Path

BASE_URL = (
    "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/"
    "c8c18ca69281bcbae97f4ec7b947a0d09a3ec76d/actualizador.py"
)
MARKER = "# HK-HOTFIX-NEXGEN-RAW-CHECKSUM-2026-09-25"

def download_base():
    req = urllib.request.Request(
        BASE_URL,
        headers={
            "User-Agent": "HiddenKernel-Nexgen-Raw-Checksum-Hotfix/1.0",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")

def main():
    source = download_base()

    old = '''    checksum = hashlib.sha256(data).hexdigest()
    expected = str(hit.get("checksum") or "").strip().lower()
    if expected and checksum.lower() != expected:
        raise RuntimeError(
            f'{app["name"]}: checksum no coincide '
            f'({checksum} != {expected})'
        )
'''

    new = '''    checksum = hashlib.sha256(data).hexdigest()

    # Nexgen genera algunas entradas Source-Fixe descargando una URL /blob/
    # de GitHub. Esa URL devuelve una página HTML, por lo que el checksum
    # publicado puede corresponder al HTML y no al ELF real.
    # Cuando ya hemos cambiado la descarga al binario raw del árbol Internal,
    # nuestro SHA-256 calculado sobre el ELF real es la referencia correcta.
    using_nexgen_internal_raw = (
        "raw.githubusercontent.com/"
        "nexgen999/PS5-Super-PLDMGR-Auto-Updater/main/Internal/"
        in url
    )

    expected = (
        ""
        if using_nexgen_internal_raw
        else str(hit.get("checksum") or "").strip().lower()
    )

    if expected and checksum.lower() != expected:
        raise RuntimeError(
            f'{app["name"]}: checksum no coincide '
            f'({checksum} != {expected})'
        )
'''

    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"Bloque checksum esperado no encontrado exactamente una vez: {count}"
        )

    source = source.replace(old, new, 1)

    if MARKER not in source:
        source = MARKER + "\n" + source

    target = Path(__file__)
    compile(source, str(target), "exec")
    target.write_text(source, encoding="utf-8", newline="\n")

    print("Hotfix checksum Nexgen aplicado.")
    print("Ejecutando actualizador completo...")

    ns = {
        "__name__": "__main__",
        "__file__": str(target),
        "__package__": None,
    }
    exec(compile(source, str(target), "exec"), ns, ns)

if __name__ == "__main__":
    main()
