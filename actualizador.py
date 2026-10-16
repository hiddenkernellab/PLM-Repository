#!/usr/bin/env python3
"""HiddenKernel ELF updater - revision acumulativa 2026-10-16 21:56 CEST.

Base: actualizador.py de HiddenKernelLab/PLM-Repository/main (blob 2da7887),
consolidado con las mejoras locales anteriores que todavia no figuran en main.
El main usa un wrapper de iconos sobre el codigo fijado 7f9a7d1;
esta entrega conserva ese actualizador y los iconos SVG en un solo archivo,
sin ejecutar codigo remoto. Se conserva la gestion de ids y el autoload.

Revisiones de esta entrega: PS5Upload 7.0.27, PatchDL 0.2.0 y
FBNeo PS5 1.9 (nuevo ID de app PPSA99924 y helper 9092).
Conserva PS5 Library 0.7.32, RomM Sync 1.2.1, PLDMGR 0.6.1,
OnionHEN 0.9.0, PS4Mount 0.5.1, PS5SX2 2.10, iconos ilustrados,
y retira duplicados beta ya superados.

NO hace push, commits ni modifica GitHub. Genera localmente payloads.json
 e icons.json junto al script. No ejecuta codigo remoto.
"""
import json
import base64
import os
import re
import urllib.request
from pathlib import Path

CATALOG = Path(__file__).resolve().parent / 'payloads.json'
API = 'https://api.github.com/repos/{repo}/releases/latest'
HEX64 = re.compile(r'[a-f0-9]{64}\Z')

