#!/usr/bin/env python3
# HiddenKernel actualizador - escena PS5 2026-10-03.
#
# Parte de la version de actualizador.py publicada en HiddenKernel el 03/10/2026
# y añade la nueva sección EMULADORES, además de seguir las novedades oficiales.
#
# Añade:
# - EMULADORES: PS5SX2 Installer + Helper (PS2, instalación/actualización directa)
# - EMULADORES: PS5 RetroArch (multisistema, ZIP para instalación manual)
# - EMULADORES: ProsperoEden (Nintendo Switch, FFPFSC para instalación manual)
# - UTILIDADES: Kura Loader (payload PS5)
# - Vigila OnionHEN DPI v2 y lo añadirá cuando OnionBuddies publique una release ELF oficial
# - Mantiene el comportamiento anterior para ShadowMountPlus, OnionHEN, kstuff, etc.;
#   por tanto ShadowMountPlus 1.7beta4 se recogerá automáticamente al ejecutar.
#
# Nota: RetroArch y ProsperoEden son aplicaciones nativas, no payloads ELF. PLDMGR
# puede descargar sus archivos desde el repositorio, pero su instalación final es manual.

import re
import urllib.request

BASE_COMMIT = "031e13821a48c4583f2bded81cb467b465701b48"
BASE_URL = (
    "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/"
    f"{BASE_COMMIT}/actualizador.py"
)


