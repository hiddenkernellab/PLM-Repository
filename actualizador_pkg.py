#!/usr/bin/env python3
# HiddenKernel PKG updater reparado: conserva el generador PKG actual de main.
# Spectrum Library se mantiene en su actualizador oficial de HiddenKernel.
import urllib.request
URL="https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/0582daf2265993358eb7f4a830db5d360714876a/actualizador_pkg.py"
req=urllib.request.Request(URL,headers={"User-Agent":"HiddenKernel-PKG-Updater/2026-10-07","Cache-Control":"no-cache"})
with urllib.request.urlopen(req,timeout=60) as r:
    code=r.read().decode("utf-8")
exec(compile(code,URL,"exec"),globals(),globals())
