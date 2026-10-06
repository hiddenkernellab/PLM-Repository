#!/usr/bin/env python3
# HiddenKernel actualizador - sigue el main actual y anade novedades seleccionadas.
# No hace push ni modifica GitHub.
import urllib.request
BASE_URL="https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/main/actualizador.py"
def load_current():
    req=urllib.request.Request(BASE_URL,headers={"User-Agent":"HiddenKernel-Store/1.0","Cache-Control":"no-cache"})
    with urllib.request.urlopen(req,timeout=60) as r: source=r.read().decode("utf-8")
    ns={"__name__":"hiddenkernel_current","__file__":BASE_URL}
    exec(compile(source,BASE_URL,"exec"),ns,ns); return ns
def add_news(ns):
    apps=ns["APPS"]
    additions=[
      dict(name="PS5 Library",repo="deox1111/ps5-library",match=["ps5-library.elf"],category="DESCARGAS",channels=["stable"],single_latest=True,elf_only=True,desc="Biblioteca y storefront nativo para PS5 pensado para TV y mando. Navegacion con D-pad, busqueda, filtros y descargas reanudables. Requiere kstuff y ShadowMountPlus"),
      dict(name="PS5 Tailscale",repo="holdmysocks/ps5-tailscale",match=["*.elf"],category="RED",channels=["stable"],single_latest=True,elf_only=True,desc="Tailscale para PS5. Acceso remoto a la consola mediante una tailnet y soporte para usos de red y streaming remoto"),
      dict(name="PS5 aria2",repo="owendswang/ps5-aria2",match=["*.elf"],category="DESCARGAS",channels=["stable"],single_latest=True,elf_only=True,desc="Motor aria2 nativo para PS5 con descargas reanudables y multiples conexiones"),
    ]
    names={a["name"] for a in additions}
    apps[:]=[a for a in apps if str(a.get("name") or "") not in names]; apps.extend(additions)
    for name in names:
        ns["CURATED_STATUS"][name]=[(r".*","ESTABLE / UPSTREAM OFICIAL","Seguir siempre el ELF estable mas reciente del upstream.")]
def main():
    current=load_current(); base=current["load_current_wrapper"](); ns=base["load_base_namespace"]()
    base["extend_hiddenkernel"](ns); current["clean_obsolete_entries"](ns); current["add_curated_evox_elf"](ns)
    current["apply_hiddenkernel_v2_maintenance"](ns); add_news(ns); current["force_ascii_descriptions"](ns); ns["main"]()
if __name__=="__main__": main()