TRACKED = (
    {
        'key': 'ps5upload', 'name': 'ps5upload', 'repo': 'phantomptr/ps5upload',
        'tag': 'v7.0.27', 'asset': 'ps5upload-7.0.27.elf',
        'sha256': '855f106a64a6e8a1ec0a3fac65e21585f209c9d6751995def04ee551b90a61ea',
        'date': '2026-10-16', 'category': 'ARCHIVOS / RED',
        'description': ('PS5Upload 7.0.27: transferencia y gestion remota de PS5. '
                        'Corrige instalaciones por streaming incompletas: el '
                        'servidor espera hasta enviar cada byte al menos una vez. '
                        'Evita el fallo intermitente del puerto ELF 9021 al '
                        'reemplazar elfldr. Conserva mejoras de 7.0.26: registro '
                        'de juegos via ShadowMountPlus, reanudacion de cargas, '
                        'RAR grandes y actualizacion de payloads guardados. '
                        'Actualizar tambien cliente y helper 7.0.27.'),
    },
    {
        'key': 'nuvio', 'name': 'Nuvio PS5', 'repo': 'theghostonline/Nuvio-PS5',
        'tag': 'v1.8.0', 'asset': 'nuvio-ps5.elf',
        'sha256': '2c4812fdf411116652db756a5bd563cb4934f9df76373f59bdba3ff25a79cc3b',
        'date': '2026-10-12', 'category': 'MULTIMEDIA',
        'description': ('Reproductor multimedia PS5. El ELF instala Nuvio y su servicio '
                        'para abrirlo posteriormente desde el menu, sin reenviar el ELF '
                        'en cada inicio. Corrige errores de reproduccion y busqueda.'),
    },
    {
        'key': 'ps5sx2', 'name': 'PS5SX2 Helper', 'repo': 'Swordpdf/PS5SX2',
        'tag': 'vk-285-171', 'asset': 'PS5SXHelper.elf',
        'sha256': '9fa809eb10e1fe5149b2d031f55497d7b050e950ec5aec38bac7ebe1ef6da153',
        'date': '2026-10-14', 'category': 'EMULADORES',
        'description': ('PS5SX2 2.10: helper para permisos, montaje /data y mosaicos '
                        'de DVD PS2 con ShadowMountPlus. Sustituye el bot 2.03. '
                        'Cargar despues de ShadowMountPlus. No cargar varios helpers '
                        'a la vez; no apagar con disco insertado: riesgo kernel panic.'),
    },
    {
        'key': 'ps5sx2_installer', 'name': 'PS5SX2 Installer', 'repo': 'Swordpdf/PS5SX2',
        'tag': 'vk-285-171', 'asset': 'PS5SX2Installer.elf',
        'sha256': '6b1be3ea24ec8144b27b2a1f3e279cd17574f3093e9431abf8579dcc6c0bfae9',
        'date': '2026-10-14', 'category': 'EMULADORES',
        'description': ('Instalador oficial PS5SX2 2.10. Descarga e instala la '
                        'aplicacion; usar junto con PS5SXHelper.elf. No autocargar.'),
    },
    {
        'key': 'patchdl', 'name': 'PatchDL', 'repo': 'knutwurst/ps5-patchdl',
        'tag': 'v0.2.0', 'asset': 'patchdl_0.2.0.elf',
        'sha256': 'a3de131bc9c8c552b4a9fb813037df1b7beea24efeb053e46fca5a7ca59820f3',
        'date': '2026-10-16', 'category': 'DESCARGAS',
        'description': ('PatchDL 0.2.0: descarga e instala actualizaciones oficiales '
                        'para juegos PS5 Y PS4 ya instalados, con cola, reanudacion '
                        'y comprobacion de la version tras instalar. '
                        'Usa el instalador propio de la consola y busca parches '
                        'compatibles con el firmware. Corrige un salto erroneo '
                        'del estado de instalacion a completado. '
                        'El autor probo PS4 con Bloodborne 1.00 a 1.09 en FW 11.60; '
                        '0.1.0 fue confirmada por un usuario en FW 13.60. '
                        'Solo actualizaciones oficiales, no descarga juegos; '
                        'no afirmar compatibilidad con FPKG o ShadowMountPlus.'),
    },
    {
        'key': 'onionhen', 'name': 'OnionHEN',
        'repo': 'aydencharles/onionHEN',
        'tag': 'v0.9.0', 'asset': 'OnionHEN.elf',
        'sha256': '1f1f7c883d5d998be1d95d7d80b718f85180f8156f257661b0f445a7c6b7c212',
        'date': '2026-10-15', 'category': 'HEN / AIO',
        'description': ('OnionHEN 0.9.0 estable: HEN con Toolbox, cheats, overlay y '
                        'servicios en segundo plano. Amplia compatibilidad a FW '
                        '13.00-13.60 y algunas consolas 5.50; corrige bloqueos '
                        'al abrir menus de cheats vacios y mejora elfldr. '
                        'Incluye kstuff-lite 1.11, que puede desactivarse si '
                        'se usa kstuff externo. Requiere elfldr activo en 9021. '
                        'NO cargar junto a etaHEN, CheatRunner, YonCore ni '
                        'otros inyectores de atajos; riesgo de cuelgue. '
                        'No relanzar en la misma sesion.'),
    },
    {
        'key': 'ps5_library', 'name': 'PS5 Library',
        'repo': 'deox1111/ps5-library',
        'tag': 'v0.7.32', 'asset': 'ps5-library.elf',
        'sha256': '9979b2d2677efb8e98285b369527d93af5d5800b561687767a4795827c7694a1',
        'date': '2026-10-16', 'category': 'DESCARGAS',
        'description': ('PS5 Library 0.7.32: biblioteca, catalogos, descargas '
                        'y descompresion en PS5. Corrige fallos de catalogos '
                        'bloqueados por nanoDNS: para el servidor del catalogo '
                        'intenta resolver mediante DNS sobre HTTPS (Cloudflare) '
                        'cuando el DNS de la consola devuelve 0.0.0.0 o loopback. '
                        'ATENCION: este comportamiento puede eludir bloqueos DNS '
                        'intencionados para dominios de catalogos; no desactiva '
                        'globalmente nanoDNS. Portadas de catalogos grandes '
                        'aproximadamente el doble de rapidas y diagnostico DNS. '
                        'Modo reposo solo en SSD interno, NO en USB/exFAT. '
                        'Probado por upstream en FW 13.60; requiere kstuff y '
                        'ShadowMountPlus. No confundir con el agente rdiol12.'),
    },
    {
        'key': 'pldmgr', 'name': 'Payload Manager',
        'repo': 'itsPLK/ps5-payload-manager',
        'tag': 'v0.6.1', 'asset': 'pldmgr_v0.6.1.elf',
        'sha256': '5165cbe4c13360828bd0f5d558cdbb9e2d55b0660b1dc7f7a58d3f4ee9e23285',
        'date': '2026-10-14', 'category': 'SISTEMA',
        'description': ('Gestor de payloads con tienda visual, busqueda, detalles, favoritos '
                        'sincronizados y autoload. La v0.6.1 recupera el cierre automatico '
                        'del reproductor de discos al iniciar, util para BD-JB antiguos '
                        '(autoloaders anteriores a v1.4.0). Conserva las mejoras de '
                        'v0.6.0: catalogos grandes, red, instalacion y checksums. '
                        'Es el gestor oficial, distinto de HK-PLDMGR-Install-Update. '
                        'Puede actualizarse tambien desde su propia interfaz.'),
    },
    {
        'key': 'ps4mount', 'name': 'PS4Mount', 'repo': 'gasb07/ps4mount',
        'tag': 'v0.5.1', 'asset': 'ps4mount.elf',
        'sha256': '23ef99696af8da139fafd13e97e0d1f94968f2e745cb79e45a6aa71bc6391549',
        'date': '2026-10-15', 'category': 'JUEGOS / COMPATIBILIDAD',
        'description': ('Monta PS4 FPKG y actualizaciones desde USB exFAT sin copiar '
                        'al SSD interno; interfaz web en puerto 8770. DLC limitados. '
                        'v0.5.1 agrega marcas de tiempo a logs. Experimental; '
                        'probado en FW 13.20; no autocargar.'),
    },
    {
        'key': 'romm-sync', 'name': 'RomM Sync', 'repo': 's0liton/RommPS',
        'tag': 'v1.2.1', 'asset': 'romm-sync.elf',
        'sha256': '8d7e44c512b311f4bbb522f6761a6319533bcd9d988a72bd313197d8161dd696',
        'date': '2026-10-15', 'category': 'EMULADORES',
        'description': ('RomM Sync 1.2.1: cliente de RomM para PS5; descarga juegos y BIOS a las carpetas '
                        'de emuladores y sincroniza partidas y savestates. La v1.2.0 '
                        'descarga saves al terminar cada juego, permite desactivar '
                        'sincronizacion por plataforma, incorpora actividad, conflictos, '
                        'restauracion y nuevos perfiles. Requiere un servidor RomM. '
                        'ELF independiente; RommPS tambien tiene app nativa opcional.'),
    },
    {
        'key': 'lz4', 'name': 'LZ4 Compression',
        'repo': 'theghostonline/PS5-LZ4-Compression',
        'tag': 'v1.5.0', 'asset': 'lz4-compression.elf',
        'sha256': 'edb4f2c5922bea293cc5c5354bd301fb0bde48856c0d2a8d115801d3c778b3f1',
        'date': '2026-10-14', 'category': 'JUEGOS / COMPATIBILIDAD',
        'description': ('Compresion LZ4 de juegos PS5 para APR-EMU. Requiere app '
                        'PPSA99420 del ZIP oficial; el ELF no instala la interfaz. '
                        'No borrar originales sin comprobar; no autocargar.'),
    },
    {
        'key': 'librepad', 'name': 'LibrePadPS5', 'repo': 'arwebSE/LibrePadPS5',
        'tag': 'v1.1.3', 'asset': 'LibrePadPS5.elf',
        'sha256': '736ea4b0a17aafce4ade2b696a6d5d2a8b856b83c6960a3d0ec117e23ba2c2c0',
        'date': '2026-10-12', 'category': 'MANDOS / AUDIO',
        'description': ('Hasta cuatro mandos PlayStation, Xbox, Switch y 8BitDo '
                        'por USB, adaptadores o Bluetooth opcional. Panel web 8096. '
                        'Bluetooth interno desactivado por defecto; probar manualmente.'),
    },
    {
        'key': 'fbneo_ps5', 'name': 'FBNeo PS5',
        'repo': 'MisterTemaki/fbneo-ps5',
        'tag': 'v1.9', 'asset': 'FBNeoPS5-v1.9.elf',
        'sha256': 'caed9d16060616637ad80cb54bdfd0239b4b734775e45cc17811f876c4897817',
        'date': '2026-10-16', 'category': 'EMULADORES',
        'description': ('FBNeo PS5 1.9: emulador arcade nativo (NO Lua). '
                        'Cambia el ID de aplicacion a PPSA99924 para evitar '
                        'colisiones con otro homebrew; instala en '
                        '/data/homebrew/PPSA99924 y usa helper puerto 9092. '
                        'Conserva ROMs, partidas, portadas y ajustes en /data/fbneo. '
                        'Incluye actualizacion desde la app con verificacion SHA-256 '
                        'y acelera el escaneo de bibliotecas grandes. '
                        'Si queda el antiguo PPSA99012, identificarlo antes de '
                        'borrar la carpeta o el icono. '
                        'El autor documento 270 pruebas simuladas, pero no '
                        'verifico el cambio de ID ni el actualizador en PS5 real. '
                        'Requiere entorno homebrew, elfldr y ShadowMountPlus.'),
    },
    {
        'key': 'ps5library_agent', 'name': 'PS5Library Agent (rdiol12)',
        'repo': 'rdiol12/PS5Library', 'tag': 'v0.2.91',
        'asset': 'ps5library-agent.elf',
        'sha256': 'ac78389a628401edba3c081f00156238ad5652b1b7ad241f5ccc7713179f0c82',
        'date': '2026-10-14', 'category': 'DESCARGAS',
        'description': ('Agente de PS5Library de rdiol12 para inventario y '
                        'gestion de archivos. Requiere la app PKG y servidor propio '
                        'para funciones remotas. Distinto de PS5 Library de deox1111.'),
    },

)

