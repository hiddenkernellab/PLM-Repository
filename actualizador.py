#!/usr/bin/env python3
import hashlib
import io
import json
import os
import re
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

UA = "HiddenKernel-Store/1.0"
TOKEN = os.getenv("GITHUB_TOKEN", "")
PAGES = "https://hiddenkernellab.github.io/PLM-Repository"
MIRROR = Path("payloads")

APPS = [
    # ESENCIALES
    dict(name="PS5 Payload Manager", repo="itsPLK/ps5-payload-manager",
         match=["pldmgr"], exclude=["debug"], category="ESENCIALES",
         desc=("Gestor web para instalar, ordenar, ejecutar y actualizar payloads y "
               "configurar el autoload desde PS5, PC o un telefono.")),
    dict(name="kstuff-lite", repo="EchoStretch/kstuff-lite",
         match=["kstuff"], exclude=["debug"], category="ESENCIALES",
         desc=("Kstuff ligero que aplica los parches necesarios para el entorno homebrew. "
               "Se usa habitualmente junto con ShadowMountPlus."),
         channels=["beta"]),
    dict(name="ShadowMountPlus", repo="drakmor/ShadowMountPlus",
         match=["shadowmount"], archive=["shadowmount"], category="ESENCIALES",
         desc=("Monta y registra juegos desde almacenamiento interno o externo. "
               "Se mantiene la rama 1.6beta16 y las 1.7 alpha por separado."),
         stable_override=r"(?i)^1\.6beta16$",
         exclude_versions=[r"(?i)^v?1\.4(?:\D|$)"],
         always_alpha=True),
    dict(name="nanoDNS", repo="drakmor/nanoDNS",
         match=["nanodns"], category="ESENCIALES",
         desc=("DNS local para bloquear dominios de PSN y actualizaciones, con "
               "redirecciones configurables desde la propia consola.")),

    # HEN / AIO
    dict(name="OnionHEN", repo="aydencharles/onionHEN",
         match=["onionhen"], archive=["onionhen"], category="HEN / AIO",
         desc=("HEN AIO con Toolbox, trucos, overlays y servicios integrados.")),
    dict(name="etaHEN", repo="etaHEN/etaHEN",
         match=["etahen"], category="HEN / AIO",
         desc=("HEN AIO con Toolbox, plugins, trucos y servicios integrados.")),
    dict(name="PIZZA-HEN", repo="Michele-M-Media/PIZZA-HEN",
         match=["pizza"], archive=["pizza"], category="HEN / AIO",
         desc=("HEN AIO con KStuff, ShadowMount, Toolbox, FTP, ps5debug-NG "
               "e instalador de PKG. Algunas funciones son experimentales.")),

    # GESTIÓN
    dict(name="PLDMGR Install & Update", repo="hiddenkernellab/PLDMGR-install-update",
         match=["hk-pldmgr-install-update"], category="SISTEMA",
         install_filename="HK-PLDMGR-Install-Update.elf",
         desc=("Instala, repara y actualiza PS5 Payload Manager y vuelve a crear "
               "su archivo de autoload.")),
    dict(name="PS5 WebKit Autoloader", repo="itsPLK/ps5-webkit-autoloader",
         match=["webkit-autoloader-installer"], exclude=["host"], category="SISTEMA",
         desc=("Autoloader WebKit para lanzar de forma automatica el exploit y los payloads.")),
    dict(name="ProsperoMgr",
         catalog_url=("https://nexgen999.github.io/PS5-Super-PLDMGR-Auto-Updater/"
                      "json/ps5_hen_loader.json"),
         catalog_names=["ProsperoMgr", "Prospero Manager"],
         source="https://github.com/notmaj0r/ProsperoMgr",
         category="SISTEMA",
         desc=("Gestor web AIO para archivos, payloads, PKG, saves, procesos, "
               "autoload y datos del sistema.")),
    dict(name="ELF Arsenal",
         api="https://git.etawen.dev/api/v1/repos/soniciso/elf-arsenal/releases",
         source="https://git.etawen.dev/soniciso/elf-arsenal/releases",
         match=["elf-arsenal"], category="SISTEMA",
         desc=("AIO con muchas herramientas y payloads integrados. Proyecto discontinuado; "
               "se conserva por su utilidad en sistemas ya configurados.")),

    # ARCHIVOS / PC
    dict(name="BFpilot", repo="ItsBlurf/BFpilot",
         match=["bfpilot"], exclude=["alpha", "installer", "lite"], category="ARCHIVOS / PC",
         desc=("Explorador web AIO para mover archivos, extraer ZIP/RAR/7z "
               "e instalar PKG locales.")),
    dict(name="PS5 Web File Manager", repo="owendswang/ps5-web-file-manager",
         match=["web-file-mgr"], category="ARCHIVOS / PC",
         desc=("Explorador web ligero para mover archivos desde la red local "
               "e instalar PKG.")),
    dict(name="ftpsrv", repo="ps5-payload-dev/ftpsrv",
         match=["ftpsrv"], prefer=["ps5"], exclude=["ps4", "install"],
         category="ARCHIVOS / PC",
         desc=("Servidor FTP ligero para acceder a los archivos de la PS5 desde PC o telefono.")),
    dict(name="ps5upload", repo="phantomptr/ps5upload",
         match=["ps5upload"], category="ARCHIVOS / PC",
         desc=("Transfiere archivos entre PS5 y PC/Android con control de integridad y soporte para reanudar envios.")),

    # JUEGOS / COMPATIBILIDAD
    dict(name="PS5 Game Compressor", repo="juma-sayeh/PS5-Game-Compressor",
         match=["game-compressor"], category="JUEGOS / COMPATIBILIDAD",
         desc=("Comprime, descomprime, valida y repara juegos usados con "
               "ShadowMountPlus y ofrece funciones para APR Emu.")),
    dict(name="APR Emu Updater", repo="tsuramatsu1/apr-emu-updater",
         match=["apr_emu_updater"], category="JUEGOS / COMPATIBILIDAD",
         desc=("Gestiona APR Emu por juego y su uso junto con ShadowMountPlus.")),
    dict(name="PS5 App Dumper", repo="EchoStretch/ps5-app-dumper",
         match=["app", "dumper"], archive=["dumper"], category="JUEGOS / COMPATIBILIDAD",
         desc=("Vuelca aplicaciones y juegos PS5 para copias de seguridad y "
               "flujos de compatibilidad.")),

    # UTILIDADES
    dict(name="Lapy JB Daemon", repo="ArkSama/PS5-Lapy-JB-Daemon",
         match=["lapy", "daemon"], category="UTILIDADES",
         desc=("Da acceso jailbreak bajo demanda a apps compatibles con la API de etaHEN. Requiere kstuff.")),
    dict(name="garlic-savemgr",
         api="https://git.etawen.dev/api/v1/repos/earthonion/garlic-savemgr/releases",
         source="https://git.etawen.dev/earthonion/garlic-savemgr/releases",
         match=["garlic-savemgr"], exclude=["worker"], category="UTILIDADES",
         desc=("Gestor de saves para copiar, importar, descifrar, cifrar "
               "y volver a firmar partidas.")),
    dict(name="np-fake-signin", repo="earthonion/np-fake-signin",
         match=["np", "fake", "signin"], prefer=["ps5"], exclude=["ps4"],
         archive=["np-fake-signin"], category="UTILIDADES",
         install_filename="np-fake-signin.elf",
         desc=("Simula el acceso a PSN para el usuario activo. "
               "Requiere una cuenta activada offline y reiniciar al terminar.")),
    dict(name="Common FPS for PS5", repo="porhe911/Common-FPS-for-PS5",
         match=["common", "fps"], exclude=["plugin"], archive=["common"],
         category="UTILIDADES",
         desc=("Muestra los FPS en tiempo real en juegos PS4/PS5. "
               "Disponible como ELF y como plugin para etaHEN.")),

    # MANDOS
    dict(name="Ghostcontrol", repo="StonedModder/Ghostcontrol-PS5-USB-Controller-Patcher",
         match=["ghost-control-ps5"], category="MANDOS",
         desc=("Permite usar varios mandos USB de terceros mediante un DualSense virtual.")),

    # DESCARGAS
    dict(name="Pegasus DL", repo="pegasus-ps5/pegasus-dl",
         match=["pegasus"], category="DESCARGAS",
         desc=("Gestor de descargas web. Desde 1.8.0 puede enviar enlaces .pkg "
               "al descargador nativo de PS5.")),
    dict(name="Spectrum Library", repo="Phoenixx1202/Spectrum-Library",
         match=["spectrum"], archive=["spectrum"], category="DESCARGAS",
         desc=("Biblioteca y gestor de descargas con portadas, grupos, cola "
               "y selector de destino.")),
]

