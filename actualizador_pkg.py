#!/usr/bin/env python3
"""Genera el catalogo HiddenKernel Homebrew para Pegasus DL.

Politica HiddenKernel:
- solo homebrew/utilidades y enlaces publicos verificables;
- nada de juegos comerciales, DLC o updates comerciales;
- el catalogo Pegasus se mantiene separado de payloads.json;
- hashes y procedencia se guardan en un manifest aparte;
- mirrors externos se validan contra el SHA-256 publicado por GitHub;
- si una fuente falla temporalmente, se conserva la ultima entrada valida.
"""

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

UA = "HiddenKernel-PKG-Catalog/1.2"
TOKEN = os.getenv("GITHUB_TOKEN", "")
OUT = Path("pegasus-homebrew.json")
MANIFEST = Path("pegasus-homebrew-manifest.json")
NEXGEN_INDEX = (
    "https://raw.githubusercontent.com/nexgen999/"
    "PS5-Super-PLDMGR-Auto-Updater/main/PKGjson/pkg.json"
)
NEXGEN_MIRROR_REPO = "nexgen999/Evox_PS5PKG_Private"
NEXGEN_ALLOWED_PREFIX = (
    "https://github.com/nexgen999/Evox_PS5PKG_Private/releases/download/"
)
LAPY_POSTER = "https://pkg-zone.com/storage/users/Lapy/avatar.jpg"
ITEMZFLOW_POSTER = (
    "https://raw.githubusercontent.com/LightningMods/Itemzflow/"
    "9126e4788eb8a9d9657b8096ec7e25eb3bc9ab8d/"
    "App-Media-Assets/sce_sys/icon0.png"
)

_nexgen_cache = None


def _headers(accept_json=False):
    h = {"User-Agent": UA}
    if accept_json:
        h["Accept"] = "application/vnd.github+json"
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


def request_json(url):
    req = urllib.request.Request(url, headers=_headers(True))
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def request_bytes(url):
    req = urllib.request.Request(url, headers=_headers(False))
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def github_latest(repo):
    return request_json(f"https://api.github.com/repos/{repo}/releases/latest")


def github_release(repo, tag):
    return request_json(f"https://api.github.com/repos/{repo}/releases/tags/{tag}")


def find_asset(release, predicate):
    for a in release.get("assets", []):
        if predicate(str(a.get("name", ""))):
            return a
    raise RuntimeError("No se encontro el asset esperado")


def sha_from_asset(asset):
    value = str(asset.get("digest") or "")
    if re.fullmatch(r"sha256:[0-9a-fA-F]{64}", value):
        return value.split(":", 1)[1].lower()
    return ""


def valid_sha(value):
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", str(value or "")))


def normalize_version(value):
    s = str(value or "").strip()
    s = re.sub(r"^[vV]", "", s)
    s = s.rstrip(". ")
    return s or "unknown"


def package(title_id, title, version, description, source, url, size=None, poster_url=None):
    item = {
        "titleId": title_id,
        "title": title,
        "version": str(version),
        "description": description,
        "downloadSource": source,
        "downloadLinks": [{"name": "Descarga", "url": url}],
    }
    if poster_url:
        item["posterUrl"] = poster_url
    if size:
        item["sizeBytes"] = int(size)
    return item


def load_previous_catalog():
    if not OUT.is_file():
        return {}
    try:
        obj = json.loads(OUT.read_text(encoding="utf-8"))
        return {
            p.get("titleId"): p for p in obj.get("packages", [])
            if isinstance(p, dict) and p.get("titleId")
        }
    except Exception:
        return {}


def load_previous_manifest():
    if not MANIFEST.is_file():
        return {}
    try:
        obj = json.loads(MANIFEST.read_text(encoding="utf-8"))
        return {
            p.get("titleId"): p for p in obj.get("packages", [])
            if isinstance(p, dict) and p.get("titleId")
        }
    except Exception:
        return {}


def nexgen_index():
    global _nexgen_cache
    if _nexgen_cache is None:
        _nexgen_cache = request_json(NEXGEN_INDEX)
    return _nexgen_cache


def find_nexgen_entry(*names):
    wanted = {n.casefold() for n in names}
    obj = nexgen_index()
    packages = obj.get("packages", obj) if isinstance(obj, dict) else obj
    if not isinstance(packages, list):
        raise RuntimeError("Formato inesperado del indice PKG de Nexgen")
    for item in packages:
        if not isinstance(item, dict):
            continue
        fields = {
            str(item.get("name") or "").casefold(),
            str(item.get("title") or "").casefold(),
        }
        if fields & wanted:
            return item
    raise RuntimeError(f"No se encontro {names[0]} en el indice PKG de Nexgen")


