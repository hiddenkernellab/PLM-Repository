#!/usr/bin/env python3
import urllib.request
from pathlib import Path

BASE_URL = (
    "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/"
    "089b64c0660dbf92239e6991d57cd050a6395031/actualizador.py"
)
MARKER = "# HK-HOTFIX-FPKG-SOURCES-2026-09-25"

def download_base():
    req = urllib.request.Request(
        BASE_URL,
        headers={
            "User-Agent": "HiddenKernel-FPKG-Hotfix/3.0",
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

    source = replace_once(
        source,
        'catalog_name_regex=[r"^Kstuff .* Fpkg Dr Test\\\\d+$"],\n'
        '         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",',
        'catalog_name_regex=[r"^Kstuff .* Fpkg Dr Test\\\\d+$"],\n'
        '         catalog_raw_dir="Internal/payloads/beta/Kstuff-Darkmor",\n'
        '         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",',
        "Kstuff Drakmor raw dir",
    )

    source = replace_once(
        source,
        'catalog_name_regex=[r"^A53 Kstuff Shadowmountplus 3In1$"],\n'
        '         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",',
        'catalog_name_regex=[r"^A53 Kstuff Shadowmountplus 3In1$"],\n'
        '         catalog_raw_dir="Internal/payloads/beta/SoNic-AIO",\n'
        '         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",',
        "AIO raw dir",
    )

    source = replace_once(
        source,
        'catalog_name_regex=[r"^A53 Ppr Install 1140 .*"],\n'
        '         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",',
        'catalog_name_regex=[r"^A53 Ppr Install 1140 .*"],\n'
        '         catalog_raw_dir="Internal/payloads/beta/a53_ppr",\n'
        '         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",',
        "A53 1140 raw dir",
    )

    source = replace_once(
        source,
        'catalog_name_regex=[r"^A53 Ppr Install 1160 .*"],\n'
        '         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",',
        'catalog_name_regex=[r"^A53 Ppr Install 1160 .*"],\n'
        '         catalog_raw_dir="Internal/payloads/beta/a53_ppr",\n'
        '         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",',
        "A53 1160 raw dir",
    )

    source = replace_once(
        source,
        '''    url = hit.get("url") or hit.get("source_direct")
    if not url:
        raise RuntimeError(
            f'{app["name"]}: el catálogo no proporciona URL descargable.'
        )

    data = get_bytes(url)
    filename = hit.get("filename") or Path(url.split("?", 1)[0]).name
    if not filename.lower().endswith((".elf", ".bin")):
''',
        '''    url = hit.get("url") or hit.get("source_direct")
    if not url:
        raise RuntimeError(
            f'{app["name"]}: el catálogo no proporciona URL descargable.'
        )

    filename = hit.get("filename") or Path(url.split("?", 1)[0]).name

    raw_dir = app.get("catalog_raw_dir")
    if raw_dir:
        url = (
            "https://raw.githubusercontent.com/"
            "nexgen999/PS5-Super-PLDMGR-Auto-Updater/main/"
            f'{raw_dir.strip("/")}/{filename}'
        )

    data = get_bytes(url)
    if not filename.lower().endswith((".elf", ".bin")):
''',
        "descarga directa de binarios de catalogo",
    )

    source = replace_once(
        source,
        '''    return [{
        "name": app["name"],
        "filename": filename,
        "url": url,
''',
        '''    checksum = hashlib.sha256(data).hexdigest()
    expected = str(hit.get("checksum") or "").strip().lower()
    if expected and checksum.lower() != expected:
        raise RuntimeError(
            f'{app["name"]}: checksum del mirror no coincide '
            f'({checksum} != {expected})'
        )

    return [{
        "name": app["name"],
        "filename": filename,
        "url": url,
''',
        "validacion checksum catalogo",
    )

    source = replace_once(
        source,
        '"checksum": hashlib.sha256(data).hexdigest(),\n    }]\n\ndef process(app):',
        '"checksum": checksum,\n    }]\n\ndef process(app):',
        "checksum final catalogo",
    )

    source = source.replace(
        'compatibility="segun build; validar firmware antes de usar",',
        'compatibility="FW 1.00-11.60 en la build test3; validar builds futuras",',
        1,
    )

    if MARKER not in source:
        source = MARKER + "\n" + source

    target = Path(__file__)
    compile(source, str(target), "exec")
    target.write_text(source, encoding="utf-8", newline="\n")

    print("Hotfix FPKG/A53 aplicado y actualizador completo validado.")
    print("Ejecutando catálogo corregido...")

    ns = {
        "__name__": "__main__",
        "__file__": str(target),
        "__package__": None,
    }
    exec(compile(source, str(target), "exec"), ns, ns)

if __name__ == "__main__":
    main()
