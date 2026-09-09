import hashlib
import io
import json
import os
import re
import urllib.request
import zipfile
from pathlib import Path
from datetime import datetime


USER_AGENT = "HiddenKernel-Repository/1.0"
TOKEN = os.getenv("GITHUB_TOKEN", "")

PAGES_BASE = (
    "https://hiddenkernellab.github.io/"
    "PLM-Repository"
)

MIRROR_DIR = Path("payloads")


APPS = [
    {
        "name": "Payload Manager",
        "repo": "itsPLK/ps5-payload-manager",

        "asset_contains": [
            "pldmgr"
        ],

        "asset_excludes": [
            "debug"
        ],

        "archive_contains": [
            "pldmgr"
        ],

        "description":
            "Gestor de payloads para PS5.",

        "category": "SYSTEM",

        "channels": [
            "stable",
            "beta",
            "alpha"
        ]
    },

    {
        "name": "ShadowMountPlus",
        "repo": "drakmor/ShadowMountPlus",

        "asset_contains": [
            "shadowmount"
        ],

        "asset_excludes": [],

        "archive_contains": [
            "shadowmount"
        ],

        "description":
            "Montaje automático de contenido compatible en PS5.",

        "category": "GAMES",

        "channels": [
            "stable",
            "beta",
            "alpha"
        ]
    }
]


def github_json(url):

    headers = {
        "Accept":
            "application/vnd.github+json",

        "User-Agent":
            USER_AGENT,

        "X-GitHub-Api-Version":
            "2022-11-28"
    }

    if TOKEN:
        headers["Authorization"] = (
            f"Bearer {TOKEN}"
        )

    request = urllib.request.Request(
        url,
        headers=headers
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        return json.load(response)


def download_bytes(url):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                USER_AGENT
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=180
    ) as response:

        return response.read()


def sha256_bytes(data):

    return hashlib.sha256(
        data
    ).hexdigest()