def verified_nexgen_asset(entry, previous_manifest, title_id):
    url = str(entry.get("url") or entry.get("download") or entry.get("download_url") or "")
    if not url.startswith(NEXGEN_ALLOWED_PREFIX):
        raise RuntimeError("URL del mirror fuera del repositorio permitido")

    tail = url[len(NEXGEN_ALLOWED_PREFIX):]
    if "/" not in tail:
        raise RuntimeError("URL de release del mirror no reconocida")
    tag, encoded_name = tail.split("/", 1)
    asset_name = urllib.parse.unquote(encoded_name)
    rel = github_release(NEXGEN_MIRROR_REPO, tag)
    asset = find_asset(rel, lambda n: n == asset_name)
    if asset.get("browser_download_url") != url:
        raise RuntimeError("La URL del indice no coincide con el asset de GitHub")

    digest = sha_from_asset(asset)
    if not digest:
        digest = hashlib.sha256(request_bytes(url)).hexdigest()

    version = normalize_version(entry.get("version"))
    prev = previous_manifest.get(title_id, {})
    if (prev.get("version") == version and valid_sha(prev.get("sha256"))
            and prev.get("sha256", "").lower() != digest.lower()):
        raise RuntimeError(
            f"{title_id}: mismo numero de version pero cambio el SHA-256; revision manual"
        )
    return version, url, int(asset.get("size") or 0), digest


def build_nexgen_pkg(previous_manifest, *, title_id, names, title, description, source, poster):
    entry = find_nexgen_entry(*names)
    version, url, size, digest = verified_nexgen_asset(entry, previous_manifest, title_id)
    return (
        package(title_id, title, version, description, source, url, size, poster),
        {
            "titleId": title_id,
            "version": version,
            "url": url,
            "sha256": digest,
            "sizeBytes": size,
            "posterUrl": poster,
            "provenance": "PKG publico espejado por Nexgen y verificado contra el SHA-256 del asset de GitHub.",
        },
    )


def build_ps5_xplorer(previous_manifest):
    return build_nexgen_pkg(
        previous_manifest,
        title_id="LAPY20011",
        names=("PS5-Xplorer",),
        title="PS5-Xplorer",
        description=(
            "Explorador de archivos para PS5 de Lapy. Puede usarse con kstuff + "
            "Lapy JB Daemon sin cargar etaHEN completo."
        ),
        source="https://pkg-zone.com/details/LAPY20011",
        poster=LAPY_POSTER,
    )


def build_avatar_changer(previous_manifest):
    return build_nexgen_pkg(
        previous_manifest,
        title_id="LAPY20016",
        names=("Avatar-Changer", "Avatar Changer", "Avatar Changer PS5"),
        title="Avatar Changer PS5",
        description=(
            "Utilidad de Lapy para cambiar el avatar del perfil desde la consola. "
            "Trabaja con avatares preparados para la aplicacion y requiere un entorno jailbreak compatible."
        ),
        source="https://pkg-zone.com/details/LAPY20016",
        poster=LAPY_POSTER,
    )


def build_itemzflow(previous_manifest):
    return build_nexgen_pkg(
        previous_manifest,
        title_id="ITEM00001",
        names=("Itemzflow_Game_Manager", "Itemzflow Game Manager", "Itemzflow"),
        title="Itemzflow Game Manager",
        description=(
            "Gestor de biblioteca para PS5 orientado a homebrew y copias autorizadas. "
            "Permite gestionar titulos, montajes y metadatos desde una interfaz nativa."
        ),
        source="https://pkg-zone.com/details/ITEM00001",
        poster=ITEMZFLOW_POSTER,
    )


def build_websrv_launcher(previous_manifest):
    rel = github_latest("ps5-payload-dev/websrv")
    tag = rel["tag_name"]
    url = (
        "https://raw.githubusercontent.com/ps5-payload-dev/websrv/"
        f"{tag}/homebrew/IV9999-FAKE00000_00-HOMEBREWLOADER01.pkg"
    )
    poster = f"https://raw.githubusercontent.com/ps5-payload-dev/websrv/{tag}/icon0.png"

    prev = previous_manifest.get("FAKE00000", {})
    if prev.get("version") == tag and prev.get("url") == url and valid_sha(prev.get("sha256")):
        digest = prev["sha256"].lower()
        size = prev.get("sizeBytes")
    else:
        data = request_bytes(url)
        digest = hashlib.sha256(data).hexdigest()
        size = len(data)

    return (
        package(
            "FAKE00000",
            "Homebrew Launcher (websrv)",
            tag,
            "Acceso directo oficial al Homebrew Launcher. Requiere websrv activo; websrv busca aplicaciones en /data/homebrew y tambien en almacenamiento USB/extendido.",
            "https://github.com/ps5-payload-dev/websrv",
            url,
            size,
            poster,
        ),
        {
            "titleId": "FAKE00000",
            "version": tag,
            "url": url,
            "sha256": digest,
            "sizeBytes": size,
            "posterUrl": poster,
            "provenance": "PKG oficial incluido en ps5-payload-websrv.",
        },
    )


