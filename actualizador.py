#!/usr/bin/env python3
# HiddenKernel - actualizador limpio + radar evoX-CoreOS
# Fecha: 2026-10-03
#
# Base exacta: hiddenkernellab/PLM-Repository @
# a418c0637cee4b507891188ca2e0045260be5d9e
#
# OBJETIVOS
# ---------
# 1) Conservar las primeras pruebas FPKG como historico TEST/LEGACY:
#    - A53/PPR separados
#    - kstuff FPKG test builds
#    - AIO 3-in-1 experimentales
#    - ShadowMountPlus alpha FPKG/legacy
#    - ramas alternativas antiguas de kstuff/ShadowMountPlus
# 2) Mantener el stack actual y útil:
#    - kstuff-lite oficial (actualmente 1.11)
#    - ShadowMountPlus 1.7 beta más reciente (actualmente 1.7beta4)
# 3) Retirar BackPork del catálogo curado porque ShadowMountPlus 1.7 ya incorpora
#    backports PKG y el propio proyecto advierte de no usar ambos a la vez.
# 4) Retirar etaHEN 2.6B de ALTERNATIVOS (build de pruebas ya caducada).
# 5) Aplicar la regla "nuevas incorporaciones = ELF" y no añadir ZIP/FFPFSC
#    como entradas de PLDMGR.
# 6) Añadir una selección útil y mantenida de lo que está apareciendo en
#    evoX-CoreOS / entorno de Jhon, preferentemente desde el upstream oficial.
#
# NOTA
# ----
# evoX-CoreOS sustituye al antiguo "PS5 Super PLDMGR Auto Updater" de Nexgen.
# Este script NO importa sus ~100 payloads a ciegas: usa evoX como radar,
# pero HiddenKernel sigue siendo un catálogo curado y más limpio.

import urllib.request

BASE_COMMIT = "a418c0637cee4b507891188ca2e0045260be5d9e"
BASE_URL = (
    "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/"
    f"{BASE_COMMIT}/actualizador.py"
)


def download_current_updater():
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


def load_current_wrapper():
    ns = {
        "__name__": "hiddenkernel_current_wrapper",
        "__file__": BASE_URL,
    }
    source = download_current_updater()
    exec(compile(source, BASE_URL, "exec"), ns, ns)
    return ns


def clean_obsolete_entries(ns):
    apps = ns["APPS"]

    # Las tres familias FPKG de prueba nacieron antes de que el flujo actual
    # quedase integrado en kstuff-lite 1.11 + ShadowMountPlus 1.7.
    obsolete_categories = {
        "FPKG INTEGRADO",
        "FPKG MODULAR",
        "FPKG LEGACY",
    }

    # Entradas antiguas/duplicadas que ya no aportan nada al catálogo normal.
    obsolete_pairs = {
        ("ALTERNATIVOS", "kstuff-lite Drakmor"),
        ("ALTERNATIVOS", "ShadowMountPlus"),
        ("ALTERNATIVOS", "PS5 BackPork"),
        ("ALTERNATIVOS", "etaHEN"),  # 2.6B de pruebas/caducada
        ("EMULADORES", "PS5 RetroArch (manual)"),       # ZIP, no ELF
        ("EMULADORES", "ProsperoEden (Switch, manual)"),# FFPFSC, no ELF
    }

    kept = []
    for app in apps:
        cat = str(app.get("category") or "")
        name = str(app.get("name") or "")
        if cat in obsolete_categories:
            continue
        if (cat, name) in obsolete_pairs:
            continue
        kept.append(app)

    apps[:] = kept

    # Reordenamos el catálogo tras eliminar las secciones FPKG legacy.
    order = [
        "ESENCIALES",
        "HEN / AIO",
        "SISTEMA",
        "ARCHIVOS / RED",
        "PKG / INSTALACION",
        "JUEGOS / COMPATIBILIDAD",
        "EMULADORES",
        "MULTIMEDIA",
        "UTILIDADES",
        "CHEATS",
        "MANDOS / AUDIO",
        "DESCARGAS",
        "PERSONALIZACION",
        "ALTERNATIVOS",
    ]
    ns["CAT_ORDER"].clear()
    ns["CAT_ORDER"].update({name: i for i, name in enumerate(order)})