def release_timestamp(release):

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


    unstable_terms = (
        "alpha",
        "test",
        "experimental",
        "nightly",
        "canary",
        "dev"
    )


    beta_terms = (
        "beta",
        "preview",
        "release candidate",
        "-rc",
        "_rc",
        " rc"
    )


    if any(
        term in text
        for term in unstable_terms
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


def valid_payload_filename(
    filename,
    app
):

    low = filename.lower()


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


def pick_direct_asset(
    release,
    app
):

    candidates = []


    for asset in release.get(
        "assets",
        []
    ):

        filename = asset.get(
            "name",
            ""
        )

        if valid_payload_filename(
            filename,
            app
        ):
            candidates.append(asset)


    if not candidates:
        return None


    candidates.sort(
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


    return candidates[0]


def pick_archive_asset(
    release,
    app
):

    candidates = []


    for asset in release.get(
        "assets",
        []
    ):

        filename = asset.get(
            "name",
            ""
        )

        low = filename.lower()


        if not low.endswith(".zip"):
            continue


        preferred = app.get(
            "archive_contains",
            []
        )


        if preferred:

            if not any(
                term.lower() in low
                for term in preferred
            ):
                continue


        candidates.append(asset)


    if not candidates:
        return None


    candidates.sort(
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


    return candidates[0]


def find_payload_in_zip(
    zip_data,
    app
):

    with zipfile.ZipFile(
        io.BytesIO(zip_data)
    ) as archive:

        candidates = []


        for member in archive.namelist():

            filename = Path(
                member
            ).name


            if not filename:
                continue


            if valid_payload_filename(
                filename,
                app
            ):
                candidates.append(
                    member
                )


        if not candidates:
            return None


        candidates.sort(
            key=lambda member: (
                len(
                    Path(member).name
                ),

                Path(
                    member
                ).name.lower()
            )
        )


        selected = candidates[0]


        return (
            Path(selected).name,
            archive.read(selected)
        )


def safe_path(text):

    return re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        text
    )


def mirror_payload(
    app,
    release,
    filename,
    data,
    channel
):

    version = (
        release.get("tag_name")
        or release.get("name")
        or "unknown"
    )


    app_dir = safe_path(
        app["name"]
    )


    version_dir = safe_path(
        version
    )


    destination = (
        MIRROR_DIR
        / app_dir
        / version_dir
        / filename
    )


    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    destination.write_bytes(
        data
    )


    relative = destination.as_posix()


    url = (
        f"{PAGES_BASE}/"
        f"{relative}"
    )


    return {
        "filename":
            filename,

        "url":
            url,

        "source_direct":
            url,

        "checksum":
            sha256_bytes(data),

        "mirrored":
            True,

        "channel":
            channel
    }


def get_payload(
    app,
    release,
    channel
):

    direct = pick_direct_asset(
        release,
        app
    )


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
                sha256_bytes(data),

            "mirrored":
                False,

            "channel":
                channel
        }


    archive_asset = (
        pick_archive_asset(
            release,
            app
        )
    )


    if not archive_asset:
        return None


    archive_url = (
        archive_asset.get(
            "browser_download_url",
            ""
        )
    )


    if not archive_url:
        return None


    zip_data = download_bytes(
        archive_url
    )


    extracted = find_payload_in_zip(
        zip_data,
        app
    )


    if not extracted:
        return None


    filename, payload_data = (
        extracted
    )


    return mirror_payload(
        app,
        release,
        filename,
        payload_data,
        channel
    )


def format_name(
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


def format_description(
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
        f"INESTABLE · "
        f"{base}"
    )


def release_date(release):

    raw = (
        release.get("published_at")
        or release.get("created_at")
        or ""
    )


    return (
        raw[:10]
        if raw
        else ""
    )


def make_entry(
    app,
    release,
    payload,
    channel
):

    repo_url = (
        f'https://github.com/'
        f'{app["repo"]}/releases'
    )


    version = (
        release.get("tag_name")
        or release.get("name")
        or "unknown"
    )


    return {
        "name":
            format_name(
                app["name"],
                channel
            ),

        "filename":
            payload["filename"],

        "url":
            payload["url"],

        "source":
            repo_url,

        "source_direct":
            payload[
                "source_direct"
            ],

        "description":
            format_description(
                app["description"],
                channel
            ),

        "last_update":
            release_date(
                release
            ),

        "version":
            version,

        "category":
            app["category"],

        "checksum":
            payload[
                "checksum"
            ]
    }


def process_app(app):

    url = (
        "https://api.github.com/"
        f'repos/{app["repo"]}/'
        "releases?per_page=100"
    )


    releases = github_json(
        url
    )


    releases = [
        release
        for release in releases
        if not release.get(
            "draft",
            False
        )
    ]


    releases.sort(
        key=release_timestamp,
        reverse=True
    )


    entries = []


    for channel in app.get(
        "channels",
        [
            "stable",
            "beta",
            "alpha"
        ]
    ):

        selected = None


        for release in releases:

            if (
                classify_release(
                    release
                )
                != channel
            ):
                continue


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

                selected = (
                    release,
                    payload
                )

                break


        if selected:

            release, payload = (
                selected
            )


            entries.append(
                make_entry(
                    app,
                    release,
                    payload,
                    channel
                )
            )


    return entries


def main():

    output = []


    for app in APPS:

        print(
            f'Procesando '
            f'{app["name"]}...'
        )


        try:

            entries = (
                process_app(app)
            )


            output.extend(
                entries
            )


            print(
                f"  {len(entries)} "
                f"entrada(s)"
            )


            for entry in entries:

                print(
                    f'   - '
                    f'{entry["name"]} '
                    f'{entry["version"]}'
                )


        except Exception as error:

            print(
                f"  ERROR: {error}"
            )


    with open(
        "payloads.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=4
        )

        file.write("\n")


    print(
        f"payloads.json generado "
        f"con {len(output)} "
        f"entrada(s)."
    )


if __name__ == "__main__":
    main()
