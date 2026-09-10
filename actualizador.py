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
    # ==========================================================
    # ESENCIALES
    # Lo mínimo que aparece de forma consistente en setups actuales.
    # ==========================================================
    dict(name="PS5 Payload Manager", repo="itsPLK/ps5-payload-manager",
         match=["pldmgr"], exclude=["debug"], category="ESENCIALES",
         desc=("Dashboard web para instalar, organizar, lanzar y actualizar payloads "
               "ELF/BIN y gestionar el autoload desde PS5, móvil o PC.")),
    dict(name="kstuff-lite", repo="EchoStretch/kstuff-lite",
         match=["kstuff"], exclude=["debug"], category="ESENCIALES",
         desc=("Versión ligera de kstuff. Aplica los parches necesarios para el entorno "
               "homebrew y es la pareja habitual de ShadowMountPlus en configuraciones "
               "modulares actuales."),
         channels=["beta"]),
    dict(name="ShadowMountPlus", repo="drakmor/ShadowMountPlus",
         match=["shadowmount"], archive=["shadowmount"], category="ESENCIALES",
         desc=("Auto-mounter en segundo plano para detectar, montar y registrar juegos "
               "desde almacenamiento interno o externo. HiddenKernel mantiene la "
               "1.6beta16 como rama conservadora y muestra las 1.7 alpha aparte."),
         stable_override=r"(?i)^1\.6beta", always_alpha=True),
    dict(name="nanoDNS", repo="drakmor/nanoDNS",
         match=["nanodns"], category="ESENCIALES",
         desc=("Proxy DNS local para PS4/PS5. Permite bloquear dominios de PSN y "
               "actualizaciones desde la propia consola y aplicar redirecciones locales.")),

    # ==========================================================
    # HEN / AIO
    # Alternativas: no hace falta cargar todas.
    # ==========================================================
    dict(name="OnionHEN", repo="aydencharles/onionHEN",
         match=["onionhen"], archive=["onionhen"], category="HEN / AIO",
         desc=("Homebrew Enabler y Toolbox AIO con cheats, overlays, gestión de payloads, "
               "fan control y servicios. Soporte declarado por el desarrollador: "
               "FW 4.03-12.70.")),
    dict(name="etaHEN", repo="etaHEN/etaHEN",
         match=["etahen"], category="HEN / AIO",
         desc=("Homebrew Enabler AIO con Toolbox, cheats, plugins y servicios integrados. "
               "Sigue siendo una referencia, aunque el stack modular actual puede "
               "sustituir varias de sus funciones.")),
    dict(name="PIZZA-HEN", repo="Michele-M-Media/PIZZA-HEN",
         match=["pizza"], archive=["pizza"], category="HEN / AIO",
         desc=("Entorno AIO activo con KStuff/ShadowMount, Toolbox, FTP, ps5debug-NG, "
               "CheatRunner e instalación de PKG. Algunas funciones se mantienen "
               "explícitamente experimentales.")),

    # ==========================================================
    # GESTIÓN
    # Dashboards, autoloaders y AIO de administración.
    # ==========================================================
    dict(name="PLDMGR Install & Update", repo="hiddenkernellab/PLDMGR-install-update",
         match=["hk-pldmgr-install-update"], category="GESTIÓN",
         desc=("Herramienta HiddenKernel que comprueba la última release oficial de "
               "PS5 Payload Manager, crea /data/ps5_autoloader si falta, instala o "
               "repara pldmgr.elf y recrea autoload.txt.")),
    dict(name="PS5 WebKit Autoloader", repo="itsPLK/ps5-webkit-autoloader",
         match=["webkit-autoloader-installer"], exclude=["host"], category="GESTIÓN",
         desc=("Autoloader WebKit offline para automatizar exploit y payloads. "
               "FW 1.00-5.50 & 7.00-12.70. La estabilidad varía según firmware.")),
    dict(name="Prospero Manager",
         catalog_url=("https://nexgen999.github.io/PS5-Super-PLDMGR-Auto-Updater/"
                      "json/ps5_hen_loader.json"),
         catalog_names=["ProsperoMgr", "Prospero Manager"],
         source="https://github.com/notmaj0r/ProsperoMgr",
         category="GESTIÓN",
         desc=("AIO web de nueva generación: archivos y ZIP, payloads, repositorios, "
               "PKG local/URL, saves, procesos, autoload, temperaturas y perfil. "
               "Actualmente se usa como sucesor funcional de ELF Arsenal.")),
    dict(name="ELF Arsenal",
         api="https://git.etawen.dev/api/v1/repos/soniciso/elf-arsenal/releases",
         source="https://git.etawen.dev/soniciso/elf-arsenal/releases",
         match=["elf-arsenal"], category="GESTIÓN",
         desc=("AIO clásico que integra múltiples payloads y herramientas en una sola "
               "interfaz. Se conserva por utilidad y compatibilidad con setups existentes, "
               "pero el proyecto está discontinuado y no es la opción preferente actual.")),

    # ==========================================================
    # ARCHIVOS / PC
    # Opciones distintas: AIO, file manager ligero, FTP y PC/Android.
    # ==========================================================
    dict(name="BFpilot", repo="ItsBlurf/BFpilot",
         match=["bfpilot"], exclude=["alpha", "installer", "lite"], category="ARCHIVOS / PC",
         desc=("Explorador web AIO para PS5. Gestión de archivos, extracción ZIP/RAR/7z, "
               "instalación local de PKG y acceso desde navegador.")),
    dict(name="PS5 Web File Manager", repo="owendswang/ps5-web-file-manager",
         match=["web-file-mgr"], category="ARCHIVOS / PC",
         desc=("Explorador web ligero y muy activo para gestionar archivos desde la LAN. "
               "Las versiones recientes incluyen instalación de PKG y acceso directo "
               "desde la fila Media.")),
    dict(name="ftpsrv", repo="ps5-payload-dev/ftpsrv",
         match=["ftpsrv"], prefer=["ps5"], exclude=["ps4", "install"],
         category="ARCHIVOS / PC",
         desc=("Servidor FTP ligero para PS5. La opción simple cuando solo necesitas "
               "acceso remoto al sistema de archivos.")),
    dict(name="ps5upload", repo="phantomptr/ps5upload",
         match=["ps5upload"], category="ARCHIVOS / PC",
         desc=("Enlace con PC/Android para transferencias rápidas y verificadas, "
               "reanudación, archivos, montaje e instalación de PKG según firmware "
               "y parches disponibles.")),

    # ==========================================================
    # JUEGOS / COMPATIBILIDAD
    # Herramientas directamente útiles para dumps/montajes.
    # ==========================================================
    dict(name="PS5 Game Compressor", repo="juma-sayeh/PS5-Game-Compressor",
         match=["game-compressor"], category="JUEGOS / COMPATIBILIDAD",
         desc=("Comprime, descomprime, valida, repara y mueve juegos utilizados con "
               "ShadowMountPlus; también integra flujos APR-EMU.")),
    dict(name="APR Emu Updater", repo="tsuramatsu1/apr-emu-updater",
         match=["apr_emu_updater"], category="JUEGOS / COMPATIBILIDAD",
         desc=("Gestiona el override de APR Emu por juego para ShadowMountPlus y otros "
               "flujos compatibles. Debe mantenerse cargado mientras se usa el override.")),
    dict(name="PS5 App Dumper", repo="EchoStretch/ps5-app-dumper",
         match=["app", "dumper"], archive=["dumper"], category="JUEGOS / COMPATIBILIDAD",
         desc=("Payload para volcar aplicaciones/juegos PS5 y preparar archivos para "
               "copias de seguridad, análisis y flujos de compatibilidad.")),

    # ==========================================================
    # UTILIDADES
    # Funciones claras y no cubiertas totalmente por los esenciales.
    # ==========================================================
    dict(name="Lapy JB Daemon", repo="ArkSama/PS5-Lapy-JB-Daemon",
         match=["lapy", "daemon"], category="UTILIDADES",
         desc=("Daemon jailbreak-on-demand para PS5-Xplorer y apps que esperan la API "
               "de etaHEN. Permite usarlas sin cargar etaHEN completo; requiere kstuff.")),
    dict(name="garlic-savemgr",
         api="https://git.etawen.dev/api/v1/repos/earthonion/garlic-savemgr/releases",
         source="https://git.etawen.dev/earthonion/garlic-savemgr/releases",
         match=["garlic-savemgr"], exclude=["worker"], category="UTILIDADES",
         desc=("Gestor de partidas guardadas con interfaz web: backup, importación, "
               "descifrado/cifrado y resignado de saves según la versión.")),
    dict(name="np-fake-signin", repo="earthonion/np-fake-signin",
         match=["np", "fake", "signin"], archive=["np-fake-signin"], category="UTILIDADES",
         desc=("Simula el estado de inicio de sesión PSN para el usuario activo. "
               "Requiere cuenta activada offline y reinicio después de usarlo.")),
    dict(name="Common FPS for PS5", repo="porhe911/Common-FPS-for-PS5",
         match=["common", "fps"], exclude=["plugin"], archive=["common"],
         category="UTILIDADES",
         desc=("Overlay universal de FPS en tiempo real para juegos PS4/PS5 en PS5. "
               "Disponible como ELF independiente y como plugin para etaHEN.")),

    # ==========================================================
    # MANDOS
    # Una única herramienta general para no inflar la tienda.
    # ==========================================================
    dict(name="Ghostcontrol", repo="StonedModder/Ghostcontrol-PS5-USB-Controller-Patcher",
         match=["ghost-control-ps5"], category="MANDOS",
         desc=("Patcher para usar mandos USB de terceros mediante un DualSense virtual. "
               "Incluye matriz de compatibilidad para DS4, HORIPAD, 8BitDo, Xbox y otros.")),

    # ==========================================================
    # DESCARGAS
    # Dos proyectos activos y con enfoques distintos.
    # ==========================================================
    dict(name="Pegasus DL", repo="pegasus-ps5/pegasus-dl",
         match=["pegasus"], category="DESCARGAS",
         desc=("Gestor de descargas con interfaz web. Desde 1.8.0 puede entregar "
               "enlaces .pkg al descargador nativo de PS5 tras confirmación del usuario "
               "y admite flujos con Real-Debrid/TorBox.")),
    dict(name="Spectrum Library", repo="Phoenixx1202/Spectrum-Library",
         match=["spectrum"], archive=["spectrum"], category="DESCARGAS",
         desc=("Biblioteca/gestor de descargas con interfaz visual, categorías, "
               "carátulas, cola y selección de destinos.")),
]