FIXED = [
    dict(
        name="etaHEN",
        filename="etaHEN-2.6B.bin",
        url=("https://raw.githubusercontent.com/zecoxao/zecoxao.github.io/"
             "main/luasauce/payloads/etaHEN-2.6B.bin"),
        source=("https://github.com/zecoxao/zecoxao.github.io/blob/"
                "main/luasauce/payloads/etaHEN-2.6B.bin"),
        version="2.6B",
        date="2026-08-18",
        channel="beta",
        category="HEN / AIO",
        status=("BUILD DE PRUEBAS; esta build caduca el 1 de octubre de 2026"),
        desc=("Build de pruebas de etaHEN con Toolbox, plugins, trucos y servicios integrados.")
    ),
]

CAT_ORDER = {"ESENCIALES": 0, "HEN / AIO": 1, "SISTEMA": 2, "ARCHIVOS / PC": 3, "JUEGOS / COMPATIBILIDAD": 4, "UTILIDADES": 5, "MANDOS": 6, "DESCARGAS": 7}

# Capa de curación basada en documentación/release notes del desarrollador y
# feedback público concreto. Las reglas son VERSION-ESPECÍFICAS: cuando cambia
# la versión dejan de aplicarse y entra la valoración automática de la nueva
# release, evitando arrastrar una reputación antigua a un binario nuevo.
CURATED_STATUS = {
    "ProsperoMgr": [
        (r".*", "BETA ACTIVA / SUCESOR ACTUAL",
         "Prospero Manager apareció a finales de agosto como sucesor funcional de ELF Arsenal. Integra gestión de archivos, payloads, PKG, saves y autoload; sigue siendo una beta joven y conviene mantener backups."),
    ],
    "ELF Arsenal": [
        (r"\b1\.6\.22\b", "LEGACY / PRECAUCIÓN",
         "ELF Arsenal está discontinuado. Sigue siendo útil para setups existentes, pero hubo reportes recientes de kernel panics y problemas graves de datos/configuración; para instalaciones nuevas es preferible usar herramientas modulares o Prospero Manager."),
    ],
    "PS5 Web File Manager": [
        (r"\b1\.7\b", "ACTIVO / RECIENTE",
         "Proyecto activo con release 1.7 a finales de agosto. Las versiones recientes añadieron y corrigieron instalación de PKG desde almacenamiento interno."),
    ],
    "APR Emu Updater": [
        (r"\b2\.0\.6\b", "ACTIVO / RECOMENDADO CON APR EMU",
         "Release 2.0.6 del 29 de agosto corrige detección de ShadowMountPlus y notificaciones; la 2.0.5 corrigió pérdida de registros y fallos del override tras reposo."),
    ],
    "PS5 App Dumper": [
        (r"\b1\.11\b", "BETA OFICIAL",
         "Release oficial 1.11 Beta; corrige archivos PlayGo ausentes y amplía soporte declarado hasta FW 13.60."),
    ],
    "Lapy JB Daemon": [
        (r"\b1\.2\b", "ÚTIL EN STACK MODULAR",
         "Se usa para dar jailbreak-on-demand a apps que esperan la API de etaHEN sin cargar etaHEN completo. El desarrollador documenta FW 3.00-12.00 con kstuff."),
    ],
    "BFpilot": [
        (r"\b0\.4\.4\b", "VALIDADO EN HARDWARE",
         "La release 0.4.4 pasó la suite 44/44 y pruebas de reinyección, instalación PKG, archivos comprimidos y transferencias en PS5 FW 11.60."),
    ],
    "PS5 File Explorer": [
        (r"0\.2\.1", "BUILD CORE RECOMENDADA",
         "El desarrollador recomienda file-explorer-core.elf como primera opción para máxima compatibilidad; la build completa añade el launcher y más dependencias."),
    ],
    "ChronicLoader": [
        (r"\b0\.1\b", "RELEASE INICIAL / PRECAUCIÓN",
         "Primera release pública. El payload gestiona backups, hashes y autoload; el propio autor advierte específicamente que su HTML generador de configuración estaba apenas probado."),
    ],
    "VoidShell": [
        (r"\b1\.1", "RELEASE OFICIAL",
         "Release pública del dashboard/daemon. La API de gestión está pensada para la LAN; conviene no exponer una PS5 modificada a redes no confiables."),
    ],
    "PS5 BackPork": [
        (r"\b0\.1\b", "USO AVANZADO / PRECAUCIÓN",
         "El desarrollador recomienda sideload de las mínimas librerías posibles y advierte que no puede garantizar ausencia de efectos secundarios."),
    ],
    "Ghostcontrol": [
        (r"\b1\.0\.5\b", "VALIDACIÓN PARCIAL EN HARDWARE",
         "La release 1.0.5 amplía soporte y el proyecto mantiene una matriz de mandos con estados Working/Untested; la compatibilidad depende del modelo y modo USB."),
    ],
    "ps5debug-NG": [
        (r"\b1\.3\.0\b", "VALIDACIÓN PARCIAL EN HARDWARE",
         "La release 1.3.0 se publica como hardware-verified, pero sus propias notas aclaran que algunas familias de firmware compatibles aún no estaban completamente probadas en hardware."),
    ],
    "ps5upload": [
        (r"\b5\.17\.", "VALIDACIÓN PARCIAL EN HARDWARE",
         "El desarrollador documenta pruebas de hardware en FW 5.10 y 9.60. El payload cubre más firmwares, pero la instalación PKG tiene limitaciones conocidas en algunos FW 11.60+ y depende de kstuff/fpkg-enable."),
    ],
    "bdj_unpatch": [
        (r"\b2\.0\b", "USO ESPECÍFICO / PRECAUCIÓN",
         "Está pensado para habilitar el flujo BD-JB5 en firmwares altos sobre una consola ya jailbreakeada. Modifica bdjstack.jar, crea backup y una reinstalación de firmware elimina el parche."),
    ],
    "ps5-payload-websrv": [
        (r"\b0\.33\b", "RELEASE OFICIAL",
         "Release oficial del servidor web. Su función es servir navegación/launch remoto; la estabilidad de homebrew lanzado también depende del payload previo y del estado de la consola."),
    ],
    "PLDMGR Install & Update": [
        (r"0\.1\.", "EN PRUEBAS",
         "Primera serie de pruebas de HiddenKernel; validar en consola antes de considerarla madura."),
    ],
    "PS5 WebKit Autoloader": [
        (r"\b0\.4\.0\b", "PRECAUCIÓN",
         "Release oficial actual, pero hay reportes públicos de kernel panic/apagados en algunos firmwares 12.x; varios usuarios indican mejor comportamiento al volver a 0.3.1."),
    ],
    "etaHEN": [
        (r"\b2\.5B\b", "RELEASE OFICIAL",
         "Versión oficial para FW hasta 10.01. Para firmwares posteriores se usa la rama 2.6B de pruebas."),
    ],
    "OnionHEN": [
        (r"\b0\.0\.12\b", "RELEASE OFICIAL",
         "Release oficial con soporte declarado para FW 4.03-12.70; no hay una advertencia general de inestabilidad en sus notas actuales."),
    ],
    "PIZZA-HEN": [
        (r"\b2\.00\b", "VALIDACIÓN ESTÁTICA / EXPERIMENTAL",
         "El propio proyecto define v2.00 como software experimental y señala que el checkpoint I18N tiene PASS estático, no una nueva validación completa en hardware."),
        (r"\b1\.0\b", "VALIDACIÓN PARCIAL EN HARDWARE",
         "El desarrollador confirmó en hardware la ruta DPIv2 en FW 12.20-12.70; el acceso directo CheatRunner de Game Options se mantiene experimental."),
        (r"\b0\.1\b", "EXPERIMENTAL",
         "El desarrollador la publicó expresamente como primera beta pública y software experimental."),
    ],
    "kstuff-lite": [
        (r"\b1\.10\b", "EN PRUEBAS",
         "La versión 1.10 fue publicada como Beta; las notas indican mejoras de estabilidad/rendimiento y soporte hasta FW 12.70, pero el desarrollador no la presenta como estable."),
    ],
    "ShadowMountPlus": [
        (r"1\.6beta16", "MÁS PROBADA",
         "Sigue siendo la rama práctica más conservadora: otras herramientas la usan como baseline y existen reportes de usuarios que volvieron a 1.6beta16 tras problemas con 1.7 alpha."),
        (r"1\.7alpha13fix1", "EXPERIMENTAL / PRECAUCIÓN",
         "Pre-release alpha. Corrige un cierre de Shell y apagados inesperados en FW 12+, pero el propio desarrollador mantiene la rama 1.7 como experimental."),
        (r"1\.7alpha", "EXPERIMENTAL",
         "Rama alpha de desarrollo; prioriza funciones/correcciones nuevas y no debe presentarse como la opción más estable."),
    ],
    "APR Emu Updater": [
        (r"\b2\.0\.6\b", "RELEASE DE CORRECCIONES",
         "Corrige problemas de notificaciones/detección y mantiene compatibilidad con el método antiguo en ShadowMountPlus 1.6beta16 o anterior; las funciones 1.7 usan el nuevo slot de emulación."),
    ],
    "PS5 Game Compressor": [
        (r"\b1\.0\.4\b", "RELEASE DE COMPATIBILIDAD",
         "Añade compatibilidad y corrige flujos APR-EMU, firmware 4.51 y relanzado del servidor; no hay base para llamarla estable absoluta."),
        (r"\b1\.0\.3\b", "MEJORA DE ESTABILIDAD",
         "El propio desarrollador la describe como una pequeña release de estabilidad, con correcciones de fiabilidad USB-a-USB y reparación de imágenes FFPFSC."),
    ],
    "PS5 App Dumper": [
        (r"\b1\.11\b", "EN PRUEBAS",
         "La release oficial se denomina 'PS5 App Dumper 1.11 Beta'; corrige archivos PlayGo ausentes y amplía soporte hasta FW 13.60."),
    ],
    "np-fake-signin": [
        (r"\b0\.[12]_?beta\b", "EXPERIMENTAL / PRECAUCIÓN",
         "Las antiguas releases beta indican explícitamente que podían contener fallos y que aún no estaban probadas en PS5."),
    ],
    "PoorDS4": [
        (r"rc38", "VALIDACIÓN PARCIAL EN HARDWARE",
         "FW 11.60 está probado con varios juegos, reconexiones, cambio de juego, multijugador y limpieza de reposo; 8.60 y 12.40 conservan validación estructural pero requieren más prueba RC38 en hardware."),
    ],
    "Common FPS for PS5": [
        (r"\b1\.1\.0\b", "VALIDADO EN HARDWARE",
         "El proyecto documenta pruebas repetidas en PS5 FW 9.60, contador visible en dos juegos y reinicios normales; no debe extrapolarse esa validación a todos los firmwares."),
    ],
    "Pegasus DL": [
        (r"\b1\.8\.0\b", "RELEASE OFICIAL",
         "Release oficial actual con handoff nativo de enlaces .pkg; no hay una advertencia general de inestabilidad en las notas de esta versión."),
    ],
    "Spectrum Library": [
        (r"\b1\.4\.4\b", "MEJORA DE ESTABILIDAD",
         "Las notas de la versión mejoran la estabilidad de descargas grandes, reintentos/reanudación y manejo de interrupciones de red."),
    ],
}

