import hashlib
import io
import json
import os
import re
import urllib.request
import zipfile

from datetime import datetime
from pathlib import Path


USER_AGENT = "HiddenKernel-Repository/1.0"
TOKEN = os.getenv("GITHUB_TOKEN", "")

PAGES_BASE = "https://hiddenkernellab.github.io/PLM-Repository"
MIRROR_DIR = Path("payloads")


APPS = [

    # =========================================================
    # SYSTEM
    # =========================================================

    {
        "name": "Payload Manager",
        "repo": "itsPLK/ps5-payload-manager",
        "asset_contains": ["pldmgr"],
        "asset_excludes": ["debug"],
        "description": "Gestor web de payloads para PS5.",
        "category": "SYSTEM"
    },

    {
        "name": "Lapy JB Daemon",
        "repo": "itsPLK/PS5-Lapy-JB-Daemon",
        "asset_contains": ["lapy", "daemon"],
        "description": "Daemon jailbreak-on-demand para herramientas compatibles.",
        "category": "SYSTEM"
    },

    {
        "name": "nanoDNS",
        "repo": "drakmor/nanoDNS",
        "asset_contains": ["nanodns"],
        "description": "Servidor DNS ligero para PS5.",
        "category": "SYSTEM"
    },

    {
        "name": "WebKit Autoloader",
        "repo": "itsPLK/ps5-webkit-autoloader",
        "asset_contains": ["webkit-autoloader-installer"],
        "asset_excludes": ["host"],
        "description": "Instalador del cargador automático basado en WebKit.",
        "category": "SYSTEM"
    },


    # =========================================================
    # HEN
    # =========================================================

    {
        "name": "etaHEN",
        "repo": "etaHEN/etaHEN",
        "asset_contains": ["etahen"],
        "description": "AIO Homebrew Enabler para PS5.",
        "category": "HEN",

        # La beta 2.6B se gestiona aparte.
        "channels": ["stable"]
    },

    {
        "name": "OnionHEN",
        "repo": "aydencharles/onionHEN",
        "asset_contains": ["onionhen"],
        "archive_contains": ["onionhen"],
        "description": "HEN y Toolbox todo-en-uno para PS5.",
        "category": "HEN"
    },

    {
        "name": "PIZZA-HEN",
        "repo": "Michele-M-Media/PIZZA-HEN",
        "asset_contains": ["pizza-hen"],
        "archive_contains": ["pizza-hen"],
        "description": "Entorno homebrew todo-en-uno para PS5.",
        "category": "HEN"
    },


    # =========================================================
    # GAMES
    # =========================================================

    {
        "name": "kstuff-lite",
        "repo": "EchoStretch/kstuff-lite",
        "asset_contains": ["kstuff"],
        "asset_excludes": ["debug"],
        "description": "Versión ligera de kstuff para PS5.",
        "category": "GAMES"
    },

    {
        "name": "ShadowMountPlus",
        "repo": "drakmor/ShadowMountPlus",
        "asset_contains": ["shadowmount"],
        "archive_contains": ["shadowmount"],
        "description": "Montaje automático de contenido compatible en PS5.",
        "category": "GAMES"
    },

    {
        "name": "APR Emu Updater",
        "repo": "tsuramatsu1/apr-emu-updater",
        "asset_contains": ["apr_emu_updater"],
        "description": "Mantiene disponible APR Emu para los títulos compatibles.",
        "category": "GAMES"
    },

    {
        "name": "Game Compressor",
        "repo": "juma-sayeh/PS5-Game-Compressor",
        "asset_contains": ["game-compressor"],
        "description": "Herramienta para comprimir juegos de PS5.",
        "category": "GAMES"
    },

    {
        "name": "PS5 App Dumper",
        "repo": "EchoStretch/ps5-app-dumper",
        "asset_contains": ["ps5-app-dumper"],
        "description": "Payload para volcar aplicaciones PS5 a almacenamiento USB.",
        "category": "GAMES"
    },


    # =========================================================
    # TOOLS
    # =========================================================

    {
        "name": "ELF Arsenal",

        "api":
            "https://git.etawen.dev/api/v1/repos/"
            "soniciso/elf-arsenal/releases",

        "source":
            "https://git.etawen.dev/"
            "soniciso/elf-arsenal/releases",

        "asset_contains": ["elf-arsenal"],

        "description":
            "Colección de payloads ELF empaquetados "
            "en una sola herramienta.",

        "category": "TOOLS"
    },

    {
        "name": "FTP Server PS5",
        "repo": "ps5-payload-dev/ftpsrv",

        "asset_contains": ["ftpsrv"],
        "asset_prefer": ["ps5"],

        "asset_excludes": [
            "ps4",
            "install"
        ],

        "description":
            "Servidor FTP para PS5.",

        "category": "TOOLS"
    },

    {
        "name": "Garlic Save Manager",

        "api":
            "https://git.etawen.dev/api/v1/repos/"
            "earthonion/garlic-savemgr/releases",

        "source":
            "https://git.etawen.dev/"
            "earthonion/garlic-savemgr/releases",

        "asset_contains": ["garlic-savemgr"],
        "asset_excludes": ["worker"],

        "description":
            "Gestor de partidas guardadas de PS5 "
            "con interfaz web.",

        "category": "TOOLS"
    },

    {
        "name": "PoorDS4",
        "repo": "ItsBlurf/PoorDS4",

        "asset_contains": ["poords4rc"],

        "asset_excludes": [
            "status",
            "stop"
        ],

        "archive_contains": ["poords4"],

        "description":
            "Permite utilizar un DualShock 4 inalámbrico "
            "en una PS5 con jailbreak.",

        "category": "TOOLS"
    },

    {
        "name": "Prospero Manager",
        "repo": "notmaj0r/ProsperoMgr",

        "asset_contains": ["prosperomgr"],
        "archive_contains": ["prosperomgr"],

        "description":
            "Gestor web todo-en-uno para PS5.",

        "category": "TOOLS"
    },

    {
        "name": "Common FPS PS5",
        "repo": "porhe911/Common-FPS-for-PS5",

        "asset_contains": ["common_fps_ps5"],
        "asset_excludes": ["plugin"],
        "archive_contains": ["common"],

        "description":
            "Overlay y monitorización de FPS para PS5.",

        "category": "TOOLS"
    },

    {
        "name": "PS5Upload",
        "repo": "phantomptr/ps5upload",

        "asset_contains": ["ps5upload"],
        "asset_excludes": ["debug"],

        "description":
            "Servidor y herramienta de transferencia para PS5.",

        "category": "TOOLS"
    },


    # =========================================================
    # STORES
    # =========================================================

    {
        "name": "Pegasus DL",
        "repo": "pegasus-ps5/pegasus-dl",

        "asset_contains": ["pegasus"],

        "description":
            "Gestor de descargas y catálogos "
            "mediante interfaz web local.",

        "category": "STORES"
    },

    {
        "name": "Spectrum Library",
        "repo": "Phoenixx1202/Spectrum-Library",

        "asset_contains": ["spectrum"],
        "archive_contains": ["spectrum"],

        "description":
            "Biblioteca y gestor de contenido Spectrum para PS5.",

        "category": "STORES"
    }
]


