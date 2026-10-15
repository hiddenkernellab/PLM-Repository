#!/usr/bin/env python3
"""HiddenKernel: actualizador ELF, revision 2026-10-15 06:27 CEST.

Lee el catalogo existente y actualiza solo releases ELF comprobables.
No ejecuta generadores antiguos, no descarga ni ejecuta codigo remoto
y no realiza commits ni push. Python 3.12, sin dependencias externas.

Fuentes: releases oficiales con ELF y SHA-256 verificables.
Las incorporaciones y migraciones principales son curadas; las demas se actualizan
solo si el ELF de la release se identifica sin ambiguedad.
Adaptado al main de HiddenKernel del 14/10/2026, 21:40 UTC (commit f38a3f5b).
Conserva Payload Manager 0.6.1, PatchDL 0.0.7 y Orbit Store 1.3.5;
parte de PS4Mount 0.5.0 del main y lo actualiza a 0.5.1.
Los cuatro cambios anteriores pendientes siguen disponibles.
Actualiza RomM Sync a 1.2.0 y PS4Mount a 0.5.1 desde sus releases oficiales.
Conserva el generador de iconos actual; incorpora PS5SX2 2.10, LZ4 1.5.0,
LibrePadPS5 y PS5Library Agent 0.2.91 (proyecto independiente).
Payload Manager 0.6.1 y PS4Mount 0.5.0 ya estaban en el catalogo actual.
No cargar el antiguo ps5sx2-bot junto al helper nuevo.
No incluye Raiju: upstream 404 y desarrollo aun pre-alpha.
"""
import json
import base64
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CATALOG = Path(__file__).resolve().parent / "payloads.json"
API = "https://api.github.com/repos/{repo}/releases/latest"

