#!/usr/bin/env python3
import re
import urllib.request
from pathlib import Path

BASE_URL = (
    "https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/"
    "1a632c6f7572bcab8e5092e0d8e4cfbc62e25805/actualizador.py"
)
MARKER = "# HK-CATALOG-2026-09-25"

def download_base():
    req = urllib.request.Request(
        BASE_URL,
        headers={
            "User-Agent": "HiddenKernel-Updater-Bootstrap/1.0",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")

def replace_once(s, old, new, label):
    count = s.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: se esperaba exactamente 1 coincidencia y hay {count}"
        )
    return s.replace(old, new, 1)

def build_updated_source():
    s = download_base()

    s = replace_once(
        s,
r'''    dict(name="ps5upload", repo="phantomptr/ps5upload",
         match=["ps5upload"], category="ARCHIVOS / PC",
         desc=("Transfiere archivos entre PS5 y PC/Android con control de integridad y soporte para reanudar envios.")),
''',
r'''    dict(name="ps5upload", repo="phantomptr/ps5upload",
         match=["ps5upload"], category="ARCHIVOS / PC",
         channels=["stable"], single_latest=True,
         desc=("Transfiere archivos entre PS5 y PC/Android con control de integridad y soporte para reanudar envios.")),
    dict(name="ftpsrv Drakmor", repo="drakmor/ftpsrv",
         match=["ftpsrv"], prefer=["ps5"], exclude=["ps4", "autopause"],
         category="ALTERNATIVOS", channels=["stable"], single_latest=True,
         desc=("Fork de ftpsrv orientado a PS5 con /proc, utilidades LOWER/UPPER y "
               "soporte reciente de descifrado SELF en firmwares altos.")),
''',
        "ps5upload / ftpsrv Drakmor",
    )

    s = replace_once(
        s,
r'''    # PKG / INSTALACION
    dict(name="singleDPI", repo="MaxMilu/ps5-direct-package-installer",
''',
r'''    # PKG / INSTALACION
    dict(name="PKG Manager", repo="itsPLK/ps5-pkg-manager",
         match=["pkg-manager"], category="PKG / INSTALACION",
         channels=["stable"], single_latest=True,
         desc=("Gestor de PKG con instalacion local, Direct Install y recursos SMB. "
               "La rama 1.3 corrige la instalacion consecutiva en FW 9.60+ y mejora bibliotecas grandes.")),
    dict(name="singleDPI", repo="MaxMilu/ps5-direct-package-installer",
''',
        "PKG Manager",
    )

    s = replace_once(
        s,
r'''    # UTILIDADES
    dict(name="garlic-savemgr",
''',
r'''    # UTILIDADES
    dict(name="ps5debug-NG", repo="Pharaoh2k/ps5debug-NG",
         match=["ps5debug-ng"], category="UTILIDADES",
         channels=["stable"], single_latest=True,
         desc=("Servidor de depuracion, memoria y herramientas para PS5. "
               "La rama 1.3.2 prioriza correcciones de escritura, sesiones y escaneo.")),
    dict(name="garlic-savemgr",
''',
        "ps5debug-NG",
    )

    s = replace_once(
        s,
r'''    # MANDOS
    dict(name="Ghostcontrol", optional=True,
''',
r'''    # ALTERNATIVOS / USO AVANZADO
    dict(name="PS5 BackPork", repo="BestPig/BackPork",
         match=["backpork"], category="ALTERNATIVOS",
         channels=["stable"], single_latest=True,
         desc=("Sideload de librerias de sistema para compatibilidad/backports. "
               "No debe ejecutarse junto con los backports PKG de ShadowMountPlus 1.7.")),

    # MANDOS
    dict(name="Ghostcontrol", optional=True,
''',
        "PS5 BackPork",
    )

    s = replace_once(
        s,
r'''    dict(name="Spectrum Library", repo="Phoenixx1202/Spectrum-Library",
         match=["spectrum"], archive=["spectrum"], category="DESCARGAS",
         desc=("Biblioteca y gestor de descargas con portadas, grupos, cola "
               "y selector de destino.")),
]
''',
r'''    dict(name="Spectrum Library", repo="Phoenixx1202/Spectrum-Library",
         match=["spectrum"], archive=["spectrum"], category="DESCARGAS",
         desc=("Biblioteca y gestor de descargas con portadas, grupos, cola "
               "y selector de destino.")),

    # FPKG INTEGRADO
    dict(name="FPKG Integrado - Kstuff Drakmor", optional=True,
         catalog_url=("https://nexgen999.github.io/PS5-Super-PLDMGR-Auto-Updater/"
                      "json/PS5_Beta.json"),
         catalog_name_regex=[r"^Kstuff .* Fpkg Dr Test\d+$"],
         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",
         category="FPKG INTEGRADO",
         status="EXPERIMENTAL / FPKG",
         compatibility="segun build; validar firmware antes de usar",
         desc=("Rama Kstuff de pruebas FPKG de Drakmor con el flujo PPR/A53 integrado. "
               "Se mantiene separada de kstuff-lite oficial.")),
    dict(name="FPKG Integrado - ShadowMountPlus", repo="drakmor/ShadowMountPlus",
         match=["shadowmount"], archive=["shadowmount"],
         channels=["beta"], single_latest=True,
         category="FPKG INTEGRADO",
         install_filename="fpkg-integrado-shadowmountplus.elf",
         desc=("ShadowMountPlus 1.7 para acompañar la rama Kstuff/PPR integrada. "
               "Se mantiene como entrada separada para poder actualizarlo o aislar fallos.")),
    dict(name="FPKG AIO - A53+Kstuff+SMP 3in1", optional=True,
         catalog_url=("https://nexgen999.github.io/PS5-Super-PLDMGR-Auto-Updater/"
                      "json/PS5_Beta.json"),
         catalog_name_regex=[r"^A53 Kstuff Shadowmountplus 3In1$"],
         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",
         category="FPKG INTEGRADO",
         status="EXPERIMENTAL / AIO",
         compatibility="experimental; usar solo para pruebas",
         desc=("AIO experimental que agrupa A53, Kstuff y ShadowMountPlus. "
               "No sustituye al stack por piezas cuando se busca aislar fallos.")),

    # FPKG MODULAR
    dict(name="FPKG Modular - Kstuff Lite", repo="EchoStretch/kstuff-lite",
         match=["kstuff"], exclude=["debug"],
         channels=["stable"], single_latest=True,
         category="FPKG MODULAR",
         install_filename="fpkg-modular-kstuff-lite.elf",
         desc=("Kstuff Lite oficial para el stack FPKG modular. "
               "En 1.11 incorpora soporte FPKG y soporte de firmware ampliado.")),
    dict(name="FPKG Modular - ShadowMountPlus", repo="drakmor/ShadowMountPlus",
         match=["shadowmount"], archive=["shadowmount"],
         channels=["beta"], single_latest=True,
         category="FPKG MODULAR",
         install_filename="fpkg-modular-shadowmountplus.elf",
         desc=("ShadowMountPlus 1.7 para el stack FPKG modular. "
               "Se carga separado del A53 para poder diagnosticar cada pieza.")),
    dict(name="A53 PPR Modular 1.00-11.40", optional=True,
         catalog_url=("https://nexgen999.github.io/PS5-Super-PLDMGR-Auto-Updater/"
                      "json/PS5_Beta.json"),
         catalog_name_regex=[r"^A53 Ppr Install 1140 .*"],
         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",
         category="FPKG MODULAR",
         status="EXPERIMENTAL / A53",
         compatibility="FW 1.00-11.40",
         desc=("A53/PPR separado para el stack modular FPKG. "
               "Usar junto con Kstuff Lite y ShadowMountPlus compatibles.")),
    dict(name="A53 PPR Modular 11.60", optional=True,
         catalog_url=("https://nexgen999.github.io/PS5-Super-PLDMGR-Auto-Updater/"
                      "json/PS5_Beta.json"),
         catalog_name_regex=[r"^A53 Ppr Install 1160 .*"],
         source="https://github.com/nexgen999/PS5-Super-PLDMGR-Auto-Updater",
         category="FPKG MODULAR",
         status="EXPERIMENTAL / A53",
         compatibility="FW 11.60",
         desc=("A53/PPR separado especifico para 11.60 dentro del stack modular FPKG. "
               "No usar la variante 11.40 en una 11.60.")),
]
''',
        "ramas FPKG",
    )

    s = s.replace('category="PRUEBAS FPKG",', 'category="FPKG LEGACY",')

    s = replace_once(
        s,
r'''CAT_ORDER = {"ESENCIALES": 0, "HEN / AIO": 1, "SISTEMA": 2, "ARCHIVOS / PC": 3, "PKG / INSTALACION": 4, "JUEGOS / COMPATIBILIDAD": 5, "UTILIDADES": 6, "MANDOS": 7, "DESCARGAS": 8, "PRUEBAS FPKG": 9, "ALTERNATIVOS": 10}''',
r'''CAT_ORDER = {"ESENCIALES": 0, "HEN / AIO": 1, "SISTEMA": 2, "ARCHIVOS / PC": 3, "PKG / INSTALACION": 4, "JUEGOS / COMPATIBILIDAD": 5, "UTILIDADES": 6, "MANDOS": 7, "DESCARGAS": 8, "FPKG INTEGRADO": 9, "FPKG MODULAR": 10, "FPKG LEGACY": 11, "ALTERNATIVOS": 12}''',
        "orden de categorias",
    )

    s = replace_once(
        s,
r'''    "ps5debug-NG": [
        (r"\b1\.3\.0\b", "VALIDACIÓN PARCIAL EN HARDWARE",
         "La release 1.3.0 se publica como hardware-verified, pero sus propias notas aclaran que algunas familias de firmware compatibles aún no estaban completamente probadas en hardware."),
    ],
''',
r'''    "ps5debug-NG": [
        (r"\b1\.3\.2\b", "MEJORA DE ESTABILIDAD",
         "La release 1.3.2 corrige errores de escritura, tres fallos que terminaban sesiones, un comparador de escaneo y amplía soporte declarado hasta FW 13.60."),
        (r"\b1\.3\.0\b", "VALIDACIÓN PARCIAL EN HARDWARE",
         "La release 1.3.0 se publica como hardware-verified, pero sus propias notas aclaran que algunas familias de firmware compatibles aún no estaban completamente probadas en hardware."),
    ],
    "PKG Manager": [
        (r"\b1\.3\.0\b", "MEJORA DE ESTABILIDAD",
         "La release 1.3.0 corrige instalaciones consecutivas en FW 9.60+ y mejora navegacion/paginacion de recursos SMB grandes."),
    ],
    "ftpsrv Drakmor": [
        (r"1\.16-ng-stable", "ESTABLE SEGÚN DESARROLLADOR",
         "La release 1.16-ng-stable añade /proc, LOWER/UPPER y soporte PS5 declarado hasta FW 13.60."),
    ],
''',
        "estado de payloads nuevos",
    )

    s = replace_once(
        s,
r'''    "PS5 App Dumper": [
        (r"\b1\.11\b", "hasta FW 13.60"),
    ],
''',
r'''    "PS5 App Dumper": [
        (r"\b1\.11\b", "hasta FW 13.60"),
    ],
    "ps5debug-NG": [
        (r"\b1\.3\.2\b", "hasta FW 13.60"),
    ],
    "ftpsrv Drakmor": [
        (r"1\.16-ng-stable", "hasta FW 13.60"),
    ],
    "PS5 BackPork": [
        (r"\b0\.1\b", "hasta FW 12.00"),
    ],
''',
        "compatibilidad payloads nuevos",
    )

    s = replace_once(
        s,
r'''    wanted = {
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
''',
r'''    wanted = {
        str(x).strip().lower()
        for x in app.get("catalog_names", [app["name"]])
    }
    name_regexes = [
        re.compile(str(x), flags=re.I)
        for x in app.get("catalog_name_regex", [])
    ]

    matches = []
    for item in items:
        raw_name = str(item.get("name") or "").strip()
        name = raw_name.lower()
        if name in wanted or any(rx.search(raw_name) for rx in name_regexes):
            matches.append(item)

    if not matches:
        raise RuntimeError(
            f'No se encontró {app["name"]} en el catálogo externo.'
        )

    def catalog_rank(item):
        raw_name = str(item.get("name") or "")
        test = re.search(r"\btest\s*(\d+)\b", raw_name, flags=re.I)
        if test:
            return (1, int(test.group(1)), raw_name.lower())
        return (0, 0, raw_name.lower())

    hit = max(matches, key=catalog_rank) if name_regexes else matches[0]
''',
        "seleccion por regex en catalogos",
    )

    s = replace_once(
        s,
r'''    version = str(hit.get("version") or "unknown")
    pseudo = {
''',
r'''    version = str(hit.get("version") or "unknown")
    if version.strip().lower() in {"source-fixe", "source fixe", "unknown"}:
        version = str(hit.get("name") or version)
    pseudo = {
''',
        "version de builds de mirror",
    )

    s = replace_once(
        s,
r'''    return [{
        "name": app["name"],
        "filename": filename,
        "url": url,
        "source": app.get("source") or hit.get("source") or app["catalog_url"],
        "source_direct": hit.get("source_direct") or url,
        "description": build_description(app, pseudo, ch),
''',
r'''    description = build_description(app, pseudo, ch)
    if app.get("status"):
        description = re.sub(
            r"ESTADO: [^.]+\.",
            f'ESTADO: {app["status"]}.',
            description,
            count=1
        )
    if app.get("compatibility"):
        if "COMPATIBILIDAD:" in description:
            description = re.sub(
                r"COMPATIBILIDAD: [^.]+\.",
                f'COMPATIBILIDAD: {app["compatibility"]}.',
                description,
                count=1
            )
        else:
            description += f' COMPATIBILIDAD: {app["compatibility"]}.'

    return [{
        "name": app["name"],
        "filename": filename,
        "url": url,
        "source": app.get("source") or hit.get("source") or app["catalog_url"],
        "source_direct": hit.get("source_direct") or url,
        "description": description,
''',
        "estado y compatibilidad de catalogos externos",
    )

    return MARKER + "\n" + s

def main():
    target = Path(__file__)
    source = build_updated_source()
    compile(source, str(target), "exec")
    target.write_text(source, encoding="utf-8", newline="\n")
    print("actualizador.py completo generado y validado.")
    print("Ejecutando el actualizador nuevo...")

    ns = {
        "__name__": "__main__",
        "__file__": str(target),
        "__package__": None,
    }
    exec(compile(source, str(target), "exec"), ns, ns)

if __name__ == "__main__":
    main()
