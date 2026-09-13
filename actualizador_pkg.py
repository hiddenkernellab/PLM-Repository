#!/usr/bin/env python3
"""Genera el catalogo HiddenKernel Homebrew para Pegasus DL.

Politica HiddenKernel:
- solo homebrew/utilidades y enlaces publicos verificables;
- nada de juegos comerciales, DLC o updates comerciales;
- el catalogo Pegasus se mantiene separado de payloads.json;
- hashes y procedencia se guardan en un manifest aparte;
- mirrors externos se validan contra el SHA-256 publicado por GitHub;
- las portadas externas se referencian por URL y no se copian al repositorio;
- si una fuente falla temporalmente, se conserva la ultima entrada valida.
"""

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

UA = "HiddenKernel-PKG-Catalog/1.4"
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
AVATAR_POSTER = "https://pbs.twimg.com/media/Gl2XTLuXIAADCEL.jpg"
XPLORER_POSTER = "https://ig.2468c.com/2024/06/08/a06a1c240d8f4.jpg"
ITEMZFLOW_POSTER = (
    "https://raw.githubusercontent.com/LightningMods/Itemzflow/"
    "9126e4788eb8a9d9657b8096ec7e25eb3bc9ab8d/"
    "App-Media-Assets/sce_sys/icon0.png"
)

PKGZONE_BASE = "https://pkg-zone.com"
PKGZONE_MAX_PAGES = 20
PKGZONE_AUTO_SOURCE_TYPE = "pkg-zone-auto"

# Importación automática conservadora:
# se admiten utilidades, emuladores y homebrew. No se autoimportan Media,
# Retail PKG, DLC, Update ni Game genérico, porque esas categorías pueden
# contener binarios comerciales o contenido cuya redistribución no esté clara.
PKGZONE_ALLOWED_CATEGORIES = {
    "utility",
    "emulator",
    "homebrew",
    "hb game",
    "homebrew game",
}

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


def request_text(url):
    data = request_bytes(url)
    return data.decode("utf-8", errors="replace")


def _clean_html(fragment):
    s = re.sub(r"<[^>]+>", " ", str(fragment or ""), flags=re.S)
    s = unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


class _TextCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []

    def handle_data(self, data):
        value = re.sub(r"\s+", " ", data or "").strip()
        if value:
            self.items.append(value)


def _next_text_value(items, label):
    wanted = str(label).strip().casefold()
    for i, value in enumerate(items):
        if str(value).strip().casefold() == wanted:
            for candidate in items[i + 1:]:
                candidate = str(candidate).strip()
                if candidate:
                    return candidate
    return ""


def parse_pkgzone_cards(page_html):
    """Extrae las tarjetas que PKG-Zone marca explícitamente como PS5."""
    blocks = re.findall(
        r'<article\b[^>]*class=["\'][^"\']*\bpkg\b[^"\']*["\'][^>]*>(.*?)</article>',
        page_html,
        flags=re.I | re.S,
    )
    cards = []

    for block in blocks:
        plain = _clean_html(block)
        if "supports ps5" not in plain.casefold():
            continue

        m_id = re.search(r'/details/([^"\'/?#<>\s]+)', block, flags=re.I)
        if not m_id:
            continue
        title_id = urllib.parse.unquote(m_id.group(1)).strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]{4,40}", title_id):
            continue

        m_title = re.search(
            r'class=["\'][^"\']*\btitle\b[^"\']*\bfont-bold\b[^"\']*["\'][^>]*>(.*?)</div>',
            block,
            flags=re.I | re.S,
        )
        title = _clean_html(m_title.group(1)) if m_title else title_id

        m_version = re.search(
            r'class=["\'][^"\']*\bnumber\b[^"\']*["\'][^>]*>(.*?)</div>',
            block,
            flags=re.I | re.S,
        )
        version_text = _clean_html(m_version.group(1)) if m_version else ""
        version = re.split(r"\|\s*Supports\s+PS5", version_text, flags=re.I)[0].strip()
        version = normalize_version(version)

        m_author = re.search(
            r'class=["\'][^"\']*dark:text-gray-300[^"\']*["\'][^>]*>(.*?)</div>',
            block,
            flags=re.I | re.S,
        )
        author = _clean_html(m_author.group(1)) if m_author else ""
        if author in {"-//-", "--"}:
            author = ""

        cards.append({
            "titleId": title_id,
            "title": title,
            "version": version,
            "author": author,
        })

    return cards


