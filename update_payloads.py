#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SOURCES_FILE = ROOT / "sources.json"
OUTPUT_FILE = ROOT / "payloads.json"

TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
USER_AGENT = "HiddenKernel-PLM-Repository/1.0"

CHANNEL_ORDER = ("stable", "beta", "alpha")
CATEGORY_ORDER = {
    "SYSTEM": 0,
    "HEN": 1,
    "GAMES": 2,
    "TOOLS": 3,
    "STORES": 4,
    "EXPERIMENTAL": 5,
}

ALPHA_RE = re.compile(
    r"(?i)(alpha|experimental|nightly|canary|(?:^|[\s._-])dev(?:$|[\s._-0-9]))"
)
BETA_RE = re.compile(
    r"(?i)(beta|release[\s._-]*candidate|\brc[\s._-]*\d*|preview)"
)

def github_json(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as response:
        return json.load(response)

def release_channel(release):
    text = f'{release.get("tag_name", "")} {release.get("name", "")}'.strip()

    # Primero respetamos cómo la llama el propio desarrollador.
    if ALPHA_RE.search(text):
        return "alpha"
    if BETA_RE.search(text):
        return "beta"

    # Si GitHub la marca como prerelease pero no dice "alpha",
    # la tratamos como beta para no hacerla pasar por estable.
    if release.get("prerelease", False):
        return "beta"

    return "stable"

def published_timestamp(release):
    value = release.get("published_at") or release.get("created_at") or ""
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0

def find_asset(release, pattern):
    rx = re.compile(pattern)
    assets = [
        asset
        for asset in release.get("assets", [])
        if rx.search(asset.get("name", ""))
    ]
    if not assets:
        return None

    assets.sort(
        key=lambda asset: (
            0 if asset.get("name", "").lower().endswith(".elf") else 1,
            len(asset.get("name", "")),
            asset.get("name", "").lower(),
        )
    )
    return assets[0]

def sha256_url(url):
    req = Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()

    with urlopen(req, timeout=180) as response:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()

def display_name(base_name, channel):
    if channel == "stable":
        return base_name
    if channel == "beta":
        return f"{base_name} (Beta)"
    return f"{base_name} (Alpha - INESTABLE)"

def description_for(source, channel):
    base = source.get("description", "").strip()

    if channel == "stable":
        prefix = "RECOMENDADA · Versión estable."
    elif channel == "beta":
        prefix = "BETA · Versión de pruebas."
    else:
        prefix = "INESTABLE · Versión alpha/experimental."

    return f"{prefix} {base}".strip()

def previous_payloads():
    if not OUTPUT_FILE.exists():
        return {}

    try:
        data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        items = data.get("payloads", []) if isinstance(data, dict) else []
        return {
            item["name"]: item
            for item in items
            if isinstance(item, dict) and item.get("name")
        }
    except (json.JSONDecodeError, OSError):
        return {}

def entry_name(source, channel):
    return display_name(source["name"], channel)

def make_entry(source, release, asset, channel):
    direct_url = asset["browser_download_url"]

    # Deliberadamente generamos solo campos admitidos por el formato
    # oficial de repositorios personalizados de Payload Manager.
    return {
        "name": display_name(source["name"], channel),
        "filename": asset["name"],
        "url": direct_url,
        "description": description_for(source, channel),
        "version": release.get("tag_name") or release.get("name") or "unknown",
        "category": source["category"],
        "checksum": sha256_url(direct_url),
    }

def build_source(source, old):
    api_url = f'https://api.github.com/repos/{source["repo"]}/releases?per_page=100'
    releases = github_json(api_url)

    releases = [
        release for release in releases
        if not release.get("draft", False)
    ]
    releases.sort(key=published_timestamp, reverse=True)

    result = []
    wanted_channels = source.get("channels", list(CHANNEL_ORDER))

    for channel in wanted_channels:
        selected = None

        # Escoge la release más reciente de ESTE canal que tenga
        # un ELF que coincida con asset_regex.
        for release in releases:
            if release_channel(release) != channel:
                continue

            asset = find_asset(release, source["asset_regex"])
            if asset:
                selected = (release, asset)
                break

        if not selected:
            continue

        release, asset = selected
        name = entry_name(source, channel)

        try:
            result.append(make_entry(source, release, asset, channel))
        except Exception as exc:
            # Si GitHub/descarga/checksum falla, no rompemos el catálogo:
            # conservamos la entrada anterior de ese canal si existe.
            if name in old:
                print(
                    f"AVISO: fallo generando {name}; conservo la anterior: {exc}",
                    file=sys.stderr,
                )
                result.append(old[name])
            else:
                print(
                    f"AVISO: fallo generando {name}: {exc}",
                    file=sys.stderr,
                )

    return result

def main():
    config = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    old = previous_payloads()
    generated = []

    for source_index, source in enumerate(config["payloads"]):
        try:
            print(f'Consultando {source["name"]} -> {source["repo"]}')
            entries = build_source(source, old)

            # Si no conseguimos ninguna release válida, mantenemos las
            # entradas anteriores de ese proyecto.
            if not entries:
                for channel in source.get("channels", list(CHANNEL_ORDER)):
                    name = entry_name(source, channel)
                    if name in old:
                        entries.append(old[name])

            for item in entries:
                channel = "stable"
                if "(Beta)" in item["name"]:
                    channel = "beta"
                elif "(Alpha - INESTABLE)" in item["name"]:
                    channel = "alpha"

                item["_source_order"] = source_index
                item["_channel_order"] = CHANNEL_ORDER.index(channel)
                generated.append(item)

        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            print(
                f'ERROR consultando {source["name"]}: {exc}',
                file=sys.stderr,
            )

            # También aquí conservamos lo anterior para no dejar el repo roto.
            for channel in source.get("channels", list(CHANNEL_ORDER)):
                name = entry_name(source, channel)
                if name in old:
                    item = dict(old[name])
                    item["_source_order"] = source_index
                    item["_channel_order"] = CHANNEL_ORDER.index(channel)
                    generated.append(item)

    generated.sort(
        key=lambda item: (
            CATEGORY_ORDER.get(item.get("category", ""), 99),
            item.get("_source_order", 9999),
            item.get("_channel_order", 9999),
        )
    )

    for item in generated:
        item.pop("_source_order", None)
        item.pop("_channel_order", None)

    output = {
        "name": config.get("name", "HiddenKernel Repository"),
        "payloads": generated,
    }

    temp = OUTPUT_FILE.with_suffix(".json.tmp")
    temp.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp.replace(OUTPUT_FILE)

    print(f"OK: {len(generated)} entradas escritas en {OUTPUT_FILE.name}")

if __name__ == "__main__":
    main()
