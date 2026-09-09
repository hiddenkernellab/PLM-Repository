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

    # SYSTEM
    {
        "name": "Payload Manager",
        "repo": "itsPLK/ps5-payload-manager",
        "match": ["pldmgr"],
        "exclude": ["debug"],
        "description": "Gestor de payloads para PS5.",
        "category": "SYSTEM",
    },

    {
        "name": "Lapy JB Daemon",
        "repo": "itsPLK/PS5-Lapy-JB-Daemon",
        "match": ["lapy", "daemon"],
        "description": "Daemon jailbreak-on-demand para herramientas compatibles.",
        "category": "SYSTEM",
    },

    {
        "name": "nanoDNS",
        "repo": "drakmor/nanoDNS",
        "match": ["nanodns"],
        "description": "Servidor DNS ligero para PS5.",
        "category": "SYSTEM",
    },

    {
        "name": "WebKit Autoloader",
        "repo": "itsPLK/ps5-webkit-autoloader",
        "match": ["webkit-autoloader-installer"],
        "exclude": ["host"],
        "description": "Instalador del cargador automático basado en WebKit.",
        "category": "SYSTEM",
    },


    # HEN
    {
        "name": "etaHEN",
        "repo": "etaHEN/etaHEN",
        "match": ["etahen"],
        "description": "AIO Homebrew Enabler para PS5.",
        "category": "HEN",
        "channels": ["stable"],
    },

    {
        "name": "OnionHEN",
        "repo": "aydencharles/onionHEN",
        "match": ["onionhen"],
        "archive_match": ["onionhen"],
        "description": "HEN y Toolbox todo-en-uno para PS5.",
        "category": "HEN",
    },

    {
        "name": "PIZZA-HEN",
        "repo": "Michele-M-Media/PIZZA-HEN",
        "match": ["pizza"],
        "archive_match": ["pizza"],
        "description": "Entorno homebrew todo-en-uno para PS5.",
        "category": "HEN",
    },


    # GAMES
    {
        "name": "kstuff-lite",
        "repo": "EchoStretch/kstuff-lite",
        "match": ["kstuff"],
        "exclude": ["debug"],
        "description": "Versión ligera de kstuff para PS5.",
        "category": "GAMES",
    },

    {
        "name": "ShadowMountPlus",
        "repo": "drakmor/ShadowMountPlus",
        "match": ["shadowmount"],
        "archive_match": ["shadowmount"],
        "description": "Montaje automático de contenido compatible en PS5.",
        "category": "GAMES",

        # No mostramos la antigua 1.4 como recomendada.
        # Se usa la última 1.6beta como recomendada hasta
        # que exista una estable real más nueva.
        "channels": ["stable", "alpha"],
        "stable_fallback_regex": r"(?i)^1\.6beta",
    },

    {
        "name": "APR Emu Updater",
        "repo": "tsuramatsu1/apr-emu-updater",
        "match": ["apr_emu_updater"],
        "description": "Mantiene disponible APR Emu para títulos compatibles.",
        "category": "GAMES",
    },

    {
        "name": "Game Compressor",
        "repo": "juma-sayeh/PS5-Game-Compressor",
        "match": ["game-compressor"],
        "description": "Herramienta para comprimir juegos de PS5.",
        "category": "GAMES",
    },

    {
        "name": "PS5 App Dumper",
        "repo": "EchoStretch/ps5-app-dumper",
        "match": ["ps5-app-dumper"],
        "archive_match": ["ps5-app-dumper"],
        "description": "Payload para volcar aplicaciones PS5 a almacenamiento USB.",
        "category": "GAMES",
    },


    # TOOLS
    {
        "name": "ELF Arsenal",
        "api": "https://git.etawen.dev/api/v1/repos/soniciso/elf-arsenal/releases",
        "source": "https://git.etawen.dev/soniciso/elf-arsenal/releases",
        "match": ["elf-arsenal"],
        "description": "Colección de payloads ELF empaquetados en una sola herramienta.",
        "category": "TOOLS",
    },

    {
        "name": "FTP Server PS5",
        "repo": "ps5-payload-dev/ftpsrv",
        "match": ["ftpsrv"],
        "prefer": ["ps5"],
        "exclude": ["ps4", "install"],
        "description": "Servidor FTP para PS5.",
        "category": "TOOLS",
    },

    {
        "name": "Garlic Save Manager",
        "api": "https://git.etawen.dev/api/v1/repos/earthonion/garlic-savemgr/releases",
        "source": "https://git.etawen.dev/earthonion/garlic-savemgr/releases",
        "match": ["garlic-savemgr"],
        "exclude": ["worker"],
        "description": "Gestor de partidas guardadas de PS5 con interfaz web.",
        "category": "TOOLS",
    },

    {
        "name": "PoorDS4",
        "repo": "ItsBlurf/PoorDS4",
        "match": ["poords4rc"],
        "exclude": ["status", "stop"],
        "archive_match": ["poords4"],
        "description": "Permite utilizar un DualShock 4 inalámbrico en PS5 con jailbreak.",
        "category": "TOOLS",
    },

    {
        "name": "Prospero Manager",
        "repo": "notmaj0r/ProsperoMgr",
        "match": ["prospero"],
        "archive_match": ["prospero"],
        "description": "Gestor web todo-en-uno para PS5.",
        "category": "TOOLS",
    },

    {
        "name": "Common FPS PS5",
        "repo": "porhe911/Common-FPS-for-PS5",
        "match": ["common_fps_ps5"],
        "exclude": ["plugin"],
        "archive_match": ["common"],
        "description": "Overlay y monitorización de FPS para PS5.",
        "category": "TOOLS",
    },

    {
        "name": "PS5Upload",
        "repo": "phantomptr/ps5upload",
        "match": ["ps5upload"],
        "exclude": ["debug"],
        "archive_match": ["ps5upload"],
        "description": "Servidor y herramienta de transferencia para PS5.",
        "category": "TOOLS",
    },


    # STORES
    {
        "name": "Pegasus DL",
        "repo": "pegasus-ps5/pegasus-dl",
        "match": ["pegasus"],
        "description": "Gestor de descargas y catálogos mediante interfaz web local.",
        "category": "STORES",
    },

    {
        "name": "Spectrum Library",
        "repo": "Phoenixx1202/Spectrum-Library",
        "match": ["spectrum"],
        "archive_match": ["spectrum"],
        "description": "Biblioteca y gestor de contenido Spectrum para PS5.",
        "category": "STORES",
    },
]


