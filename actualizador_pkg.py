#!/usr/bin/env python3
"""Genera un catalogo separado de homebrew PKG para Pegasus DL.

Politica HiddenKernel:
- solo homebrew/utilidades redistribuibles o enlaces oficiales/publicos;
- nada de juegos comerciales, DLC o updates comerciales;
- el catalogo Pegasus se mantiene separado de payloads.json;
- los hashes/procedencia se guardan en un manifest aparte para auditoria.
"""

import hashlib
import json
import os
import re
import urllib.request
from pathlib import Path

UA = "HiddenKernel-PKG-Catalog/1.1"
TOKEN = os.getenv("GITHUB_TOKEN", "")
OUT = Path("pegasus-homebrew.json")
MANIFEST = Path("pegasus-homebrew-manifest.json")


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


def package(title_id, title, version, description, source, url, size=None):
    item = {
        "titleId": title_id,
        "title": title,
        "version": str(version),
        "description": description,
        "downloadSource": source,
        "downloadLinks": [{"name": "Descarga", "url": url}],
    }
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


def build_ps5_xplorer():
    # PKG-Zone identifica el homebrew como LAPY20011 / v1.05. El mirror de
    # Nexgen aloja el mismo PKG y GitHub publica su SHA-256 en la metadata.
    pinned_sha = "ea13710e6ffaf290f11bdafa890f76e530e3015cdac6d2cf4a14085c824e6039"
    rel = github_release("nexgen999/Evox_PS5PKG_Private", "v1.0")
    a = find_asset(rel, lambda n: n == "PS5PKG_PS5-Xplorer_v1.05.pkg")
    digest = sha_from_asset(a)
    if digest and digest != pinned_sha:
        raise RuntimeError(
            "PS5-Xplorer: cambio de hash inesperado; se requiere revision manual"
        )
    url = a["browser_download_url"]
    return (
        package(
            "LAPY20011",
            "PS5-Xplorer",
            "1.05",
            "Explorador de archivos para PS5 de Lapy. Puede usarse con kstuff + Lapy JB Daemon sin cargar etaHEN completo.",
            "https://pkg-zone.com/details/LAPY20011",
            url,
            a.get("size"),
        ),
        {
            "titleId": "LAPY20011",
            "version": "1.05",
            "url": url,
            "sha256": pinned_sha,
            "provenance": "PKG de PS5-Xplorer 1.05; mirror publico verificado por SHA-256.",
        },
    )


def build_websrv_launcher(previous_manifest):
    rel = github_latest("ps5-payload-dev/websrv")
    tag = rel["tag_name"]
    url = (
        "https://raw.githubusercontent.com/ps5-payload-dev/websrv/"
        f"{tag}/homebrew/IV9999-FAKE00000_00-HOMEBREWLOADER01.pkg"
    )

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
        ),
        {
            "titleId": "FAKE00000",
            "version": tag,
            "url": url,
            "sha256": digest,
            "sizeBytes": size,
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

    return (
        package(
            "RMTC00001",
            "ezRemote Client (launcher)",
            pkg_version,
            f"Acceso directo de ezRemote Client. La release actual del bundle es {bundle_version}; para funcionar hay que extraer ezremote-client.zip en /data/homebrew y cargar websrv.",
            "https://github.com/cy33hc/ps5-ezremote-client",
            a["browser_download_url"],
            a.get("size"),
        ),
        {
            "titleId": "RMTC00001",
            "version": pkg_version,
            "bundleVersion": bundle_version,
            "url": a["browser_download_url"],
            "sha256": digest,
            "sizeBytes": a.get("size"),
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
        ("LAPY20011", lambda: build_ps5_xplorer()),
        ("FAKE00000", lambda: build_websrv_launcher(previous_manifest)),
        ("RMTC00001", lambda: build_ezremote()),
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