def build_ezremote():
    rel = github_latest("cy33hc/ps5-ezremote-client")
    a = find_asset(rel, lambda n: n.lower().endswith(".pkg"))
    digest = sha_from_asset(a)
    if not digest:
        digest = hashlib.sha256(request_bytes(a["browser_download_url"])).hexdigest()

    m = re.search(r"_([0-9]+(?:\.[0-9]+)+)\.pkg$", a["name"], flags=re.I)
    pkg_version = m.group(1) if m else rel["tag_name"]
    bundle_version = rel["tag_name"]
    poster = (
        "https://raw.githubusercontent.com/cy33hc/ps5-ezremote-client/"
        f"{bundle_version}/data/sce_sys/icon0.png"
    )

    return (
        package(
            "RMTC00001",
            "ezRemote Client (launcher)",
            pkg_version,
            f"Acceso directo de ezRemote Client. La release actual del bundle es {bundle_version}; para funcionar hay que extraer ezremote-client.zip en /data/homebrew y cargar websrv.",
            "https://github.com/cy33hc/ps5-ezremote-client",
            a["browser_download_url"],
            a.get("size"),
            poster,
        ),
        {
            "titleId": "RMTC00001",
            "version": pkg_version,
            "bundleVersion": bundle_version,
            "url": a["browser_download_url"],
            "sha256": digest,
            "sizeBytes": a.get("size"),
            "posterUrl": poster,
            "provenance": "PKG oficial de la release de ps5-ezremote-client.",
        },
    )


def validate(packages, manifest):
    seen = set()
    for p in packages:
        tid = str(p.get("titleId") or "").strip()
        if not tid or tid in seen:
            raise RuntimeError(f"titleId invalido/duplicado: {tid!r}")
        seen.add(tid)
        if not str(p.get("title") or "").strip():
            raise RuntimeError(f"Titulo vacio: {tid}")
        links = p.get("downloadLinks") or []
        if not links:
            raise RuntimeError(f"Sin enlace: {p.get('title')}")
        for link in links:
            url = str(link.get("url") or "")
            if not url.startswith("https://"):
                raise RuntimeError(f"Solo HTTPS en el catalogo: {url}")
        poster = str(p.get("posterUrl") or "")
        if poster and not poster.startswith("https://"):
            raise RuntimeError(f"posterUrl no HTTPS: {poster}")

    by_id = {m.get("titleId"): m for m in manifest}
    for tid in seen:
        m = by_id.get(tid)
        if not m or not valid_sha(m.get("sha256")):
            raise RuntimeError(f"Manifest sin SHA-256 valido: {tid}")


def main():
    previous_catalog = load_previous_catalog()
    previous_manifest = load_previous_manifest()
    packages = []
    manifest = []

    builders = [
        ("LAPY20016", lambda: build_avatar_changer(previous_manifest)),
        ("RMTC00001", lambda: build_ezremote()),
        ("FAKE00000", lambda: build_websrv_launcher(previous_manifest)),
        ("ITEM00001", lambda: build_itemzflow(previous_manifest)),
        ("LAPY20011", lambda: build_ps5_xplorer(previous_manifest)),
    ]

    for title_id, builder in builders:
        try:
            pkg, meta = builder()
            packages.append(pkg)
            manifest.append(meta)
            print(f"OK PKG {pkg['title']}: {pkg['version']}")
        except Exception as exc:
            old_pkg = previous_catalog.get(title_id)
            old_meta = previous_manifest.get(title_id)
            if old_pkg and old_meta and valid_sha(old_meta.get("sha256")):
                packages.append(old_pkg)
                manifest.append(old_meta)
                print(f"AVISO PKG {title_id}: {exc}. Se conserva la entrada anterior.")
            else:
                raise RuntimeError(
                    f"{title_id}: {exc}; no hay una entrada anterior valida"
                ) from exc

    validate(packages, manifest)
    packages.sort(key=lambda p: p["title"].casefold())
    manifest.sort(key=lambda p: p["titleId"].casefold())

    OUT.write_text(
        json.dumps({"name": "HiddenKernel Homebrew", "packages": packages},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    MANIFEST.write_text(
        json.dumps({
            "name": "HiddenKernel Homebrew integrity manifest",
            "policy": "Solo homebrew/utilidades legales. No juegos comerciales, DLC ni updates comerciales.",
            "packages": manifest,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generado {OUT} con {len(packages)} paquetes.")


if __name__ == "__main__":
    main()
