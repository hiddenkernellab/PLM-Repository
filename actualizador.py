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

UA = "HiddenKernel-Repository/1.0"
TOKEN = os.getenv("GITHUB_TOKEN", "")
PAGES = "https://hiddenkernellab.github.io/PLM-Repository"
MIRROR = Path("payloads")

APPS = [
    # SYSTEM
    dict(name="Payload Manager", repo="itsPLK/ps5-payload-manager",
         match=["pldmgr"], exclude=["debug"], category="SISTEMA",
         desc="Gestor de payloads para PS5."),
    dict(name="PLDMGR Install & Update",
         local_path="payloads/PLDMGR-Install-Update.elf",
         local_version="v0.1-test",
         source="https://github.com/hiddenkernellab/PLDMGR-install-update",
         category="SISTEMA",
         desc="Instala o actualiza Payload Manager y configura automáticamente el autoloader."),
    dict(name="Lapy JB Daemon", repo="itsPLK/PS5-Lapy-JB-Daemon",
         match=["lapy", "daemon"], category="SISTEMA",
         desc="Daemon jailbreak-on-demand para herramientas compatibles."),
    dict(name="nanoDNS", repo="drakmor/nanoDNS",
         match=["nanodns"], category="SISTEMA",
         desc="Servidor DNS ligero para PS5."),
    dict(name="WebKit Autoloader", repo="itsPLK/ps5-webkit-autoloader",
         match=["webkit-autoloader-installer"], exclude=["host"], category="SISTEMA",
         desc="Instalador del cargador automático basado en WebKit."),

    # HEN
    dict(name="etaHEN", repo="etaHEN/etaHEN",
         match=["etahen"], category="HEN",
         desc="AIO Homebrew Enabler para PS5."),
    dict(name="OnionHEN", repo="aydencharles/onionHEN",
         match=["onionhen"], archive=["onionhen"], category="HEN",
         desc="HEN y Toolbox todo-en-uno para PS5."),
    dict(name="PIZZA-HEN", repo="Michele-M-Media/PIZZA-HEN",
         match=["pizza"], archive=["pizza"], category="HEN",
         desc="Entorno homebrew todo-en-uno para PS5."),

    # GAMES
    dict(name="kstuff lite", repo="EchoStretch/kstuff-lite",
         match=["kstuff"], exclude=["debug"], category="JUEGOS",
         desc="Versión ligera de kstuff para PS5.",
         channels=["beta"]),
    dict(name="ShadowMountPlus", repo="drakmor/ShadowMountPlus",
         match=["shadowmount"], archive=["shadowmount"], category="JUEGOS",
         desc="Montaje automático de contenido compatible en PS5.",
         stable_override=r"(?i)^1\.6beta", always_alpha=True),
    dict(name="APR Emu Updater", repo="tsuramatsu1/apr-emu-updater",
         match=["apr_emu_updater"], category="JUEGOS",
         desc="Actualizador y gestor de APR Emu para títulos compatibles."),
    dict(name="Game Compressor", repo="juma-sayeh/PS5-Game-Compressor",
         match=["game-compressor"], category="JUEGOS",
         desc="Herramienta para comprimir y gestionar imágenes de juegos PS5."),
    dict(name="PS5 App Dumper", repo="EchoStretch/ps5-app-dumper",
         match=["app", "dumper"], archive=["dumper"], category="JUEGOS",
         desc="Payload para volcar aplicaciones PS5."),

    # TOOLS
    dict(name="ELF Arsenal",
         api="https://git.etawen.dev/api/v1/repos/soniciso/elf-arsenal/releases",
         source="https://git.etawen.dev/soniciso/elf-arsenal/releases",
         match=["elf-arsenal"], category="UTILIDADES",
         desc="Colección de payloads ELF en una sola herramienta."),
    dict(name="FTP Server PS5", repo="ps5-payload-dev/ftpsrv",
         match=["ftpsrv"], prefer=["ps5"], exclude=["ps4", "install"], category="UTILIDADES",
         desc="Servidor FTP para PS5."),
    dict(name="Garlic Save Manager",
         api="https://git.etawen.dev/api/v1/repos/earthonion/garlic-savemgr/releases",
         source="https://git.etawen.dev/earthonion/garlic-savemgr/releases",
         match=["garlic-savemgr"], exclude=["worker"], category="UTILIDADES",
         desc="Gestor de partidas guardadas de PS5."),
    dict(name="PoorDS4", repo="ItsBlurf/PoorDS4",
         match=["poords4"], exclude=["status", "stop"], archive=["poords4"], category="UTILIDADES",
         desc="Compatibilidad inalámbrica con DualShock 4 en PS5."),
    dict(name="Prospero Manager", repo="notmaj0r/ProsperoMgr",
         match=["prospero"], archive=["prospero"], category="UTILIDADES",
         desc="Gestor web todo-en-uno para PS5."),
    dict(name="Common FPS PS5", repo="porhe911/Common-FPS-for-PS5",
         match=["common", "fps"], exclude=["plugin"], archive=["common"], category="UTILIDADES",
         desc="Overlay y monitorización de FPS para PS5."),

    # STORES / DOWNLOADERS
    dict(name="Pegasus DL", repo="pegasus-ps5/pegasus-dl",
         match=["pegasus"], category="TIENDAS",
         desc="Gestor de descargas y catálogos mediante interfaz web local."),
    dict(name="Spectrum Library", repo="Phoenixx1202/Spectrum-Library",
         match=["spectrum"], archive=["spectrum"], category="TIENDAS",
         desc="Biblioteca y utilidades Spectrum para PS5."),
]