OLD_PS5SX2_NAMES = {
    'ps5sx2 aio', 'ps5sx2 bot', 'ps5sx2 helper',
    'ps5sx2 disclaunch', 'disclaunch',
}
OLD_PS5SX2_FILES = {
    'ps5sx2-aio.elf', 'ps5sx2-bot.elf',
    'ps5sxhelper.elf', 'disclaunch.elf',
}


def version_numbers(value):
    """Compare human-facing dotted versions, ignoring PS5SX2 vk build IDs."""
    value = str(value)
    match = re.search(r'\d+(?:\.\d+){1,3}', value)
    nums = [int(x) for x in match.group().split('.')] if match else [
        int(x) for x in re.findall(r'\d+', value)[:3]]
    return tuple((nums + [0] * 4)[:4])


def fetch_release(repo):
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'HiddenKernel-ELF-Updater/2026-10-16',
    }
    token = os.getenv('GITHUB_TOKEN', '').strip()
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(API.format(repo=repo), headers=headers)
    with urllib.request.urlopen(req, timeout=18) as response:
        release = json.load(response)
    if not isinstance(release, dict):
        raise ValueError('Respuesta de GitHub invalida')
    return release


def checked_asset(repo, release, asset_name):
    """Return validated (tag, name, URL, SHA256, date) or None."""
    if release.get('draft') or release.get('prerelease'):
        return None
    tag = str(release.get('tag_name') or '')
    if not tag or '/' in tag or '..' in tag or not re.search(r'\d', tag):
        return None
    if '/' in asset_name or '..' in asset_name or not asset_name.endswith('.elf'):
        return None
    matches = [a for a in release.get('assets', [])
               if isinstance(a, dict) and a.get('name') == asset_name]
    if len(matches) != 1:
        return None
    asset = matches[0]
    digest = str(asset.get('digest') or '')
    url = 'https://github.com/' + repo + '/releases/download/' + tag + '/' + asset_name
    if (asset.get('browser_download_url') != url or
            not digest.startswith('sha256:') or not HEX64.fullmatch(digest[7:])):
        return None
    date = str(release.get('published_at') or '')[:10]
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
        date = '2026-10-14'
    return tag, asset_name, url, digest[7:], date