FIXED_ENTRIES = [

    {
        "name": "etaHEN",
        "channel": "beta",

        "filename": "etaHEN-2.6B.bin",

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

        "last_update": "2026-05-25",
        "version": "2.6B",
        "category": "HEN",
    }
]


CATEGORY_ORDER = {
    "SYSTEM": 0,
    "HEN": 1,
    "GAMES": 2,
    "TOOLS": 3,
    "STORES": 4,
}


def releases_url(app):

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


def open_url(url, timeout=60):

    headers = {
        "User-Agent": USER_AGENT
    }

    if "api.github.com" in url:

        headers["Accept"] = (
            "application/vnd.github+json"
        )

        headers["X-GitHub-Api-Version"] = (
            "2022-11-28"
        )

        if TOKEN:
            headers["Authorization"] = (
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


def download(url):

    with open_url(
        url,
        180
    ) as response:

        return response.read()


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


def release_text(release):

    return (
        f'{release.get("tag_name", "")} '
        f'{release.get("name", "")}'
    ).strip()


def channel_of(release):

    text = (
        release_text(
            release
        ).lower()
    )

    alpha_terms = (
        "alpha",
        "experimental",
        "nightly",
        "canary",
        "test",
        "-dev",
        "_dev",
        " dev",
    )

    beta_terms = (
        "beta",
        "preview",
        "release candidate",
        "-rc",
        "_rc",
        " rc",
    )

    if any(
        term in text
        for term in alpha_terms
    ):
        return "alpha"

    if any(
        term in text
        for term in beta_terms
    ):
        return "beta"

    if release.get(
        "prerelease",
        False
    ):
        return "beta"

    return "stable"


def valid_payload(
    filename,
    app
):

    low = (
        Path(
            filename
        ).name.lower()
    )

    if not (
        low.endswith(".elf")
        or low.endswith(".bin")
    ):
        return False

    for term in app.get(
        "match",
        []
    ):

        if (
            term.lower()
            not in low
        ):
            return False

    for term in app.get(
        "exclude",
        []
    ):

        if (
            term.lower()
            in low
        ):
            return False

    return True


def asset_url(asset):

    return (
        asset.get(
            "browser_download_url"
        )
        or asset.get(
            "download_url"
        )
        or ""
    )


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

    prefer = [

        item.lower()

        for item
        in app.get(
            "prefer",
            []
        )
    ]

    items.sort(

        key=lambda asset: (

            -sum(

                item in asset.get(
                    "name",
                    ""
                ).lower()

                for item
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
            "archive_match"
        )
        or app.get(
            "match",
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


def extract_from_zip(
    data,
    app
):

    with zipfile.ZipFile(
        io.BytesIO(
            data
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


def safe(text):

    return re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        text
    ).strip("_")


def channel_filename(
    filename,
    channel
):

    if channel == "stable":
        return filename

    path = Path(
        filename
    )

    if channel == "beta":
        suffix = "_beta"

    else:
        suffix = "_unstable"

    return (
        f"{path.stem}"
        f"{suffix}"
        f"{path.suffix}"
    )


def get_payload(
    app,
    release,
    channel
):

    direct = pick_direct(
        release,
        app
    )

    if direct:

        url = asset_url(
            direct
        )

        if not url:
            return None

        data = download(
            url
        )

        return {

            "filename":
                channel_filename(
                    direct["name"],
                    channel
                ),

            "url":
                url,

            "source_direct":
                url,

            "checksum":
                hashlib.sha256(
                    data
                ).hexdigest()
        }

    archive = pick_zip(
        release,
        app
    )

    if not archive:
        return None

    url = asset_url(
        archive
    )

    if not url:
        return None

    extracted = extract_from_zip(
        download(
            url
        ),
        app
    )

    if not extracted:
        return None

    filename, data = (
        extracted
    )

    filename = channel_filename(
        filename,
        channel
    )

    version = (
        release.get("tag_name")
        or release.get("name")
        or "unknown"
    )

    destination = (

        MIRROR_DIR

        / safe(
            app["name"]
        )

        / safe(
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


def display_name(
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


def display_description(
    base,
    channel
):

    if channel == "stable":

        return (
            f"RECOMENDADA · "
            f"{base}"
        )

    if channel == "beta":

        return (
            f"BETA · "
            f"{base}"
        )

    return (
        f"ALPHA / TEST / INESTABLE · "
        f"{base}"
    )


def candidate_releases(
    releases,
    app,
    channel
):

    if channel != "stable":

        return [

            release

            for release
            in releases

            if channel_of(
                release
            ) == channel
        ]

    candidates = [

        release

        for release
        in releases

        if channel_of(
            release
        ) == "stable"
    ]

    fallback = app.get(
        "stable_fallback_regex"
    )

    if fallback:

        regex = re.compile(
            fallback
        )

        for release in releases:

            if (
                regex.search(
                    release_text(
                        release
                    )
                )

                and release
                not in candidates
            ):

                candidates.append(
                    release
                )

    candidates.sort(
        key=release_time,
        reverse=True
    )

    return candidates


def make_entry(
    app,
    release,
    payload,
    channel
):

    raw_date = (
        release.get("published_at")
        or release.get("created_at")
        or ""
    )

    return {

        "name":
            display_name(
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
            display_description(
                app["description"],
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


def process_app(app):

    releases = get_json(
        releases_url(
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
        key=release_time,
        reverse=True
    )

    output = []

    channels = app.get(
        "channels",
        [
            "stable",
            "beta",
            "alpha"
        ]
    )

    for channel in channels:

        candidates = (
            candidate_releases(
                releases,
                app,
                channel
            )
        )

        for release in candidates:

            try:

                payload = get_payload(
                    app,
                    release,
                    channel
                )

            except Exception as error:

                print(
                    f'  Falló '
                    f'{release.get("tag_name", "")}: '
                    f'{error}'
                )

                continue

            if payload:

                output.append(

                    make_entry(
                        app,
                        release,
                        payload,
                        channel
                    )
                )

                break

    return output


def fixed_entry(item):

    data = download(
        item["url"]
    )

    channel = (
        item["channel"]
    )

    return {

        "name":
 