def discover_pkgzone_ps5():
    """Recorre las páginas filtradas para PS5 y devuelve cada Title ID una vez."""
    found = {}
    for page in range(1, PKGZONE_MAX_PAGES + 1):
        query = urllib.parse.urlencode({"console": "ps5", "page": page})
        url = f"{PKGZONE_BASE}/?{query}"
        html = request_text(url)
        cards = parse_pkgzone_cards(html)

        if not cards:
            break

        added = 0
        for card in cards:
            tid = card["titleId"]
            if tid not in found:
                found[tid] = card
                added += 1

        # Si una página repite exactamente las tarjetas anteriores, hemos
        # alcanzado el final aunque el sitio siga devolviendo HTML válido.
        if added == 0:
            break

    if not found:
        raise RuntimeError("PKG-Zone no devolvió ninguna tarjeta PS5")
    return list(found.values())


def pkgzone_detail_metadata(title_id):
    url = f"{PKGZONE_BASE}/details/{urllib.parse.quote(title_id, safe='')}"
    html = request_text(url)
    parser = _TextCollector()
    parser.feed(html)
    items = parser.items

    category = _next_text_value(items, "Category")
    author = _next_text_value(items, "Author")
    updated = _next_text_value(items, "Updated")

    # En algunas fichas Author puede estar vacío y la siguiente etiqueta es User.
    if author.casefold() in {"user", "image", "show apps from user share"}:
        author = ""

    return {
        "detailsUrl": url,
        "category": category.strip(),
        "author": author.strip(),
        "updated": updated.strip(),
    }


def pkgzone_category_allowed(category):
    value = re.sub(r"\s+", " ", str(category or "")).strip().casefold()
    if value in PKGZONE_ALLOWED_CATEGORIES:
        return True
    return "homebrew" in value or value.startswith("hb ")


def pkgzone_cover_url(title_id):
    """
    Referencia la portada directamente desde PKG-Zone.
    HiddenKernel NO descarga, copia ni vuelve a publicar esta imagen.
    """
    return f"{PKGZONE_BASE}/images/{urllib.parse.quote(title_id, safe='')}/cover.png"


def previous_pkgzone_auto(previous_catalog, previous_manifest, reserved_ids):
    packages = []
    manifest = []
    for title_id, meta in previous_manifest.items():
        if title_id in reserved_ids:
            continue
        if meta.get("sourceType") != PKGZONE_AUTO_SOURCE_TYPE:
            continue
        pkg = previous_catalog.get(title_id)
        if pkg:
            packages.append(pkg)
            manifest.append(meta)
    return packages, manifest