def matches_target(item, key):
    if not isinstance(item, dict):
        return False
    name = str(item.get('name', '')).strip().casefold()
    filename = str(item.get('filename', '')).strip().casefold()
    if key == 'ps5sx2':
        return name in OLD_PS5SX2_NAMES or filename in OLD_PS5SX2_FILES
    if key == 'ps5sx2_installer':
        return name == 'ps5sx2 installer' or filename == 'ps5sx2installer.elf'
    if key == 'fbneo_ps5':
        return (name == 'fbneo ps5' or
                (filename.startswith('fbneops5') and filename.endswith('.elf')))
    if key == 'ps5upload':
        return name == 'ps5upload' or bool(re.fullmatch(
            r'ps5upload[-_]v?\d+(?:\.\d+)*\.elf', filename))
    if key == 'nuvio':
        return name == 'nuvio ps5' or filename == 'nuvio-ps5.elf'
    if key == 'onionhen':
        return name == 'onionhen' or filename.startswith('onionhen_v') and filename.endswith('.elf')
    if key == 'patchdl':
        return name == 'patchdl' or bool(re.fullmatch(
            r'patchdl[-_]v?\d+(?:\.\d+)*\.elf', filename))
    if key == 'pldmgr':
        # Deliberadamente NO toca HK-PLDMGR-Install-Update, un producto distinto.
        return name in ('payload manager', 'pldmgr') or bool(re.fullmatch(
            r'pldmgr(?:_v?\d+(?:\.\d+)*)?\.elf', filename))
    if key == 'ps4mount':
        return name == 'ps4mount' or filename == 'ps4mount.elf'
    if key == 'lz4':
        return name == 'lz4 compression' or filename == 'lz4-compression.elf'
    if key == 'librepad':
        return name in ('librepadps5', 'librepad ps5') or filename == 'librepadps5.elf'
    if key == 'ps5_library':
        # PS5 Library de deox1111, NO el agente de rdiol12.
        return (name == 'ps5 library' or
                (filename == 'ps5-library.elf' and
                 'deox1111/ps5-library' in str(item.get('source', '')).casefold()))
    if key == 'ps5library_agent':
        return name in ('ps5library agent (rdiol12)', 'ps5library-agent') or filename == 'ps5library-agent.elf'
    if key == 'romm-sync':
        return (str(item.get('id', '')).strip().casefold() == 'romm-sync' or
                filename == 'romm-sync.elf' or
                name in ('romm sync', 'rommps'))
    return False


