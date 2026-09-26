#!/usr/bin/env python3
"""Bootstrap de una sola ejecución para integrar EvoX-CoreOS en Pegasus."""

from pathlib import Path
import subprocess

TARGET = Path("actualizador_pkg.py")

CONST_MARKER = 'PKGZONE_AUTO_SOURCE_TYPE = "pkg-zone-auto"\n'
CONST_INSERT = 'PKGZONE_AUTO_SOURCE_TYPE = "pkg-zone-auto"\n\nEVOX_CATALOG_URL = (\n    "https://raw.githubusercontent.com/nexgen999/"\n    "evoX-CoreOS/main/json/pegasus_catalog.json"\n)\nEVOX_IMPORT_SOURCE_TYPE = "evox-coreos-import"\n\n# Sincronización selectiva: solo utilidades/homebrew conocidas. Si el catálogo\n# de EvoX incorpora contenido comercial en el futuro, HiddenKernel no lo arrastra.\nEVOX_ALLOWED_TITLE_IDS = {\n    "NPXS39041",  # PS5 Homebrew Store\n    "MOUU12023",  # Internet Browser Game / Media\n    "MOUS21425",  # PS5-SHOP-APPKG\n    "PPSA99051",  # PS5Library\n    "PPNX00999",  # PS5 Webkit\n    "PPSA99002",  # ProsperoLight\n    "PPSA99001",  # ProsperoRadio\n    "PPSA99003",  # ProsperoTV\n}\n\nEVOX_TITLE_OVERRIDES = {\n    "NPXS39041": "PS5 Homebrew Store",\n    "MOUU12023": "Internet Browser (Game / Media)",\n    "MOUS21425": "PS5-SHOP-APPKG",\n    "PPSA99051": "PS5Library",\n    "PPNX00999": "PS5 Webkit",\n    "PPSA99002": "ProsperoLight",\n    "PPSA99001": "ProsperoRadio",\n    "PPSA99003": "ProsperoTV",\n}\n\nEVOX_DESCRIPTION_OVERRIDES = {\n    "NPXS39041": "Instalador de PS5 Homebrew Store. Fuente externa de la escena homebrew.",\n    "MOUU12023": (\n        "Accesos directos al navegador de PS5. Incluye las variantes Game Menu y "\n        "Media Menu del mismo Title ID para evitar duplicados en Pegasus."\n    ),\n    "MOUS21425": "Aplicación PS5-SHOP-APPKG; requiere el payload ps5shopappkg-dpi compatible.",\n    "PPSA99051": "Cliente PS5Library; requiere ps5library-agent.elf para funcionar.",\n    "PPNX00999": "Instalador de acceso WebKit para PS5 mantenido por la comunidad.",\n    "PPSA99002": "ProsperoLight, cliente Moonlight para PS5.",\n    "PPSA99001": "ProsperoRadio, reproductor de radio para PS5.",\n    "PPSA99003": "ProsperoTV, reproductor IPTV para PS5.",\n}\n'
FUNC_MARKER = "\ndef previous_pkgzone_auto(previous_catalog, previous_manifest, reserved_ids):\n"
FUNC_INSERT = '\ndef github_release_asset_from_url(url, previous_artifact=None):\n    # Valida un asset de GitHub Releases y devuelve tag, tamaño y SHA-256.\n    m = re.fullmatch(\n        r"https://github\\.com/([^/]+)/([^/]+)/releases/download/([^/]+)/(.+)",\n        str(url or ""),\n    )\n    if not m:\n        raise RuntimeError(f"URL no reconocida como GitHub Release: {url}")\n\n    repo = f"{m.group(1)}/{m.group(2)}"\n    tag = urllib.parse.unquote(m.group(3))\n    asset_name = urllib.parse.unquote(m.group(4))\n    rel = github_release(repo, tag)\n    asset = find_asset(rel, lambda n: n == asset_name)\n    canonical = str(asset.get("browser_download_url") or "")\n    if canonical != url:\n        raise RuntimeError(\n            f"El asset de GitHub no coincide con la URL publicada: {url}"\n        )\n\n    version = normalize_version(tag)\n    digest = sha_from_asset(asset)\n    if not digest:\n        previous_artifact = previous_artifact or {}\n        if (\n            previous_artifact.get("url") == url\n            and previous_artifact.get("version") == version\n            and valid_sha(previous_artifact.get("sha256"))\n        ):\n            digest = previous_artifact["sha256"].lower()\n        else:\n            digest = hashlib.sha256(request_bytes(url)).hexdigest()\n\n    return version, int(asset.get("size") or 0), digest\n\n\ndef previous_evox_import(previous_catalog, previous_manifest, reserved_ids):\n    packages = []\n    manifest = []\n    for title_id, meta in previous_manifest.items():\n        if title_id in reserved_ids:\n            continue\n        if meta.get("sourceType") != EVOX_IMPORT_SOURCE_TYPE:\n            continue\n        pkg = previous_catalog.get(title_id)\n        if pkg and valid_sha(meta.get("sha256")):\n            packages.append(pkg)\n            manifest.append(meta)\n    return packages, manifest\n\n\ndef build_evox_imports(previous_catalog, previous_manifest, reserved_ids):\n    # Normaliza el subconjunto homebrew de EvoX-CoreOS para Pegasus DL.\n    obj = request_json(EVOX_CATALOG_URL)\n    raw = obj.get("packages", obj) if isinstance(obj, dict) else obj\n    if not isinstance(raw, list):\n        raise RuntimeError("Formato inesperado del catálogo EvoX-CoreOS")\n\n    grouped = {}\n    for item in raw:\n        if not isinstance(item, dict):\n            continue\n        title_id = str(item.get("titleId") or "").strip()\n        if title_id not in EVOX_ALLOWED_TITLE_IDS or title_id in reserved_ids:\n            continue\n\n        url = str(item.get("url") or "").strip()\n        if not url.startswith("https://github.com/"):\n            print(f"OMITIDO EvoX {title_id}: URL no GitHub")\n            continue\n\n        grouped.setdefault(title_id, []).append(item)\n\n    packages = []\n    manifest = []\n\n    for title_id, entries in grouped.items():\n        old_pkg = previous_catalog.get(title_id, {})\n        old_meta = previous_manifest.get(title_id, {})\n        old_artifacts = {\n            str(a.get("url") or ""): a\n            for a in old_meta.get("artifacts", [])\n            if isinstance(a, dict)\n        }\n\n        try:\n            links = []\n            artifacts = []\n            versions = []\n\n            for entry in entries:\n                url = str(entry.get("url") or "")\n                version, size, digest = github_release_asset_from_url(\n                    url,\n                    old_artifacts.get(url),\n                )\n                versions.append(version)\n\n                label = str(\n                    entry.get("title")\n                    or entry.get("name")\n                    or entry.get("filename")\n                    or "Descarga"\n                )\n                if title_id == "MOUU12023":\n                    folded = label.casefold()\n                    if "game" in folded:\n                        label = "Game Menu"\n                    elif "media" in folded:\n                        label = "Media Menu"\n\n                links.append({"name": label, "url": url})\n                artifacts.append({\n                    "name": str(entry.get("filename") or label),\n                    "version": version,\n                    "url": url,\n                    "sha256": digest,\n                    "sizeBytes": size,\n                })\n\n            if not artifacts:\n                continue\n\n            title = EVOX_TITLE_OVERRIDES.get(\n                title_id,\n                str(\n                    entries[0].get("title")\n                    or entries[0].get("name")\n                    or title_id\n                ),\n            )\n            version = versions[0] if len(set(versions)) == 1 else " / ".join(versions)\n            poster_candidates = [\n                str(e.get("posterUrl") or "")\n                for e in entries\n                if str(e.get("posterUrl") or "").startswith("https://")\n            ]\n            poster = resolve_poster(title_id, *poster_candidates)\n            description = EVOX_DESCRIPTION_OVERRIDES.get(\n                title_id,\n                str(\n                    entries[0].get("description")\n                    or "Utilidad homebrew para PS5."\n                ),\n            )\n\n            pkg = {\n                "titleId": title_id,\n                "title": title,\n                "version": version,\n                "description": description,\n                "downloadSource": "https://github.com/nexgen999/evoX-CoreOS",\n                "downloadLinks": links,\n            }\n            if poster:\n                pkg["posterUrl"] = poster\n            if len(artifacts) == 1 and artifacts[0]["sizeBytes"]:\n                pkg["sizeBytes"] = artifacts[0]["sizeBytes"]\n\n            primary = artifacts[0]\n            meta = {\n                "titleId": title_id,\n                "version": version,\n                "url": primary["url"],\n                "sha256": primary["sha256"],\n                "sizeBytes": primary["sizeBytes"],\n                "posterUrl": poster,\n                "imageSource": poster,\n                "sourceType": EVOX_IMPORT_SOURCE_TYPE,\n                "sourceCatalog": EVOX_CATALOG_URL,\n                "artifacts": artifacts,\n                "provenance": (\n                    "Entrada homebrew importada de EvoX-CoreOS. Cada descarga "\n                    "se valida contra el asset publicado en GitHub Releases; "\n                    "HiddenKernel no aloja el binario."\n                ),\n            }\n            packages.append(pkg)\n            manifest.append(meta)\n            print(f"OK EvoX import {title}: {version}")\n\n        except Exception as exc:\n            if (\n                old_pkg\n                and old_meta.get("sourceType") == EVOX_IMPORT_SOURCE_TYPE\n                and valid_sha(old_meta.get("sha256"))\n            ):\n                packages.append(old_pkg)\n                manifest.append(old_meta)\n                print(\n                    f"AVISO EvoX {title_id}: {exc}. "\n                    "Se conserva la entrada anterior."\n                )\n            else:\n                print(f"AVISO EvoX {title_id}: {exc}. Se omite esta entrada.")\n\n    return packages, manifest\n\n\ndef previous_pkgzone_auto(previous_catalog, previous_manifest, reserved_ids):\n'
MAIN_OLD = '    reserved_ids = {title_id for title_id, _ in builders}\n\n    try:\n        auto_packages, auto_manifest = build_pkgzone_auto(\n'
MAIN_NEW = '    reserved_ids = {title_id for title_id, _ in builders}\n\n    try:\n        evox_packages, evox_manifest = build_evox_imports(\n            previous_catalog, previous_manifest, reserved_ids\n        )\n        packages.extend(evox_packages)\n        manifest.extend(evox_manifest)\n    except Exception as exc:\n        evox_packages, evox_manifest = previous_evox_import(\n            previous_catalog, previous_manifest, reserved_ids\n        )\n        if evox_packages:\n            packages.extend(evox_packages)\n            manifest.extend(evox_manifest)\n            print(\n                f"AVISO EvoX-CoreOS: {exc}. Se conservan "\n                f"{len(evox_packages)} entradas importadas anteriores."\n            )\n        else:\n            print(\n                f"AVISO EvoX-CoreOS: {exc}. "\n                "No hay entradas importadas previas."\n            )\n\n    reserved_ids.update(\n        p.get("titleId") for p in evox_packages if p.get("titleId")\n    )\n\n    try:\n        auto_packages, auto_manifest = build_pkgzone_auto(\n'
OLD_POLICY = '                    "Solo homebrew/utilidades legales. Importación automática de PKG-Zone "\n                    "limitada a Utility/Emulator/Homebrew; no juegos comerciales, DLC, "\n                    "updates, Retail PKG ni Media comercial."\n'
NEW_POLICY = '                    "Solo homebrew/utilidades legales. Importación automática de PKG-Zone "\n                    "limitada a Utility/Emulator/Homebrew y sincronización selectiva de "\n                    "utilidades conocidas de EvoX-CoreOS; no juegos comerciales, DLC, "\n                    "updates, Retail PKG ni Media comercial."\n'


