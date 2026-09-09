import hashlib
import json
import os
import urllib.request


USER_AGENT = "HiddenKernel-Repository/1.0"
TOKEN = os.getenv("GITHUB_TOKEN", "")


APPS = [
    {
        "name": "Payload Manager",
        "repo": "itsPLK/ps5-payload-manager",
        "asset_contains": ["pldmgr"],
        "asset_excludes": ["debug"],
        "description": "Gestor de payloads para PS5.",
        "category": "SYSTEM",
        "channels": ["stable", "beta", "alpha"]
    },
    {
        "name": "ShadowMountPlus",
        "repo": "drakmor/ShadowMountPlus",
        "asset_contains": ["shadowmount"],
        "asset_excludes": [],
        "description": "Montaje automático de contenido compatible en PS5.",
        "category": "GAMES",
        "channels": ["stable", "beta", "alpha"]
    }
]


def github_json(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28"
    }

    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = urllib.request.Request(
        url,
        headers=headers
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:
        return json.load(response)


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


def pick_asset(release, app):
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

        if not (
            low.endswith(".elf")
            or low.endswith(".bin")
        ):
            continue

        if any(
            term.lower() not in low
            for term in app.get(
                "asset_contains",
                []
            )
        ):
            continue

        if any(
            term.lower() in low
            for term in app.get(
                "asset_excludes",
                []
            )
        ):
            continue

        candidates.append(asset)

    if not candidates:
        return None

    candidates.sort(
        key=lambda asset: (
            0
            if asset.get(
                "name",
                ""
            ).lower().endswith(".elf")
            else 1,

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


def sha256_url(url):
    digest = hashlib.sha256()

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=180
    ) as response:

        while True:
            chunk = response.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def format_name(base, channel):
    if channel == "stable":
        return base

    if channel == "beta":
        return f"{base} (Beta)"

    return f"{base} (INESTABLE)"


def format_description(
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
        f"ALPHA / INESTABLE · {base}"
    )


def release_date(release):
    raw = (
        release.get("published_at")
        or release.get("created_at")
        or ""
    )

    return raw[:10] if raw else ""


def make_entry(
    app,
    release,
    asset,
    channel
):
    direct_url = asset[
        "browser_download_url"
    ]

    repo_url = (
        f'https://github.com/'
        f'{app["repo"]}/releases'
    )

    return {
        "name": format_name(
            app["name"],
            channel
        ),

        "filename":
            asset["name"],

        "url":
            direct_url,

        "source":
            repo_url,

        "source_direct":
            direct_url,

        "description":
            format_description(
                app["description"],
                channel
            ),

        "last_update":
            release_date(release),

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
            app["category"],

        "checksum":
            sha256_url(
                direct_url
            )
    }


def process_app(app):
    url = (
        "https://api.github.com/"
        f'repos/{app["repo"]}/'
        "releases?per_page=100"
    )

    releases = github_json(url)

    releases = [
        release
        for release in releases
        if not release.get(
            "draft",
            False
        )
    ]

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

            asset = pick_asset(
                release,
                app
            )

            if asset:
                selected = (
                    release,
                    asset
                )

                break

        if selected:

            release, asset = selected

            entries.append(
                make_entry(
                    app,
                    release,
                    asset,
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
            entries = process_app(
                app
            )

            output.extend(entries)

            print(
                f"  {len(entries)} "
                f"entrada(s)"
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