# Versiones y SHA-256 comprobados en las releases oficiales.
# Se utilizan como respaldo si GitHub API no responde.
TRACKED = (
    {
        "key": "ps5upload",
        "name": "ps5upload",
        "repo": "phantomptr/ps5upload",
        "tag": "v7.0.22",
        "asset": "ps5upload-7.0.22.elf",
        "sha256": "e382353612fdf85b2fdbfea75f4f5ebad260c767faa51b0446118646a6db0267",
        "date": "2026-10-12",
        "category": "ARCHIVOS / RED",
        "description": (
            "Servidor PS5Upload para transferencias y gestion de archivos desde "
            "un cliente compatible. Desde 7.0.22 se mejora la exportacion "
            "de capturas HDR PNG con perfil ICC. Algunas funciones requieren "
            "actualizar tambien el cliente."
        ),
    },
    {
        "key": "nuvio",
        "name": "Nuvio PS5",
        "repo": "theghostonline/Nuvio-PS5",
        "tag": "v1.8.0",
        "asset": "nuvio-ps5.elf",
        "sha256": "2c4812fdf411116652db756a5bd563cb4934f9df76373f59bdba3ff25a79cc3b",
        "date": "2026-10-12",
        "category": "MULTIMEDIA",
        "description": (
            "Reproductor multimedia PS5. El ELF instala Nuvio y su servicio "
            "para abrirlo posteriormente desde el menu, sin reenviar el ELF "
            "en cada inicio. Corrige errores de reproduccion y busqueda."
        ),
    },
    {
        "key": "ps5sx2",
        "name": "PS5SX2 Helper",
        "repo": "Swordpdf/PS5SX2",
        "tag": "vk-285-171",
        "asset": "PS5SXHelper.elf",
        "sha256": "9fa809eb10e1fe5149b2d031f55497d7b050e950ec5aec38bac7ebe1ef6da153",
        "date": "2026-10-14",
        "category": "EMULADORES",
        "description": (
            "PS5SX2 2.10: helper para permisos, montaje /data y mosaicos de DVD PS2 "
            "en el menu de PS5, con ShadowMountPlus. Sustituye al antiguo "
            "ps5sx2-bot.elf (2.03), al helper anterior y a los lanzadores de disco. "
            "Cargar despues de ShadowMountPlus; no cargar bot ni otros helpers a la vez. "
            "AVISO: extraer el disco antes de apagar la consola; el autor advierte "
            "de posibles kernel panic al apagar con el disco dentro. "
            "PS5 no lee discos PS2 en formato CD. Funcionalidad experimental."
        ),
    },
    {
        "key": "ps5sx2_installer",
        "name": "PS5SX2 Installer",
        "repo": "Swordpdf/PS5SX2",
        "tag": "vk-285-171",
        "asset": "PS5SX2Installer.elf",
        "sha256": "6b1be3ea24ec8144b27b2a1f3e279cd17574f3093e9431abf8579dcc6c0bfae9",
        "date": "2026-10-14",
        "category": "EMULADORES",
        "description": (
            "Instalador oficial PS5SX2 2.10: descarga e instala la aplicacion "
            "desde las releases de Swordpdf. Se usa con PS5SXHelper.elf, "
            "que sustituye al antiguo bot 2.03. No es necesario autocargarlo."
        ),
    },
    {
        "key": "pldmgr",
        "name": "Payload Manager",
        "repo": "itsPLK/ps5-payload-manager",
        "tag": "v0.6.1",
        "asset": "pldmgr_v0.6.1.elf",
        "sha256": "5165cbe4c13360828bd0f5d558cdbb9e2d55b0660b1dc7f7a58d3f4ee9e23285",
        "date": "2026-10-14",
        "category": "SISTEMA",
        "description": (
            "Payload Manager 0.6.1: busqueda, filtros, favoritos y autoload. "
            "Recupera el cierre automatico del reproductor de discos al iniciar "
            "para BD-JB antiguos. Es diferente de HK-PLDMGR-Install-Update. "
            "Tambien puede actualizarse desde su propia interfaz."
        ),
    },
    {
        "key": "patchdl",
        "name": "PatchDL",
        "repo": "knutwurst/ps5-patchdl",
        "tag": "v0.0.7",
        "asset": "patchdl_0.0.7.elf",
        "sha256": "925d211fa8aaeb6b52b635c54641a14e36239ad3ebbdd3f7738c79a1c1e688e3",
        "date": "2026-10-14",
        "category": "DESCARGAS",
        "description": (
            "Descarga actualizaciones oficiales de juegos instalados con cola, "
            "reanudacion y panel web. 0.0.7 corrige arranque y acceso directo "
            "en FW 13.xx; probado en 11.60 y 13.60. No descarga juegos."
        ),
    },
    {
        "key": "ps4mount",
        "name": "PS4Mount",
        "repo": "gasb07/ps4mount",
        "tag": "v0.5.1",
        "asset": "ps4mount.elf",
        "sha256": "23ef99696af8da139fafd13e97e0d1f94968f2e745cb79e45a6aa71bc6391549",
        "date": "2026-10-15",
        "category": "JUEGOS / COMPATIBILIDAD",
        "description": (
            "PS4Mount 0.5.1: monta PS4 FPKG y actualizaciones desde USB exFAT "
            "sin copiarlos al SSD interno; interfaz web local en puerto 8770. "
            "DLC con limitaciones. 0.5.1 agrega fecha y hora a cada linea "
            "de log. Probado por el autor en FW 13.20; "
            "otras versiones sin verificar. EXPERIMENTAL: no autocargar."
        ),
    },
    {
        "key": "romm",
        "name": "RomM Sync",
        "repo": "s0liton/RommPS",
        "tag": "v1.2.0",
        "asset": "romm-sync.elf",
        "sha256": "5e33f6178780a939e2ea4a13f363b5fe63bc2a63739d90c3ec3faaa71e169861",
        "date": "2026-10-14",
        "category": "EMULADORES",
        "description": (
            "RomM Sync / RommPS 1.2.0: sincroniza ROMs, partidas y estados "
            "con un servidor RomM propio. Descarga las partidas al terminar "
            "cada juego, permite desactivar o ajustar la sincronizacion por "
            "plataforma, muestra conflictos y actividad y permite restaurar "
            "partidas. Soporta Porpoise, SwanStationPS5 y PS5NES. "
            "Requiere servidor RomM; el ELF es el agente PS5, no el de PS4. "
            "RommPS puede actualizar tambien sus componentes desde la app."
        ),
    },
    {
        "key": "lz4",
        "name": "LZ4 Compression",
        "repo": "theghostonline/PS5-LZ4-Compression",
        "tag": "v1.5.0",
        "asset": "lz4-compression.elf",
        "sha256": "edb4f2c5922bea293cc5c5354bd301fb0bde48856c0d2a8d115801d3c778b3f1",
        "date": "2026-10-14",
        "category": "JUEGOS / COMPATIBILIDAD",
        "description": (
            "LZ4 Compression 1.5.0: compresion y verificacion de juegos PS5 "
            "para APR-EMU. Corrige Ghost of Yotei y permisos de paquetes "
            "(v1.4.3); incorpora actualizacion automatica de app y motor "
            "e informes de compatibilidad por juego. Requiere tambien "
            "instalar la app PPSA99420 desde el ZIP oficial una vez; "
            "el ELF por si solo no instala toda la interfaz. "
            "No autocargar ni borrar los originales sin probar."
        ),
    },

    {
        "key": "librepad",
        "name": "LibrePadPS5",
        "repo": "arwebSE/LibrePadPS5",
        "tag": "v1.1.3",
        "asset": "LibrePadPS5.elf",
        "sha256": "736ea4b0a17aafce4ade2b696a6d5d2a8b856b83c6960a3d0ec117e23ba2c2c0",
        "date": "2026-10-12",
        "category": "MANDOS / AUDIO",
        "description": (
            "LibrePadPS5 1.1.3: hasta cuatro mandos de PlayStation, Xbox, "
            "Switch y 8BitDo mediante USB, adaptadores o Bluetooth opcional; "
            "panel web local en puerto 8096 y remapeo. Bluetooth interno "
            "desactivado por defecto. Probado principalmente en FW 12.60; "
            "8BitDo Adapter 2 confirmado en 13.60. Detener otros payloads "
            "de mandos antes de cargar; probar manualmente, no autoload."
        ),
    },

    {
        "key": "ps5library_agent",
        "name": "PS5Library Agent (rdiol12)",
        "repo": "rdiol12/PS5Library",
        "tag": "v0.2.91",
        "asset": "ps5library-agent.elf",
        "sha256": "ac78389a628401edba3c081f00156238ad5652b1b7ad241f5ccc7713179f0c82",
        "date": "2026-10-14",
        "category": "DESCARGAS",
        "description": (
            "Agente de la plataforma PS5Library de rdiol12: inventario local, "
            "almacenamiento y gestion desde la app nativa. Requiere instalar "
            "PS5Library-0.2.91.pkg de la misma release; para catalogos y "
            "descargas remotas necesita servidor privado propio. No es "
            "PS5 Library de deox1111 (0.7.x). No autocargar si no usas "
            "su aplicacion; no usar para formatear USB sin copia previa."
        ),
    },

)

