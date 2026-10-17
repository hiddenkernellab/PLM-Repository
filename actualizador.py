#!/usr/bin/env python3
"""HiddenKernelLab | Actualizador del catalogo PLDMGR.

Base: hiddenkernellab/PLM-Repository/main, consultado 2026-10-17
(blob ff5e6310446343b6a47cc354844239845e769d1d).
Mantiene los IDs, las categorias y los iconos del repositorio.
No modifica GitHub por si mismo. Requiere Python 3.10+.
Uso local: python actualizador.py [--offline]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import NamedTemporaryFile

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "payloads.json"
ICONS = ROOT / "icons.json"
GITHUB_API = "https://api.github.com/repos/{}/releases/latest"
SHA256 = re.compile(r"^[0-9a-f]{64}$")

RETIRADOS = frozenset({
    "airpsx", "jailbreak-store", "ps5-file-explorer", "zftpd-zhttp",
})

CATEGORIAS = (
    "ESENCIALES", "HEN / AIO", "SISTEMA", "ARCHIVOS / RED",
    "PKG / INSTALACION", "JUEGOS / COMPATIBILIDAD",
    "DESCARGAS / TIENDAS", "EMULADORES", "MULTIMEDIA",
    "MANDOS / AUDIO", "TRUCOS / PARTIDAS", "PERSONALIZACION",
    "UTILIDADES", "DESARROLLO / AVANZADO",
)
AVANZADOS = frozenset({
    "ps5debug-ng", "ps5lm", "kura-loader", "lapy-jb-daemon",
    "ps5library-agent-rdiol12", "np-fake-signin",
})
RENOMBRAR_CATEGORIAS = {
    "ARCHIVOS / PC": "ARCHIVOS / RED",
    "CHEATS": "TRUCOS / PARTIDAS",
    "DESCARGAS": "DESCARGAS / TIENDAS",
    "MANDOS": "MANDOS / AUDIO",
}

# Builds experimentales que requieren revision manual.
NO_AUTOMATICOS = frozenset({
    "kstuff-fpkg", "shadowmountplus", "ps5sx2-helper",
    "ps5sx2-installer", "etahen-13.60", "pldmgr-install-update",
    "ps5-hardware-overlay",
})

FTP_VERSION = "1.16-ng-stable"
FTP_REPO = "drakmor/ftpsrv"
FTP_ARCHIVO = "ftpsrv-ps5.elf"
FTP_URL = (
    "https://github.com/drakmor/ftpsrv/releases/download/"
    + FTP_VERSION + "/" + FTP_ARCHIVO
)
FTP_SHA = "f19ae469b25453a7a4af4529527521d31f143100f18a2c6839666e7121c8bd32"
FTP_DESCRIPCION = (
    "ftpsrv de Drakmor, version NG estable para PS5. Compatible hasta FW "
    "13.60 segun el autor. Incorpora funciones FTP avanzadas, listado virtual "
    "/proc y descifrado SELF en varios firmwares. AVISO: algunas operaciones "
    "sobre /proc pueden finalizar procesos; usar con cuidado. No esta confirmado "
    "que corrija los directorios duplicados de Solid Explorer. Ejecutar solo "
    "un servidor FTP en el mismo puerto."
)

# Release upstream: el tag v0.0.18 contiene el ELF AIO 1.0.18.
# No usar overlay_payload.elf, que es la carga interna.
OVERLAY_RELEASE = {
    "name": "PS5 Hardware Overlay (KUS)",
    "filename": "ps5-overlay-kus_v1.0.18.elf",
    "url": "https://github.com/smoxa/ps5-new-overlay/releases/download/v0.0.18/ps5-overlay-kus_v1.0.18.elf",
    "source": "https://github.com/smoxa/ps5-new-overlay/releases",
    "source_direct": "https://github.com/smoxa/ps5-new-overlay/releases/download/v0.0.18/ps5-overlay-kus_v1.0.18.elf",
    "description": (
        "Overlay KUS 1.0.18 (release GitHub v0.0.18): HUD de 12 metricas "
        "(FPS, temperaturas, CPU/GPU, RAM, SSD M.2, ventilador, consumo, IP), "
        "configuracion web en puerto 8585 y descarga en caliente. "
        "ELF AIO ps5-overlay-kus; NO ejecutar overlay_payload.elf por separado. "
        "Requiere jailbreak y cargador ELF; compatibilidad por firmware "
        "no confirmada en todos los modelos. EXPERIMENTAL: no autocargar; "
        "no ejecutar simultaneamente con otros overlays de ShellUI."
    ),
    "last_update": "2026-10-17",
    "version": "v0.0.18",
    "category": "UTILIDADES",
    "checksum": "96562d1fc8deb641c67e19dc618cf2334f14512bc02e15732f53361f31005e29",
}

# ps5-signal v0.2.0: SHA-256 oficial del ELF normal, NO de ps5-signal-dev.elf.
PS5_SIGNAL = {
    "name": "PS5 Signal",
    "filename": "ps5-signal.elf",
    "url": "https://github.com/Marice/ps5-signal/releases/download/v0.2.0/ps5-signal.elf",
    "source": "https://github.com/Marice/ps5-signal/releases",
    "source_direct": "https://github.com/Marice/ps5-signal/releases/download/v0.2.0/ps5-signal.elf",
    "description": (
        "Personaliza el LED y los pitidos de PS5; tonos y secuencias de inicio, "
        "volumen del pitido (0-2), LED segun temperatura de CPU/SoC y API "
        "local 127.0.0.1:9150. Version 0.2.0 corrige que la 0.1.0 "
        "desactivase los pitidos del sistema, recupera la conexion al salir "
        "del modo reposo y respeta el LED original durante el reposo. "
        "Compatible segun el autor desde FW 9.00; probado solo en PS5 Pro "
        "13.60. Si 0.1.0 desactivo el pitido, volver a activarlo una vez "
        "en Ajustes. No usar ps5-signal-dev.elf (escucha en red). "
        "EXPERIMENTAL en otros firmwares; autocarga opcional."
    ),
    "last_update": "2026-10-17",
    "version": "v0.2.0",
    "category": "PERSONALIZACION",
    "checksum": "189b51ac204600f40d4aa9adc8394e897decf96042689c2066d9292b47fd173e",
    "icon_key": "ps5-signal",
    "id": "ps5-signal",
}


def migrar_overlay(item: dict) -> None:
    # Mantener el ID y el icono del usuario.
    if (str(item.get("version")) in {"v1.0.15", "1.0.15"}
            or "/v1.0.15/" in str(item.get("url", ""))):
        item.update(OVERLAY_RELEASE)
        print("ACTUALIZADO: PS5 Hardware Overlay -> KUS 1.0.18 (tag v0.0.18)")


def migrar_signal(item: dict) -> None:
    # No retroceder si el catalogo ya contiene una version posterior.
    if version_numerica(item.get("version", "")) < version_numerica(PS5_SIGNAL["version"]):
        preserved = {k: item[k] for k in ("id", "icon_key") if k in item}
        item.update(PS5_SIGNAL)
        item.update(preserved)
        print("ACTUALIZADO: PS5 Signal -> v0.2.0 (ELF normal oficial)")


def leer_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError(f"JSON sin objeto raiz: {path}")
    return value


def escribir_si_cambia(path: Path, value: dict) -> bool:
    data = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return False
    temp = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp",
                                delete=False) as f:
            temp = Path(f.name)
            f.write(data)
        with temp.open("r", encoding="utf-8") as f:
            json.load(f)
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()
    return True


def version_numerica(value: object) -> tuple[int, ...]:
    """Orden conservador; no sirve para comparar vk o sufijos alpha/beta."""
    m = re.search(r"\d+(?:\.\d+){0,3}", str(value))
    if not m:
        return (0, 0, 0, 0)
    numbers = [int(s) for s in m.group(0).split(".")]
    return tuple((numbers + [0] * 4)[:4])


def solicitar_release(repo: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "HiddenKernelLab-Catalog-Updater/2026-10-17",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(GITHUB_API.format(repo), headers=headers)
    with urllib.request.urlopen(request, timeout=9) as response:
        obj = json.load(response)
    if not isinstance(obj, dict):
        raise ValueError("Respuesta de GitHub invalida")
    return obj


def github_repo(item: dict) -> str | None:
    src = str(item.get("source", "")).rstrip("/")
    match = re.fullmatch(r"https://github\.com/([^/]+/[^/]+)/releases", src)
    if match:
        return match.group(1)
    return None


def candidates(item: dict, tag: str) -> list[str]:
    """Intentar nombres de activos verificables sin inventar enlaces."""
    name = str(item.get("url", "")).split("/")[-1]
    oldtag = str(item.get("version", ""))
    parts = str(item.get("url", "")).split("/releases/download/")
    if len(parts) == 2:
        oldtag = parts[1].split("/", 1)[0]
    shortold, shortnew = oldtag.removeprefix("v"), tag.removeprefix("v")
    found = [name]
    for old, new in ((oldtag, tag), (shortold, shortnew)):
        if old and old in name:
            found.append(name.replace(old, new, 1))
    if item.get("id") == "payload-manager":
        found.insert(0, f"pldmgr_{tag}.elf")
    if item.get("id") == "ps5upload":
        found.insert(0, f"ps5upload-{shortnew}.elf")
    if item.get("id") == "patchdl":
        found.insert(0, f"patchdl_{shortnew}.elf")
    return list(dict.fromkeys(x for x in found if x.lower().endswith(".elf")))


def elegir_activo(item: dict, repo: str, release: dict) -> tuple | None:
    if release.get("draft") or release.get("prerelease"):
        return None
    tag = str(release.get("tag_name") or "")
    if not tag or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", tag):
        return None
    old_tag = str(item.get("version", ""))
    if version_numerica(tag) <= version_numerica(old_tag):
        return None
    old_release_url = str(item.get("url", ""))
    if "/releases/download/" not in old_release_url:
        return None
    possible = set(candidates(item, tag))
    matches = []
    for asset in release.get("assets", []):
        name = str(asset.get("name", ""))
        digest = str(asset.get("digest", ""))
        url = str(asset.get("browser_download_url", ""))
        expected = f"https://github.com/{repo}/releases/download/{tag}/{name}"
        if (name in possible and digest.startswith("sha256:")
                and SHA256.fullmatch(digest[7:]) and url == expected):
            matches.append((tag, name, url, digest[7:]))
    if len(matches) != 1:
        return None
    date = str(release.get("published_at") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        date = str(item.get("last_update", ""))
    return *matches[0], date


def refrescar(item: dict, releases: dict) -> dict:
    ident = str(item.get("id", ""))
    if ident in NO_AUTOMATICOS:
        return item
    repo = github_repo(item)
    if not repo or not str(item.get("url", "")).endswith(".elf"):
        return item
    if repo not in releases:
        try:
            releases[repo] = solicitar_release(repo)
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            print(f"AVISO: no se pudo consultar {repo}: {str(exc)[:110]}")
            releases[repo] = None
    release = releases[repo]
    if not release:
        return item
    choice = elegir_activo(item, repo, release)
    if not choice:
        return item
    tag, asset, url, sha, date = choice
    out = dict(item)
    out.update(version=tag, url=url, source_direct=url, checksum=sha,
               last_update=date, filename=asset)
    out["description"] = re.sub(
        r"\s*AVISO: version [^ ]+ detectada automaticamente; revisar cambios upstream\.",
        "", str(item.get("description", "")))
    out["description"] += (
        f" AVISO: version {tag} nueva detectada y SHA-256 verificado; "
        "consultar los cambios del desarrollador antes de autocargar.")
    print(f"ACTUALIZADO: {item.get('name')} -> {tag}")
    return out


def normalizar_categoria(item: dict) -> None:
    ident = str(item.get("id", ""))
    if ident in AVANZADOS:
        category = "DESARROLLO / AVANZADO"
    elif ident == "garlic-savemgr":
        category = "TRUCOS / PARTIDAS"
    elif ident == "ps5-syslang":
        category = "PERSONALIZACION"
    else:
        category = RENOMBRAR_CATEGORIAS.get(item.get("category"), item.get("category"))
    item["category"] = category


def normalizar_descripcion(item: dict) -> None:
    ident = item["id"]
    if ident == "ps5upload":
        item["description"] = (
            "PS5Upload, servidor de transferencias y gestion remota. Permite "
            "reanudacion, extraccion de RAR y gestion de payloads. Usar una version "
            "compatible del cliente y del helper. Version instalada en el catalogo: "
            + str(item["version"]) + ". Consultar cambios upstream."
        )
    elif ident == "orbit-store":
        item["description"] = (
            "Orbit Store " + str(item["version"]) + ": gestor de descargas "
            "con extraccion ZIP/RAR/7z, control de descargas y soporte USB. "
            "ESTADO: BETA; revisar los cambios upstream antes de autocargar."
        )
    elif ident == "ps4mount" and version_numerica(item.get("version")) >= (0, 6, 0, 0):
        item["description"] = (
            "PS4Mount " + str(item["version"]) + ": monta juegos PS4 FPKG y "
            "actualizaciones desde USB exFAT sin copiar al SSD interno; "
            "panel web en el puerto 8770. Desde 0.6.0 registra nuevos juegos "
            "mas rapido sin recorrer toda la biblioteca y corrige Stop para "
            "poder reiniciar el payload sin reiniciar la consola. Si se viene "
            "de 0.5.1 y se uso Stop, reiniciar la PS5 una vez antes de cargar "
            "la nueva version. ESTADO: EXPERIMENTAL; no autocargar. "
            "Consultar notas upstream para cambios posteriores."
        )
    elif ident == "ps5-webkit-autoloader":
        item["description"] = str(item.get("description", "")).replace(
            "ESTADO: ESTABLE. COMPATIBILIDAD: FW 1.00-5.50 y 7.00-13.60.",
            "ESTADO: ESTABLE. COMPATIBILIDAD: rama 0.6.x FW 7.00-13.60 "
            "segun exploit; NO admite FW 1.00-5.50."
        )


def migrar_ftp(item: dict) -> None:
    item.update(
        id="ftpsrv", icon_key="ftpsrv", name="ftpsrv (Drakmor)",
        filename=FTP_ARCHIVO, url=FTP_URL,
        source=f"https://github.com/{FTP_REPO}/releases",
        source_direct=FTP_URL, description=FTP_DESCRIPCION,
        version=FTP_VERSION, last_update="2026-09-20",
        category="ARCHIVOS / RED", checksum=FTP_SHA,
    )


def validar(catalogo: dict) -> None:
    items = catalogo.get("payloads")
    if not isinstance(items, list) or not items:
        raise ValueError("Catalogo sin payloads: no se guardan cambios")
    ids = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Entrada invalida")
        ident = item.get("id")
        if not isinstance(ident, str) or not ident or ident in ids:
            raise ValueError(f"ID vacio/duplicado: {ident}")
        ids.add(ident)
        if item.get("category") not in CATEGORIAS:
            raise ValueError(f"Categoria inesperada en {ident}: {item.get('category')}")
        if not SHA256.fullmatch(str(item.get("checksum", ""))):
            raise ValueError(f"Checksum incorrecto en {ident}")
        for field in ("url", "source_direct"):
            if not str(item.get(field, "")).startswith("https://"):
                raise ValueError(f"URL invalida de {field} en {ident}")
    required = {"nanodns", "payload-manager", "apr-emu-updater",
                "kstuff-fpkg", "shadowmountplus", "ftpsrv"}
    if not required.issubset(ids):
        raise ValueError("Faltan esenciales: " + repr(sorted(required - ids)))
    if RETIRADOS & ids:
        raise ValueError("Entradas obsoletas todavia presentes")


def icono_nuevo(item: dict) -> str:
    """Solo para futuras entradas sin icono: no sobreescribe imagenes existentes."""
    category = str(item.get("category", ""))
    colors = {
        "ESENCIALES": ("#163968", "#4e88d8"),
        "HEN / AIO": ("#2d245b", "#9b5edd"),
        "EMULADORES": ("#205a74", "#35c5cb"),
        "ARCHIVOS / RED": ("#174d66", "#54a9e5"),
        "DESCARGAS / TIENDAS": ("#4b3b8c", "#a676e5"),
        "MANDOS / AUDIO": ("#265747", "#5ecca7"),
        "PERSONALIZACION": ("#3b2468", "#b17fe3"),
    }
    a, b = colors.get(category, ("#243b60", "#709dd9"))
    if item.get("id") == "ps5-signal":
        a, b = "#0b2558", "#9556c8"
        shape = (
            '<path d="M36 31q28-10 56 0l-7 60q-21 10-42 0z" '
            'stroke="white" stroke-width="5" fill="none"/>'
            '<path d="M42 43q22 8 44 0" stroke="#66dcff" '
            'stroke-width="6" stroke-linecap="round"/>'
            '<path d="M68 49v24a9 9 0 1 1-6-9V53l18-5v20a9 9 0 1 1-6-9V46z" '
            'fill="white"/>'
        )
    elif category == "EMULADORES":
        shape = '<rect x="25" y="29" width="78" height="70" rx="12" stroke="white" stroke-width="7" fill="none"/><path d="M41 80h19M50 70v20" stroke="white" stroke-width="6"/><circle cx="83" cy="81" r="5" fill="white"/>'
    elif category == "ARCHIVOS / RED":
        shape = '<circle cx="64" cy="63" r="31" stroke="white" stroke-width="7" fill="none"/><path d="M33 63h62M64 32a45 45 0 010 62M64 32a45 45 0 000 62" stroke="white" stroke-width="5" fill="none"/>'
    elif category == "DESCARGAS / TIENDAS":
        shape = '<path d="M64 29v51m-19-20 19 20 19-20M34 90v10h60V90" stroke="white" stroke-width="9" stroke-linejoin="round" stroke-linecap="round" fill="none"/>'
    else:
        shape = '<rect x="34" y="34" width="60" height="60" rx="11" stroke="white" stroke-width="7" fill="none"/><path d="M50 64h28M64 50v28" stroke="white" stroke-width="7"/>'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">'
           f'<defs><linearGradient id="bg" x2="1" y2="1">'
           f'<stop stop-color="{a}"/><stop offset="1" stop-color="{b}"/>'
           f'</linearGradient></defs><rect width="128" height="128" rx="22" '
           f'fill="url(#bg)"/>{shape}</svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode("ascii")


def procesar(offline: bool = False) -> tuple[int, int, bool, bool]:
    catalogo = leer_json(CATALOG)
    items = catalogo.get("payloads")
    if not isinstance(items, list) or not items:
        raise ValueError("payloads.json esta vacio o mal formado")
    icons_original = leer_json(ICONS) if ICONS.exists() else {"icons": {}}
    original_icons = icons_original.get("icons")
    if not isinstance(original_icons, dict):
        raise ValueError("icons.json no tiene objeto 'icons'")

    initial = len(items)
    activos = [dict(x) for x in items if x.get("id") not in RETIRADOS]
    if not any(x.get("id") == "ps5-signal" for x in activos):
        activos.append(dict(PS5_SIGNAL))
        print("AÑADIDO: PS5 Signal v0.2.0 (ELF oficial)")
    if not any(x.get("id") == "ftpsrv" for x in activos):
        raise ValueError("No se encontro ftpsrv original: no se toca el catalogo")
    cache: dict[str, dict | None] = {}
    resultado = []
    for item in activos:
        if item.get("id") == "ps5-hardware-overlay":
            migrar_overlay(item)
        if item.get("id") == "ps5-signal":
            migrar_signal(item)
        if item.get("id") == "ftpsrv":
            if (github_repo(item) != FTP_REPO or
                    version_numerica(item.get("version", "")) < version_numerica(FTP_VERSION)):
                migrar_ftp(item)
        if not offline:
            item = refrescar(item, cache)
        normalizar_categoria(item)
        normalizar_descripcion(item)
        item.setdefault("icon_key", str(item.get("id", "")))
        resultado.append(item)

    orden = {category: i for i, category in enumerate(CATEGORIAS)}
    resultado.sort(key=lambda x: (orden.get(x.get("category"), 999),
                                  str(x.get("name", "")).casefold()))
    catalogo["payloads"] = resultado
    catalogo["icons_url"] = "icons.json"
    validar(catalogo)

    imagenes = {}
    for item in resultado:
        key = item["icon_key"]
        if key in imagenes:
            raise ValueError("icon_key duplicado: " + key)
        imagenes[key] = original_icons.get(key) or icono_nuevo(item)
    icon_data = {"icons": imagenes}
    if len(json.dumps(icon_data).encode("utf-8")) > 4 * 1024 * 1024:
        raise ValueError("El archivo de iconos supera 4 MB")

    json.loads(json.dumps(catalogo, ensure_ascii=False))
    json.loads(json.dumps(icon_data, ensure_ascii=False))
    changed_icons = escribir_si_cambia(ICONS, icon_data)
    changed_catalog = escribir_si_cambia(CATALOG, catalogo)
    return initial, len(resultado), changed_catalog, changed_icons


def main() -> int:
    parser = argparse.ArgumentParser(description="Actualizador de HiddenKernelLab")
    parser.add_argument("--offline", action="store_true",
                        help="Aplicar limpieza y verificar JSON sin consultar releases")
    args = parser.parse_args()
    try:
        original, current, changed_catalog, changed_icons = procesar(args.offline)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: catalogo sin cambios seguros: " + str(exc), file=sys.stderr)
        return 1
    print(f"HiddenKernel: {original} -> {current} entradas; "
          f"payloads.json {'modificado' if changed_catalog else 'sin cambios'}; "
          f"icons.json {'modificado' if changed_icons else 'sin cambios'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