def make_entry(spec, tag, filename, url, checksum, date, release_name=''):
    version = tag
    if spec['key'] in ('ps5sx2', 'ps5sx2_installer'):
        m = re.search(r'\b(\d+\.\d+)\b', release_name)
        version = (m.group(1) + ' (' + tag + ')') if m else (
            '2.10 (' + tag + ')' if tag == spec['tag'] else tag)
    entry = {
        'name': spec['name'], 'filename': filename, 'url': url,
        'source': 'https://github.com/' + spec['repo'] + '/releases',
        'source_direct': url, 'description': spec['description'],
        'last_update': date, 'version': version,
        'category': spec['category'], 'checksum': checksum,
    }
    if spec['key'] == 'romm-sync':
        # Preserve the existing favorites, autoload slot and icon across the rename.
        entry['id'] = 'romm-sync'
        entry['icon_key'] = 'romm-sync'
    return entry


def select_tracked(spec):
    tag = spec['tag']
    asset = spec['asset']
    url = 'https://github.com/' + spec['repo'] + '/releases/download/' + tag + '/' + asset
    choice = (tag, asset, url, spec['sha256'], spec['date'])
    release_name = ''
    try:
        release = fetch_release(spec['repo'])
        if spec['key'] == 'ps5upload':
            candidate_asset = ('ps5upload-' + str(release.get('tag_name', '')).removeprefix('v') + '.elf')
        elif spec['key'] == 'patchdl':
            candidate_asset = ('patchdl_' + str(release.get('tag_name', '')).removeprefix('v') + '.elf')
        elif spec['key'] == 'pldmgr':
            candidate_asset = 'pldmgr_' + str(release.get('tag_name', '')) + '.elf'
        else:
            candidate_asset = asset
        candidate = checked_asset(spec['repo'], release, candidate_asset)
        if candidate and version_numbers(candidate[0]) >= version_numbers(tag):
            choice = candidate
            release_name = str(release.get('name') or '')
        elif candidate is None:
            print('AVISO: release sin ELF/SHA256 comprobable:', spec['name'])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('AVISO: API no disponible para', spec['name'], '-', str(exc)[:100])
    entry = make_entry(spec, *choice, release_name=release_name)
    if choice[0] != spec['tag']:
        entry['description'] = (spec['description'] +
                                ' AVISO: version ' + choice[0] +
                                ' detectada automaticamente; revisar cambios upstream.')
    return entry


def replace_entry(items, spec, entry):
    old = [x for x in items if matches_target(x, spec['key'])]
    if old:
        # PS5SX2 uses vk build IDs; preserve idempotence on its known pinned tag.
        if spec['key'] in ('ps5sx2', 'ps5sx2_installer') and any(x == entry for x in old) and len(old) == 1:
            return items, False
        if max(version_numbers(x.get('version', '')) for x in old) > version_numbers(entry['version']):
            print('OMITIDO: version mas reciente en catalogo:', spec['name'])
            return items, False
        if len(old) == 1 and all(str(old[0].get(k,'')) == str(entry.get(k,'')) for k in ('version','filename','url','checksum')):
            # Conservar id/icon_key, pero consolidar descripciones pendientes
            # aunque el main ya tenga el ELF nuevo. Evitar fechas hacia atras.
            corrected = dict(old[0])
            for field in ('description', 'category', 'source', 'source_direct'):
                if entry.get(field) and corrected.get(field) != entry[field]:
                    corrected[field] = entry[field]
            if str(entry.get('last_update', '')) > str(corrected.get('last_update', '')):
                corrected['last_update'] = entry['last_update']
            if corrected != old[0]:
                return [corrected if x is old[0] else x for x in items], True
            return items, False
        preferred = next((x for x in old if x.get('version') == entry.get('version')
                          and x.get('checksum') == entry.get('checksum')), None)
        if preferred is None:
            preferred = old[0]
        for k in ('id', 'icon_key'):
            if preferred.get(k):
                entry[k] = preferred[k]
    indices = [i for i, x in enumerate(items) if matches_target(x, spec['key'])]
    first = indices[0] if indices else len(items)
    kept = [x for x in items if not matches_target(x, spec['key'])]
    kept.insert(first, entry)
    return kept, kept != items