OLD_PS5SX2_NAMES = {
    "ps5sx2 aio", "ps5sx2 bot",
    "ps5sx2 helper", "ps5sx2 disclaunch", "disclaunch",
}
OLD_PS5SX2_FILES = {
    "ps5sx2-aio.elf", "ps5sx2-bot.elf",
    "ps5sxhelper.elf", "disclaunch.elf",
}


def version_numbers(value):
    """Version comparable para v7.0.22, 1.8.0 o 2.03 (vk-285-163)."""
    value = str(value)
    # PS5SX2: comparar la version visible, no los numeros del build vk.
    match = re.search(r"\d+(?:\.\d+){1,3}", value)
    if match:
        nums = [int(x) for x in match.group().split(".")]
    else:
        nums = [int(x) for x in re.findall(r"\d+", value)[:3]]
    return tuple((nums + [0] * 4)[:4])


def fetch_release(repo, include_prerelease=False):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "HiddenKernel-ELF-Updater/2026-10-15",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    url = ("https://api.github.com/repos/" + repo + "/releases?per_page=10"
           if include_prerelease else API.format(repo=repo))
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=18) as response:
        return json.load(response)


def release_asset(spec, release):
    """Solo aceptar un ELF con nombre, URL y SHA-256 verificables."""
    if release.get("draft") or (release.get("prerelease") and not spec.get("allow_prerelease")):
        return None
    tag = str(release.get("tag_name", ""))
    if not tag:
        return None
    if spec["key"] == "ps5upload":
        asset_name = "ps5upload-" + tag.removeprefix("v") + ".elf"
    elif spec["key"] == "patchdl":
        asset_name = "patchdl_" + tag.removeprefix("v") + ".elf"
    elif spec["key"] == "pldmgr":
        asset_name = "pldmgr_" + tag + ".elf"
    else:
        asset_name = spec["asset"]
    expected = (
        "https://github.com/" + spec["repo"]
        + "/releases/download/" + tag + "/" + asset_name
    )
    matches = [a for a in release.get("assets", []) if a.get("name") == asset_name]
    if len(matches) != 1:
        return None
    asset = matches[0]
    digest = str(asset.get("digest") or "")
    if (asset.get("browser_download_url") != expected
            or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest)):
        return None
    return {
        "tag": tag,
        "asset": asset_name,
        "sha256": digest[7:],
        "date": str(release.get("published_at") or spec["date"])[:10],
        "release_name": str(release.get("name") or ""),
    }


