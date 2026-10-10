#!/usr/bin/env python3
# HiddenKernel RADAR - 2026-10-10
# Basado en main de hiddenkernellab/PLM-Repository (commit bb83d07c...)
# Actualiza KStuff, ShadowMountPlus y PS5SX2 AIO.
# No realiza push, ni altera el repositorio remoto.

import json
import urllib.request
from pathlib import Path

# Snapshot exacto del main revisado. Evita ejecutar recursivamente este wrapper
# si posteriormente se publica como actualizador.py en la rama main.
MAIN_SHA = "bb83d07c9d3d8779eb5339ca7b9a8d2269811e8a"
MAIN_URL = (
    "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/"
    + MAIN_SHA + "/actualizador.py"
)

KSTUFF_URL = (
    "https://nexgen999.github.io/evoX-CoreOS/payloads/PS5_Beta/"
    "kstuff_Drakmor_Experimental/Source-Fixe/"
    "kstuff-1.13-fpkg-dr-test5.elf"
)
SMP_URL = (
    "https://github.com/drakmor/ShadowMountPlus/releases/download/"
    "1.7-beta5fix1/shadowmountplus.elf"
)

SELECTED = [
    {
        "name": "KStuff FPKG",
        "filename": "kstuff-1.13-fpkg-dr-test5.elf",
        "url": KSTUFF_URL,
        "source": "https://github.com/nexgen999/evoX-CoreOS",
        "source_direct": KSTUFF_URL,
        "description": (
            "KStuff FPKG 1.13-dr-test5. Build experimental distribuida por evoX. "
            "AVISO: el catalogo de evoX etiqueta el archivo como test5 pero "
            "su descripcion menciona test3; no se ha verificado una release "
            "publica oficial de esta build. ESTADO: EXPERIMENTAL."
        ),
        "last_update": "2026-10-10",
        "version": "1.13-dr-test5",
        "category": "ESENCIALES",
        "checksum": "829b45fe871dd64fbd53874ae4558076c2f1e1f203fe1ab52db5510d5fc45923",
    },
    {
        "name": "ShadowMountPlus",
        "filename": "shadowmountplus_1.7-beta5fix1.elf",
        "url": SMP_URL,
        "source": "https://github.com/drakmor/ShadowMountPlus/releases",
        "source_direct": SMP_URL,
        "description": (
            "Montaje automatico de juegos PS5, backports y fakelib. "
            "1.7beta5 incorpora modos fakelib por juego, mejoras de sandbox USB, "
            "fuentes y recuperacion de ShellCore. fix1 corrige iconos de juegos "
            "PS4 en unidades externas. Ya no usa auto-pausa ni autotune de "
            "KStuff: usar KStuff reciente y evitar etaHEN simultaneo. "
            "ESTADO: BETA RECIENTE; PROBAR ANTES DE AUTOCARGAR."
        ),
        "last_update": "2026-10-10",
        "version": "1.7-beta5fix1",
        "category": "ESENCIALES",
        "checksum": "e85fd63b705498488f39c09c9aea6f9fa22e0df2e932865de49a8cedf25172d5",
    },
]


def run_main_snapshot():
    req = urllib.request.Request(
        MAIN_URL,
        headers={"User-Agent": "HiddenKernel-Radar/2026-10-10", "Cache-Control": "no-cache"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        source = response.read().decode("utf-8")
    # Al ejecutarlo con otro __name__, el main del script original no se inicia
    # automaticamente. Invocamos main() exactamente una vez.
    namespace = {"__name__": "__hiddenkernel_main_snapshot__"}
    exec(compile(source, MAIN_URL, "exec"), namespace, namespace)
    namespace["main"]()


def update_catalog(path=Path("payloads.json")):
    if not path.is_file():
        raise FileNotFoundError(f"No se ha generado {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("payloads"), list):
        raise ValueError("Formato inesperado de payloads.json: no se modifica")
    payloads = data["payloads"]
    retained = []
    for item in payloads:
        if not isinstance(item, dict):
            retained.append(item)
            continue
        name = str(item.get("name", "")).casefold()
        # Se eliminan variantes antiguas y duplicadas, no otras herramientas.
        if "kstuff" in name or "k-stuff" in name or "shadowmount" in name:
            continue
        retained.append(item)
    retained.extend(SELECTED)
    data["payloads"] = retained
    # Escritura atomica para no dejar un JSON truncado si falla el proceso.
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    print(f"HiddenKernel: {len(retained)} entradas; KStuff test5 y SMP beta5fix1 incluidos")



def update_ps5sx2_aio(path=Path("payloads.json")):
    """Replace legacy PS5SX2 payloads with the official 2.01 AIO ELF."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("payloads"), list):
        raise ValueError("Formato inesperado de payloads.json")
    old_names = {"ps5sx2 helper", "ps5sx2 installer", "ps5sx2 aio", "disclaunch", "ps5sx2 disclaunch"}
    old_files = {"ps5sxhelper.elf", "ps5sx2installer.elf", "disclaunch.elf", "ps5sx2-aio.elf"}
    kept = []
    for item in data["payloads"]:
        if not isinstance(item, dict):
            kept.append(item)
            continue
        name = str(item.get("name", "")).strip().casefold()
        filename = str(item.get("filename", "")).strip().casefold()
        if name in old_names or filename in old_files:
            continue
        kept.append(item)
    url = "https://github.com/Swordpdf/PS5SX2/releases/download/vk-285-161/ps5sx2-aio.elf"
    kept.append({
        "name": "PS5SX2 AIO",
        "filename": "ps5sx2-aio.elf",
        "url": url,
        "source": "https://github.com/Swordpdf/PS5SX2/releases",
        "source_direct": url,
        "description": (
            "PS5SX2 2.01: instalador, helper y lanzador automatico de discos PS2 "
            "en un solo ELF. Sustituye PS5SXHelper, PS5SX2Installer y DiscLaunch. "
            "No ejecutar a la vez que los payloads anteriores; reiniciar antes "
            "de cambiar el autoload. ESTADO: EN PRUEBAS."
        ),
        "last_update": "2026-10-10",
        "version": "2.01 (vk-285-161)",
        "category": "EMULADORES",
        "checksum": "b52c7a70c266826974314417bc059063b6e8ab0b8cc9537471f65f0e4915560d",
    })
    data["payloads"] = kept
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    print("HiddenKernel: PS5SX2 AIO 2.01 incluido; Installer, Helper y DiscLaunch retirados")

def main():
    run_main_snapshot()
    update_catalog()
    update_ps5sx2_aio()


if __name__ == "__main__":
    main()
