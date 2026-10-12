#!/usr/bin/env python3
"""HiddenKernel: actualizador ELF independiente, 2026-10-12.

Lee el catalogo existente y actualiza solo releases ELF comprobables.
No ejecuta generadores antiguos, no descarga ni ejecuta codigo remoto
y no realiza commits ni push. Python 3.12, sin dependencias externas.

Fuentes: releases oficiales con ELF y SHA-256 verificables.
Las tres migraciones principales son curadas; las demas se actualizan
solo si el ELF de la release se identifica sin ambiguedad.
"""
import json
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
        "name": "PS5SX2 Bot",
        "repo": "Swordpdf/PS5SX2",
        "tag": "vk-285-163",
        "asset": "ps5sx2-bot.elf",
        "sha256": "3420cdb5c826014b22b8ca8fa60a2026f0d9f91d3f5a5b818d4c98373eccb123",
        "date": "2026-10-11",
        "category": "EMULADORES",
        "description": (
            "Helper, instalador y lanzador de discos de PS5SX2. "
            "Sustituye el antiguo ps5sx2-aio.elf, PS5SXHelper y "
            "PS5SX2Installer. La aplicacion PS5SX2 se instala aparte."
        ),
    },
)

OLD_PS5SX2_NAMES = {
    "ps5sx2 aio", "ps5sx2 bot", "ps5sx2 installer",
    "ps5sx2 helper", "ps5sx2 disclaunch", "disclaunch",
}
OLD_PS5SX2_FILES = {
    "ps5sx2-aio.elf", "ps5sx2-bot.elf",
    "ps5sx2installer.elf", "ps5sxhelper.elf", "disclaunch.elf",
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


def fetch_release(repo):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "HiddenKernel-ELF-Updater/2026-10-12",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(API.format(repo=repo), headers=headers)
    with urllib.request.urlopen(req, timeout=18) as response:
        return json.load(response)


def release_asset(spec, release):
    """Solo aceptar un ELF con nombre, URL y SHA-256 verificables."""
    if release.get("draft") or release.get("prerelease"):
        return None
    tag = str(release.get("tag_name", ""))
    if not tag:
        return None
    if spec["key"] == "ps5upload":
        asset_name = "ps5upload-" + tag.removeprefix("v") + ".elf"
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


def select_release(spec):
    chosen = pinned_release(spec)
    try:
        live = release_asset(spec, fetch_release(spec["repo"]))
        if live and version_numbers(live["tag"]) >= version_numbers(chosen["tag"]):
            chosen = live
        elif live is None:
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
    if key == "ps5upload":
        return name == "ps5upload" or bool(re.fullmatch(
            r"ps5upload[-_]v?\d+(?:\.\d+)*\.elf", filename))
    if key == "nuvio":
        return name == "nuvio ps5" or filename == "nuvio-ps5.elf"
    return False


def make_entry(spec, release):
    tag, filename = release["tag"], release["asset"]
    url = (
        "https://github.com/" + spec["repo"]
        + "/releases/download/" + tag + "/" + filename
    )
    version = tag
    if spec["key"] == "ps5sx2":
        match = re.search(r"\b(\d+\.\d+)\b", release["release_name"])
        version = (match.group(1) + " (" + tag + ")") if match else ("2.03 (" + tag + ")" if tag == spec["tag"] else tag)
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
        highest = max(version_numbers(x.get("version", "")) for x in current)
        if highest > version_numbers(entry["version"]):
            print("OMITIDO: version mas nueva ya en catalogo:", spec["name"])
            return items, False
        if len(current) == 1 and current[0] == entry:
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


if __name__ == "__main__":
    update_catalog()
