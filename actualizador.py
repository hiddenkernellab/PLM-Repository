#!/usr/bin/env python3
"""HiddenKernel ELF updater - 2026-10-15 10:06 CEST.

Integracion acumulativa contrastada con PLM-Repository/main, commit 205cabb2.
Conserva: iconos, PLDMGR 0.6.1, PatchDL 0.0.7, RomM Sync 1.2.0,
PS4Mount 0.5.1, PS5SX2 2.10 (helper e installer), LZ4 1.5.0,
LibrePadPS5 1.1.3, PS5Library Agent 0.2.91 y Orbit Store 1.3.5.
Actualiza PS5Upload a 7.0.23, incluyendo SHA-256 oficial y fallback offline.
No ejecuta codigo remoto ni realiza commits ni push.
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
        'tag': 'v7.0.23', 'asset': 'ps5upload-7.0.23.elf',
        'sha256': '419b56a10336dda8f4a28672271dfb635e74b05966cc08d44305e70f862dc110',
        'date': '2026-10-15', 'category': 'ARCHIVOS / RED',
        'description': ('PS5Upload 7.0.23: compatibilidad restaurada con Payload Manager '
                        '0.6.1; transferencias y bibliotecas grandes mas fluidas, '
                        'copias Android corregidas y exportacion/importacion de '
                        'listas de payloads. Algunas funciones requieren actualizar '
                        'tambien el cliente de ordenador o Android.'),
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
        'tag': 'v0.0.7', 'asset': 'patchdl_0.0.7.elf',
        'sha256': '925d211fa8aaeb6b52b635c54641a14e36239ad3ebbdd3f7738c79a1c1e688e3',
        'date': '2026-10-14', 'category': 'DESCARGAS',
        'description': ('Descarga e instala actualizaciones oficiales compatibles de juegos '
                        'ya instalados, con cola y reanudacion desde interfaz web. '
                        'La v0.0.7 corrige el arranque y acceso directo en FW 13.xx; '
                        'probado por el autor en 11.60 y 13.60. Solo actualizaciones '
                        'oficiales, no descarga juegos.'),
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
        'tag': 'v1.2.0', 'asset': 'romm-sync.elf',
        'sha256': '5e33f6178780a939e2ea4a13f363b5fe63bc2a63739d90c3ec3faaa71e169861',
        'date': '2026-10-14', 'category': 'EMULADORES',
        'description': ('Cliente de RomM para PS5: descarga juegos y BIOS a las carpetas '
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
        'User-Agent': 'HiddenKernel-ELF-Updater/2026-10-14',
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
    if key == 'ps5upload':
        return name == 'ps5upload' or bool(re.fullmatch(
            r'ps5upload[-_]v?\d+(?:\.\d+)*\.elf', filename))
    if key == 'nuvio':
        return name == 'nuvio ps5' or filename == 'nuvio-ps5.elf'
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
    return make_entry(spec, *choice, release_name=release_name)


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
            return items, False
        if len(old) == 1:
            for k in ('id','icon_key'):
                if old[0].get(k): entry[k] = old[0][k]
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
    label=symbol(item)
    color=PALETTE[n%len(PALETTE)]
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">'
         f'<rect width="128" height="128" rx="25" fill="{color}"/>'
         f'<rect x="10" y="10" width="108" height="108" rx="19" fill="none" stroke="#ffffff" stroke-opacity=".28" stroke-width="2"/>'
         f'<circle cx="64" cy="43" r="17" fill="#ffffff" fill-opacity=".16"/>'
         f'<path d="M55 43h18M64 34v18" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>'
         f'<text x="64" y="94" text-anchor="middle" fill="white" font-family="Arial,sans-serif" font-size="22" font-weight="bold">{label}</text></svg>')
    return 'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()

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