# =============================================================
# ENTRADAS ESPECIALES
# =============================================================

# etaHEN 2.6B no está publicado actualmente como una release
# normal del repositorio oficial, por eso se mantiene como entrada
# especial de Beta.

FIXED_ENTRIES = [

    {
        "name": "etaHEN",
        "channel": "beta",

        "filename":
            "etaHEN-2.6B.bin",

        "url":
            "https://raw.githubusercontent.com/"
            "zecoxao/zecoxao.github.io/"
            "refs/heads/main/luasauce/payloads/"
            "etaHEN-2.6B.bin",

        "source":
            "https://github.com/"
            "zecoxao/zecoxao.github.io/"
            "tree/main/luasauce/payloads",

        "description":
            "AIO Homebrew Enabler para PS5. "
            "Build 2.6B de pruebas.",

        "last_update":
            "2026-05-25",

        "version":
            "2.6B",

        "category":
            "HEN"
    }
]


# =============================================================
# API
# =============================================================

def releases_api(app):

    if app.get("api"):
        return app["api"]

    return (
        "https://api.github.com/repos/"
        f'{app["repo"]}/releases?per_page=100'
    )


def source_url(app):

    if app.get("source"):
        return app["source"]

    return (
        f'https://github.com/'
        f'{app["repo"]}/releases'
    )