def add_curated_evox_elf(ns):
    apps = ns["APPS"]
    names = {str(a.get("name") or "") for a in apps}

    additions = [
        # MANDOS / AUDIO
        dict(
            name="AnyPad PS5",
            repo="sinfiltros/AnyPad-PS5",
            match=["anypad-ps5"],
            category="MANDOS / AUDIO",
            channels=["alpha"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Crea mandos virtuales DualSense para usar gamepads Bluetooth externos. "
                "Proyecto alpha; DS4 validado y otros mandos dependen del modelo/firmware"
            ),
        ),
        dict(
            name="FGG XSense",
            repo="FGGstore/FGG-XSense",
            match=["fgg-xsense"],
            category="MANDOS / AUDIO",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Payload dedicado para usar mandos Xbox en una PS5 con jailbreak. "
                "Se conserva como alternativa estable a AnyPad"
            ),
        ),
        dict(
            name="FGG PlayPods",
            repo="FGGstore/FGG-PlayPods",
            match=["fgg-playpods"],
            category="MANDOS / AUDIO",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Permite enviar el audio de la PS5 a auriculares Bluetooth corrientes "
                "sin dongle externo"
            ),
        ),

        # ARCHIVOS / RED
        dict(
            name="zftpd",
            repo="seregonwar/zftpd",
            match=["zftpd-ps5-v"],
            exclude=["zhttp"],
            category="ARCHIVOS / RED",
            channels=["stable", "beta", "alpha"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Servidor FTP moderno para PS5. Se selecciona únicamente la build PS5 ELF "
                "normal, separada de la variante HTTP"
            ),
        ),
        dict(
            name="zftpd + zhttp",
            repo="seregonwar/zftpd",
            match=["zftpd-ps5-zhttp"],
            category="ARCHIVOS / RED",
            channels=["stable", "beta", "alpha"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Variante PS5 de zftpd que añade el servidor zhttp para administración "
                "y transferencias desde la red local"
            ),
        ),
        dict(
            name="AirPSX",
            repo="barisyild/airpsx",
            match=["airpsx"],
            exclude=[".zip"],
            category="ARCHIVOS / RED",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Escritorio web remoto tipo AirDroid para administrar una PS5 modificada "
                "desde el navegador de otro dispositivo"
            ),
        ),
        dict(
            name="unrar-ps5",
            repo="bizkut/unrar-ps5",
            match=["unrar_ps5"],
            category="ARCHIVOS / RED",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Extrae RAR y 7z directamente en PS5, incluidos multipartes, y puede "
                "colocar homebrew extraído en una ruta configurable"
            ),
        ),
        dict(
            name="FGG Unpack",
            repo="FGGstore/FGG-Unpack",
            match=["fgg-unpack"],
            category="ARCHIVOS / RED",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Extractor ligero de ZIP y 7z directamente en una PS5 con jailbreak"
            ),
        ),

        # PKG
        dict(
            name="PKG Receiver",
            repo="Loopayeh/pkg-sender",
            match=["pkg-receiver"],
            category="PKG / INSTALACION",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Receptor PS5 para PKG Sender. Permite enviar e instalar PKG por LAN "
                "desde la aplicación de escritorio/móvil compatible"
            ),
        ),

        # JUEGOS / COMPATIBILIDAD
        dict(
            name="PS5 Game Compressor Fork",
            repo="gcoding97/PS5-Game-Compressor",
            match=["game-compressor"],
            category="JUEGOS / COMPATIBILIDAD",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Fork mantenido de PS5 Game Compressor para comprimir juegos directamente "
                "en PS5 y reducir espacio ocupado"
            ),
        ),

        # EMULACIÓN
        dict(
            name="RomM Sync",
            repo="s0liton/ps5-romm",
            match=["romm-sync"],
            category="EMULADORES",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Cliente PS5 para servidores RomM: biblioteca, descarga de ROM/BIOS hacia "
                "perfiles de emulador y sincronización de saves/savestates"
            ),
        ),

        # BACKUP / JUEGOS
        dict(
            name="PS5 App Dumper",
            repo="EchoStretch/ps5-app-dumper",
            match=["ps5-app-dumper"],
            category="JUEGOS / COMPATIBILIDAD",
            channels=["stable", "beta"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Dumper moderno de aplicaciones PS5. La rama 2.10 anade volcado de DLC, "
                "cola ampliada, deteccion de dumps incompletos y mejoras de gestion"
            ),
        ),

        # UTILIDADES / RED
        dict(
            name="PS5LM",
            repo="cobanov/PS5LM",
            match=["ps5lm.elf"],
            category="UTILIDADES",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Ejecuta modelos GGUF localmente en PS5 mediante llama.cpp y ofrece "
                "biblioteca web, chat local y API compatible con OpenAI en la LAN"
            ),
        ),
        dict(
            name="PS5 SysLang",
            repo="owendswang/ps5-syslang",
            match=["ps5-syslang"],
            category="UTILIDADES",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Permite cambiar el idioma de ShellUI, incluso en consolas con "
                "limitaciones regionales de idioma"
            ),
        ),
        dict(
            name="PS5 Fan Control",
            repo="owendswang/ps5-fan-control",
            match=["ps5-fan-control"],
            category="UTILIDADES",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Control independiente del ventilador con temperatura objetivo configurable"
            ),
        ),

        # MULTIMEDIA
        dict(
            name="PS Play",
            repo="MounirHero/PS-PLAY",
            match=["psplay"],
            category="MULTIMEDIA",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Hub multimedia nativo para PS5 con USB, red, DLNA, IPTV y reproducción "
                "de medios desde una interfaz adaptada al mando"
            ),
        ),
        dict(
            name="Nuvio PS5",
            repo="theghostonline/Nuvio-PS5",
            match=["nuvio-ps5"],
            category="MULTIMEDIA",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Interfaz Nuvio para PS5 con reproductor nativo orientado a 4K/HDR "
                "y funciones de streaming multimedia"
            ),
        ),

        # UTILIDADES
        dict(
            name="PS5 Hardware Overlay",
            repo="smoxa/ps5-new-overlay",
            match=["ps5_overlay.elf"],
            category="UTILIDADES",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Overlay ligero con FPS, temperaturas, carga CPU/GPU, RAM/VRAM "
                "y ventilador durante el juego"
            ),
        ),
        dict(
            name="PS5 Date & Time Sync",
            repo="kerrdec97/ps5-date-time-sync",
            match=["ps5-date-time-sync"],
            category="UTILIDADES",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Restaura automáticamente fecha y hora de la consola mediante NTP; "
                "útil en consolas offline o con PSN bloqueado"
            ),
        ),
        dict(
            name="CheatRunner",
            repo="notmaj0r/CheatRunner",
            match=["cheatrunner"],
            category="CHEATS",
            channels=["stable", "beta", "alpha"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Trainer de cheats con interfaz web local, separado de los HEN/AIO"
            ),
        ),

        # DESCARGAS
        dict(
            name="PatchDL",
            repo="knutwurst/patchdl",
            match=["patchdl"],
            category="DESCARGAS",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Busca y descarga actualizaciones compatibles de juegos y permite "
                "gestionar el proceso desde la propia PS5"
            ),
        ),
        dict(
            name="Orbit Store",
            repo="saawant12/orbit-store-ps5",
            match=["orbit_store"],
            category="DESCARGAS",
            channels=["stable", "beta"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Gestor de descargas para PS5 con cola persistente, pausa/reanudación, "
                "selección de almacenamiento e interfaz local para móvil/PC. "
                "Usar únicamente con contenido que se tenga derecho a descargar"
            ),
        ),

        # PERSONALIZACIÓN
        dict(
            name="PS5 Wallpaper Modder",
            repo="hgr9519/ps5-wallpaper-modd",
            match=["ps5-wallpaper-modd"],
            category="PERSONALIZACION",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Cambia fondos del sistema desde JPG/PNG/DDS e incluye copia de seguridad "
                "y restauración de los wallpapers originales"
            ),
        ),
    ]

    # Para todas las nuevas incorporaciones: ELF y nada más.
    previous_valid = ns["valid"]

    def valid_curated(filename, app):
        if app.get("elf_only") and not str(filename).lower().endswith(".elf"):
            return False
        return previous_valid(filename, app)

    ns["valid"] = valid_curated

    for item in additions:
        if item["name"] not in names:
            apps.append(item)
            names.add(item["name"])

    # Estados conservadores donde realmente aportan contexto.
    curated = ns["CURATED_STATUS"]

    curated["AnyPad PS5"] = [
        (
            r".*",
            "ALPHA / EN PRUEBAS",
            "Proyecto muy reciente. Conviene validar mando y firmware antes de ponerlo en autoload.",
        )
    ]
    curated["Orbit Store"] = [
        (
            r".*",
            "BETA / EN PRUEBAS",
            "La aplicación sigue ampliando validación en hardware; usar la cola y descargas con la consola despierta.",
        )
    ]
    curated["PS5 Wallpaper Modder"] = [
        (
            r".*",
            "PRECAUCIÓN / CON BACKUP",
            "Modifica recursos visuales del sistema; usar primero su función de copia de seguridad y conservarla.",
        )
    ]
    curated["AirPSX"] = [
        (
            r".*",
            "RED LOCAL / PRECAUCIÓN",
            "Expone funciones de administración en una interfaz web; mantenerla restringida a una red local de confianza.",
        )
    ]




