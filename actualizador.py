#!/usr/bin/env python3
"""HiddenKernel ELF updater - 2026-10-14.

Basado en PLM-Repository/main (commit 7fce507, 2026-10-14).
Conserva las migraciones curadas, el refresco conservador de releases oficiales,
la poda exacta de AnyPad y la escritura atomica. Incorpora Payload Manager v0.6.1 y PatchDL v0.0.7 desde upstreams
oficiales, con SHA-256 validado por GitHub.

No ejecuta codigo remoto ni realiza operaciones de escritura en GitHub.
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
        'tag': 'v7.0.22', 'asset': 'ps5upload-7.0.22.elf',
        'sha256': 'e382353612fdf85b2fdbfea75f4f5ebad260c767faa51b0446118646a6db0267',
        'date': '2026-10-12', 'category': 'ARCHIVOS / RED',
        'description': ('Servidor PS5Upload para transferencias y gestion de archivos desde '
                        'un cliente compatible. Desde 7.0.22 se mejora la exportacion '
                        'de capturas HDR PNG con perfil ICC. Algunas funciones requieren '
                        'actualizar tambien el cliente.'),
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
        'key': 'ps5sx2', 'name': 'PS5SX2 Bot', 'repo': 'Swordpdf/PS5SX2',
        'tag': 'vk-285-163', 'asset': 'ps5sx2-bot.elf',
        'sha256': '3420cdb5c826014b22b8ca8fa60a2026f0d9f91d3f5a5b818d4c98373eccb123',
        'date': '2026-10-11', 'category': 'EMULADORES',
        'description': ('Helper, instalador y lanzador de discos de PS5SX2. '
                        'Sustituye el antiguo ps5sx2-aio.elf, PS5SXHelper y '
                        'PS5SX2Installer. La aplicacion PS5SX2 se instala aparte.'),
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
)

PS4MOUNT = {
    'key': 'ps4mount', 'name': 'PS4Mount', 'repo': 'gasb07/ps4mount',
    'asset': 'ps4mount.elf', 'category': 'JUEGOS / COMPATIBILIDAD',
    'description': ('Monta PS4 fake PKG y sus actualizaciones desde USB exFAT sin '
                    'copiarlos al almacenamiento interno. Crea accesos en el menu '
                    'y ofrece panel web local en puerto 8770. Requiere soporte FPKG '
                    'y acceso a klog. DLC no soportados. Probado por el autor solo '
                    'en FW 13.20; otras versiones sin verificar. ESTADO: EXPERIMENTAL. '
                    'No incluir en autoload hasta probar compatibilidad.'),
}

OLD_PS5SX2_NAMES = {
    'ps5sx2 aio', 'ps5sx2 bot', 'ps5sx2 installer', 'ps5sx2 helper',
    'ps5sx2 disclaunch', 'disclaunch',
}
OLD_PS5SX2_FILES = {
    'ps5sx2-aio.elf', 'ps5sx2-bot.elf', 'ps5sx2installer.elf',
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
    return False


def make_entry(spec, tag, filename, url, checksum, date, release_name=''):
    version = tag
    if spec['key'] == 'ps5sx2':
        m = re.search(r'\b(\d+\.\d+)\b', release_name)
        version = (m.group(1) + ' (' + tag + ')') if m else (
            '2.03 (' + tag + ')' if tag == spec['tag'] else tag)
    return {
        'name': spec['name'], 'filename': filename, 'url': url,
        'source': 'https://github.com/' + spec['repo'] + '/releases',
        'source_direct': url, 'description': spec['description'],
        'last_update': date, 'version': version,
        'category': spec['category'], 'checksum': checksum,
    }


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
        if spec['key'] == 'ps5sx2' and any(x == entry for x in old) and len(old) == 1:
            return items, False
        if max(version_numbers(x.get('version', '')) for x in old) > version_numbers(entry['version']):
            print('OMITIDO: version mas reciente en catalogo:', spec['name'])
            return items, False
        if len(old) == 1 and old[0] == entry:
            return items, False
    indices = [i for i, x in enumerate(items) if matches_target(x, spec['key'])]
    first = indices[0] if indices else len(items)
    kept = [x for x in items if not matches_target(x, spec['key'])]
    kept.insert(first, entry)
    return kept, kept != items


def refresh_other_official_releases(items):
    """Conservative upstream updates already present in the catalog."""
    cache, changes, result = {}, [], []
    for item in items:
        if any(matches_target(item, spec['key']) for spec in TRACKED + (PS4MOUNT,)):
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

    # New PS4Mount: do not add any unverified ELF, even as a fallback.
    try:
        release = fetch_release(PS4MOUNT['repo'])
        found = checked_asset(PS4MOUNT['repo'], release, PS4MOUNT['asset'])
        if found and version_numbers(found[0]) >= version_numbers('v0.3.1'):
            entry = make_entry(PS4MOUNT, *found)
            items, did_change = replace_entry(items, PS4MOUNT, entry)
            if did_change:
                changes.append('PS4Mount ' + entry['version'])
        else:
            print('AVISO: PS4Mount sin release estable >=0.3.1, ELF y SHA256 comprobables; sin cambios')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('AVISO: PS4Mount no verificable; se conserva catalogo:', str(exc)[:120])

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