def open_url(
    url,
    timeout=60
):

    headers = {
        "User-Agent":
            USER_AGENT
    }

    if "api.github.com" in url:

        headers.update({
            "Accept":
                "application/vnd.github+json",

            "X-GitHub-Api-Version":
                "2022-11-28"
        })

        if TOKEN:

            headers[
                "Authorization"
            ] = (
                f"Bearer {TOKEN}"
            )

    request = urllib.request.Request(
        url,
        headers=headers
    )

    return urllib.request.urlopen(
        request,
        timeout=timeout
    )


def get_json(url):

    with open_url(
        url,
        30
    ) as response:

        return json.load(
            response
        )


def download_bytes(url):

    with open_url(
        url,
        180
    ) as response:

        return response.read()


# =============================================================
# VERSIONES
# =============================================================

def release_time(release):

    raw = (
        release.get("published_at")
        or release.get("created_at")
        or ""
    )

    if not raw:
        return 0

    try:

        return datetime.fromisoformat(
            raw.replace(
                "Z",
                "+00:00"
            )
        ).timestamp()

    except ValueError:

        return 0


def classify_release(release):

    text = (
        f'{release.get("tag_name", "")} '
        f'{release.get("name", "")}'
    ).lower()


    alpha_terms = (

        "alpha",
        "experimental",
        "nightly",
        "canary",
        "test",

        "-dev",
        "_dev",
        " dev"
    )


    beta_terms = (

        "beta",
        "preview",
        "release candidate",

        "-rc",
        "_rc",
        " rc"
    )


    # ALPHA / TEST
    if any(
        term in text
        for term in alpha_terms
    ):

        return "alpha"


    # BETA / RC
    if any(
        term in text
        for term in beta_terms
    ):

        return "beta"


    # GitHub prerelease sin nombre especial
    if release.get(
        "prerelease",
        False
    ):

        return "beta"


    return "stable"


# =============================================================
# ARCHIVOS
# =============================================================

def valid_payload(
    filename,
    app
):

    low = Path(
        filename
    ).name.lower()


    if not (
        low.endswith(".elf")
        or low.endswith(".bin")
    ):

        return False


    for required in app.get(
        "asset_contains",
        []
    ):

        if (
            required.lower()
            not in low
        ):

            return False


    for excluded in app.get(
        "asset_excludes",
        []
    ):

        if (
            excluded.lower()
            in low
        ):

            return False


    return True


def pick_direct(
    release,
    app
):

    items = [

        asset

        for asset
        in release.get(
            "assets",
            []
        )

        if valid_payload(
            asset.get(
                "name",
                ""
            ),
            app
        )
    ]


    if not items:
        return None


    prefer = app.get(
        "asset_prefer",
        []
    )


    items.sort(

        key=lambda asset: (

            -sum(
                term.lower()
                in asset.get(
                    "name",
                    ""
                ).lower()

                for term
                in prefer
            ),

            len(
                asset.get(
                    "name",
                    ""
                )
            ),

            asset.get(
                "name",
                ""
            ).lower()
        )
    )


    return items[0]


def pick_zip(
    release,
    app
):

    items = [

        asset

        for asset
        in release.get(
            "assets",
            []
        )

        if asset.get(
            "name",
            ""
        ).lower().endswith(
            ".zip"
        )
    ]


    if not items:
        return None


    terms = (

        app.get(
            "archive_contains"
        )

        or app.get(
            "asset_contains",
            []
        )
    )


    preferred = [

        asset

        for asset
        in items

        if any(

            term.lower()
            in asset.get(
                "name",
                ""
            ).lower()

            for term
            in terms
        )
    ]


    items = (
        preferred
        or items
    )


    items.sort(

        key=lambda asset: (

            len(
                asset.get(
                    "name",
                    ""
                )
            ),

            asset.get(
                "name",
                ""
            ).lower()
        )
    )


    return items[0]


