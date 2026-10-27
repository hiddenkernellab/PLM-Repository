#!/usr/bin/env python3
"""HiddenKernelLab | Actualizador del catalogo PLDMGR.

Reemplaza el actualizador.py existente en PLM-Repository. GitHub Actions
lo ejecuta cada 3 horas: actualiza las releases verificables, depura el
catalogo, conserva IDs/favoritos/autoload e iconos, y genera los JSON.

No modifica el repositorio remoto por si mismo. Requiere Python 3.10+.
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

# Limpiar solo las cuatro entradas acordadas; las alternativas utiles siguen.
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

# Fijar builds experimentales que funcionan con combinaciones concretas.
# No sustituirlas por una beta incompatible sin revision manual.
NO_AUTOMATICOS = frozenset({
    "kstuff-fpkg", "shadowmountplus", "ps5sx2-helper",
    "ps5sx2-installer", "etahen-13.60", "pldmgr-install-update",
    "ps5-hardware-overlay",  # v0.0.18 tag follows v1.0.15; manual review needed
    "ps5-linux-loader",  # compatibilidad retail 11.40 aun no probada
})

# Unica migracion forzosa: la version PS5 estable de Drakmor.
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


# Release upstream verificada: la etiqueta v0.0.18 contiene el ELF AIO 1.0.18.
# NO usar overlay_payload.elf: es la carga interna, no el lanzador autonomo.
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

# Release estable publicada el 18/10/2026 y contrastada con el espejo
# itsPLK/ps5-payloads-mirror (SHA-256 de su copia ELF).
# Este upstream es Forgejo, por lo que refrescar() no puede seguirlo por
# la API GitHub; migrar solo desde versiones anteriores y no retroceder.
GARLIC_RELEASE = {
    "version": "v1.14.0",
    "filename": "garlic-savemgr_v1.14.0.elf",
    "url": "https://git.etawen.dev/earthonion/garlic-savemgr/releases/download/v1.14.0/garlic-savemgr.elf",
    "checksum": "0b96822e3f554666b7fa4ead673c60ef602e5534a9f01a45e94d0580bd6e9edd",
    "last_update": "2026-10-18",
}

# ELFs completos con assets y digest SHA-256 publicados. No se incluyen
# ZIP/FFPFSC, utilidades dependientes de PC ni prereleases. El loader Linux
# tiene release estable, pero su compatibilidad retail sigue experimental.
# Se preservan todos los IDs y sus iconos existentes.
NUEVOS_ELF_VERIFICADOS = (
    {
        "id": "hearbridge", "icon_key": "hearbridge", "name": "HearBridge PS5",
        "filename": "HearBridge-1.3.6.elf", "version": "v1.3.6",
        "url": "https://github.com/X-F1REBALL-X/HearBridge-PS5/releases/download/v1.3.6/HearBridge-1.3.6.elf",
        "source": "https://github.com/X-F1REBALL-X/HearBridge-PS5/releases",
        "source_direct": "https://github.com/X-F1REBALL-X/HearBridge-PS5/releases/download/v1.3.6/HearBridge-1.3.6.elf",
        "checksum": "7b1a1b4a9a44db0723692a83718ebca63ecef38875a53a41328950f2cfa6877c",
        "last_update": "2026-10-18", "category": "MANDOS / AUDIO",
        "description": (
            "Puente de audio PS5 a auriculares Bluetooth A2DP sin dongle, "
            "con panel web en puerto 8090, ecualizador, perfiles por juego "
            "y cambio de auriculares. ELF estable 1.3.6 para chips Marvell/NXP "
            "y MediaTek. Posibles conflictos de reconexion con mandos y "
            "cortes de audio en algunos auriculares; probar manualmente, "
            "no autocargar hasta confirmar estabilidad. Alternativa a FGG PlayPods."
        ),
    },
    {
        "id": "ps5-tabshifter", "icon_key": "ps5-tabshifter", "name": "PS5 TabShifter",
        "filename": "TabShifter.elf", "version": "v.1.2.1",
        "url": "https://github.com/xvvulcanvx/PS5-TabShifter/releases/download/v.1.2.1/TabShifter.elf",
        "source": "https://github.com/xvvulcanvx/PS5-TabShifter/releases",
        "source_direct": "https://github.com/xvvulcanvx/PS5-TabShifter/releases/download/v.1.2.1/TabShifter.elf",
        "checksum": "147945cffb28405557a49cd4929c7d0534c55f6a757aba0063f9ce475c1c7255",
        "last_update": "2026-10-17", "category": "PERSONALIZACION",
        "description": (
            "Organiza iconos entre Juegos y Multimedia, fija apps al inicio "
            "y oculta elementos del sistema; panel web en puerto 9095. "
            "Crea copia .bak de las bases de datos antes de modificar. "
            "Probado por el autor en FW 12.02 a 13.60; NO se ha confirmado "
            "su uso en FW 7.20 ni 11.40. No autocargar."
        ),
    },
    {
        "id": "ps5-60fps", "icon_key": "ps5-60fps", "name": "fps60 (PS5 60 FPS)",
        "filename": "fps60.elf", "version": "v1.0.0",
        "url": "https://github.com/eladharels/ps5-60FPS/releases/download/v1.0.0/fps60.elf",
        "source": "https://github.com/eladharels/ps5-60FPS/releases",
        "source_direct": "https://github.com/eladharels/ps5-60FPS/releases/download/v1.0.0/fps60.elf",
        "checksum": "5331ebf1b69cd272a0491f899b14ca5d59240adee2e69078631473070ddeca9b",
        "last_update": "2026-10-16", "category": "JUEGOS / COMPATIBILIDAD",
        "description": (
            "Aplica en memoria parches de 60 FPS para versiones concretas de "
            "juegos PS4/PS5; panel web puerto 8060, sin alterar archivos. "
            "El autor confirma pruebas reales en Gravity Rush 2 (01.11) "
            "y The Order: 1886 (01.02, posibles softlocks). "
            "Otros parches comunitarios no probados; usar manualmente."
        ),
    },
    {
        "id": "ps5-linux-loader", "icon_key": "ps5-linux-loader",
        "name": "PS5 Linux Loader (11.xx / 13.xx)",
        "filename": "ps5-linux-loader.elf",
        "version": "v2026.10.22-all11-13",
        "url": "https://github.com/soniciso1/ps5-linux-loader/releases/download/v2026.10.22-all11-13/ps5-linux-loader.elf",
        "source": "https://github.com/soniciso1/ps5-linux-loader/releases",
        "source_direct": "https://github.com/soniciso1/ps5-linux-loader/releases/download/v2026.10.22-all11-13/ps5-linux-loader.elf",
        "checksum": "2ecaaac60f9575235e064c4800051e839115d10b60fee8446b4d2416a22afc6a",
        "last_update": "2026-10-22", "category": "DESARROLLO / AVANZADO",
        "description": (
            "Arranque de Linux en PS5 desde un ELF que detecta el firmware y "
            "selecciona el perfil de memoria. Soporta 11.00, 11.20, 11.40, "
            "11.60, 13.00, 13.20, 13.40, 13.42 y 13.60; NO 7.20. "
            "Necesita kernel Linux e initrd preparados en USB, ademas de "
            "jailbreak y elfldr (9021). 11.40 arranco Linux 7.2.3 en "
            "devkit; el ELF combinado no tiene todavia validacion completa "
            "en PS5 retail. EXPERIMENTAL: probar manualmente; NO autocargar. "
            "ELF y SHA-256 verificados contra la release oficial."
        ),
    },
    {
        "id": "ps5-dump-forge", "icon_key": "ps5-dump-forge",
        "name": "PS5 Dump Forge",
        "filename": "ps5-dump-forge-0.4.1-ps5.elf",
        "version": "v0.4.1",
        "url": "https://github.com/quer3q/ps5-dump-forge/releases/download/v0.4.1/ps5-dump-forge-0.4.1-ps5.elf",
        "source": "https://github.com/quer3q/ps5-dump-forge/releases",
        "source_direct": "https://github.com/quer3q/ps5-dump-forge/releases/download/v0.4.1/ps5-dump-forge-0.4.1-ps5.elf",
        "checksum": "ea5c47d1500efc8573523d19cebaa8addac9ec51fc62a9c90048daca755f5c96",
        "last_update": "2026-10-24", "category": "JUEGOS / COMPATIBILIDAD",
        "description": (
            "Gestor y conversor de dumps PS5 directamente en la consola: "
            "carpetas, FFPKG, exFAT, FFPFS, FFPFSC y PKG debug. "
            "Permite explorar, extraer y editar contenido; copiar o convertir "
            "por SMB, FTP y NFS sin copia temporal; interfaz local en puerto "
            "8095. v0.4.1 evita el conflicto del puerto 9120 con ps5upload "
            "y repara la actualizacion desde la PS5. "
            "Precaucion: editar o reconstruir imagenes requiere espacio "
            "libre y puede ser irreversible; verificar respaldos y probar "
            "manualmente antes de usar con ShadowMountPlus. NO autocargar."
        ),
    },

)


def migrar_garlic(item: dict) -> None:
    if version_numerica(item.get("version", "")) >= version_numerica(GARLIC_RELEASE["version"]):
        return
    if item.get("id") != "garlic-savemgr" or str(item.get("source", "")).rstrip("/") != (
            "https://git.etawen.dev/earthonion/garlic-savemgr/releases"):
        raise ValueError("Origen inesperado para Garlic SaveMgr")
    item.update(GARLIC_RELEASE)
    item["source_direct"] = GARLIC_RELEASE["url"]
    item["category"] = "TRUCOS / PARTIDAS"
    print("ACTUALIZADO: Garlic SaveMgr -> v1.14.0 (ELF verificado)")



# 27/10/2026: releases upstream comprobadas. Los ELF y sus SHA-256
# proceden del espejo publico evoX-CoreOS; la fuente de cada proyecto
# sigue siendo el repositorio oficial. ShadowMountPlus se distribuye
# tambien como ZIP upstream, por lo que se utiliza el ELF extraido
# publicado por evoX. No convertir una beta en actualizacion automatica.
SHADOWMOUNT_171B8 = {
    "name": "ShadowMountPlus",
    "filename": "shadowmountplus.elf",
    "url": (
        "https://nexgen999.github.io/evoX-CoreOS/payloads/"
        "ps5_game_dump/ShadowMountPlus/1.7beta8/shadowmountplus.elf"
    ),
    "source": "https://github.com/drakmor/ShadowMountPlus/releases",
    "source_direct": (
        "https://nexgen999.github.io/evoX-CoreOS/payloads/"
        "ps5_game_dump/ShadowMountPlus/1.7beta8/shadowmountplus.elf"
    ),
    "version": "1.7beta8",
    "last_update": "2026-10-26",
    "category": "ESENCIALES",
    "checksum": "7163472217a2390f5bcbe3b61a96963976f7b7bd84d960b8d926f35b9cbecf28",
    "description": (
        "ShadowMountPlus 1.7beta8 (PRE-RELEASE): monta juegos PS4/PS5 "
        "y backports. Redisenada la interfaz web para TV y mando. "
        "Instala PKG desde almacenamiento interno/externo o mediante "
        "streaming desde navegador; permite consultar y retirar DLC/parches, "
        "instalar/reemplazar/eliminar backports, y admite param.sfo, "
        "eboot2.bin e IDs homebrew adicionales. Permite instalar juegos PS4 "
        "desde imagenes y carpetas. ATENCION: API LAN habilitada por defecto; "
        "usar solo en red de confianza y revisar acceso. "
        "ELF del espejo evoX-CoreOS, SHA-256 publicado en su catalogo. "
        "Es beta: probar manualmente con kstuff compatible y copia de "
        "seguridad antes de activar autoload. No autocargar sin prueba."
    ),
}

POORDS4_020 = {
    "name": "PoorDS4",
    "filename": "PoorDS4_v0.2.0.elf",
    "url": (
        "https://nexgen999.github.io/evoX-CoreOS/payloads/"
        "ps5_pad_utility/PoorDS4/v0.2.0/PoorDS4_v0.2.0.elf"
    ),
    "source": "https://github.com/ItsBlurf/PoorDS4/releases",
    "source_direct": (
        "https://nexgen999.github.io/evoX-CoreOS/payloads/"
        "ps5_pad_utility/PoorDS4/v0.2.0/PoorDS4_v0.2.0.elf"
    ),
    "version": "v0.2.0",
    "last_update": "2026-10-21",
    "category": "MANDOS / AUDIO",
    "checksum": "c5f257ca2bf2f95949d09f95dd6feb3353b2ad37e24c972d09fccc3beb11301c",
    "description": (
        "PoorDS4 v0.2.0: puente para usar mandos DualShock 4 en juegos "
        "y homebrew PS5. Corrige desconexiones falsas, asignacion de "
        "mandos entre jugadores, reconexion y compatibilidad con "
        "emuladores. Atajo L1+R1+L2+R2 para reiniciar deteccion. "
        "Antes de actualizar una instancia activa, detenerla con "
        "PoorDS4-stop.elf de la MISMA version. Probado en FW 11.60; "
        "en otros firmwares comprobar manualmente. No autocargar "
        "hasta verificar. SHA-256 del espejo evoX-CoreOS."
    ),
}


def migrar_shadowmountplus(item: dict) -> None:
    """Actualizar betas conocidas a beta8, sin retroceder ni pisar otras ramas."""
    if item.get("id") != "shadowmountplus":
        return
    if item.get("version") == SHADOWMOUNT_171B8["version"]:
        return
    versiones_previas = {
        "1.7-beta5fix1", "1.7beta5-fix1", "1.7beta5",
        "1.7beta6", "1.7beta6-fix1", "1.7beta6-fix2",
        "1.7beta7",
    }
    if str(item.get("version")) not in versiones_previas:
        return
    if str(item.get("source", "")).rstrip("/") != SHADOWMOUNT_171B8["source"]:
        raise ValueError("Origen inesperado para ShadowMountPlus")
    item.update(SHADOWMOUNT_171B8)
    print("ACTUALIZADO: ShadowMountPlus -> 1.7beta8 (ELF catalogado)")


def migrar_poords4(item: dict) -> None:
    if item.get("id") != "poords4":
        return
    if version_numerica(item.get("version", "")) >= version_numerica(POORDS4_020["version"]):
        return
    if str(item.get("source", "")).rstrip("/") != POORDS4_020["source"]:
        raise ValueError("Origen inesperado para PoorDS4")
    item.update(POORDS4_020)
    print("ACTUALIZADO: PoorDS4 -> v0.2.0 (ELF verificado)")


# Unico binario de uso normal. Excluir ps5-signal-dev.elf (servidor de pruebas).
PS5_SIGNAL = {
    "name": "PS5 Signal", "filename": "ps5-signal.elf",
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
    "last_update": "2026-10-17", "version": "v0.2.0",
    "category": "PERSONALIZACION",
    "checksum": "189b51ac204600f40d4aa9adc8394e897decf96042689c2066d9292b47fd173e",
    "icon_key": "ps5-signal", "id": "ps5-signal",
}



# Releases ELF estables comprobadas contra los activos y sus SHA-256 oficiales.
# El pin solo se aplica a versiones antiguas; no bloquea futuras releases.
# Permite incorporar estas novedades tambien con --offline, sin tocar otros IDs.
RELEASES_VERIFICADAS = {
    "ps5upload": {
        "repo": "phantomptr/ps5upload",
        "version": "v7.1.13",
        "filename": "ps5upload-7.1.13.elf",
        "checksum": "46bb7dc0e7f28ded2859ac4392c151e39010354c79de2f323d73aaa861287a30",
        "last_update": "2026-10-21",
        "category": "ARCHIVOS / RED",
    },
    "patchdl": {
        "repo": "knutwurst/ps5-patchdl",
        "version": "v0.2.1",
        "filename": "patchdl_0.2.1.elf",
        "checksum": "5458739714d93ad807f3720ff3a2107687bf18be6e238c3f531a93f55d3467b7",
        "last_update": "2026-10-17",
        "category": "DESCARGAS / TIENDAS",
    },
}


def aplicar_release_verificada(item: dict) -> None:
    """Actualizar solo si es el mismo upstream y una version anterior."""
    verificada = RELEASES_VERIFICADAS.get(item.get("id"))
    if not verificada:
        return
    if github_repo(item) != verificada["repo"]:
        raise ValueError("Origen inesperado en " + str(item.get("id")))
    if version_numerica(item.get("version", "")) >= version_numerica(verificada["version"]):
        return
    tag = verificada["version"]
    archivo = verificada["filename"]
    url = f"https://github.com/{verificada['repo']}/releases/download/{tag}/{archivo}"
    item.update(
        version=tag, filename=archivo, url=url, source_direct=url,
        checksum=verificada["checksum"], last_update=verificada["last_update"],
        category=verificada["category"],
    )
    print(f"ACTUALIZADO (ELF verificado): {item['id']} -> {tag}")



# Nuevos ELF oficiales. La rutina refrescar() mantiene futuras versiones al dia.
NUEVOS_PERSONALIZACION = (
    {
        "id": "ps5-theme", "icon_key": "ps5-theme", "name": "PS5 Theme",
        "filename": "ps5-theme.elf", "version": "v1.60",
        "url": "https://github.com/Blaze414/ps5-theme/releases/download/v1.60/ps5-theme.elf",
        "source": "https://github.com/Blaze414/ps5-theme/releases",
        "source_direct": "https://github.com/Blaze414/ps5-theme/releases/download/v1.60/ps5-theme.elf",
        "checksum": "732fbc113770bdac4dc0dfea1b8c6a9ecdc4bacdacb7ab0f6ed3e11987409a61",
        "category": "PERSONALIZACION", "last_update": "2026-10-14",
        "description": (
            "Temas PS5: iconos, fondos, logos, musica y sonidos; gestor en consola "
            "y red local puerto 8095. No necesita PC ni modifica archivos de sistema: "
            "usa overlays de solo lectura. Firmware hasta 13.60 segun el autor; "
            "probado en 13.42. Evitar conflictos con LiveShell al cambiar fondos."
        ),
    },
    {
        "id": "liveshell", "icon_key": "liveshell", "name": "LiveShell Engine",
        "filename": "liveshell.elf", "version": "v1.2",
        "url": "https://github.com/ZiZc3/LiveShell/releases/download/v1.2/liveshell.elf",
        "source": "https://github.com/ZiZc3/LiveShell/releases",
        "source_direct": "https://github.com/ZiZc3/LiveShell/releases/download/v1.2/liveshell.elf",
        "checksum": "5d4f9f92440c2b0c100dfc982953e1fb24ec198ea259dcb0a3bb85c6176334a0",
        "category": "PERSONALIZACION", "last_update": "2026-10-16",
        "description": (
            "Fondos animados de video en el menu PS5, con biblioteca de juegos "
            "y modo PS Store. MP4 H.264/HEVC 1080p (no 4K); videos en "
            "/data/LiveShell/video o carpeta liveshell del USB. Gestor en "
            "la propia consola. No usar a la vez que otro overlay de fondo sin probar."
        ),
    },
)


def migrar_signal(item: dict) -> None:
    if version_numerica(item.get("version", "")) < version_numerica(PS5_SIGNAL["version"]):
        preserved = {k: item[k] for k in ("id", "icon_key") if k in item}
        item.update(PS5_SIGNAL)
        item.update(preserved)
        print("ACTUALIZADO: PS5 Signal -> v0.2.0")


def migrar_overlay(item: dict) -> None:
    # Conservar el mismo ID/icono para favoritos y ajustes del usuario.
    # Solo sustituir la version antigua conocida, nunca pisar una futura.
    if (str(item.get("version")) in {"v1.0.15", "1.0.15"}
            or "/v1.0.15/" in str(item.get("url", ""))):
        item.update(OVERLAY_RELEASE)
        print("ACTUALIZADO: PS5 Hardware Overlay -> KUS 1.0.18 (tag v0.0.18)")


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
    # Mismo directorio para que os.replace mantenga atomicidad por archivo.
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
        "User-Agent": "HiddenKernelLab-Catalog-Updater/2026-10-16",
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
    # Si la version mostrada lleva anotaciones, obtener la etiqueta del enlace.
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
    # No seleccionar compilaciones debug, PS4 ni archivos de test.
    return list(dict.fromkeys(x for x in found if x.lower().endswith(".elf")))


def elegir_activo(item: dict, repo: str, release: dict) -> tuple | None:
    if release.get("draft") or release.get("prerelease"):
        return None
    tag = str(release.get("tag_name") or "")
    if not tag or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", tag):
        return None
    old_tag = str(item.get("version", ""))
    # Conservar builds especiales; normalizar 'v' sin asumir firmware compatible.
    if version_numerica(tag) <= version_numerica(old_tag):
        return None
    # No confundir series experimentales/forks de nomenclatura arbitraria.
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
            + str(item["version"]) + ". "
            + ("Desde 7.0.34 corrige nombres de archivos con diferencias "
               "entre mayusculas y minusculas en juegos Unity al subir carpetas "
               "o convertir juegos, evitando cierres al arrancar. "
               if version_numerica(item.get("version")) >= (7, 0, 34, 0) else "")
            + ("Desde 7.1.13 permite subir archivos y enviar ELF al cargador "
               "desde el navegador, con confirmacion explicita; mejora "
               "movimientos SMB. "
               if version_numerica(item.get("version")) >= (7, 1, 13, 0) else "")
            + "Consultar cambios upstream."
        )
    elif ident == "patchdl" and version_numerica(item.get("version")) >= (0, 2, 1, 0):
        item["description"] = (
            "PatchDL " + str(item["version"]) + ": descarga e instala parches "
            "oficiales de juegos PS4/PS5 ya instalados; cola, reanudacion "
            "y verificacion tras instalar. Desde 0.2.1 distingue errores de "
            "DNS, conexion y servidor, ofrece diagnostico e informe por QR, "
            "y deja sin actualizar por defecto las apps firmadas por Sony "
            "instaladas fuera de Store (Sideloaded), salvo activacion manual. "
            "El autor declara FW 1.00-13.60 y prueba en 11.60. No es para "
            "descargar juegos ni para parches FPKG; compatibilidad con "
            "ShadowMountPlus no confirmada. Consultar notas upstream."
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
        # No afirmar compatibilidad 1.00-5.50 en la rama 0.6.x.
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
    name = str(item.get("name", ""))
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


# Incorporaciones nuevas: resolver version, URL y SHA-256 desde GitHub.
# Nunca inventar un checksum ni anadir un ELF sin asset oficial verificable.
NUEVAS_FUENTES = (
    ("pscloud", "PSCloud", "bc160201983/ps5-cloud-save",
     "pscloud-dashboard.elf", "TRUCOS / PARTIDAS",
     "Copias de partidas PS5 por USB/WebDAV y sincronizacion LAN. "
     "Panel web 8082. Edicion y sincronizacion avanzada experimentales; "
     "probar restauraciones antes de confiar en copias automaticas."),
    ("recompstore", "RecompStore", "elripalda/RecompStore",
     "RecompStore-Installer.elf", "DESCARGAS / TIENDAS",
     "Instalador de tienda de ports recompilados, emuladores y homebrew. "
     "Requiere K-Stuff, elfldr 9021 y ShadowMountPlus 1.7 beta5 o superior. "
     "Los juegos requieren sus propios archivos legales."),
)


def incorporar_nuevos_oficiales(activos: list[dict], offline: bool) -> None:
    """No duplica entradas; requiere asset ELF oficial con SHA-256 de GitHub."""
    if offline:
        return
    for ident, nombre, repo, asset_name, categoria, descripcion in NUEVAS_FUENTES:
        if any(x.get("id") == ident for x in activos):
            continue
        try:
            release = solicitar_release(repo)
            if release.get("draft") or release.get("prerelease"):
                continue
            tag = str(release.get("tag_name") or "")
            if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", tag):
                continue
            esperado = (f"https://github.com/{repo}/releases/download/"
                        f"{tag}/{asset_name}")
            assets = [a for a in release.get("assets", [])
                      if a.get("name") == asset_name
                      and a.get("browser_download_url") == esperado
                      and SHA256.fullmatch(str(a.get("digest", "")).removeprefix("sha256:"))
                      and str(a.get("digest", "")).startswith("sha256:")]
            if len(assets) != 1:
                print(f"OMITIDO {nombre}: ELF o SHA-256 oficial no verificable")
                continue
            activos.append({
                "id": ident, "icon_key": ident, "name": nombre,
                "filename": asset_name, "version": tag, "url": esperado,
                "source": f"https://github.com/{repo}/releases",
                "source_direct": esperado,
                "checksum": assets[0]["digest"][7:],
                "last_update": str(release.get("published_at") or "")[:10],
                "category": categoria, "description": descripcion,
            })
            print(f"ANADIDO: {nombre} {tag} (SHA-256 oficial)")
        except (OSError, ValueError, KeyError, TimeoutError) as exc:
            print(f"OMITIDO {nombre}: no se pudo verificar release: {exc}")


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
    for nuevo in NUEVOS_PERSONALIZACION:
        if not any(x.get("id") == nuevo["id"] for x in activos):
            activos.append(dict(nuevo))
            print("AÑADIDO:", nuevo["name"], nuevo["version"])
    for nuevo in NUEVOS_ELF_VERIFICADOS:
        if not any(x.get("id") == nuevo["id"] for x in activos):
            activos.append(dict(nuevo))
            print("AÑADIDO:", nuevo["name"], nuevo["version"])
    incorporar_nuevos_oficiales(activos, offline)
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
        if item.get("id") == "garlic-savemgr":
            migrar_garlic(item)
        if item.get("id") == "shadowmountplus":
            migrar_shadowmountplus(item)
        if item.get("id") == "poords4":
            migrar_poords4(item)
        aplicar_release_verificada(item)
        if item.get("id") == "ftpsrv":
            # Migrar la version antigua una sola vez; permitir futuras
            # versiones estables verificadas de Drakmor, sin retroceder.
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

    # No regenerar iconos ya personalizados, incluso si cambia el orden.
    imagenes = {}
    for item in resultado:
        key = item["icon_key"]
        if key in imagenes:
            raise ValueError("icon_key duplicado: " + key)
        imagenes[key] = original_icons.get(key) or icono_nuevo(item)
    icon_data = {"icons": imagenes}
    if len(json.dumps(icon_data).encode("utf-8")) > 4 * 1024 * 1024:
        raise ValueError("El archivo de iconos supera 4 MB")

    # Ambas estructuras se comprueban antes de tocar los archivos originales.
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
