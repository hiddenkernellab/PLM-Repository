#!/usr/bin/env python3
import hashlib
import urllib.request
from pathlib import Path

BASE_URL = (
    "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/"
    "089b64c0660dbf92239e6991d57cd050a6395031/actualizador.py"
)
MARKER = "# HK-HOTFIX-FPKG-SOURCES-2026-09-25-V4"

def download_base():
    req = urllib.request.Request(
        BASE_URL,
        headers={
            "User-Agent": "HiddenKernel-FPKG-Hotfix/4.0",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")

def replace_once(s, old, new, label):
    count = s.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: se esperaba 1 coincidencia y hay {count}"
        )
    return s.replace(old, new, 1)

def main():
    source = download_base()

    old = '''    url = hit.get("url") or hit.get("source_direct")
    if not url:
        raise RuntimeError(
            f'{app["name"]}: el catálogo no proporciona URL descargable.'
        )

    data = get_bytes(url)
    filename = hit.get("filename") or Path(url.split("?", 1)[0]).name
    if not filename.lower().endswith((".elf", ".bin")):
'''

    new = '''    url = hit.get("url") or hit.get("source_direct")
    if not url:
        raise RuntimeError(
            f'{app["name"]}: el catálogo no proporciona URL descargable.'
        )

    filename = hit.get("filename") or Path(url.split("?", 1)[0]).name

    # Los JSON de Nexgen son el índice correcto, pero algunas URLs de GitHub
    # Pages devuelven 404 desde Actions. Para estas builds conocidas usamos
    # directamente el binario del árbol Internal del repositorio.
    nexgen_raw = (
        "https://raw.githubusercontent.com/"
        "nexgen999/PS5-Super-PLDMGR-Auto-Updater/main/"
    )

    if filename.startswith("kstuff-1.13-fpkg-dr-test"):
        url = nexgen_raw + "Internal/payloads/beta/Kstuff-Darkmor/" + filename
    elif filename.startswith("a53_ppr_install_"):
        url = nexgen_raw + "Internal/payloads/beta/a53_ppr/" + filename
    elif filename in {
        "A53-Kstuff-ShadowMountPlus-3in1.elf",
        "A53-kstuff-SMP.elf",
    }:
        url = nexgen_raw + "Internal/payloads/beta/SoNic-AIO/" + filename

    data = get_bytes(url)
    if not filename.lower().endswith((".elf", ".bin")):
'''

    source = replace_once(
        source, old, new, "descarga directa FPKG/A53"
    )

    old_return = '''    return [{
        "name": app["name"],
        "filename": filename,
        "url": url,
'''

    new_return = '''    checksum = hashlib.sha256(data).hexdigest()
    expected = str(hit.get("checksum") or "").strip().lower()
    if expected and checksum.lower() != expected:
        raise RuntimeError(
            f'{app["name"]}: checksum no coincide '
            f'({checksum} != {expected})'
        )

    return [{
        "name": app["name"],
        "filename": filename,
        "url": url,
'''

    source = replace_once(
        source, old_return, new_return, "validación checksum"
    )

    source = replace_once(
        source,
        '"checksum": hashlib.sha256(data).hexdigest(),\n    }]\n\ndef process(app):',
        '"checksum": checksum,\n    }]\n\ndef process(app):',
        "checksum final",
    )

    source = source.replace(
        'compatibility="segun build; validar firmware antes de usar",',
        'compatibility="FW 1.00-11.60 en test3; validar builds futuras",',
        1,
    )

    if MARKER not in source:
        source = MARKER + "\n" + source

    target = Path(__file__)
    compile(source, str(target), "exec")
    target.write_text(source, encoding="utf-8", newline="\n")

    print("Hotfix V4 aplicado. Ejecutando actualizador completo...")

    ns = {
        "__name__": "__main__",
        "__file__": str(target),
        "__package__": None,
    }
    exec(compile(source, str(target), "exec"), ns, ns)

if __name__ == "__main__":
    main()