RISK_TERMS = (
    "kernel panic", "kernel panics", "crash", "crashes", "crashing",
    "freeze", "freezes", "freezing", "shutdown", "shut down",
    "unexpectedly shuts", "unexpected shutdown", "black screen",
    "hang", "hangs", "hanging", "panic", "reboot loop"
)

MAX_DESCRIPTION = 420

# Compatibilidad solo cuando está confirmada por el desarrollador, release notes
# o pruebas de hardware documentadas. Las reglas son específicas de versión.
COMPATIBILITY_RULES = {
    "kstuff-lite": [
        (r"\b1\.10\b", "FW 3.00-12.70"),
        (r"\b1\.0[5-9]\b", "FW 3.00-12.70"),
    ],
    "OnionHEN": [
        (r"\b0\.0\.1[0-2]\b", "FW 4.03-12.70"),
        (r"\b0\.0\.9\b", "FW 4.03-12.70"),
    ],
    "etaHEN": [
        (r"\b2\.5B\b", "hasta FW 10.01"),
    ],
    "PS5 WebKit Autoloader": [
        (r".*", "FW 1.00-5.50 y 7.00-12.70"),
    ],
    "Lapy JB Daemon": [
        (r"\b1\.2\b", "FW 3.00-12.00"),
    ],
    "PS5 App Dumper": [
        (r"\b1\.11\b", "hasta FW 13.60"),
    ],
    "PIZZA-HEN": [
        (r"\b1\.0\b", "DPIv2 en hardware: FW 12.20-12.70"),
    ],
    "BFpilot": [
        (r"\b0\.4\.4\b", "pruebas en hardware: FW 11.60"),
    ],
    "ps5upload": [
        (r".*", "FW 1.00-12.70; probado en hardware en 5.10, 9.60 y 12.20"),
    ],
}

