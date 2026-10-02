#!/usr/bin/env python3
# HiddenKernel actualizador - escena PS5 2026-10-02.
#
# Parte de la version de actualizador.py que estaba en main en el commit
# d0ad55cc1335e432c3088fdf9e51ed7ee2d92bd3, aplica las novedades posteriores
# y ejecuta el generador normal de HiddenKernel.
#
# Añade / corrige:
# - PS5 WebKit Autoloader oficial itsPLK
# - PSVietHoa WebKit Autoloader
# - WK Autoloader Relapse de X-F1REBALL-X
# - LegacyJB
# - Jailbreak Store de notmaj0r
# - Kstuff FPKG Drakmor: sigue la rama experimental desde evoX-CoreOS
#   (incluido kstuff-fpkg-1.13-dr-test5)
# - Mantiene ShadowMountPlus FPKG en la beta mas reciente publicada por Drakmor

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

    # La rama FPKG de Drakmor ya no se toma del indice viejo de
    # PS5-Super-PLDMGR-Auto-Updater. Nexgen la publica y la usa para pruebas
    # en evoX-CoreOS; ahi esta el test5 y futuras revisiones.
    old = """    dict(name="FPKG Integrado - Kstuff Drakmor", optional=True,
         catalog_url=("https://raw.githubusercontent.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater/main/"
                      "json/PS5_Beta.json"),
         catalog_name_regex=[r"^Kstuff .* Fpkg Dr Test\\d+$"],
         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",
         category="FPKG INTEGRADO",
         status="EXPERIMENTAL / FPKG",
         compatibility="FW 1.00-11.60 en test3; validar builds futuras",
         desc=("Rama Kstuff de pruebas FPKG de Drakmor con el flujo PPR/A53 integrado. "
               "Se mantiene separada de kstuff-lite oficial.")),"""

    new = """    dict(name="FPKG Integrado - Kstuff Drakmor", optional=True,
         catalog_url=("https://raw.githubusercontent.com/nexgen999/evoX-CoreOS/main/"
                      "json/payloads/PS5_Beta.json"),
         catalog_name_regex=[r"^Kstuff[- _].*[- _]Fpkg[- _]Dr[- _]Test\\d+$"],
         source="https://github.com/nexgen999/evoX-CoreOS",
         category="FPKG INTEGRADO",
         status="EXPERIMENTAL / FPKG",
         compatibility="FPKG hasta FW 11.60; usar exFAT por encima",
         desc=("Rama Kstuff de pruebas FPKG de Drakmor con A53/PPR integrado. "
               "Se sigue desde el catalogo evoX-CoreOS que usa Nexgen para las pruebas. "
               "Se mantiene separada de kstuff-lite oficial.")),"""

    s = replace_once(s, old, new, "FPKG Kstuff Drakmor -> evoX-CoreOS")

    # El generador viejo forzaba cualquier kstuff 1.13 testX a la carpeta
    # Internal del repositorio antiguo. Eso rompe test5 porque no existe alli.
    # Si evoX ofrece local_path, usamos el RAW del propio evoX-CoreOS y dejamos
    # que el checksum del catalogo lo valide.
    old = """    if filename.startswith("kstuff-1.13-fpkg-dr-test"):
        url = nexgen_raw + "Internal/payloads/beta/Kstuff-Darkmor/" + filename
    elif filename.startswith("a53_ppr_install_"):"""

    new = """    if filename.startswith("kstuff-1.13-fpkg-dr-test"):
        local_path = str(hit.get("local_path") or "").lstrip("/")
        if local_path:
            url = (
                "https://raw.githubusercontent.com/nexgen999/evoX-CoreOS/main/"
                + local_path
            )
        else:
            url = nexgen_raw + "Internal/payloads/beta/Kstuff-Darkmor/" + filename
    elif filename.startswith("a53_ppr_install_"):"""

    s = replace_once(s, old, new, "descarga RAW Kstuff FPKG test5")

    return s


code = patch_base(download_base())
exec(compile(code, BASE_URL, "exec"), globals(), globals())
