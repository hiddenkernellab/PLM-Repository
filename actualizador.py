#!/usr/bin/env python3
# HiddenKernel RADAR - 2026-10-12 06:37 CEST
# Basado en actualizador.py main (blob SHA ee41ddd16ab90ebccc86c6b8887e506882ab0feb)
# Actualiza PS5SX2 Bot 2.03, PS5Upload 7.0.13 y Nuvio PS5 1.8.0; conserva Orbit 1.2.0.
# No realiza push ni altera GitHub.

import json
import re
import urllib.request
from pathlib import Path

# Se conserva el mecanismo de bootstrap del main actual.
MAIN_SHA = "bb83d07c9d3d8779eb5339ca7b9a8d2269811e8a"
MAIN_URL = "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/" + MAIN_SHA + "/actualizador.py"

KSTUFF_URL = (
    "https://nexgen999.github.io/evoX-CoreOS/payloads/PS5_Beta/"
    "kstuff_Drakmor_Experimental/Source-Fixe/kstuff-1.13-fpkg-dr-test5.elf"
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


def _atomic_write(path, data):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _load_catalog(path):
    if not path.is_file():
        raise FileNotFoundError(f"No se ha generado {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("payloads"), list):
        raise ValueError("Formato inesperado de payloads.json; no se modifica")
    return data


def run_main_snapshot():
    req = urllib.request.Request(
        MAIN_URL,
        headers={"User-Agent": "HiddenKernel-Radar/2026-10-12", "Cache-Control": "no-cache"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        source = response.read().decode("utf-8")
    namespace = {"__name__": "__hiddenkernel_main_snapshot__"}
    exec(compile(source, MAIN_URL, "exec"), namespace, namespace)
    namespace["main"]()


def update_catalog(path=Path("payloads.json")):
    data = _load_catalog(path)
    retained = []
    for item in data["payloads"]:
        if not isinstance(item, dict):
            retained.append(item)
            continue
        name = str(item.get("name", "")).casefold()
        if "kstuff" in name or "k-stuff" in name or "shadowmount" in name:
            continue
        retained.append(item)
    retained.extend(SELECTED)
    data["payloads"] = retained
    _atomic_write(path, data)
    print("HiddenKernel: una variante de KStuff y ShadowMountPlus conservada")


def update_ps5sx2_bot(path=Path("payloads.json")):
    """2.03: el upstream renombra AIO a ps5sx2-bot.elf; reemplaza todos los anteriores."""
    data = _load_catalog(path)
    obsolete = {
        "ps5sx2 helper", "ps5sx2 installer", "ps5sx2 aio", "ps5sx2 bot",
        "disclaunch", "ps5sx2 disclaunch",
    }
    obsolete_files = {
        "ps5sxhelper.elf", "ps5sx2installer.elf", "disclaunch.elf",
        "ps5sx2-aio.elf", "ps5sx2-bot.elf",
    }
    kept = [x for x in data["payloads"] if not (
        isinstance(x, dict) and (
            str(x.get("name", "")).strip().casefold() in obsolete or
            str(x.get("filename", "")).strip().casefold() in obsolete_files
        )
    )]
    url = "https://github.com/Swordpdf/PS5SX2/releases/download/vk-285-163/ps5sx2-bot.elf"
    kept.append({
        "name": "PS5SX2 Bot",
        "filename": "ps5sx2-bot.elf",
        "url": url,
        "source": "https://github.com/Swordpdf/PS5SX2/releases",
        "source_direct": url,
        "description": (
            "PS5SX2 2.03: helper unico con instalador y lanzador de discos PS2; "
            "sustituye ps5sx2-aio.elf. Inicio mas rapido y peticion de root "
            "compatible con etaHEN/OnionHEN/helper. Mantener el bot cargado "
            "para elevar permisos. Requiere instalar la app PS5SX2 por separado. "
            "ESTADO: EN PRUEBAS."
        ),
        "last_update": "2026-10-11",
        "version": "2.03 (vk-285-163)",
        "category": "EMULADORES",
        "checksum": "3420cdb5c826014b22b8ca8fa60a2026f0d9f91d3f5a5b818d4c98373eccb123",
    })
    data["payloads"] = kept
    _atomic_write(path, data)
    print("HiddenKernel: PS5SX2 2.03 Bot incluido; AIO 2.01 retirado")


RELEASES_VERIFIED = (
    {
        "repo": "saawant12/orbit-store-ps5",
        "name": "Orbit Store",
        "tag": "v1.2.0",
        "asset": "orbit_store.elf",
        "checksum": "86778d4fa830b1ff46379d167568c32294764cb05bc06ce6b05edc9db2a91691",
        "category": "DESCARGAS",
        "description": (
            "Orbit Store 1.2.0 beta: tienda y gestor de descargas en PS5, "
            "con extraccion de ZIP, RAR y 7z en la consola, mejoras para "
            "USB externo y control de descargas simultaneas. "
            "Usar solo para contenido autorizado. ESTADO: BETA."
        ),
    },
    {
        "repo": "theghostonline/Nuvio-PS5",
        "name": "Nuvio PS5",
        "tag": "v1.8.0",
        "asset": "nuvio-ps5.elf",
        "checksum": "2c4812fdf411116652db756a5bd563cb4934f9df76373f59bdba3ff25a79cc3b",
        "category": "MULTIMEDIA",
        "description": (
            "Nuvio PS5 1.8.0: reproductor multimedia. ELF de instalacion inicial; "
            "despues se inicia desde el menu de PS5 sin reenviar el payload. "
            "Corrige pantalla blanca tras reproduccion o reposo y mejora la busqueda. "
            "Si existe una version antigua en autoload, retirarla o sustituirla."
        ),
    },
)


def _version_key(tag):
    return tuple(int(x) for x in re.findall(r"\d+", str(tag))[:4])


def _latest_verified(spec):
    tag, checksum, asset_name = spec["tag"], spec["checksum"], spec["asset"]
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/" + spec["repo"] + "/releases/latest",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "HiddenKernel-Radar/2026-10-12"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            release = json.load(resp)
        candidate = str(release.get("tag_name", ""))
        assets = [a for a in release.get("assets", [])
                  if str(a.get("name", "")).lower() == asset_name.lower()]
        if candidate and _version_key(candidate) > _version_key(tag) and len(assets) == 1:
            digest = str(assets[0].get("digest", ""))
            url = str(assets[0].get("browser_download_url", ""))
            expected = ("https://github.com/" + spec["repo"] +
                        "/releases/download/" + candidate + "/" + asset_name)
            if digest.startswith("sha256:") and re.fullmatch(r"[0-9a-f]{64}", digest[7:]) and url == expected:
                tag, checksum = candidate, digest[7:]
            else:
                print("AVISO: release nueva sin SHA256/ELF verificable:", spec["name"])
    except (OSError, ValueError, KeyError):
        print("AVISO: GitHub API no accesible para", spec["name"], "- usando release verificada")
    url = "https://github.com/" + spec["repo"] + "/releases/download/" + tag + "/" + asset_name
    return {
        "name": spec["name"], "filename": asset_name,
        "url": url, "source": "https://github.com/" + spec["repo"] + "/releases",
        "source_direct": url, "description": spec["description"],
        "last_update": "2026-10-12", "version": tag,
        "category": spec["category"], "checksum": checksum,
    }


def update_radar_20261011(path=Path("payloads.json")):
    data = _load_catalog(path)
    items = [item for item in data["payloads"] if not (
        isinstance(item, dict)
        and str(item.get("name", "")).casefold().strip() == "anypad ps5"
        and "sinfiltros/AnyPad-PS5" in str(item.get("url", ""))
    )]
    for spec in RELEASES_VERIFIED:
        entry = _latest_verified(spec)
        old = [item for item in items if isinstance(item, dict)
               and str(item.get("name", "")).casefold() == spec["name"].casefold()]
        if old and max(_version_key(x.get("version", "")) for x in old) > _version_key(entry["version"]):
            print("HiddenKernel: no se degrada", spec["name"])
            continue
        items = [item for item in items if not (
            isinstance(item, dict)
            and (str(item.get("name", "")).casefold() == spec["name"].casefold()
                 or str(item.get("filename", "")).casefold() == spec["asset"].casefold())
        )]
        items.append(entry)
    data["payloads"] = items
    _atomic_write(path, data)


def update_ps5upload(path=Path("payloads.json")):
    """PS5Upload ELF versionado: validar el asset y digest de la ultima release."""
    data = _load_catalog(path)
    fallback_tag = "v7.0.13"
    fallback_digest = "579de1d0390925bd91fda3222ff98149b3e2425c6b5b16d6948dea8882744f66"
    tag, digest = fallback_tag, fallback_digest
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/phantomptr/ps5upload/releases/latest",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "HiddenKernel-Radar/2026-10-12"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            release = json.load(response)
        candidate = str(release.get("tag_name", ""))
        asset_name = "ps5upload-" + candidate.removeprefix("v") + ".elf"
        matches = [x for x in release.get("assets", []) if x.get("name") == asset_name]
        if candidate and _version_key(candidate) >= _version_key(tag) and len(matches) == 1:
            sha = str(matches[0].get("digest", ""))
            expected_url = "https://github.com/phantomptr/ps5upload/releases/download/" + candidate + "/" + asset_name
            if sha.startswith("sha256:") and re.fullmatch(r"[0-9a-f]{64}", sha[7:]) and matches[0].get("browser_download_url") == expected_url:
                tag, digest = candidate, sha[7:]
    except (OSError, ValueError, KeyError):
        print("AVISO: API PS5Upload no accesible; usando 7.0.13 verificada")
    version = tag.removeprefix("v")
    asset_name = "ps5upload-" + version + ".elf"
    url = "https://github.com/phantomptr/ps5upload/releases/download/" + tag + "/" + asset_name
    old = [x for x in data["payloads"] if isinstance(x, dict) and str(x.get("name", "")).casefold() == "ps5upload"]
    if old and max(_version_key(x.get("version", "")) for x in old) > _version_key(tag):
        print("HiddenKernel: no se degrada ps5upload")
        return
    kept = [x for x in data["payloads"] if not (
        isinstance(x, dict) and (
            str(x.get("name", "")).casefold() == "ps5upload" or
            re.fullmatch(r"ps5upload-[\d.]+\.elf", str(x.get("filename", "")).casefold())
        )
    )]
    kept.append({
        "name": "ps5upload", "filename": asset_name,
        "url": url, "source": "https://github.com/phantomptr/ps5upload/releases",
        "source_direct": url,
        "description": (
            "Servidor ELF para transferencias y gestion remota de archivos en PS5. "
            "Desde 7.0.10 el cliente gestiona Payload Manager y retrasa la restauracion "
            "automatica del helper 90 segundos tras detectar el loader, evitando "
            "un fallo durante el arranque. 7.0.11 permite instalar paquetes desde "
            "su tarjeta en el cliente; 7.0.12 agrega conversion Stored sin compresion "
            "en el cliente; 7.0.13 mejora verificacion de imagenes exFAT, "
            "gestion de errores 7z y rutas de envio entre consolas. "
            "Estas mejoras dependen tambien del cliente compatible."
        ),
        "last_update": "2026-10-12", "version": tag,
        "category": "ARCHIVOS / RED", "checksum": digest,
    })
    data["payloads"] = kept
    _atomic_write(path, data)
    print("HiddenKernel: ps5upload", tag, "ELF verificado")


def main():
    run_main_snapshot()
    update_catalog()
    update_ps5sx2_bot()
    update_radar_20261011()
    update_ps5upload()


if __name__ == "__main__":
    main()
