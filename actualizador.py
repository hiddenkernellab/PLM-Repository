#!/usr/bin/env python3
# HiddenKernel actualizador - escena PS5 2026-09-29.
#
# Parte de la version de actualizador.py que estaba en main en el commit
# d0ad55cc1335e432c3088fdf9e51ed7ee2d92bd3, aplica las novedades de hoy y
# ejecuta el generador normal de HiddenKernel.
#
# Añade:
# - PS5 WebKit Autoloader oficial itsPLK (descripcion/compatibilidad Relapse)
# - PSVietHoa WebKit Autoloader
# - WK Autoloader Relapse de X-F1REBALL-X
# - LegacyJB
# - Jailbreak Store de notmaj0r

import urllib.request

BASE_URL = (
    "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/"
    "d0ad55cc1335e432c3088fdf9e51ed7ee2d92bd3/actualizador.py"
)


def download_base():
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


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"No se encontro el bloque esperado: {label}")
    return text.replace(old, new, 1)


def patch_base(s):
    old = """    dict(name="PS5 WebKit Autoloader", repo="itsPLK/ps5-webkit-autoloader",
         match=["webkit-autoloader-installer"], exclude=["host"], category="SISTEMA",
         desc=("Autoloader WebKit para lanzar de forma automatica el exploit y los payloads.")),
    dict(name="ps5-payload-websrv", repo="ps5-payload-dev/websrv","""

    new = """    dict(name="PS5 WebKit Autoloader", repo="itsPLK/ps5-webkit-autoloader",
         match=["webkit-autoloader-installer"], exclude=["host"], category="SISTEMA",
         desc=("Autoloader WebKit oficial de itsPLK. Integra Relapse para FW 7.00-13.60 "
               "y umtx2 para FW 1.00-5.50, con instalacion en Media y carga automatizada "
               "de payloads.")),
    dict(name="PSVietHoa WebKit Autoloader",
         repo="thanhsondev/psviethoa-webkit-autoloader",
         match=["psviethoa-webkit-autoloader-installer"], exclude=["host"],
         category="SISTEMA", channels=["stable"], single_latest=True,
         desc=("Fork independiente del WebKit Autoloader con Relapse para FW 7.00-13.60 "
               "y umtx2 para FW 1.00-5.50. Usa Title ID PSVH00001 y puede convivir "
               "con el WebKit Autoloader oficial.")),
    dict(name="WK Autoloader Relapse (X-F1REBALL-X)",
         repo="X-F1REBALL-X/wk-autoloader-relapse",
         match=["installer"], category="SISTEMA",
         channels=["stable"], single_latest=True,
         desc=("Variante con Relapse para FW 7.00-13.60 y umtx2 para FW 1.00-5.50. "
               "Permite elegir Payload Manager en 8084 o Elf Launcher en 1000, recuerda "
               "la seleccion y usa Title ID SLKT00001 para convivir con otros autoloaders.")),
    dict(name="LegacyJB",
         repo="Phoenixx1202/LegacyJB",
         match=["legacyjb"], prefer=[".bin"], category="SISTEMA",
         channels=["stable"], single_latest=True,
         desc=("Payload Legacy Jailbreak de Phoenixx1202. Spectrum Library lo necesita "
               "para la funcion Homebrew si no se usa etaHEN con Jailbreak Legacy activado. "
               "Se sigue automaticamente la ultima release estable.")),
    dict(name="Jailbreak Store",
         repo="notmaj0r/JailbreakStore",
         match=["jailbreakstore"], category="SISTEMA",
         channels=["stable"], single_latest=True,
         desc=("Payload que transforma el acceso de PlayStation Store NPXS40047 en un "
               "lanzador WebView personalizado. El autor advierte de que modifica la base "
               "de datos de PS5 y que una corrupcion puede hacer perder FPKG de PS4.")),
    dict(name="ps5-payload-websrv", repo="ps5-payload-dev/websrv","""

    s = replace_once(s, old, new, "APPS / WebKit autoloaders")

    old = """    "PS5 WebKit Autoloader": [
        (r"\\b0\\.4\\.0\\b", "PRECAUCIÓN",
         "Release oficial actual, pero hay reportes públicos de kernel panic/apagados en algunos firmwares 12.x; varios usuarios indican mejor comportamiento al volver a 0.3.1."),
    ],"""

    new = """    "PS5 WebKit Autoloader": [
        (r"\\b0\\.5\\.0\\b", "EN PRUEBAS",
         "Primera integracion oficial de Relapse. El propio desarrollador la presenta como soporte inicial y recomienda valorar 0.4.0 en FW 7.00-12.00 si ya funciona bien."),
        (r"\\b0\\.4\\.0\\b", "PRECAUCIÓN",
         "Release oficial anterior; existen reportes publicos de kernel panic/apagados en algunos firmwares 12.x."),
    ],
    "Jailbreak Store": [
        (r".*", "PRECAUCIÓN",
         "El autor advierte expresamente de que modificar la base de datos puede corromperla y provocar la perdida de FPKG de PS4."),
    ],"""

    s = replace_once(s, old, new, "CURATED_STATUS")

    old = """    "PS5 WebKit Autoloader": [
        (r".*", "FW 1.00-5.50 y 7.00-12.70"),
    ],"""

    new = """    "PS5 WebKit Autoloader": [
        (r".*", "FW 1.00-5.50 y 7.00-13.60"),
    ],
    "PSVietHoa WebKit Autoloader": [
        (r".*", "FW 1.00-5.50 y 7.00-13.60"),
    ],
    "WK Autoloader Relapse (X-F1REBALL-X)": [
        (r".*", "FW 1.00-5.50 y 7.00-13.60"),
    ],"""

    s = replace_once(s, old, new, "COMPATIBILITY_RULES")

    old = """    if name == "PS5 WebKit Autoloader":
        # Upstream, itsPLK mirror y Nexgen coinciden en esta convención.
        return f"webkit-autoloader-installer_{_ensure_v(raw)}.elf"
    if name == "ftpsrv":"""

    new = """    if name == "PS5 WebKit Autoloader":
        # Upstream, itsPLK mirror y Nexgen coinciden en esta convención.
        return f"webkit-autoloader-installer_{_ensure_v(raw)}.elf"
    if name == "WK Autoloader Relapse (X-F1REBALL-X)":
        # Upstream publica un nombre generico (installer.elf); HiddenKernel lo
        # hace unico para no compartir carpeta con otros instaladores.
        return f"wk-autoloader-relapse_{_ensure_v(raw)}.elf"
    if name == "ftpsrv":"""

    s = replace_once(s, old, new, "canonical_repo_filename")

    old = """        "PS5 WebKit Autoloader": "webkit-autoloader-installer",
        "kstuff-lite": "kstuff-lite","""

    new = """        "PS5 WebKit Autoloader": "webkit-autoloader-installer",
        "WK Autoloader Relapse (X-F1REBALL-X)": "wk-autoloader-relapse",
        "kstuff-lite": "kstuff-lite","""

    s = replace_once(s, old, new, "expected_storage_root")
    return s


code = patch_base(download_base())
exec(compile(code, BASE_URL, "exec"), globals(), globals())