def build_pkgzone_auto(previous_catalog, previous_manifest, reserved_ids):
    packages = []
    manifest = []

    for card in discover_pkgzone_ps5():
        title_id = card["titleId"]
        if title_id in reserved_ids:
            continue

        old_pkg = previous_catalog.get(title_id, {})
        old_meta = previous_manifest.get(title_id, {})

        try:
            detail = pkgzone_detail_metadata(title_id)
        except Exception as exc:
            if old_pkg and old_meta.get("sourceType") == PKGZONE_AUTO_SOURCE_TYPE:
                packages.append(old_pkg)
                manifest.append(old_meta)
                print(f"AVISO PKG-Zone {title_id}: {exc}. Se conserva la entrada anterior.")
                continue
            print(f"AVISO PKG-Zone {title_id}: no se pudo leer la ficha ({exc}); se omite.")
            continue

        category = detail.get("category", "")
        if not pkgzone_category_allowed(category):
            print(f"OMITIDO PKG-Zone {title_id}: categoría {category or 'desconocida'}")
            continue

        title = card.get("title") or title_id
        version = normalize_version(card.get("version"))
        author = detail.get("author") or card.get("author") or ""
        download_url = f"{PKGZONE_BASE}/download/ps5/{urllib.parse.quote(title_id, safe='')}/latest"
        source = detail["detailsUrl"]
        poster = pkgzone_cover_url(title_id)

        author_text = f" de {author}" if author else ""
        description = (
            f"{title}{author_text}. Entrada PS5 detectada automáticamente en PKG-Zone. "
            f"Categoría: {category}. Fuente externa; HiddenKernel enlaza el PKG original "
            f"y no lo redistribuye ni está afiliado con su desarrollador."
        )

        pkg = package(
            title_id,
            title,
            version,
            description,
            source,
            download_url,
            None,
            poster,
        )

        meta = {
            "titleId": title_id,
            "version": version,
            "url": download_url,
            "posterUrl": poster,
            "imageSource": poster,
            "imagePolicy": (
                "Referencia externa. HiddenKernel no descarga, almacena ni redistribuye esta imagen."
            ),
            "category": category,
            "author": author,
            "updated": detail.get("updated", ""),
            "sourceType": PKGZONE_AUTO_SOURCE_TYPE,
            "verification": "PKG-Zone HTTPS source; no SHA-256 local",
            "provenance": (
                "Detectado automáticamente en el catálogo PS5 de PKG-Zone y "
                "filtrado a categorías homebrew/utilidad permitidas. "
                "El PKG y su portada permanecen alojados por la fuente externa."
            ),
        }
        packages.append(pkg)
        manifest.append(meta)
        print(f"OK PKG-Zone {title}: {version} [{category}]")

    return packages, manifest


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
        poster=XPLORER_POSTER,
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
        poster=AVATAR_POSTER,
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
        if not m:
            raise RuntimeError(f"Manifest ausente: {tid}")

        if m.get("sourceType") == PKGZONE_AUTO_SOURCE_TYPE:
            url = str(m.get("url") or "")
            expected = f"{PKGZONE_BASE}/download/ps5/{tid}/"
            if not url.startswith(expected):
                raise RuntimeError(f"URL PKG-Zone inesperada para {tid}: {url}")

            poster = str(m.get("posterUrl") or "")
            expected_poster = f"{PKGZONE_BASE}/images/{tid}/"
            if poster and not poster.startswith(expected_poster):
                raise RuntimeError(
                    f"Portada automática no externa para {tid}: {poster}"
                )
            continue


        if not valid_sha(m.get("sha256")):
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

    reserved_ids = {title_id for title_id, _ in builders}
    try:
        auto_packages, auto_manifest = build_pkgzone_auto(
            previous_catalog, previous_manifest, reserved_ids
        )
        packages.extend(auto_packages)
        manifest.extend(auto_manifest)
    except Exception as exc:
        old_packages, old_manifest = previous_pkgzone_auto(
            previous_catalog, previous_manifest, reserved_ids
        )
        if old_packages:
            packages.extend(old_packages)
            manifest.extend(old_manifest)
            print(
                f"AVISO PKG-Zone: {exc}. Se conservan "
                f"{len(old_packages)} entradas automáticas anteriores."
            )
        else:
            print(f"AVISO PKG-Zone: {exc}. No hay entradas automáticas previas.")

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
            "policy": ("Solo homebrew/utilidades legales. Importación automática de PKG-Zone "
                       "limitada a Utility/Emulator/Homebrew; no juegos comerciales, DLC, "
                       "updates, Retail PKG ni Media comercial."),
            "packages": manifest,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generado {OUT} con {len(packages)} paquetes.")


if __name__ == "__main__":
    main()