def compatibility_for(app, rel):
    text = rtext(rel)
    for pattern, value in COMPATIBILITY_RULES.get(app["name"], []):
        if re.search(pattern, text, flags=re.I):
            return value

    # Detección automática conservadora desde las notas oficiales.
    body = clean_md(rel.get("body") or "")
    patterns = [
        r"supported firmware[: ]+([0-9.]+\s*[–-]\s*[0-9.]+)",
        r"supports firmware[: ]+([0-9.]+\s*[–-]\s*[0-9.]+)",
        r"firmware[: ]+([0-9.]+\s*[–-]\s*[0-9.]+)",
        r"firmware\s+([0-9.]+)\s+(?:through|to)\s+([0-9.]+)",
    ]

    for rx in patterns:
        m = re.search(rx, body, flags=re.I)
        if not m:
            continue
        if len(m.groups()) == 1:
            return f"FW {m.group(1).replace('–', '-')}"
        return f"FW {m.group(1)}-{m.group(2)}"

    return ""

# Recomendaciones de comunidad revisadas manualmente.
# Caducan solas para no presentar como "actual" información vieja de redes/foros.
CURRENT_RECOMMENDATIONS = {
    "PS5 Payload Manager": {
        "until": "2026-10-25",
        "label": "RECOMENDADO ACTUAL",
        "note": "Se repite como centro de gestión en setups recientes y el propio proyecto recomienda usarlo con un autoloader."
    },
    "kstuff-lite": {
        "until": "2026-10-25",
        "label": "RECOMENDADO ACTUAL",
        "note": "Forma parte del núcleo modular más repetido actualmente junto a ShadowMountPlus."
    },
    "ShadowMountPlus": {
        "until": "2026-10-25",
        "label": "RECOMENDADO ACTUAL",
        "note": "Sigue siendo el mounter de referencia. La 1.6beta16 es la opción conservadora y las 1.7 alpha se muestran como experimentales."
    },
    "nanoDNS": {
        "until": "2026-10-25",
        "label": "RECOMENDADO ACTUAL",
        "note": "Se repite como complemento del stack ligero para bloquear servicios de Sony/actualizaciones desde la consola."
    },
    "OnionHEN": {
        "until": "2026-10-25",
        "label": "AIO ACTUAL",
        "note": "Alternativa AIO muy reciente y activa; varios usuarios reportan buen funcionamiento, aunque la estabilidad sigue variando por firmware."
    },
    "ProsperoMgr": {
        "until": "2026-10-25",
        "label": "NUEVO AIO A SEGUIR",
        "note": "La comunidad lo está señalando como sucesor de ELF Arsenal. Es muy completo, pero todavía es una beta joven."
    },
    "BFpilot": {
        "until": "2026-10-25",
        "label": "RECOMENDADO PARA ARCHIVOS",
        "note": "Aparece en setups recientes como opción rápida y práctica para mover/gestionar archivos y PKG."
    },
    "PS5 Web File Manager": {
        "until": "2026-10-25",
        "label": "ALTERNATIVA ACTIVA",
        "note": "Proyecto muy reciente y activo para gestión web de archivos, con releases nuevas durante agosto."
    },
    "ftpsrv": {
        "until": "2026-10-25",
        "label": "MUY USADO",
        "note": "Sigue apareciendo en configuraciones recientes porque es pequeño, simple y cumple bien como FTP."
    },
    "ps5upload": {
        "until": "2026-10-25",
        "label": "RECOMENDADO PARA PC/ANDROID",
        "note": "Proyecto muy activo para transferencias; las versiones 5.17.x han ido corrigiendo reintentos, espacio y fiabilidad."
    },
    "PS5 Game Compressor": {
        "until": "2026-10-25",
        "label": "RECOMENDADO ACTUAL",
        "note": "Muy citado en setups recientes como herramienta práctica para imágenes y juegos usados con ShadowMountPlus."
    },
    "APR Emu Updater": {
        "until": "2026-10-25",
        "label": "RECOMENDADO SI USAS APR EMU",
        "note": "Proyecto activo con varias correcciones a finales de agosto; tiene sentido para usuarios que usan el override APR Emu."
    },
    "garlic-savemgr": {
        "until": "2026-10-25",
        "label": "RECOMENDADO PARA SAVES",
        "note": "Mantener copias de las partidas es especialmente recomendable en un entorno jailbreak donde los KP siguen siendo posibles."
    },
    "Lapy JB Daemon": {
        "until": "2026-10-25",
        "label": "RECOMENDADO EN STACK MODULAR",
        "note": "Aparece en configuraciones recientes junto a Payload Manager, kstuff-lite y ShadowMountPlus para apps que necesitan jailbreak-on-demand."
    },
}
def current_recommendation(app_name):
    rec = CURRENT_RECOMMENDATIONS.get(app_name)
    if not rec:
        return ""

    try:
        today = datetime.utcnow().date()
        until = datetime.strptime(rec["until"], "%Y-%m-%d").date()
    except Exception:
        return ""

    if today > until:
        return ""

    return f'{rec["label"]}: {rec["note"]}'

def req(url, timeout=60):
    # Forzamos revalidación en cada ejecución: nada de reutilizar respuestas
    # antiguas de API/CDN cuando acaba de salir una release.
    h = {
        "User-Agent": UA,
        "Cache-Control": "no-cache, no-store, max-age=0",
        "Pragma": "no-cache",
    }
    if "api.github.com" in url:
        h["Accept"] = "application/vnd.github+json"
        h["X-GitHub-Api-Version"] = "2022-11-28"
        if TOKEN:
            h["Authorization"] = f"Bearer {TOKEN}"
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=h),
        timeout=timeout
    )

def get_json(url):
    with req(url, 30) as r:
        return json.load(r)

def get_bytes(url):
    with req(url, 180) as r:
        return r.read()

def api_url(app):
    return app.get("api") or f'https://api.github.com/repos/{app["repo"]}/releases?per_page=100'

def github_latest_url(app):
    if app.get("api") or not app.get("repo"):
        return None
    return f'https://api.github.com/repos/{app["repo"]}/releases/latest'

def source_url(app):
    if app.get("source"):
        return app["source"]
    if app.get("repo"):
        return f'https://github.com/{app["repo"]}/releases'
    return app.get("catalog_url", "")

def rtime(rel):
    raw = rel.get("published_at") or rel.get("created_at") or ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0

def rtext(rel):
    return f'{rel.get("tag_name","")} {rel.get("name","")}'.strip()

def channel(rel):
    t = rtext(rel).lower()
    if any(x in t for x in ("alpha", "experimental", "nightly", "canary", "test", "-dev", "_dev", " dev")):
        return "alpha"
    if any(x in t for x in ("beta", "preview", "release candidate", "-rc", "_rc", " rc")):
        return "beta"
    if rel.get("prerelease", False):
        return "beta"
    return "stable"

def valid(filename, app):
    n = Path(filename).name.lower()
    if not n.endswith((".elf", ".bin")):
        return False
    if any(x.lower() not in n for x in app.get("match", [])):
        return False
    if any(x.lower() in n for x in app.get("exclude", [])):
        return False
    return True

def asset_url(a):
    return a.get("browser_download_url") or a.get("download_url") or ""

def direct_asset(rel, app):
    xs = [a for a in rel.get("assets", []) if valid(a.get("name", ""), app)]
    pref = [x.lower() for x in app.get("prefer", [])]
    xs.sort(key=lambda a: (
        -sum(x in a.get("name","").lower() for x in pref),
        len(a.get("name","")), a.get("name","").lower()))
    return xs[0] if xs else None