def previous_generator():
    try:
        return subprocess.check_output(
            ["git", "show", "HEAD^:actualizador_pkg.py"],
            text=True,
            encoding="utf-8",
        )
    except Exception as exc:
        raise RuntimeError(
            "No se pudo recuperar actualizador_pkg.py del commit anterior. "
            "Sube este archivo sustituyendo al actual y deja que lo ejecute "
            "el workflow del repositorio."
        ) from exc


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"No se encontró el marcador para {label}")
    return text.replace(old, new, 1)


def apply_patch(source):
    if "EVOX_IMPORT_SOURCE_TYPE" in source:
        return source

    source = replace_once(source, CONST_MARKER, CONST_INSERT, "constantes EvoX")
    source = replace_once(source, FUNC_MARKER, FUNC_INSERT, "funciones EvoX")
    source = replace_once(source, MAIN_OLD, MAIN_NEW, "main")
    if OLD_POLICY in source:
        source = source.replace(OLD_POLICY, NEW_POLICY, 1)
    return source


def main():
    base = previous_generator()
    patched = apply_patch(base)

    compile(patched, str(TARGET), "exec")
    TARGET.write_text(patched, encoding="utf-8")
    print("OK: actualizador_pkg.py convertido al generador definitivo con EvoX-CoreOS.")

    namespace = {
        "__name__": "__main__",
        "__file__": str(TARGET.resolve()),
    }
    exec(compile(patched, str(TARGET), "exec"), namespace, namespace)


if __name__ == "__main__":
    main()