def refresh_other_official_releases(items):
    """Conservative upstream updates already present in the catalog."""
    cache, changes, result = {}, [], []
    for item in items:
        if any(matches_target(item, spec['key']) for spec in TRACKED):
            result.append(item)
            continue
        source = str(item.get('source', '')).rstrip('/')
        match = re.fullmatch(r'https://github\.com/([^/]+/[^/]+)/releases', source)
        if not match:
            result.append(item)
            continue
        repo = match.group(1)
        url = str(item.get('url', ''))
        prefix = 'https://github.com/' + repo + '/releases/download/'
        if not url.startswith(prefix) or not url.lower().endswith('.elf'):
            result.append(item)
            continue
        old_asset = url.rsplit('/', 1)[-1]
        old_tag = str(item.get('version', ''))
        if not re.search(r'\d', old_tag):
            result.append(item)
            continue
        if repo not in cache:
            try:
                cache[repo] = fetch_release(repo)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                cache[repo] = None
                print('AVISO: sin acceso a', repo, '-', str(exc)[:100])
        release = cache[repo]
        if not release or release.get('draft') or release.get('prerelease'):
            result.append(item)
            continue
        tag = str(release.get('tag_name') or '')
        if not tag or version_numbers(tag) <= version_numbers(old_tag):
            result.append(item)
            continue
        candidates = [old_asset]
        for old, new in ((old_tag, tag),
                         (old_tag.removeprefix('v'), tag.removeprefix('v'))):
            if old and old in old_asset:
                candidates.append(old_asset.replace(old, new, 1))
        found = None
        for asset_name in dict.fromkeys(candidates):
            found = checked_asset(repo, release, asset_name)
            if found:
                break
        if not found:
            result.append(item)
            continue
        new_tag, asset_name, new_url, checksum, date = found
        newer = dict(item)
        newer.update(version=new_tag, url=new_url, source_direct=new_url,
                     checksum=checksum, last_update=date)
        filename = str(item.get('filename', ''))
        for old, new in ((old_tag, tag),
                         (old_tag.removeprefix('v'), tag.removeprefix('v'))):
            if old and old in filename:
                filename = filename.replace(old, new, 1)
                break
        newer['filename'] = filename
        result.append(newer)
        changes.append(str(item.get('name')) + ' -> ' + tag)
    return result, changes


def update_catalog(path=CATALOG):
    if not path.is_file():
        raise FileNotFoundError('No existe payloads.json junto a actualizador.py')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('payloads'), list):
        raise ValueError('Formato de payloads.json invalido: no se modifica')
    items = data['payloads']
    if not all(isinstance(x, dict) for x in items):
        raise ValueError('Catalogo con entradas invalidas: no se modifica')
    changes = []
    for spec in TRACKED:
        entry = select_tracked(spec)
        items, did_change = replace_entry(items, spec, entry)
        if did_change:
            changes.append(spec['name'] + ' ' + entry['version'])

    items, other_changes = refresh_other_official_releases(items)
    changes.extend(other_changes)
    old_count = len(items)
    items = [x for x in items if not (
        str(x.get('name', '')).strip().casefold() == 'anypad ps5' and
        'sinfiltros/anypad-ps5' in
        (str(x.get('source', '')) + ' ' + str(x.get('url', ''))).casefold())]
    if len(items) != old_count:
        changes.append('retirado AnyPad (origen 404)')
    # El upstream websrv v0.35 es PRE-RELEASE (10/10/2026).
    # Conservar la ultima estable 0.34, quitar solo la beta duplicada.
    websrv_stable = any(
        str(x.get('name', '')).casefold() == 'ps5-payload-websrv' and
        str(x.get('version', '')) == 'v0.34' and
        'ps5-payload-dev/websrv' in str(x.get('source', ''))
        for x in items)
    if websrv_stable:
        before = len(items)
        items = [x for x in items if not (
            str(x.get('name', '')).casefold() == 'ps5-payload-websrv' and
            str(x.get('version', '')) == 'v0.35' and
            'ps5-payload-dev/websrv' in str(x.get('source', '')))]
        if len(items) != before:
            changes.append('retirado websrv v0.35 pre-release duplicado; mantenido v0.34 estable')
    if not changes:
        print('HiddenKernel: sin cambios, catalogo intacto (' + str(len(items)) + ' entradas).')
        return False
    data['payloads'] = items
    tmp = path.with_name(path.name + '.tmp')
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        check = json.loads(tmp.read_text(encoding='utf-8'))
        if len(check['payloads']) != len(items):
            raise ValueError('El catalogo temporal no supera la validacion')
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()
    print('HiddenKernel:', len(items), 'entradas;', '; '.join(changes))
    return True


