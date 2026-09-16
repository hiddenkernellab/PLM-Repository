#!/usr/bin/env python3
"""Genera el catálogo HiddenKernel Homebrew para Pegasus DL.

Política HiddenKernel:
- solo homebrew/utilidades y enlaces públicos verificables;
- nada de juegos comerciales, DLC o updates comerciales;
- el catálogo Pegasus se mantiene separado de payloads.json;
- hashes y procedencia se guardan en un manifest aparte;
- mirrors externos se validan contra el SHA-256 publicado por GitHub;
- las portadas externas se referencian por URL y no se copian al repositorio;
- si una fuente falla temporalmente, se conserva la última entrada válida.

Cambio 2026-09-16:
- las portadas ya no usan hosts sueltos/Twitter para PS5-Xplorer o Avatar Changer;
- prioridad de portada: icono oficial explícito -> PKG-Zone -> override estable;
- se valida que la URL de portada responda como imagen antes de publicarla.
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

UA = "HiddenKernel-PKG-Catalog/1.5"
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

PKGZONE_BASE = "https://pkg-zone.com"
PKGZONE_MAX_PAGES = 20
PKGZONE_AUTO_SOURCE_TYPE = "pkg-zone-auto"

# Fallbacks estables por Title ID. Para Lapy usamos su ficha PS5 de PKG-Zone,
# que identifica la aplicación por Title ID y evita imágenes ajenas.
POSTER_OVERRIDES = {
    "LAPY20011": f"{PKGZONE_BASE}/images/LAPY20011/cover.png",
    "LAPY20016": f"{PKGZONE_BASE}/images/LAPY20016/cover.png",
    "ITEM00001": (
        "https://raw.githubusercontent.com/LightningMods/Itemzflow/"
        "9126e4788eb8a9d9657b8096ec7e25eb3bc9ab8d/"
        "App-Media-Assets/sce_sys/icon0.png"
    ),
}

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
    return request_bytes(url).decode("utf-8", errors="replace")


def is_valid_image_url(url):
    """Comprueba HTTPS + respuesta de tipo image/* sin descargar la imagen completa."""
    if not str(url or "").startswith("https://"):
        return False
    try:
        req = urllib.request.Request(
            url,
            headers={**_headers(False), "Range": "bytes=0-1023"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            ctype = (r.headers.get("Content-Type") or "").lower()
            return ctype.startswith("image/")
    except Exception:
        return False


def pkgzone_cover_url(title_id):
    return f"{PKGZONE_BASE}/images/{urllib.parse.quote(title_id, safe='')}/cover.png"


def resolve_poster(title_id, *official_candidates):
    """Prioridad: oficial explícita -> PKG-Zone -> override estable.

    Si la comprobación temporal de red falla para todas, conserva el override
    conocido para evitar que un corte puntual borre la portada del catálogo.
    """
    candidates = []
    for url in official_candidates:
        if url:
            candidates.append(url)

    pz = pkgzone_cover_url(title_id)
    if pz not in candidates:
        candidates.append(pz)

    override = POSTER_OVERRIDES.get(title_id)
    if override and override not in candidates:
        candidates.append(override)

    for url in candidates:
        if is_valid_image_url(url):
            return url

    return override or (candidates[0] if candidates else None)


def _clean_html(fragment):
    s = re.sub(r"<[^>]+>", " ", str(fragment or ""), flags=re.S)
    s = unescape(s)
    return re.sub(r"\s+", " ", s).strip()


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
            "version": normalize_version(version),
            "author": author,
        })

    return cards


def discover_pkgzone_ps5():
    found = {}
    for page in range(1, PKGZONE_MAX_PAGES + 1):
        query = urllib.parse.urlencode({"console": "ps5", "page": page})
        html = request_text(f"{PKGZONE_BASE}/?{query}")
        cards = parse_pkgzone_cards(html)
        if not cards:
            break

        added = 0
        for card in cards:
            tid = card["titleId"]
            if tid not in found:
                found[tid] = card
                added += 1
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


def github_latest(repo):
    return request_json(f"https://api.github.com/repos/{repo}/releases/latest")


def github_release(repo, tag):
    return request_json(f"https://api.github.com/repos/{repo}/releases/tags/{tag}")


def find_asset(release, predicate):
    for asset in release.get("assets", []):
        if predicate(str(asset.get("name", ""))):
            return asset
    raise RuntimeError("No se encontró el asset esperado")


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
        raise RuntimeError("Formato inesperado del índice PKG de Nexgen")

    for item in packages:
        if not isinstance(item, dict):
            continue
        fields = {
            str(item.get("name") or "").casefold(),
            str(item.get("title") or "").casefold(),
        }
        if fields & wanted:
            return item
    raise RuntimeError(f"No se encontró {names[0]} en el índice PKG de Nexgen")


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
        raise RuntimeError("La URL del índice no coincide con el asset de GitHub")

    digest = sha_from_asset(asset)
    if not digest:
        digest = hashlib.sha256(request_bytes(url)).hexdigest()

    version = normalize_version(entry.get("version"))
    prev = previous_manifest.get(title_id, {})
    if (
        prev.get("version") == version
        and valid_sha(prev.get("sha256"))
        and prev.get("sha256", "").lower() != digest.lower()
    ):
        raise RuntimeError(
            f"{title_id}: mismo número de versión pero cambió el SHA-256; revisión manual"
        )

    return version, url, int(asset.get("size") or 0), digest


def build_nexgen_pkg(
    previous_manifest, *, title_id, names, title, description, source,
    official_posters=()
):
    entry = find_nexgen_entry(*names)
    version, url, size, digest = verified_nexgen_asset(
        entry, previous_manifest, title_id
    )
    poster = resolve_poster(title_id, *official_posters)

    return (
        package(title_id, title, version, description, source, url, size, poster),
        {
            "titleId": title_id,
            "version": version,
            "url": url,
            "sha256": digest,
            "sizeBytes": size,
            "posterUrl": poster,
            "imageSource": poster,
            "imagePolicy": (
                "Referencia externa validada. HiddenKernel no almacena ni redistribuye la imagen."
            ),
            "provenance": (
                "PKG público espejado por Nexgen y verificado contra el SHA-256 "
                "del asset de GitHub."
            ),
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
    )


def build_avatar_changer(previous_manifest):
    return build_nexgen_pkg(
        previous_manifest,
        title_id="LAPY20016",
        names=("Avatar-Changer", "Avatar Changer", "Avatar Changer PS5"),
        title="Avatar Changer PS5",
        description=(
            "Utilidad de Lapy para cambiar el avatar del perfil desde la consola. "
            "Trabaja con avatares preparados para la aplicación y requiere un entorno jailbreak compatible."
        ),
        source="https://pkg-zone.com/details/LAPY20016",
    )


def build_itemzflow(previous_manifest):
    official = POSTER_OVERRIDES["ITEM00001"]
    return build_nexgen_pkg(
        previous_manifest,
        title_id="ITEM00001",
        names=("Itemzflow_Game_Manager", "Itemzflow Game Manager", "Itemzflow"),
        title="Itemzflow Game Manager",
        description=(
            "Gestor de biblioteca para PS5 orientado a homebrew y copias autorizadas. "
            "Permite gestionar títulos, montajes y metadatos desde una interfaz nativa."
        ),
        source="https://pkg-zone.com/details/ITEM00001",
        official_posters=(official,),
    )


def build_websrv_launcher(previous_manifest):
    rel = github_latest("ps5-payload-dev/websrv")
    tag = rel["tag_name"]
    url = (
        "https://raw.githubusercontent.com/ps5-payload-dev/websrv/"
        f"{tag}/homebrew/IV9999-FAKE00000_00-HOMEBREWLOADER01.pkg"
    )
    official_poster = (
        f"https://raw.githubusercontent.com/ps5-payload-dev/websrv/{tag}/icon0.png"
    )
    poster = resolve_poster("FAKE00000", official_poster)

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
            (
                "Acceso directo oficial al Homebrew Launcher. Requiere websrv activo; "
                "websrv busca aplicaciones en /data/homebrew y también en almacenamiento USB/extendido."
            ),
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
            "imageSource": poster,
            "provenance": "PKG oficial incluido en ps5-payload-websrv.",
        },
    )


def build_ezremote():
    rel = github_latest("cy33hc/ps5-ezremote-client")
    asset = find_asset(rel, lambda n: n.lower().endswith(".pkg"))
    digest = sha_from_asset(asset)
    if not digest:
        digest = hashlib.sha256(request_bytes(asset["browser_download_url"])).hexdigest()

    m = re.search(r"_([0-9]+(?:\.[0-9]+)+)\.pkg$", asset["name"], flags=re.I)
    pkg_version = m.group(1) if m else rel["tag_name"]
    bundle_version = rel["tag_name"]
    official_poster = (
        "https://raw.githubusercontent.com/cy33hc/ps5-ezremote-client/"
        f"{bundle_version}/data/sce_sys/icon0.png"
    )
    poster = resolve_poster("RMTC00001", official_poster)

    return (
        package(
            "RMTC00001",
            "ezRemote Client (launcher)",
            pkg_version,
            (
                f"Acceso directo de ezRemote Client. La release actual del bundle es "
                f"{bundle_version}; para funcionar hay que extraer ezremote-client.zip "
                "en /data/homebrew y cargar websrv."
            ),
            "https://github.com/cy33hc/ps5-ezremote-client",
            asset["browser_download_url"],
            asset.get("size"),
            poster,
        ),
        {
            "titleId": "RMTC00001",
            "version": pkg_version,
            "bundleVersion": bundle_version,
            "url": asset["browser_download_url"],
            "sha256": digest,
            "sizeBytes": asset.get("size"),
            "posterUrl": poster,
            "imageSource": poster,
            "provenance": "PKG oficial de la release de ps5-ezremote-client.",
        },
    )


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
        download_url = (
            f"{PKGZONE_BASE}/download/ps5/"
            f"{urllib.parse.quote(title_id, safe='')}/latest"
        )
        source = detail["detailsUrl"]
        poster = resolve_poster(title_id)

        author_text = f" de {author}" if author else ""
        description = (
            f"{title}{author_text}. Entrada PS5 detectada automáticamente en PKG-Zone. "
            f"Categoría: {category}. Fuente externa; HiddenKernel enlaza el PKG original "
            "y no lo redistribuye ni está afiliado con su desarrollador."
        )

        packages.append(
            package(
                title_id, title, version, description, source,
                download_url, None, poster
            )
        )
        manifest.append({
            "titleId": title_id,
            "version": version,
            "url": download_url,
            "posterUrl": poster,
            "imageSource": poster,
            "imagePolicy": (
                "Referencia externa validada. HiddenKernel no descarga, almacena ni redistribuye esta imagen."
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
        })
        print(f"OK PKG-Zone {title}: {version} [{category}]")

    return packages, manifest


def validate(packages, manifest):
    seen = set()
    for p in packages:
        tid = str(p.get("titleId") or "").strip()
        if not tid or tid in seen:
            raise RuntimeError(f"titleId inválido/duplicado: {tid!r}")
        seen.add(tid)

        if not str(p.get("title") or "").strip():
            raise RuntimeError(f"Título vacío: {tid}")

        links = p.get("downloadLinks") or []
        if not links:
            raise RuntimeError(f"Sin enlace: {p.get('title')}")

        for link in links:
            url = str(link.get("url") or "")
            if not url.startswith("https://"):
                raise RuntimeError(f"Solo HTTPS en el catálogo: {url}")

        poster = str(p.get("posterUrl") or "")
        if poster and not poster.startswith("https://"):
            raise RuntimeError(f"posterUrl no HTTPS: {poster}")

    by_id = {m.get("titleId"): m for m in manifest}
    for tid in seen:
        meta = by_id.get(tid)
        if not meta:
            raise RuntimeError(f"Manifest ausente: {tid}")

        if meta.get("sourceType") == PKGZONE_AUTO_SOURCE_TYPE:
            url = str(meta.get("url") or "")
            expected = f"{PKGZONE_BASE}/download/ps5/{tid}/"
            if not url.startswith(expected):
                raise RuntimeError(f"URL PKG-Zone inesperada para {tid}: {url}")
            continue

        if not valid_sha(meta.get("sha256")):
            raise RuntimeError(f"Manifest sin SHA-256 válido: {tid}")


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
                # Si el único problema fue red/portada, corrige de todos modos los
                # dos overrides conocidos para no volver a publicar el host antiguo.
                if title_id in POSTER_OVERRIDES:
                    poster = POSTER_OVERRIDES[title_id]
                    old_pkg = dict(old_pkg)
                    old_meta = dict(old_meta)
                    old_pkg["posterUrl"] = poster
                    old_meta["posterUrl"] = poster
                    old_meta["imageSource"] = poster
                packages.append(old_pkg)
                manifest.append(old_meta)
                print(f"AVISO PKG {title_id}: {exc}. Se conserva la entrada anterior.")
            else:
                raise RuntimeError(
                    f"{title_id}: {exc}; no hay una entrada anterior válida"
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
        json.dumps(
            {"name": "HiddenKernel Homebrew", "packages": packages},
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    MANIFEST.write_text(
        json.dumps(
            {
                "name": "HiddenKernel Homebrew integrity manifest",
                "policy": (
                    "Solo homebrew/utilidades legales. Importación automática de PKG-Zone "
                    "limitada a Utility/Emulator/Homebrew; no juegos comerciales, DLC, "
                    "updates, Retail PKG ni Media comercial."
                ),
                "packages": manifest,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"Generado {OUT} con {len(packages)} paquetes.")


if __name__ == "__main__":
    main()
