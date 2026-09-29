#!/usr/bin/env python3
# HiddenKernel actualizador PKG - Spectrum Library.
#
# Parte del actualizador_pkg.py que estaba en main en el commit
# d0ad55cc1335e432c3088fdf9e51ed7ee2d92bd3, añade Spectrum Library como
# PKG oficial de Pegasus y ejecuta el generador normal.
#
# Spectrum se obtiene siempre desde la ultima GitHub Release oficial de
# Phoenixx1202/Spectrum-Library y se verifica por SHA-256.

import urllib.request

BASE_URL = (
    "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/"
    "d0ad55cc1335e432c3088fdf9e51ed7ee2d92bd3/actualizador_pkg.py"
)


def download_base():
    req = urllib.request.Request(
        BASE_URL,
        headers={
            "User-Agent": "HiddenKernel-PKG-Catalog/1.5",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"No se encontro el bloque esperado: {label}")
    return text.replace(old, new, 1)


def patch_base(s):
    marker = """def build_websrv_launcher(previous_manifest):"""

    spectrum = """def build_spectrum_library(previous_manifest):
    rel = github_latest("Phoenixx1202/Spectrum-Library")
    asset = find_asset(
        rel,
        lambda n: n.lower().endswith(".pkg") and "spectrum" in n.lower(),
    )

    version = normalize_version(rel.get("tag_name") or rel.get("name"))
    url = str(asset.get("browser_download_url") or "")
    if not url:
        raise RuntimeError("Spectrum Library: asset PKG sin URL")

    digest = sha_from_asset(asset)
    previous = previous_manifest.get("SLIB00001", {})

    if not digest:
        if (
            previous.get("version") == version
            and previous.get("url") == url
            and valid_sha(previous.get("sha256"))
        ):
            digest = previous["sha256"].lower()
        else:
            digest = hashlib.sha256(request_bytes(url)).hexdigest()

    if (
        previous.get("version") == version
        and valid_sha(previous.get("sha256"))
        and previous.get("sha256", "").lower() != digest.lower()
    ):
        raise RuntimeError(
            "Spectrum Library: mismo numero de version pero cambio el SHA-256"
        )

    size = int(asset.get("size") or 0)

    return (
        package(
            "SLIB00001",
            "Spectrum Library",
            version,
            (
                "Biblioteca y gestor de contenido para PS5. Las versiones actuales "
                "incluyen soporte Homebrew PS5 y seleccion de contenido PS4/PS5. "
                "La funcion Homebrew requiere LegacyJB compatible o etaHEN con "
                "Jailbreak Legacy activado."
            ),
            "https://github.com/Phoenixx1202/Spectrum-Library",
            url,
            size,
        ),
        {
            "titleId": "SLIB00001",
            "version": version,
            "url": url,
            "sha256": digest,
            "sizeBytes": size,
            "sourceType": "github-release-official",
            "provenance": (
                "PKG oficial enlazado directamente desde GitHub Releases de "
                "Phoenixx1202/Spectrum-Library."
            ),
        },
    )


def build_websrv_launcher(previous_manifest):"""

    s = replace_once(s, marker, spectrum, "build_spectrum_library")

    old = """        ("ITEM00001", lambda: build_itemzflow(previous_manifest)),
        ("LAPY20011", lambda: build_ps5_xplorer(previous_manifest)),"""

    new = """        ("ITEM00001", lambda: build_itemzflow(previous_manifest)),
        ("SLIB00001", lambda: build_spectrum_library(previous_manifest)),
        ("LAPY20011", lambda: build_ps5_xplorer(previous_manifest)),"""

    s = replace_once(s, old, new, "builders / Spectrum Library")
    return s


code = patch_base(download_base())
exec(compile(code, BASE_URL, "exec"), globals(), globals())