def apply_hiddenkernel_v2_maintenance(ns):
    """Mantenimiento conservador sin cambiar el schema publico de Payload Manager."""
    apps = ns["APPS"]

    # Las familias FPKG historicas se conservan como TEST/LEGACY.
    obsolete_categories = set()
    kept = []
    for app in apps:
        name = str(app.get("name") or "")
        cat = str(app.get("category") or "")
        repo = str(app.get("repo") or "")

        if cat in obsolete_categories:
            continue
        if cat == "ALTERNATIVOS" and name == "etaHEN":
            continue
        if repo in {"juma-sayeh/PS5-Game-Compressor", "gcoding97/PS5-Game-Compressor"}:
            continue
        if name == "ProsperoMgr":
            continue
        kept.append(app)

    apps[:] = kept

    apps.extend([
        dict(
            name="etaHEN 13.60",
            repo="GronedWaffel/etahen-13.60",
            match=["etaHEN-13.60.elf"],
            category="HEN / AIO",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Port no oficial de etaHEN 2.5B para PS5 FW 13.60. "
                "Usar solo en 13.60; no sustituye a etaHEN oficial 2.5B"
            ),
        ),
        dict(
            name="ProsperoMgr",
            repo="notmaj0r/ProsperoMgr",
            match=["ProsperoMgr.elf"],
            category="SISTEMA",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Gestor web AIO para archivos, payloads, PKG, saves, procesos, "
                "autoload y datos del sistema. Release oficial estable"
            ),
        ),
        dict(
            name="PS5 Game Compressor",
            repo="gcoding97/PS5-Game-Compressor",
            match=["game-compressor.elf"],
            category="JUEGOS / COMPATIBILIDAD",
            channels=["stable"],
            single_latest=True,
            elf_only=True,
            desc=(
                "Fork mantenido de PS5 Game Compressor para comprimir, descomprimir, "
                "validar y reparar juegos usados con ShadowMountPlus"
            ),
        ),
    ])

    curated = ns["CURATED_STATUS"]
    curated["etaHEN 13.60"] = [
        (
            r".*",
            "NO OFICIAL / FW 13.60",
            "Port r3 validado en hardware 13.60. No usar como sustituto general de etaHEN oficial.",
        )
    ]
    curated["PS5 App Dumper"] = [
        (r".*", "BETA / UTIL", "La rama 2.x sigue marcada beta por upstream.")
    ]
    curated["PS5LM"] = [
        (r".*", "EXPERIMENTAL / LOCAL", "Proyecto nuevo; modelos pequenos y ejecucion local en PS5.")
    ]
    curated["ProsperoMgr"] = [
        (r".*", "ESTABLE", "Release oficial estable desde el upstream del autor.")
    ]
    curated["PS5 Game Compressor"] = [
        (r".*", "ESTABLE", "Fork mantenido; usar la release oficial mas reciente.")
    ]