def pinned_release(spec):
    return {
        "tag": spec["tag"],
        "asset": spec["asset"],
        "sha256": spec["sha256"],
        "date": spec["date"],
        "release_name": "",
    }


def release_order(key, value):
    """Version ordering; PS5SX2 tags use vk build numbers, not semver."""
    if key in {"ps5sx2", "ps5sx2_installer"}:
        match = re.search(r"vk-(\d+)-(\d+)", str(value))
        if match:
            return (int(match.group(1)), int(match.group(2)), 0, 0, 1, 0)
    return version_numbers(value) + (1, 0)


def select_release(spec):
    chosen = pinned_release(spec)
    try:
        response = fetch_release(spec["repo"], bool(spec.get("allow_prerelease")))
        releases = response if isinstance(response, list) else [response]
        verified = [x for r in releases if isinstance(r, dict)
                    if (x := release_asset(spec, r)) is not None]
        if verified:
            live = max(verified, key=lambda x: release_order(spec["key"], x["tag"]))
            if release_order(spec["key"], live["tag"]) >= release_order(spec["key"], chosen["tag"]):
                chosen = live
        else:
            print("AVISO: release actual sin ELF/SHA-256 valido:", spec["name"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("AVISO: API no disponible para", spec["name"], "-", str(exc)[:140])
    return chosen


def matches_target(item, key):
    if not isinstance(item, dict):
        return False
    name = str(item.get("name", "")).strip().casefold()
    filename = str(item.get("filename", "")).strip().casefold()
    if key == "ps5sx2":
        return name in OLD_PS5SX2_NAMES or filename in OLD_PS5SX2_FILES
    if key == "ps5sx2_installer":
        return name == "ps5sx2 installer" or filename == "ps5sx2installer.elf"
    if key == "pldmgr":
        return name in {"ps5 payload manager", "payload manager", "pldmgr"} or bool(
            re.fullmatch(r"pldmgr(?:_v[0-9.]+)?\.elf", filename))
    if key == "ps5upload":
        return name == "ps5upload" or bool(re.fullmatch(
            r"ps5upload[-_]v?\d+(?:\.\d+)*\.elf", filename))
    if key == "nuvio":
        return name == "nuvio ps5" or filename == "nuvio-ps5.elf"
    if key == "ps4mount":
        return name == "ps4mount" or filename == "ps4mount.elf"
    if key == "patchdl":
        return name == "patchdl" or bool(re.fullmatch(r"patchdl[-_]v?\d+(?:\.\d+)*\.elf", filename))
    if key == "romm":
        return name in {"romm sync", "rommps", "ps5-romm"} or filename == "romm-sync.elf"
    if key == "lz4":
        return name == "lz4 compression" or filename == "lz4-compression.elf"
    if key == "librepad":
        return name in {"librepadps5", "librepad ps5"} or filename == "librepadps5.elf"
    if key == "ps5library_agent":
        return name in {"ps5library agent (rdiol12)", "ps5library-agent"} or filename == "ps5library-agent.elf"
    return False


def make_entry(spec, release):
    tag, filename = release["tag"], release["asset"]
    url = (
        "https://github.com/" + spec["repo"]
        + "/releases/download/" + tag + "/" + filename
    )
    version = tag
    if spec["key"] in {"ps5sx2", "ps5sx2_installer"}:
        match = re.search(r"\b(\d+\.\d+)\b", release["release_name"])
        version = ((match.group(1) + " (" + tag + ")") if match else
                   ("2.10 (" + tag + ")" if tag == spec["tag"] else tag))
    return {
        "name": spec["name"],
        "filename": filename,
        "url": url,
        "source": "https://github.com/" + spec["repo"] + "/releases",
        "source_direct": url,
        "description": spec["description"],
        "last_update": release["date"],
        "version": version,
        "category": spec["category"],
        "checksum": release["sha256"],
    }


def update_entries(items, spec, entry):
    indices = [i for i, item in enumerate(items) if matches_target(item, spec["key"])]
    current = [items[i] for i in indices]
    if current:
        highest = max(release_order(spec["key"], x.get("version", "")) for x in current)
        if highest > release_order(spec["key"], entry["version"]):
            print("OMITIDO: version mas nueva ya en catalogo:", spec["name"])
            return items, False
        if len(current) == 1:
            # Avoid rewriting metadata or rolling back publication dates when
            # the API is temporarily unavailable but the ELF is unchanged.
            stable_fields = ("version", "filename", "url", "checksum")
            if all(str(current[0].get(k, "")) == str(entry.get(k, ""))
                   for k in stable_fields):
                return items, False
    first = indices[0] if indices else len(items)
    result = [x for x in items if not matches_target(x, spec["key"])]
    result.insert(first, entry)
    return result, result != items



def refresh_other_official_releases(items):
    """Actualiza otros ELF solo si la release oficial coincide exactamente.

    Nunca incorpora proyectos nuevos, no toca builds especiales ni .bin,
    y no actualiza si falta SHA-256 o el nombre del ELF no es identificable.
    """
    repo_cache = {}
    changes = []
    result = []
    for item in items:
        if any(matches_target(item, x["key"]) for x in TRACKED):
            result.append(item)
            continue
        source = str(item.get("source", "")).rstrip("/")
        match = re.fullmatch(r"https://github\.com/([^/]+/[^/]+)/releases", source)
        if not match:
            result.append(item)
            continue
        repo = match.group(1)
        url = str(item.get("url", ""))
        prefix = "https://github.com/" + repo + "/releases/download/"
        if not url.startswith(prefix) or not url.lower().endswith(".elf"):
            result.append(item)
            continue
        old_asset = url.rsplit("/", 1)[-1]
        old_tag = str(item.get("version", ""))
        if not re.search(r"\d", old_tag):
            result.append(item)
            continue
        if repo not in repo_cache:
            try:
                repo_cache[repo] = fetch_release(repo)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                repo_cache[repo] = None
                print("AVISO: sin acceso a", repo, "-", str(exc)[:100])
        release = repo_cache[repo]
        if not release or release.get("draft") or release.get("prerelease"):
            result.append(item)
            continue
        new_tag = str(release.get("tag_name") or "")
        if not new_tag or version_numbers(new_tag) <= version_numbers(old_tag):
            result.append(item)
            continue

        old_short = old_tag.removeprefix("v")
        new_short = new_tag.removeprefix("v")
        candidates = [old_asset]
        # Probar sustitucion versionada, sin adivinar nombres de otros proyectos.
        for old, new in ((old_tag, new_tag), (old_short, new_short)):
            if old and old in old_asset:
                candidates.append(old_asset.replace(old, new, 1))
        # Algunas entradas usan un alias local, pero la URL oficial tiene el
        # nombre verdadero del ELF; se usa siempre la URL para verificar.
        asset_map = {str(a.get("name")): a for a in release.get("assets", [])}
        selected = None
        for name in dict.fromkeys(candidates):
            a = asset_map.get(name)
            if a is None or not name.lower().endswith(".elf"):
                continue
            expected = prefix + new_tag + "/" + name
            digest = str(a.get("digest") or "")
            if (a.get("browser_download_url") == expected
                    and re.fullmatch(r"sha256:[a-f0-9]{64}", digest)):
                selected = (name, expected, digest[7:])
                break
        if selected is None:
            result.append(item)
            continue

        asset_name, new_url, checksum = selected
        newer = dict(item)
        newer["version"] = new_tag
        newer["url"] = new_url
        newer["source_direct"] = new_url
        newer["checksum"] = checksum
        newer["last_update"] = str(release.get("published_at") or "")[:10] or str(
            item.get("last_update", ""))
        # No cambiar el nombre local si es un alias; si incluye la version
        # antigua, renombrarlo para evitar nombres de versiones obsoletas.
        filename = str(item.get("filename", ""))
        for old, new in ((old_tag, new_tag), (old_short, new_short)):
            if old and old in filename:
                filename = filename.replace(old, new, 1)
                break
        newer["filename"] = filename
        result.append(newer)
        changes.append(str(item.get("name")) + " -> " + new_tag)
    return result, changes


def update_catalog(path=CATALOG):
    if not path.is_file():
        raise FileNotFoundError("No existe payloads.json junto a actualizador.py")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("payloads"), list):
        raise ValueError("Formato de payloads.json invalido: no se modifica")
    items = data["payloads"]
    if not all(isinstance(x, dict) for x in items):
        raise ValueError("Catalogo con entradas invalidas: no se modifica")

    changed = []
    for spec in TRACKED:
        release = select_release(spec)
        entry = make_entry(spec, release)
        items, did_change = update_entries(items, spec, entry)
        if did_change:
            changed.append(spec["name"] + " " + entry["version"])

    items, other_changes = refresh_other_official_releases(items)
    changed.extend(other_changes)

    # Eliminar solo AnyPad del origen caido, nunca herramientas no relacionadas.
    old_count = len(items)
    items = [
        x for x in items if not (
            str(x.get("name", "")).strip().casefold() == "anypad ps5"
            and "sinfiltros/AnyPad-PS5".casefold()
            in (str(x.get("source", "")) + " " + str(x.get("url", ""))).casefold()
        )
    ]
    if len(items) != old_count:
        changed.append("retirado AnyPad (origen 404)")

    if not changed:
        print("HiddenKernel: sin cambios, catalogo intacto (" + str(len(items)) + " entradas).")
        return False

    data["payloads"] = items
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # Comprobar JSON escrito antes de reemplazar.
        check = json.loads(tmp.read_text(encoding="utf-8"))
        if len(check["payloads"]) != len(items):
            raise ValueError("El catalogo temporal no supera la validacion")
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()
    print("HiddenKernel:", len(items), "entradas;", "; ".join(changed))
    return True




# Iconos SVG: mecanismo del main actual, conservado sin alterar su formato.
PALETTE = ('#245b93','#177b79','#744c9e','#99522b','#366a42','#8b4461')

def slug(s):
    s = re.sub(r'[^a-z0-9._-]+','-',s.lower()).strip('-')
    return s[:110] or 'payload'

def symbol(item):
    t = (item.get('name','')+' '+item.get('category','')+' '+item.get('description','')).lower()
    for terms, sign in [
        (('ftp','upload','transfer','network','red'), 'FTP'),
        (('save','backup','guardad'), 'SAVE'),
        (('mount','disco','usb'), 'DISK'),
        (('emul','ps2','ps3','retro'), 'EMU'),
        (('cheat','trainer','trucos'), 'CODE'),
        (('video','media','nuvio'), 'PLAY'),
        (('payload','autoload','loader'), 'ELF'),
        (('debug','log','kernel'), 'SYS'),
    ]:
        if any(w in t for w in terms): return sign
    return 'PS5'

def svg_icon(item, n):
    label=symbol(item)
    color=PALETTE[n%len(PALETTE)]
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">'
         f'<rect width="128" height="128" rx="25" fill="{color}"/>'
         f'<rect x="10" y="10" width="108" height="108" rx="19" fill="none" stroke="#ffffff" stroke-opacity=".28" stroke-width="2"/>'
         f'<circle cx="64" cy="43" r="17" fill="#ffffff" fill-opacity=".16"/>'
         f'<path d="M55 43h18M64 34v18" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>'
         f'<text x="64" y="94" text-anchor="middle" fill="white" font-family="Arial,sans-serif" font-size="22" font-weight="bold">{label}</text></svg>')
    return 'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()