PALETTE = ('#245b93','#177b79','#744c9e','#99522b','#366a42','#8b4461')

def slug(s):
    s = re.sub(r'[^a-z0-9._-]+','-',s.lower()).strip('-')
    return s[:110] or 'payload'

def symbol(item):
    t = (item.get('name','')+' '+item.get('category','')+' '+item.get('description','')).lower()
    for terms, sign in [
        (('ftp','upload','transfer','network','red'), 'FTP'),
        (('save','backup','guardad'), 'SAVE'),
        (('mount','disco','usb'), 'DISK'),
        (('emul','ps2','ps3','retro'), 'EMU'),
        (('cheat','trainer','trucos'), 'CODE'),
        (('video','media','nuvio'), 'PLAY'),
        (('payload','autoload','loader'), 'ELF'),
        (('debug','log','kernel'), 'SYS'),
    ]:
        if any(w in t for w in terms): return sign
    return 'PS5'

def svg_icon(item, n):
    """Illustrated 128px SVG icons compatible with official PLDMGR icons.json."""
    name = str(item.get('name', '')).lower()
    category = str(item.get('category', '')).lower()
    label = name + ' ' + category
    themes = (
        ('#18306e', '#4d95f7', '#c9f6ff'),
        ('#443070', '#bd6fee', '#ffe5fa'),
        ('#064c59', '#27c5c3', '#d6ffff'),
        ('#6e283e', '#f67d73', '#ffe8c4'),
        ('#36501d', '#9acc53', '#f8ffd9'),
        ('#634017', '#e9a64a', '#fff4bb'),
    )
    bg1, bg2, glow = themes[n % len(themes)]
    if any(w in label for w in ('mandos','pad','controller','xsense','ds4')):
        shape = ('<path d="M40 51Q26 52 22 79q-2 15 12 17l22-14h16l22 14q14-2 12-17-4-27-18-28z" fill="white"/>'
                 '<path d="M40 65v17M32 73h16" stroke="#4862a2" stroke-width="6" stroke-linecap="round"/>'
                 '<circle cx="83" cy="68" r="5" fill="#ff7b87"/><circle cx="93" cy="79" r="5" fill="#91e5dc"/>')
    elif any(w in label for w in ('emuladores','ps5sx','snes','genesis','fbneo','xpsemu')):
        shape = ('<rect x="24" y="29" width="80" height="69" rx="13" fill="white"/>'
                 '<rect x="32" y="37" width="64" height="39" rx="5" fill="#233c79"/>'
                 '<path d="M42 87h18M51 78v18" stroke="#497fc2" stroke-width="5"/>'
                 '<circle cx="82" cy="88" r="5" fill="#f585b7"/><circle cx="94" cy="82" r="5" fill="#7be8dd"/>')
    elif any(w in label for w in ('ftp','network','red','upload','websrv','tailscale','aria2')):
        shape = ('<circle cx="64" cy="61" r="32" fill="none" stroke="white" stroke-width="7"/>'
                 '<ellipse cx="64" cy="61" rx="15" ry="32" fill="none" stroke="white" stroke-width="5"/>'
                 '<path d="M32 61h64M41 44h46M41 78h46" fill="none" stroke="white" stroke-width="5"/>')
    elif any(w in label for w in ('descargas','download','patchdl','pegasus','store')):
        shape = ('<path d="M64 25v52M46 58l18 19 18-19" fill="none" stroke="white" stroke-width="10" '
                 'stroke-linejoin="round" stroke-linecap="round"/>'
                 '<path d="M32 84v14h64V84" fill="none" stroke="white" stroke-width="8" stroke-linecap="round"/>')
    elif any(w in label for w in ('media','nuvio','play','audio','pods')):
        shape = ('<rect x="22" y="33" width="84" height="63" rx="13" fill="white"/>'
                 '<path d="M55 46l29 19-29 19z" fill="#4267c1"/>')
    elif any(w in label for w in ('pkg','unpack','rar','compress','lz4','disco')):
        shape = ('<path d="M64 23l39 21v44l-39 21-39-21V44z" fill="white"/>'
                 '<path d="M25 44l39 22 39-22M64 66v43" fill="none" stroke="#5977ad" stroke-width="5"/>')
    elif any(w in label for w in ('save','backup','guardad')):
        shape = ('<path d="M29 26h62l11 12v66H29z" fill="white"/>'
                 '<rect x="43" y="31" width="43" height="24" fill="#5577b7"/>'
                 '<rect x="42" y="72" width="46" height="32" rx="5" fill="#a3e0fd"/>')
    elif any(w in label for w in ('fps','fan','overlay','hardware')):
        shape = ('<circle cx="64" cy="65" r="33" fill="none" stroke="white" stroke-width="9"/>'
                 '<path d="M64 65l24-26" stroke="white" stroke-width="8" stroke-linecap="round"/>'
                 '<circle cx="64" cy="65" r="8" fill="white"/>')
    elif any(w in label for w in ('wallpaper','personalizacion')):
        shape = ('<path d="M64 21a43 43 0 100 86c9 0 13-7 9-14-4-8 1-14 9-13 16 2 24-8 24-22A42 42 0 0064 21z" fill="white"/>'
                 '<circle cx="43" cy="51" r="7" fill="#ef8ca5"/><circle cx="66" cy="39" r="7" fill="#82bdf1"/>'
                 '<circle cx="86" cy="57" r="7" fill="#efcf78"/><circle cx="49" cy="78" r="7" fill="#86cea5"/>')
    elif any(w in label for w in ('hen','kernel','kstuff','debug','jailbreak')):
        shape = ('<rect x="34" y="34" width="60" height="60" rx="11" fill="white"/>'
                 '<rect x="47" y="47" width="34" height="34" rx="5" fill="#4b72b3"/>'
                 '<path d="M49 23v11m30-11v11M49 94v11m30-11v11M23 49h11M23 79h11M94 49h11M94 79h11" '
                 'stroke="white" stroke-width="7" stroke-linecap="round"/>')
    else:
        shape = ('<path d="M90 50a31 31 0 00-53-11l-9 9m0-12v12h12M38 78a31 31 0 0053 11l9-9m0 12V80H88" '
                 'fill="none" stroke="white" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">'
           '<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="'+bg1+'"/>'
           '<stop offset="1" stop-color="'+bg2+'"/></linearGradient></defs>'
           '<rect x="3" y="3" width="122" height="122" rx="25" fill="url(#bg)"/>'
           '<circle cx="18" cy="17" r="32" fill="'+glow+'" opacity=".12"/>'
           '<rect x="4" y="4" width="120" height="120" rx="24" fill="none" stroke="white" '
           'stroke-opacity=".4" stroke-width="1.5"/>' + shape + '</svg>')
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode('utf-8')).decode('ascii')