def zip_asset(rel, app):
    xs = [a for a in rel.get("assets", []) if a.get("name","").lower().endswith(".zip")]
    terms = app.get("archive") or app.get("match", [])
    preferred = [a for a in xs if any(x.lower() in a.get("name","").lower() for x in terms)]
    xs = preferred or xs
    xs.sort(key=lambda a: (len(a.get("name","")), a.get("name","").lower()))
    return xs[0] if xs else None

def extract_elf(data, app):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xs = [m for m in z.namelist() if Path(m).name and valid(Path(m).name, app)]
        xs.sort(key=lambda m: (len(Path(m).name), Path(m).name.lower()))
        return (Path(xs[0]).name, z.read(xs[0])) if xs else None

def safe(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")

def _ensure_v(ver):
    ver = str(ver or "").strip()
    if ver and not ver.lower().startswith("v"):
        return "v" + ver
    return ver


def _strip_v(ver):
    ver = str(ver or "").strip()
    return re.sub(r"^[vV](?=\d)", "", ver)


def canonical_repo_filename(app, rel, original_filename):
    """
    Nombre con el que PLDMGR guarda el payload.

    Política HiddenKernel:
      1) Si el payload existe en el mirror oficial de itsPLK, imitamos EXACTAMENTE
         su convención de filename. Es la mejor referencia para convivir con la
         fuente predeterminada de Payload Manager.
      2) Si no está en el mirror oficial, usamos la convención ya extendida en
         repositorios PLDMGR (principalmente Nexgen) cuando la conocemos.
      3) Si no existe una convención conocida, conservamos el nombre del asset
         upstream sin inventar uno nuevo.

    IMPORTANTE: el campo version NO se fabrica aquí; display_version conserva el
    tag publicado por el desarrollador. De ese modo filename y version siguen dos
    responsabilidades distintas y se reducen falsos avisos de actualización.
    """
    name = app.get("name", "")
    raw = str(rel.get("tag_name") or rel.get("name") or "").strip()
    if not raw:
        return original_filename

    # Convenciones del mirror oficial de itsPLK / ecosistema PLDMGR.
    if name == "PS5 Payload Manager":
        return f"pldmgr_{_ensure_v(raw)}.elf"
    if name == "kstuff-lite":
        return f"kstuff-lite_{_ensure_v(raw)}.elf"
    if name == "nanoDNS":
        # itsPLK mirror: nanoDNS_0.4.elf (sin v y respetando mayúsculas).
        return f"nanoDNS_{_strip_v(raw)}.elf"
    if name == "etaHEN":
        # itsPLK mirror: etaHEN_2.5B.bin.
        return f"etaHEN_{_strip_v(raw)}.bin"
    if name == "PS5 WebKit Autoloader":
        # Upstream, itsPLK mirror y Nexgen coinciden en esta convención.
        return f"webkit-autoloader-installer_{_ensure_v(raw)}.elf"
    if name == "ftpsrv":
        return f"ftpsrv_{_ensure_v(raw)}.elf"
    if name == "PS5 App Dumper":
        return f"ps5-app-dumper_{_ensure_v(raw)}.elf"
    if name == "garlic-savemgr":
        return f"garlic-savemgr_{_ensure_v(raw)}.elf"
    if name == "PS5 Web File Manager":
        return f"ps5-web-file-manager_{_ensure_v(raw)}.elf"
    if name == "ps5upload":
        return f"ps5upload_{_ensure_v(raw)}.elf"

    if name == "ShadowMountPlus":
        v = _strip_v(raw)
        # Para la rama conservadora usamos EXACTAMENTE el nombre del mirror
        # oficial de itsPLK. Para 1.7, que el mirror oficial aún no publica,
        # seguimos la convención de Nexgen para evitar otra carpeta paralela.
        if v.lower().startswith("1.6beta16"):
            return f"ShadowMountPlus_{v}.elf"
        return f"shadowmountplus_{_ensure_v(v)}.elf"

    # Convenciones ampliamente usadas en repositorios PLDMGR cuando el mirror
    # oficial no ofrece todavía ese payload.
    known = {
        "BFpilot": ("BFpilot_", ".elf", True),
        "Lapy JB Daemon": ("Lapy-JB-Daemon_", ".elf", True),
        "PS5 Game Compressor": ("PS5-Game-Compressor_", ".elf", True),
        "APR Emu Updater": ("apr_emu_updater_", ".elf", True),
        "PIZZA-HEN": ("PIZZA-HEN_", ".elf", True),
        "OnionHEN": ("onionHEN_", ".elf", True),
        "Pegasus DL": ("pegasus-dl_", ".elf", True),
        "Spectrum Library": ("Spectrum-Library_", ".elf", True),
        "np-fake-signin": ("np-fake-signin_", ".elf", True),
        "Common FPS for PS5": ("Common_FPS_PS5_", ".elf", True),
        "Ghostcontrol": ("Ghostcontrol-PS5-USB-Controller-Patcher_", ".elf", True),
        "ELF Arsenal": ("ELF_Arsenal_", ".elf", True),
    }
    rule = known.get(name)
    if not rule:
        return original_filename

    prefix, suffix, force_v = rule
    ver = _ensure_v(raw) if force_v else raw
    return f"{prefix}{ver}{suffix}"


def expected_storage_root(item):
    """Raíz esperada según la convención elegida para el ecosistema PLDMGR."""
    name = str(item.get("name") or "")
    version = _strip_v(str(item.get("version") or ""))

    if name == "ShadowMountPlus":
        return "ShadowMountPlus" if version.lower().startswith("1.6beta16") else "shadowmountplus"

    return {
        "nanoDNS": "nanoDNS",
        "OnionHEN": "onionHEN",
        "PS5 WebKit Autoloader": "webkit-autoloader-installer",
        "PS5 Payload Manager": "pldmgr",
        "kstuff-lite": "kstuff-lite",
        "etaHEN": "etaHEN",
        "ftpsrv": "ftpsrv",
        "PS5 App Dumper": "ps5-app-dumper",
        "garlic-savemgr": "garlic-savemgr",
        "PS5 Web File Manager": "ps5-web-file-manager",
        "ps5upload": "ps5upload",
        "Pegasus DL": "pegasus-dl",
        "Spectrum Library": "Spectrum-Library",
    }.get(name)


def _pldmgr_storage_root(filename):
    """Replica la regla de PLDMGR v0.5.1 para obtener la carpeta del payload."""
    clean = str(filename or "")
    clean = re.sub(r"\.(?:elf|bin)$", "", clean, flags=re.I)
    m = re.search(r"[_-]v", clean)
    if m:
        clean = clean[:m.start()]
    else:
        m = re.search(r"[_-](?=\d)", clean)
        if m:
            clean = clean[:m.start()]
    clean = re.sub(r"(?:-ps5|_ps5|-ps4|_ps4)$", "", clean)
    return clean


def validate_canonical_storage_roots(payloads):
    """Impide que una edición futura vuelva a crear carpetas paralelas."""
    for item in payloads:
        expected = expected_storage_root(item)
        if not expected:
            continue
        got = _pldmgr_storage_root(item.get("filename"))
        if got != expected:
            raise RuntimeError(
                f'Raíz PLDMGR no compatible para {item.get("name")}: '
                f'{got!r} (esperada {expected!r})'
            )

def out_filename(filename, ch, app=None, rel=None):
    # No añadimos "_beta" ni "_unstable" por nuestra cuenta.
    if app and app.get("install_filename"):
        return app["install_filename"]
    if app and rel:
        return canonical_repo_filename(app, rel, filename)
    return filename

def payload_for(app, rel, ch):
    a = direct_asset(rel, app)
    if a:
        u = asset_url(a)
        if not u:
            return None
        data = get_bytes(u)
        return dict(filename=out_filename(a["name"], ch, app, rel), url=u,
                    source_direct=u, checksum=hashlib.sha256(data).hexdigest(),
                    asset_updated_at=a.get("updated_at") or a.get("created_at") or "")

    a = zip_asset(rel, app)
    if not a:
        return None
    u = asset_url(a)
    if not u:
        return None
    got = extract_elf(get_bytes(u), app)
    if not got:
        return None

    filename, data = got
    filename = out_filename(filename, ch, app, rel)
    ver = rel.get("tag_name") or rel.get("name") or "unknown"
    dest = MIRROR / safe(app["name"]) / safe(ver) / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    public = f"{PAGES}/{dest.as_posix()}"
    return dict(filename=filename, url=public, source_direct=public,
                checksum=hashlib.sha256(data).hexdigest(),
                asset_updated_at=a.get("updated_at") or a.get("created_at") or "")

def display_name(name, ch):
    # El canal nunca se añade al nombre visible.
    return name

def display_version(raw, ch):
    # Conservamos exactamente el tag/version publicado por el upstream.
    return str(raw or "unknown").strip()

def clean_md(text):
    s = str(text or "")
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("`", "")
    s = s.replace("**", "").replace("__", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def release_summary(rel, limit=180):
    """Extrae cambios relevantes de las notas oficiales sin inventar nada."""
    body = str(rel.get("body") or "")
    if not body.strip():
        return ""

    picked = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        low = line.lower()
        if (
            "full changelog" in low
            or "checksum" in low
            or "sha256" in low
            or line.startswith("http://")
            or line.startswith("https://")
        ):
            continue

        # Priorizamos bullets/changelog. Si no hay bullets, se cogerán
        # después frases cortas informativas.
        if re.match(r"^[-*+]\s+", line):
            line = re.sub(r"^[-*+]\s+", "", line)
            line = clean_md(line)
            if 8 <= len(line) <= 220:
                picked.append(line)
        if len(picked) >= 2:
            break

    if not picked:
        for raw in body.splitlines():
            line = clean_md(raw)
            if not line or len(line) < 12 or len(line) > 220:
                continue
            low = line.lower()
            if any(x in low for x in ("full changelog", "checksum", "sha256")):
                continue
            picked.append(line)
            if len(picked) >= 2:
                break

    if not picked:
        return ""

    s = "; ".join(picked)
    if len(s) > limit:
        s = s[:limit - 1].rstrip(" ;,.") + "…"
    return s

def curated_status(app, rel):
    text = rtext(rel)
    for pattern, label, note in CURATED_STATUS.get(app["name"], []):
        if re.search(pattern, text, flags=re.I):
            return label, note
    return None

def auto_status(app, rel, ch):
    """
    Solo calificamos "ESTABLE" si el desarrollador lo dice explícitamente.
    En cualquier otro caso usamos términos verificables y más prudentes.
    """
    whole = (
        rtext(rel) + "\n" + str(rel.get("body") or "")
    ).lower()

    if (
        "known issue" in whole
        and any(x in whole for x in RISK_TERMS)
    ):
        return (
            "PRECAUCIÓN",
            "Las notas oficiales incluyen una incidencia conocida relacionada con cierres, bloqueos o apagados."
        )

    if (
        "unstable" in whole
        or "this is experimental" in whole
        or "experimental homebrew" in whole
        or "test version" in whole
    ):
        return (
            "EXPERIMENTAL",
            "El propio desarrollador describe esta versión como experimental/inestable o de pruebas."
        )

    if (
        "hardware-confirmed" in whole
        or "hardware confirmed" in whole
        or "hardware-validated" in whole
        or "hardware validated" in whole
        or "live-tested" in whole
    ):
        return (
            "VALIDADO EN HARDWARE",
            "La documentación de la release incluye una validación explícita en hardware; revisar el firmware concreto indicado por el desarrollador."
        )

    if (
        "stable release" in whole
        or "stable version" in whole
        or re.search(r"\bstable\b", rtext(rel), flags=re.I)
    ):
        return (
            "ESTABLE SEGÚN DESARROLLADOR",
            "El upstream identifica explícitamente esta versión como estable; esto no implica compatibilidad universal con todos los firmwares/configuraciones."
        )

    if (
        "stability release" in whole
        or "improved stability" in whole
        or "stability improvements" in whole
        or "more reliable" in whole
        or "improved reliability" in whole
    ):
        return (
            "MEJORA DE ESTABILIDAD",
            "Las notas oficiales destacan correcciones o mejoras de estabilidad/fiabilidad, sin afirmar estabilidad absoluta."
        )

    if (
        ch == "alpha"
        or "alpha" in rtext(rel).lower()
        or "nightly" in rtext(rel).lower()
        or "experimental" in rtext(rel).lower()
        or "test" in rtext(rel).lower()
    ):
        return (
            "EXPERIMENTAL",
            "La versión pertenece a una rama alpha/nightly/test o equivalente."
        )

    if (
        ch == "beta"
        or rel.get("prerelease", False)
        or "beta" in rtext(rel).lower()
        or re.search(r"(^|[-_. ])rc\d*", rtext(rel).lower())
    ):
        return (
            "EN PRUEBAS",
            "El upstream la publica como pre-release, beta o release candidate; no se presenta como versión estable."
        )

    return (
        "ESTABILIDAD NO DOCUMENTADA",
        "Es una release publicada por el upstream, pero sus notas no aportan evidencia suficiente para calificarla como estable o inestable."
    )

def parse_iso(raw):
    try:
        return datetime.fromisoformat(str(raw or "").replace("Z", "+00:00"))
    except ValueError:
        return None

def github_issue_signal(app, rel):
    """
    Señal automática y prudente: busca issues ABIERTAS creadas desde la release
    que mencionen términos de crash/KP/freeze/apagado. No convierte por sí sola
    una versión en "inestable"; solo añade una alerta verificable.
    """
    repo = app.get("repo")
    if not repo or app.get("api"):
        return ""

    published = parse_iso(rel.get("published_at") or rel.get("created_at"))
    if not published:
        return ""

    url = (
        f"https://api.github.com/repos/{repo}/issues"
        "?state=open&sort=created&direction=desc&per_page=50"
    )

    try:
        issues = get_json(url)
    except Exception as e:
        print(f"  Aviso issues {app['name']}: {e}")
        return ""

    if not isinstance(issues, list):
        return ""

    hits = []
    for issue in issues:
        if issue.get("pull_request"):
            continue

        created = parse_iso(issue.get("created_at"))
        if not created or created < published:
            continue

        blob = (
            str(issue.get("title") or "") + "\n" +
            str(issue.get("body") or "")
        ).lower()

        if any(term in blob for term in RISK_TERMS):
            hits.append(issue.get("number"))

    if not hits:
        return ""

    shown = ", ".join(f"#{n}" for n in hits[:3] if n is not None)
    extra = f" ({shown})" if shown else ""
    return (
        f"ALERTA GITHUB: {len(hits)} issue(s) abierta(s) creada(s) desde esta "
        f"release mencionan crash/freeze/KP/apagado{extra}. Es una señal de "
        "precaución, no una prueba automática de que el fallo afecte a todos."
    )

def display_status(label, note):
    label = str(label or "").upper()

    if "LEGACY" in label:
        return "LEGACY"
    if "EXPERIMENT" in label or "ALPHA" in label:
        return "EXPERIMENTAL"
    if "BETA" in label or "PRUEBAS" in label or "CANDIDATE" in label:
        return "EN PRUEBAS"
    if "PRECAU" in label or "AVANZADO" in label:
        return "REVISAR"
    if "HARDWARE" in label:
        return "PRUEBAS EN HARDWARE"
    if "MAS PROBADA" in label or "MÁS PROBADA" in label:
        return "PROBADA"
    if "ESTABLE" in label and "NO DOCUMENTADA" not in label:
        return "ESTABLE"
    if "MEJORA DE ESTABILIDAD" in label:
        return "FIABILIDAD MEJORADA"

    return "ESTABILIDAD NO DOCUMENTADA"

def build_description(app, rel, ch):
    curated = curated_status(app, rel)
    if curated:
        label, status_note = curated
    else:
        label, status_note = auto_status(app, rel, ch)

    # PLDMGR no interpreta correctamente \\n en cadenas JSON del repositorio:
    # elimina la barra y acaba mostrando "n". Por eso usamos frases separadas
    # y no saltos de linea.
    parts = [
        app["desc"].strip().rstrip(".") + ".",
        f"ESTADO: {display_status(label, status_note)}."
    ]

    compat = compatibility_for(app, rel)
    if compat:
        parts.append(f"COMPATIBILIDAD: {compat}.")

    return " ".join(parts)

def candidates(rels, app, ch, latest_stable=None):
    override_ids = set()

    if app.get("stable_override"):
        rx = re.compile(app["stable_override"])
        forced = [r for r in rels if rx.search(rtext(r))]
        override_ids = {
            r.get("id") for r in forced
            if r.get("id") is not None
        }

        if ch == "stable" and forced:
            return sorted(forced, key=rtime, reverse=True)

    xs = [r for r in rels if channel(r) == ch]

    # Si una beta/alpha se ha promovido manualmente como rama estable/conservadora
    # mediante stable_override, no puede volver a aparecer en su canal original.
    if ch != "stable" and override_ids:
        xs = [
            r for r in xs
            if r.get("id") not in override_ids
        ]

    # Para proyectos GitHub normales, la release estable que GitHub marca como
    # "latest" tiene prioridad absoluta. Después dejamos las anteriores como
    # fallback por si la última no contiene un ELF/BIN compatible.
    if ch == "stable" and latest_stable:
        latest_id = latest_stable.get("id")
        xs = [
            r for r in xs
            if not (
                latest_id is not None
                and r.get("id") == latest_id
            )
        ]
        xs.insert(0, latest_stable)

    return xs

def make_entry(app, rel, p, ch):
    release_raw = rel.get("published_at") or rel.get("created_at") or ""
    asset_raw = p.get("asset_updated_at") or ""

    # Si el autor reemplaza/actualiza un asset dentro de la misma release,
    # usamos la fecha más reciente que tengamos.
    dates = [d for d in (release_raw, asset_raw) if d]
    raw = max(dates) if dates else ""

    return {
        "name": display_name(app["name"], ch),
        "filename": p["filename"],
        "url": p["url"],
        "source": source_url(app),
        "source_direct": p["source_direct"],
        "description": build_description(app, rel, ch),
        "last_update": raw[:10] if raw else "",
        "version": display_version(rel.get("tag_name") or rel.get("name") or "unknown", ch),
        "category": app["category"],
        "checksum": p["checksum"],
    }

def normalize_catalog_items(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("payloads", "items", "apps", "entries"):
            value = obj.get(key)
            if isinstance(value, list):
                return value
    return []

def process_catalog(app):
    """
    Fallback para proyectos útiles que todavía no publican un ELF mediante
    GitHub Releases. Se consulta un catálogo espejo conocido EN CADA EJECUCIÓN,
    se vuelve a descargar el binario y se recalcula SHA-256.
    """
    obj = get_json(app["catalog_url"])
    items = normalize_catalog_items(obj)
    wanted = {
        str(x).strip().lower()
        for x in app.get("catalog_names", [app["name"]])
    }

    hit = None
    for item in items:
        name = str(item.get("name") or "").strip().lower()
        if name in wanted:
            hit = item
            break

    if not hit:
        raise RuntimeError(
            f'No se encontró {app["name"]} en el catálogo externo.'
        )

    url = hit.get("url") or hit.get("source_direct")
    if not url:
        raise RuntimeError(
            f'{app["name"]}: el catálogo no proporciona URL descargable.'
        )

    data = get_bytes(url)
    filename = hit.get("filename") or Path(url.split("?", 1)[0]).name
    if not filename.lower().endswith((".elf", ".bin")):
        raise RuntimeError(
            f'{app["name"]}: el archivo del catálogo no parece ELF/BIN.'
        )

    version = str(hit.get("version") or "unknown")
    pseudo = {
        "tag_name": version,
        "name": version,
        "published_at": hit.get("last_update") or "",
        "created_at": hit.get("last_update") or "",
        "body": hit.get("description") or "",
        "prerelease": any(
            x in version.lower()
            for x in ("beta", "alpha", "test", "preview", "rc")
        ),
    }
    ch = channel(pseudo)

    return [{
        "name": hit.get("name") or app["name"],
        "filename": filename,
        "url": url,
        "source": app.get("source") or hit.get("source") or app["catalog_url"],
        "source_direct": hit.get("source_direct") or url,
        "description": build_description(app, pseudo, ch),
        "last_update": str(hit.get("last_update") or "")[:10],
        "version": display_version(version, ch),
        "category": app["category"],
        "checksum": hashlib.sha256(data).hexdigest(),
    }]

def process(app):
    if app.get("catalog_url"):
        return process_catalog(app)

    # Lista completa fresca para detectar también beta/alpha.
    rels = get_json(api_url(app))
    if not isinstance(rels, list):
        rels = [rels]

    rels = sorted(
        [r for r in rels if not r.get("draft", False)],
        key=rtime,
        reverse=True
    )

    # Versiones vetadas expresamente por proyecto. Esto se aplica antes de
    # clasificar canales, de modo que una release antigua no puede reaparecer
    # como estable, beta, alpha ni como fallback por falta de asset.
    excluded_version_patterns = [
        re.compile(pattern) for pattern in app.get("exclude_versions", [])
    ]
    if excluded_version_patterns:
        rels = [
            r for r in rels
            if not any(rx.search(rtext(r)) for rx in excluded_version_patterns)
        ]

    wanted_channels = app.get("channels", ("stable", "beta", "alpha"))

    # Para todos los repos GitHub con canal estable normal, consultamos además
    # /releases/latest. Así una release recién publicada (Pegasus 1.8.0, etc.)
    # no puede quedarse detrás de una versión antigua por orden/cache del listado.
    latest_stable = None
    latest_url = github_latest_url(app)
    if (
        latest_url
        and "stable" in wanted_channels
        and not app.get("stable_override")
    ):
        try:
            latest_stable = get_json(latest_url)
            if (
                latest_stable.get("draft", False)
                or latest_stable.get("prerelease", False)
            ):
                latest_stable = None
            elif latest_stable:
                print(f'  Latest oficial GitHub: {rtext(latest_stable)}')
        except Exception as e:
            # No bloqueamos el repo entero: seguimos con la lista de releases
            # ya descargada, también forzada sin caché.
            print(f'  Aviso latest oficial: {e}')
            latest_stable = None

    selected = {}
    selected_release_ids = set()
    selected_release_keys = set()
    # Defensa adicional: una misma versión visible no puede ocupar dos canales
    # aunque GitHub haya recreado la release y cambien id/fecha/metadatos.
    selected_versions = set()

    for ch in wanted_channels:
        for rel in candidates(
            rels,
            app,
            ch,
            latest_stable=latest_stable
        ):
            rel_id = rel.get("id")
            rel_key = (
                str(rel.get("tag_name") or ""),
                str(rel.get("name") or ""),
                str(rel.get("published_at") or rel.get("created_at") or "")
            )
            raw_version = str(
                rel.get("tag_name") or rel.get("name") or "unknown"
            ).strip().lower()
            # Solo para comparar identidad; la versión que se muestra se conserva
            # exactamente como la publica el upstream.
            version_key = re.sub(r"\s+", "", raw_version)
            version_key = re.sub(r"^v(?=\d)", "", version_key)

            if (
                (rel_id is not None and rel_id in selected_release_ids)
                or rel_key in selected_release_keys
                or version_key in selected_versions
            ):
                continue
            try:
                # payload_for vuelve a descargar SIEMPRE el asset y recalcula
                # SHA-256, incluso aunque versión/URL coincidan con la pasada.
                p = payload_for(app, rel, ch)
            except Exception as e:
                print(f'  fallo {rtext(rel)}: {e}')
                continue

            if p:
                selected[ch] = (rel, p)

                if rel_id is not None:
                    selected_release_ids.add(rel_id)
                selected_release_keys.add(rel_key)
                selected_versions.add(version_key)

                print(
                    f'  Seleccionado {ch}: '
                    f'{rtext(rel)} -> {p["filename"]}'
                )
                break

    stable_t = rtime(selected["stable"][0]) if "stable" in selected else 0
    output = []

    if "stable" in selected:
        output.append(
            make_entry(
                app,
                *selected["stable"],
                "stable"
            )
        )

    for ch in ("beta", "alpha"):
        if ch not in wanted_channels or ch not in selected:
            continue

        # No mostramos prereleases históricas más viejas que la estable,
        # salvo que el proyecto las marque expresamente como relevantes.
        if (
            rtime(selected[ch][0]) > stable_t
            or app.get(f"always_{ch}", False)
            or "stable" not in selected
        ):
            output.append(
                make_entry(
                    app,
                    *selected[ch],
                    ch
                )
            )

    return output

def fixed_entry(x):
    data = get_bytes(x["url"])
    ch = x["channel"]
    return {
        "name": display_name(x["name"], ch),
        "filename": x["filename"],
        "url": x["url"],
        "source": x["source"],
        "source_direct": x["url"],
        "description": (
            f'{x["desc"].strip().rstrip(".")}. '
            f'ESTADO: EN PRUEBAS. '
            f'COMPATIBILIDAD: hasta FW 12.70.'
        ),
        "last_update": x["date"],
        "version": display_version(x["version"], ch),
        "category": x["category"],
        "checksum": hashlib.sha256(data).hexdigest(),
    }

def sanitize_visible(value):
    if not isinstance(value, str):
        return value

    s = value
    s = s.replace("\\r\\n", " ")
    s = s.replace("\\n", " ")
    s = s.replace("\\r", " ")
    s = s.replace("\r", " ")
    s = s.replace("\n", " ")
    s = re.sub(r"\\s+", " ", s).strip()
    return s

def sanitize_payload(entry):
    for key in ("name", "filename", "description", "version", "category"):
        if key in entry:
            entry[key] = sanitize_visible(entry[key])
    return entry

def _visible_identity(item):
    """Identidad que ve PLDMGR: nombre + versión, no el hash del binario."""
    name = re.sub(
        r"\s+", " ", str(item.get("name", "")).strip().lower()
    )
    version = re.sub(
        r"\s+", "", str(item.get("version", "")).strip().lower()
    )
    version = re.sub(r"^v(?=\d)", "", version)

    # Si por algún fallo no hay versión útil, no colapsamos payloads distintos
    # solo porque compartan nombre.
    if not version or version == "unknown":
        return (
            name,
            version,
            str(item.get("filename", "")).strip().lower(),
            str(item.get("checksum", "")).strip().lower(),
        )

    return (name, version)

def dedupe_payloads(payloads):
    result = []
    seen = set()

    for item in payloads:
        # IMPORTANTE: el checksum NO forma parte de la identidad visible.
        # Si el autor recompila/reemplaza el asset de una release, el hash puede
        # cambiar sin que cambie la versión. PLDMGR no debe mostrar dos copias.
        key = _visible_identity(item)

        if key in seen:
            print(
                f'Duplicado visible eliminado: '
                f'{item.get("name")} {item.get("version")} '
                f'({item.get("filename")})'
            )
            continue

        seen.add(key)
        result.append(item)

    return result

def validate_no_visible_duplicates(payloads):
    """Falla la generación si vuelve a colarse nombre+versión duplicado."""
    seen = {}
    for item in payloads:
        key = _visible_identity(item)
        if len(key) != 2:
            continue
        if key in seen:
            prev = seen[key]
            raise RuntimeError(
                "Duplicado visible tras deduplicar: "
                f'{item.get("name")} {item.get("version")} | '
                f'{prev.get("filename")} / {item.get("filename")}'
            )
        seen[key] = item

def sort_key(x):
    # Orden profesional: categoría, nombre y versión. No inferimos calidad
    # a partir de palabras como beta/alpha para ordenar.
    return (
        CAT_ORDER.get(x.get("category", ""), 99),
        x["name"].lower(),
        str(x.get("version", "")).lower(),
    )

def main():
    print("=== HiddenKernel Store · Curated Ecosystem-Compatible ===")
    print("Actualizaciones forzadas + fichas breves + estado y compatibilidad verificada.")
    payloads = []
    for app in APPS:
        print(f'Procesando {app["name"]}...')
        try:
            xs = process(app)
            payloads.extend(xs)
            for x in xs:
                print(f'  OK {x["name"]}: {x["version"]}')
            if not xs:
                print("  Sin release compatible.")
        except Exception as e:
            print(f"  ERROR: {e}")

    for x in FIXED:
        try:
            payloads.append(fixed_entry(x))
        except Exception as e:
            print(f'  ERROR fijo {x["name"]}: {e}')

    payloads = [sanitize_payload(x) for x in payloads]
    payloads = dedupe_payloads(payloads)
    validate_no_visible_duplicates(payloads)
    validate_canonical_storage_roots(payloads)
    payloads.sort(key=sort_key)

    for x in payloads:
        desc = x.get("description", "")
        if "\n" in desc or "\r" in desc:
            raise RuntimeError(f'Descripcion con salto de linea: {x.get("name")}')

    with open("payloads.json", "w", encoding="utf-8") as f:
        json.dump({"name": "HiddenKernel Store", "payloads": payloads},
                  f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Generado payloads.json con {len(payloads)} entradas.")

if __name__ == "__main__":
    main()