def extract_payload(
    zip_data,
    app
):

    with zipfile.ZipFile(
        io.BytesIO(
            zip_data
        )
    ) as archive:


        matches = [

            member

            for member
            in archive.namelist()

            if Path(
                member
            ).name

            and valid_payload(
                Path(
                    member
                ).name,
                app
            )
        ]


        if not matches:
            return None


        matches.sort(

            key=lambda member: (

                len(
                    Path(
                        member
                    ).name
                ),

                Path(
                    member
                ).name.lower()
            )
        )


        selected = (
            matches[0]
        )


        return (

            Path(
                selected
            ).name,

            archive.read(
                selected
            )
        )


def safe_name(text):

    return re.sub(

        r"[^A-Za-z0-9._-]+",

        "_",

        text

    ).strip("_")


# =============================================================
# OBTENER PAYLOAD
# =============================================================

def get_payload(
    app,
    release
):

    direct = pick_direct(
        release,
        app
    )


    # ---------------------------------------------------------
    # ELF / BIN directo del desarrollador
    # ---------------------------------------------------------

    if direct:

        url = direct.get(
            "browser_download_url",
            ""
        )


        if not url:
            return None


        data = download_bytes(
            url
        )


        return {

            "filename":
                direct["name"],

            "url":
                url,

            "source_direct":
                url,

            "checksum":
                hashlib.sha256(
                    data
                ).hexdigest()
        }


    # ---------------------------------------------------------
    # Si solo existe ZIP, extraemos el ELF
    # ---------------------------------------------------------

    archive = pick_zip(
        release,
        app
    )


    if not archive:
        return None


    archive_url = archive.get(
        "browser_download_url",
        ""
    )


    if not archive_url:
        return None


    zip_data = download_bytes(
        archive_url
    )


    extracted = extract_payload(
        zip_data,
        app
    )


    if not extracted:
        return None


    filename, data = (
        extracted
    )


    version = (

        release.get(
            "tag_name"
        )

        or release.get(
            "name"
        )

        or "unknown"
    )


    destination = (

        MIRROR_DIR

        / safe_name(
            app["name"]
        )

        / safe_name(
            version
        )

        / filename
    )


    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    destination.write_bytes(
        data
    )


    public_url = (

        f"{PAGES_BASE}/"
        f"{destination.as_posix()}"
    )


    return {

        "filename":
            filename,

        "url":
            public_url,

        "source_direct":
            public_url,

        "checksum":
            hashlib.sha256(
                data
            ).hexdigest()
    }


# =============================================================
# NOMBRES Y DESCRIPCIONES
# =============================================================

def visible_name(
    base,
    channel
):

    if channel == "stable":
        return base


    if channel == "beta":

        return (
            f"{base} (Beta)"
        )


    return (
        f"{base} (INESTABLE)"
    )


def visible_description(
    base,
    channel
):

    if channel == "stable":

        return (
            f"RECOMENDADA · {base}"
        )


    if channel == "beta":

        return (
            f"BETA · {base}"
        )


    return (
        f"ALPHA / TEST / INESTABLE · "
        f"{base}"
    )


# =============================================================
# CREAR ENTRADA JSON
# =============================================================

def make_entry(
    app,
    release,
    payload,
    channel
):

    raw_date = (

        release.get(
            "published_at"
        )

        or release.get(
            "created_at"
        )

        or ""
    )


    return {

        "name":
            visible_name(
                app["name"],
                channel
            ),

        "filename":
            payload[
                "filename"
            ],

        "url":
            payload[
                "url"
            ],

        "source":
            source_url(
                app
            ),

        "source_direct":
            payload[
                "source_direct"
            ],

        "description":
            visible_description(
                app[
                    "description"
                ],
                channel
            ),

        "last_update":
            (
                raw_date[:10]
                if raw_date
                else ""
            ),

        "version":
            (
                release.get(
                    "tag_name"
                )

                or release.get(
                    "name"
                )

                or "unknown"
            ),

        "category":
            app[
                "category"
            ],

        "checksum":
            payload[
                "checksum"
            ]
    }


# =============================================================
# PROCESAR REPOSITORIO
# =============================================================

def process_app(app):

    releases = get_json(
        releases_api(
            app
        )
    )


    if not isinstance(
        releases,
        list
    ):

        releases = [
            releases
        ]


    releases = [

        release

        for release
        in releases

        if not release.get(
            "draft",
            False
        )
    ]


    releases.sort(
 