def update_icons(path):
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or not isinstance(data.get('payloads'),list):
        raise ValueError('Expected catalog object with payloads list')
    icons={};used=set()
    for n,item in enumerate(data['payloads']):
        if not isinstance(item,dict):raise ValueError('Invalid payload entry')
        key=item.get('icon_key') or item.get('id') or slug(item.get('name',''))
        key=slug(key)
        if key in used:
            key=slug(key+'-'+slug(item.get('filename','')))
        if key in used:
            key=slug(key+'-'+str(n))
        used.add(key)
        item['icon_key']=key
        item.setdefault('id',key)
        icons[key]=svg_icon(item,n)
    data.setdefault('name','HiddenKernel')
    data['icons_url']='icons.json'
    icon_path=path.with_name('icons.json')
    if len(icons)>4096:raise ValueError('Too many icons')
    content=json.dumps({'icons':icons},ensure_ascii=False,indent=2)+'\n'
    if len(content.encode())>=4*1024*1024:raise ValueError('Icon catalog too large')
    catalog=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    # Create local files; the user can review and upload both to GitHub together.
    tmp_icon=icon_path.with_suffix('.json.tmp')
    tmp_catalog=path.with_suffix('.json.tmp')
    tmp_icon.write_text(content,encoding='utf-8')
    tmp_catalog.write_text(catalog,encoding='utf-8')
    tmp_icon.replace(icon_path)
    tmp_catalog.replace(path)
    print(f'{len(icons)} icons generated; {path} and {icon_path}')


if __name__ == '__main__':
    update_catalog()
    update_icons(CATALOG)