def force_ascii_descriptions(ns):
    import unicodedata

    old_make_entry = ns["make_entry"]

    def clean_description(value):
        value = str(value or "")
        value = value.replace("ñ", "n").replace("Ñ", "N")
        value = unicodedata.normalize("NFKD", value)
        value = "".join(ch for ch in value if not unicodedata.combining(ch))
        return value

    def make_entry_ascii(app, rel, p, ch):
        entry = old_make_entry(app, rel, p, ch)
        entry["description"] = clean_description(entry.get("description", ""))
        return entry

    ns["make_entry"] = make_entry_ascii


def main():
    # 1) Cargamos el actualizador que está ahora mismo en HiddenKernel.
    current = load_current_wrapper()

    # 2) Ese actualizador es un wrapper sobre la base anterior; reproducimos
    #    exactamente su construcción para no perder ninguna mejora ya presente.
    ns = current["load_base_namespace"]()
    current["extend_hiddenkernel"](ns)

    # 3) Limpiamos duplicados obsoletos sin borrar el historico FPKG TEST/LEGACY.
    clean_obsolete_entries(ns)

    # 4) Anadimos solo la seleccion nueva que merece la pena y tiene ELF.
    add_curated_evox_elf(ns)

    # 5) Mantenimiento v2: upstreams oficiales, sustituciones y limpieza definitiva.
    apply_hiddenkernel_v2_maintenance(ns)

    # 6) Saneamos TODAS las descripciones para Payload Manager:
    #    sin tildes ni otros diacriticos y con n en lugar de enie.
    force_ascii_descriptions(ns)

    # 7) Ejecutamos el generador normal de HiddenKernel.
    ns["main"]()


if __name__ == "__main__":
    main()