FIXED = []

CAT_ORDER = {"ESENCIALES": 0, "HEN / AIO": 1, "GESTIÓN": 2, "ARCHIVOS / PC": 3, "JUEGOS / COMPATIBILIDAD": 4, "UTILIDADES": 5, "MANDOS": 6, "DESCARGAS": 7}

# Capa de curación basada en documentación/release notes del desarrollador y
# feedback público concreto. Las reglas son VERSION-ESPECÍFICAS: cuando cambia
# la versión dejan de aplicarse y entra la valoración automática de la nueva
# release, evitando arrastrar una reputación antigua a un binario nuevo.
CURATED_STATUS = {
    "Prospero Manager": [
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
         "Última release publicada en el repositorio oficial de etaHEN; no se etiqueta como estable absoluto porque integra componentes y funciones con distinto grado de madurez."),
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

MAX_DESCRIPTION = 900

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
    "Prospero Manager": {
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

def out_filename(filename, ch):
    if ch == "stable":
        return filename
    p = Path(filename)
    return f"{p.stem}_{'beta' if ch == 'beta' else 'unstable'}{p.suffix}"

def payload_for(app, rel, ch):
    a = direct_asset(rel, app)
    if a:
        u = asset_url(a)
        if not u:
            return None
        data = get_bytes(u)
        return dict(filename=out_filename(a["name"], ch), url=u,
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
    filename = out_filename(filename, ch)
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
    # Conservamos la versión REAL del upstream. No añadimos por nuestra cuenta
    # "beta", "estable" o "inestable". Si esas palabras forman parte del tag
    # original (ej. 1.7alpha13fix1), se mantienen porque son parte de la versión.
    v = str(raw or "unknown").strip()
    if v.lower().startswith("v") and len(v) > 1 and v[1].isdigit():
        v = v[1:]
    return v

def clean_md(text):
    s = str(text or "")
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("`", "")
    s = s.replace("**", "").replace("__", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def release_summary(rel, limit=300):
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
        if len(picked) >= 3:
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

def build_description(app, rel, ch):
    curated = curated_status(app, rel)
    if curated:
        label, status_note = curated
    else:
        label, status_note = auto_status(app, rel, ch)

    parts = [
        f"ESTADO: {label} — {status_note}",
    ]

    rec = current_recommendation(app["name"])
    if rec:
        parts.append(rec)

    parts.append(app["desc"].strip())

    changes = release_summary(rel)
    if changes:
        parts.append(f"NOTAS DE ESTA RELEASE: {changes}")

    issue_note = github_issue_signal(app, rel)
    if issue_note:
        parts.append(issue_note)

    desc = " ".join(x for x in parts if x).strip()
    if len(desc) > MAX_DESCRIPTION:
        desc = desc[:MAX_DESCRIPTION - 1].rstrip(" ;,.") + "…"
    return desc

def candidates(rels, app, ch, latest_stable=None):
    if ch == "stable" and app.get("stable_override"):
        rx = re.compile(app["stable_override"])
        forced = [r for r in rels if rx.search(rtext(r))]
        if forced:
            return sorted(forced, key=rtime, reverse=True)

    xs = [r for r in rels if channel(r) == ch]

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
        "name": app["name"],
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

    for ch in wanted_channels:
        for rel in candidates(
            rels,
            app,
            ch,
            latest_stable=latest_stable
        ):
            try:
                # payload_for vuelve a descargar SIEMPRE el asset y recalcula
                # SHA-256, incluso aunque versión/URL coincidan con la pasada.
                p = payload_for(app, rel, ch)
            except Exception as e:
                print(f'  fallo {rtext(rel)}: {e}')
                continue

            if p:
                selected[ch] = (rel, p)
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
        "filename": out_filename(x["filename"], ch),
        "url": x["url"],
        "source": x["source"],
        "source_direct": x["url"],
        "description": (f'ESTADO: {x.get("status", "ESTABILIDAD NO DOCUMENTADA")}. '
                        f'{x["desc"]}'),
        "last_update": x["date"],
        "version": display_version(x["version"], ch),
        "category": x["category"],
        "checksum": hashlib.sha256(data).hexdigest(),
    }

def sort_key(x):
    # Orden profesional: categoría, nombre y versión. No inferimos calidad
    # a partir de palabras como beta/alpha para ordenar.
    return (
        CAT_ORDER.get(x.get("category", ""), 99),
        x["name"].lower(),
        str(x.get("version", "")).lower(),
    )

def main():
    print("=== HiddenKernel Store · Curated Force Refresh v12 ===")
    print("25 herramientas útiles + updates forzados + notas upstream + recomendaciones recientes con caducidad.")
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

    payloads.sort(key=sort_key)
    with open("payloads.json", "w", encoding="utf-8") as f:
        json.dump({"name": "HiddenKernel Store", "payloads": payloads},
                  f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Generado payloads.json con {len(payloads)} entradas.")

if __name__ == "__main__":
    main()
