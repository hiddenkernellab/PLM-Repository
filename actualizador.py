#!/usr/bin/env python3
# HiddenKernel CLEAN updater 2026-10-08
# Poda el catalogo actual antes de generar los JSON.
import urllib.request

BASE_URL="https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/0582daf2265993358eb7f4a830db5d360714876a/actualizador.py"

REMOVE_NAMES={
"ELF Arsenal","PSVietHoa WebKit Autoloader","WK Autoloader Relapse (X-F1REBALL-X)",
"ftpsrv Drakmor","FPKG Integrado - Kstuff Drakmor","FPKG Integrado - ShadowMountPlus",
"FPKG AIO - A53+Kstuff+SMP 3in1","FPKG Modular - Kstuff Lite",
"FPKG Modular - ShadowMountPlus","A53 PPR Modular 1.00-11.40","A53 PPR Modular 11.60",
}
REMOVE_CATEGORIES={"FPKG INTEGRADO","FPKG MODULAR"}

ADDITIONS=[
 dict(name="PS5SX2 Installer",repo="Swordpdf/PS5SX2",match=["PS5SX2Installer.elf"],
      category="EMULADORES",channels=["stable"],single_latest=True,elf_only=True,
      install_filename="PS5SX2Installer.elf",
      desc="Instalador oficial de PS5SX2. Instala y mantiene actualizada la build principal del emulador nativo de PS2 para PS5."),
 dict(name="PS5SX2 Helper",repo="Swordpdf/PS5SX2",match=["PS5SXHelper.elf"],
      category="EMULADORES",channels=["stable"],single_latest=True,elf_only=True,
      install_filename="PS5SXHelper.elf",
      desc="Helper oficial requerido por PS5SX2 para los recompiladores y acceso a /data. Usar junto con kstuff."),
 dict(name="XPSemu Helper",optional=True,repo="ZiZc3/XPSemu",match=["helper.elf"],
      category="EMULADORES",channels=["stable","beta","alpha"],
      single_latest=True,elf_only=True,
      install_filename="xpsemu-helper.elf",
      desc=("Helper para XPSemu, emulador nativo de Xbox original en PS5. "
            "Alpha 2 elimina whitelist y admite juegos en USB. "
            "Cargar junto con kstuff; evitar cargar simultaneamente helpers equivalentes.")),
 dict(name="PuckbridgePS5",optional=True,repo="ThisIsAkill/PuckbridgePS5",match=["ghost-control-ps5.elf"],
      category="MANDOS / AUDIO",channels=["stable"],single_latest=True,elf_only=True,
      install_filename="puckbridge-ps5.elf",
      desc="Fork ampliado de Ghostcontrol para Steam Controller 2026 y mandos compatibles, con rumble, gyro, flick stick, motion controls, trigger feedback, remapeo web y perfiles."),
]

def load_base():
    req=urllib.request.Request(BASE_URL,headers={"User-Agent":"HiddenKernel-Clean-Updater/2026-10-08","Cache-Control":"no-cache"})
    with urllib.request.urlopen(req,timeout=60) as r:
        src=r.read().decode("utf-8")
    src=src.replace('if __name__ == "__main__":\n    main()','if __name__ == "__hiddenkernel_base__":\n    main()')
    ns={"__name__":"__hiddenkernel_clean__"}
    exec(compile(src,BASE_URL,"exec"),ns,ns)
    return ns

def clean(ns):
    apps=ns["APPS"]
    out=[]
    for app in apps:
        if app.get("name") in REMOVE_NAMES or app.get("category") in REMOVE_CATEGORIES:
            continue
        # Quita duplicados por nombre conservando la definicion mas reciente.
        out=[x for x in out if x.get("name")!=app.get("name")]
        out.append(app)
    newnames={x["name"] for x in ADDITIONS}
    out=[x for x in out if x.get("name") not in newnames]
    out.extend(ADDITIONS)
    apps[:]=out
    ns["FIXED"][:] = [
        x for x in ns["FIXED"]
        if x.get("name") not in {
            "kstuff-lite FPKG", "ShadowMountPlus FPKG",
            "A53 PPR Install Fast",
        }
        and not (x.get("name") == "etaHEN" and x.get("version") == "2.6B")
        and x.get("category") != "FPKG LEGACY"
    ]
    # Reorganiza entradas utiles existentes sin duplicar ni fijar versiones.
    for app in apps:
        if app.get("name") == "ps5upload":
            app["category"] = "ARCHIVOS / RED"
        elif app.get("name") == "Orbit Store":
            app["category"] = "DESCARGAS"
    curated=ns.get("CURATED_STATUS",{})
    for x in REMOVE_NAMES: curated.pop(x,None)
    curated.update({
      "PS5SX2 Installer":[(r".*","RECOMENDADO / PS2","Usar junto con PS5SX2 Helper, kstuff y ShadowMountPlus.")],
      "PS5SX2 Helper":[(r".*","RECOMENDADO / AUTOLOAD","Upstream recomienda cargar Helper junto con kstuff.")],
      "ps5upload":[(r".*","UPSTREAM / ACTUALIZABLE",
                           "Seguir la ultima release ELF oficial. v6.4.0 corrige instalacion desde enlaces y el helper de PS5.")],
      "Orbit Store":[(r".*","BETA / DESCARGAS",
                           "v0.9.0 mejora la cola y deteccion de SSD M.2; mantener actualizaciones del ELF desde upstream.")],
      "XPSemu Helper":[(r".*","ALPHA / XBOX ORIGINAL",
                           "Alpha 2: helper.elf. No es el emulador completo; requiere la app XPSemu instalada.")],
      "PuckbridgePS5":[(r".*","ESTABLE / MANDOS","Alternativa avanzada a Ghostcontrol; validar el mando antes de autoload.")],
    })

def main():
    ns=load_base()
    ns["extend_hiddenkernel"](ns)
    ns["clean_obsolete_entries"](ns)
    ns["add_curated_evox_elf"](ns)
    ns["apply_hiddenkernel_v2_maintenance"](ns)
    ns["add_verified_elf"](ns)
    ns["force_ascii_descriptions"](ns)
    clean(ns)
    # El generador original consulta siempre las releases oficiales de cada repo:
    # PS5Upload 6.4.0 y Orbit Store 0.9.0 se seleccionan automaticamente.
    ns["generate_catalog"]()

if __name__=="__main__":
    main()