def download_base_updater():
    req = urllib.request.Request(
        BASE_URL,
        headers={
            "User-Agent": "HiddenKernel-Store/1.0",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def load_base_namespace():
    # Ejecutamos el actualizador anterior como módulo para reutilizar toda su
    # lógica sin disparar main() todavía. Ese actualizador, a su vez, reconstruye
    # la base curada que ya usa HiddenKernel.
    ns = {
        "__name__": "hiddenkernel_base_updater",
        "__file__": BASE_URL,
    }
    source = download_base_updater()
    exec(compile(source, BASE_URL, "exec"), ns, ns)
    return ns


def extend_hiddenkernel(ns):
    APPS = ns["APPS"]
    names = {str(x.get("name") or "") for x in APPS}

    # Colocamos EMULADORES justo antes de UTILIDADES para que aparezca como
    # sección propia y no mezclada con herramientas genéricas.
    cat_order = ns["CAT_ORDER"]
    if "EMULADORES" not in cat_order:
        for key in list(cat_order):
            if cat_order[key] >= 6:
                cat_order[key] += 1
        cat_order["EMULADORES"] = 6

    additions = [
        dict(
            name="PS5SX2 Installer",
            repo="Swordpdf/PS5SX2",
            match=["ps5sx2installer"],
            category="EMULADORES",
            channels=["stable"],
            single_latest=True,
            desc=(
                "Instalador y actualizador oficial de PS5SX2, el port nativo de "
                "PCSX2 para PS5. Debe usarse junto con PS5SX2 Helper y ShadowMountPlus"
            ),
        ),
        dict(
            name="PS5SX2 Helper",
            repo="Swordpdf/PS5SX2",
            match=["ps5sxhelper"],
            category="EMULADORES",
            channels=["stable"],
            single_latest=True,
            desc=(
                "Payload Helper oficial requerido por PS5SX2 para preparar/jailbreakear "
                "la aplicación cuando arranca. El autor recomienda cargarlo junto con kstuff"
            ),
        ),
        dict(
            name="PS5 RetroArch (manual)",
            repo="mihawk-99/PS5_RetroArch",
            match=["ps5_retroarch"],
            exclude=["screenshots"],
            extensions=[".zip"],
            download_only=True,
            category="EMULADORES",
            channels=["alpha"],
            single_latest=True,
            desc=(
                "RetroArch nativo para PS5 con cores de PS1, PS2, PSP, N64, "
                "GameCube/Wii, DS, 3DS, Saturn, arcade y otros. PLDMGR descarga el ZIP; "
                "después hay que extraer PPSA99169 en /data/homebrew/PPSA99169. "
                "RPCS3/PS3 no se distribuye en las releases por incompatibilidad de licencia"
            ),
        ),
        dict(
            name="ProsperoEden (Switch, manual)",
            repo="blackbearreloaded/ProsperoEden",
            match=["prosperoeden"],
            extensions=[".ffpfsc"],
            download_only=True,
            category="EMULADORES",
            channels=["beta"],
            single_latest=True,
            desc=(
                "Port experimental de Eden para emulación de Nintendo Switch en PS5. "
                "PLDMGR descarga la imagen FFPFSC; después hay que moverla a una ruta "
                "escaneada por ShadowMountPlus y reiniciar/reescanear ShadowMountPlus"
            ),
        ),
        dict(
            name="Kura Loader",
            repo="NookieAI/kura",
            match=["kura-loader-ps5"],
            category="UTILIDADES",
            channels=["stable"],
            single_latest=True,
            desc=(
                "Payload PS5 de Kura para conectar la consola con su gestor de biblioteca "
                "de juegos y funciones de instalación, saves, cheats y control del ventilador"
            ),
        ),
        # A día 03/10/2026 el repositorio oficial existe, pero OnionBuddies todavía
        # no publica una GitHub Release binaria. Lo dejamos vigilado: en cuanto haya
        # un ELF oficial, el generador lo añadirá sin recurrir a MediaFire/Telegram.
        dict(
            name="OnionHEN DPI v2 Plugin",
            repo="OnionBuddies/onionHEN-dpiv2-plugin",
            match=["dpiv2"],
            category="PKG / INSTALACION",
            channels=["stable", "beta", "alpha"],
            single_latest=True,
            optional=True,
            desc=(
                "Plugin DPI v2 para OnionHEN: instalador remoto de PKG con WebUI, "
                "subidas por bloques, cola y progreso SSE. Se instala como "
                "/data/OnionHEN/plugins/DPIV00001.elf"
            ),
        ),
    ]

    # Insertar antes de UTILIDADES mantiene visualmente juntos los emuladores.
    insert_at = next(
        (i for i, app in enumerate(APPS) if app.get("category") == "UTILIDADES"),
        len(APPS),
    )
    fresh = [x for x in additions if x["name"] not in names]
    APPS[insert_at:insert_at] = fresh

    # Extensiones específicas para aplicaciones nativas. El comportamiento normal
    # del repositorio continúa restringido a ELF/BIN.
    old_valid = ns["valid"]

    def valid_extended(filename, app):
        extensions = app.get("extensions")
        if not extensions:
            return old_valid(filename, app)

        n = ns["Path"](filename).name.lower()
        if not any(n.endswith(str(ext).lower()) for ext in extensions):
            return False
        if any(x.lower() not in n for x in app.get("match", [])):
            return False
        if any(x.lower() in n for x in app.get("exclude", [])):
            return False
        return True

    ns["valid"] = valid_extended

    # Para ZIP/FFPFSC grandes usamos el SHA-256 publicado por GitHub en el asset,
    # evitando descargar cientos de MB cada vez que corre el actualizador.
    old_payload_for = ns["payload_for"]

    def payload_for_extended(app, rel, ch):
        if not app.get("download_only"):
            return old_payload_for(app, rel, ch)

        asset = ns["direct_asset"](rel, app)
        if not asset:
            return None
        url = ns["asset_url"](asset)
        if not url:
            return None

        digest = str(asset.get("digest") or "").strip()
        checksum = ""
        if digest.lower().startswith("sha256:"):
            candidate = digest.split(":", 1)[1].strip().lower()
            if re.fullmatch(r"[0-9a-f]{64}", candidate):
                checksum = candidate

        filename = ns["out_filename"](asset["name"], ch, app, rel)
        return {
            "filename": filename,
            "url": url,
            "source_direct": url,
            "checksum": checksum,
            "asset_updated_at": asset.get("updated_at") or asset.get("created_at") or "",
        }

    ns["payload_for"] = payload_for_extended

    # Fichas de estado/compatibilidad conservadoras y basadas en la documentación
    # del propio proyecto.
    curated = ns["CURATED_STATUS"]
    curated["PS5SX2 Installer"] = [
        (r".*", "EN PRUEBAS", "PS5SX2 sigue en desarrollo activo; el autor avisa de posibles asperezas y pide logs de pruebas."),
    ]
    curated["PS5SX2 Helper"] = [
        (r".*", "EN PRUEBAS", "Helper del proyecto PS5SX2; usar junto al instalador y ShadowMountPlus según la guía oficial."),
    ]

    compat = ns["COMPATIBILITY_RULES"]
    compat["PS5SX2 Installer"] = [
        (r".*", "probado por el proyecto en PS5/PS5 Pro con FW 6.02-12.70"),
    ]
    compat["PS5SX2 Helper"] = [
        (r".*", "probado por el proyecto en PS5/PS5 Pro con FW 6.02-12.70"),
    ]

    # La release usa tag técnico vk-285-118 pero nombre humano PS5SX2 1.7.
    # Mostramos 1.7 para que la Store sea más clara, sin alterar la selección.
    old_make_entry = ns["make_entry"]

    def make_entry_extended(app, rel, p, ch):
        entry = old_make_entry(app, rel, p, ch)
        if app.get("name") in ("PS5SX2 Installer", "PS5SX2 Helper"):
            m = re.search(r"PS5SX2\s+([0-9]+(?:\.[0-9]+)*)", str(rel.get("name") or ""), re.I)
            if m:
                entry["version"] = m.group(1)
        return entry

    ns["make_entry"] = make_entry_extended


def main():
    ns = load_base_namespace()
    extend_hiddenkernel(ns)
    ns["main"]()


if __name__ == "__main__":
    main()