FIXED = [
    dict(
        name="etaHEN", channel="beta", filename="etaHEN-2.6B.bin",
        url=("https://raw.githubusercontent.com/zecoxao/zecoxao.github.io/"
             "refs/heads/main/luasauce/payloads/etaHEN-2.6B.bin"),
        source=("https://github.com/zecoxao/zecoxao.github.io/"
                "tree/main/luasauce/payloads"),
        desc="AIO Homebrew Enabler para PS5. Build 2.6B de pruebas.",
        date="2026-05-25", version="2.6B", category="HEN"
    )
]

CAT_ORDER = {"SISTEMA": 0, "HEN": 1, "JUEGOS": 2, "UTILIDADES": 3, "TIENDAS": 4}

def req(url, timeout=60):
    h = {"User-Agent": UA}
    if "api.github.com" in url:
        h["Accept"] = "application/vnd.github+json"
        h["X-GitHub-Api-Version"] = "2022-11-28"
        if TOKEN:
            h["Authorization"] = f"Bearer {TOKEN}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout)

def get_json(url):
    with req(url, 30) as r:
        return json.load(r)

def get_bytes(url):
    with req(url, 180) as r:
        return r.read()

def api_url(app):
    if app.get("local_path"):
        return None
    return app.get("api") or f'https://api.github.com/repos/{app["repo"]}/releases?per_page=100'

def source_url(app):
    if app.get("source"):
        return app["source"]
    return f'https://github.com/{app["repo"]}/releases'

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
                    source_direct=u, checksum=hashlib.sha256(data).hexdigest())

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
                checksum=hashlib.sha256(data).hexdigest())

def display_name(name, ch):
    return name if ch == "stable" else f"{name} ({'Beta' if ch == 'beta' else 'INESTABLE'})"

def display_desc(desc, ch):
    prefix = {"stable": "ESTABLE", "beta": "BETA", "alpha": "ALPHA / TEST / INESTABLE"}[ch]
    return f"{prefix} · {desc}"

def candidates(rels, app, ch):
    if ch == "stable" and app.get("stable_override"):
        rx = re.compile(app["stable_override"])
        forced = [r for r in rels if rx.search(rtext(r))]
        if forced:
            return sorted(forced, key=rtime, reverse=True)
    return [r for r in rels if channel(r) == ch]

def make_entry(app, rel, p, ch):
    raw = rel.get("published_at") or rel.get("created_at") or ""
    return {
        "name": display_name(app["name"], ch),
        "filename": p["filename"],
        "url": p["url"],
        "source": source_url(app),
        "source_direct": p["source_direct"],
        "description": display_desc(app["desc"], ch),
        "last_update": raw[:10] if raw else "",
        "version": rel.get("tag_name") or rel.get("name") or "unknown",
        "category": app["category"],
        "checksum": p["checksum"],
    }

def process_local(app):
    path = Path(app["local_path"])
    if not path.is_file():
        print(f'[WARN] Falta archivo local para {app["name"]}: {path}')
        return []

    data = path.read_bytes()
    filename = path.name
    public = f"{PAGES}/{path.as_posix()}"
    version = app.get("local_version", "test")

    entry = {
        "name": app["name"],
        "filename": filename,
        "url": public,
        "source": source_url(app),
        "source_direct": public,
        "description": f'TEST · {app["desc"]}',
        "last_update": datetime.utcnow().strftime("%Y-%m-%d"),
        "version": version,
        "category": app["category"],
        "checksum": hashlib.sha256(data).hexdigest(),
    }
    return [entry]


def process(app):
    if app.get("local_path"):
        return process_local(app)

    rels = get_json(api_url(app))
    if not isinstance(rels, list):
        rels = [rels]
    rels = sorted([r for r in rels if not r.get("draft", False)], key=rtime, reverse=True)

    selected = {}
    wanted_channels = app.get("channels", ("stable", "beta", "alpha"))
    for ch in wanted_channels:
        for rel in candidates(rels, app, ch):
            try:
                p = payload_for(app, rel, ch)
            except Exception as e:
                print(f'  fallo {rtext(rel)}: {e}')
                continue
            if p:
                selected[ch] = (rel, p)
                break

    stable_t = rtime(selected["stable"][0]) if "stable" in selected else 0
    output = []
    if "stable" in selected:
        output.append(make_entry(app, *selected["stable"], "stable"))

    for ch in ("beta", "alpha"):
        if ch not in wanted_channels or ch not in selected:
            continue
        # No mostramos prereleases históricas más viejas que la recomendada,
        # salvo que el proyecto las marque como relevantes.
        if rtime(selected[ch][0]) > stable_t or app.get(f"always_{ch}", False) or "stable" not in selected:
            output.append(make_entry(app, *selected[ch], ch))
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
        "description": display_desc(x["desc"], ch),
        "last_update": x["date"],
        "version": x["version"],
        "category": x["category"],
        "checksum": hashlib.sha256(data).hexdigest(),
    }

def sort_key(x):
    n = x["name"]
    ch = 2 if "(INESTABLE)" in n else 1 if "(Beta)" in n else 0
    base = n.replace(" (Beta)", "").replace(" (INESTABLE)", "")
    return CAT_ORDER.get(x.get("category",""), 99), base.lower(), ch

def main():
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
        json.dump({"name": "HiddenKernel Repository", "payloads": payloads},
                  f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Generado payloads.json con {len(payloads)} entradas.")

if __name__ == "__main__":
    main()