def update_icons(path):
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or not isinstance(data.get('payloads'),list):
        raise ValueError('Expected catalog object with payloads list')
    icons={};used=set()
    for n,item in enumerate(data['payloads']):
        if not isinstance(item,dict):raise ValueError('Invalid payload entry')
        key=item.get('icon_key') or item.get('id') or slug(item.get('name',''))
        key=slug(key)
        if key in used:
            key=slug(key+'-'+slug(item.get('filename','')))
        if key in used:
            key=slug(key+'-'+str(n))
        used.add(key)
        item['icon_key']=key
        item.setdefault('id',key)
        icons[key]=svg_icon(item,n)
    data.setdefault('name','HiddenKernel')
    data['icons_url']='icons.json'
    icon_path=path.with_name('icons.json')
    if len(icons)>4096:raise ValueError('Too many icons')
    content=json.dumps({'icons':icons},ensure_ascii=False,indent=2)+'\n'
    if len(content.encode())>=4*1024*1024:raise ValueError('Icon catalog too large')
    catalog=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    # Create local files; the user can review and upload both to GitHub together.
    tmp_icon=icon_path.with_suffix('.json.tmp')
    tmp_catalog=path.with_suffix('.json.tmp')
    tmp_icon.write_text(content,encoding='utf-8')
    tmp_catalog.write_text(catalog,encoding='utf-8')
    tmp_icon.replace(icon_path)
    tmp_catalog.replace(path)
    print(f'{len(icons)} icons generated; {path} and {icon_path}')


if __name__ == '__main__':
    update_catalog()
    update_icons(CATALOG)
