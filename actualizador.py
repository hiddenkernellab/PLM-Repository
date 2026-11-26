#!/usr/bin/env python3
"""HiddenKernelLab PLM — actualizador del catálogo (26-11-2026).
Python 3.10+. Sustituye actualizador.py en la raíz; no hace push ni toca la PS5.
Uso: python actualizador.py [--offline] [--dry-run]
Actualiza únicamente los metadatos del catálogo, nunca el autoload de una consola.
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import os
import re
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / 'payloads.json'
ICONS = ROOT / 'icons.json'
SHA = re.compile(r'^[0-9a-f]{64}$')
TAG = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
REPO = re.compile(r'^https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/releases/?$')
CATEGORIES = ('ESENCIALES', 'HEN / AIO', 'SISTEMA', 'ARCHIVOS / RED',
              'PKG / INSTALACION', 'JUEGOS / COMPATIBILIDAD', 'DESCARGAS / TIENDAS',
              'EMULADORES', 'MULTIMEDIA', 'MANDOS / AUDIO', 'TRUCOS / PARTIDAS',
              'PERSONALIZACION', 'UTILIDADES', 'DESARROLLO / AVANZADO')
RETIRED = {'airpsx', 'jailbreak-store', 'ps5-file-explorer', 'zftpd-zhttp'}
# Conservar las decisiones anteriores para ramas especiales. No confundir
# instaladores y helpers, builds PS4/PS5, forks o releases de nomenclatura distinta.
MANUAL = {'ps5sx2-helper', 'ps5sx2-installer', 'etahen-13.60',
          'pldmgr-install-update', 'ps5-hardware-overlay', 'ps5-linux-loader',
          'hiddenkernel-4stores', 'kstuff-fpkg', 'kstuff-lite-110',
          'kstuff-dr-experimental', 'etahen', 'pizza-hen', 'onionhen'}
# SHA-256 publicados por los respectivos autores en los assets oficiales.
# El catálogo previo de itsPLK coincide con los hashes de Lite y ShadowMountPlus.
# No hay garantía de estabilidad por el mero hecho de tener un SHA-256.
PINS = {
    'kstuff-lite': ('KStuff Lite (EchoStretch)', 'EchoStretch/kstuff-lite',
        'v1.11', 'kstuff.elf', 'ab9a6cb4d3b1daf139d4d646e402b1cf569071acd64599c936d7a3a6164dc779',
        '2026-09-20', 'ESENCIALES'),
    'kstuff-lite-110': ('KStuff Lite 1.10 (alternativa)', 'EchoStretch/kstuff-lite',
        'v1.10', 'kstuff.elf', '82cbb1e70f8a562317d6b65269cf6aa0d7d94e22df4f1ac89a260ca0ec261252',
        '2026-08-12', 'ESENCIALES'),
    'shadowmountplus': ('ShadowMountPlus', 'drakmor/ShadowMountPlus',
        '1.7beta12', 'shadowmountplus.elf', '8755172ec9bef1bff5453ea75606e0caf7c41b5963f94f5a1087e7e8c6d9b1bd',
        '2026-11-08', 'ESENCIALES'),
    'kraken-mount': ('Kraken Mount', 'quer3q/kraken-mount',
        'v0.4.0', 'kraken-mount.elf', '6c778613b796039230f6690a16e4c04a76069a6b7b6c8030e292f54e904cc401',
        '2026-11-25', 'JUEGOS / COMPATIBILIDAD'),
}
# 1.15 Test3: el ELF aportado por el usuario coincide byte a byte (SHA-256)
# con el hash documentado por Wamphyre. No es una release oficial de Drakmor.
# Se conserva como entrada experimental separada, nunca como sustituto de Lite.
# El nombre stable del binario no acredita estabilidad. No importar Test8 sin hash.
EXPERIMENTAL = {
    'id': 'kstuff-dr-experimental', 'icon_key': 'kstuff-dr-experimental',
    'name': 'KStuff 1.15 DR Test3 (EXPERIMENTAL)',
    'filename': 'kstuff-1.15-dr-test3-stable.elf',
    'version': '1.15-dr-test3-stable', 'category': 'DESARROLLO / AVANZADO',
    'url': 'https://raw.githubusercontent.com/Wamphyre/wamphyre-autoloader/b1f1f286ad468efa3d30d7c83b158e30aa02fe61/payloads/default/kstuff-1.15-dr-test3-stable.elf',
    'source_direct': 'https://raw.githubusercontent.com/Wamphyre/wamphyre-autoloader/b1f1f286ad468efa3d30d7c83b158e30aa02fe61/payloads/default/kstuff-1.15-dr-test3-stable.elf',
    'source': 'https://github.com/Wamphyre/wamphyre-autoloader/blob/b1f1f286ad468efa3d30d7c83b158e30aa02fe61/payloads/default/kstuff-VENDOR.md',
    'checksum': '6c3758c2cc84e3aa7e3c41952371fd04e641647d46d03f8d4bea2ab77c16ecf5',
    'last_update': '2026-11-26',
}
# Fuentes de revisión manual:
# https://github.com/drakmor/kstuff-lite/releases
# https://github.com/Wamphyre/wamphyre-autoloader/blob/b1f1f286ad468efa3d30d7c83b158e30aa02fe61/payloads/default/kstuff-VENDOR.md
# https://github.com/itsPLK/ps5-payloads-mirror/blob/main/payloads.json

# El aviso antiguo se acumulaba porque el patrón del actualizador anterior
# no coincidía con el texto que él mismo añadía.
OLD_NOTICE = re.compile(r'\s*AVISO: version \S+ (?:nueva detectada y SHA-256 verificado; consultar los cambios del desarrollador antes de autocargar\.|detectada automaticamente; revisar cambios upstream\.)', re.I)
NOTICE = 'Consultar las notas de la version actual antes de autocargar.'

def version_key(value):
    """Sólo para series convencionales; beta8 < beta12 < estable 1.7."""
    s = str(value).strip().lower()
    m = re.fullmatch(r'v?\.?(\d+(?:\.\d+){0,3})(?:[-.]?(alpha|beta|rc)(\d+))?', s)
    if not m:
        return None
    core = tuple((list(map(int, m[1].split('.'))) + [0]*4)[:4])
    return core + ({'alpha': 0, 'beta': 1, 'rc': 2, None: 3}[m[2]], int(m[3] or 0))

def newer(a, b):
    x, y = version_key(a), version_key(b)
    return x is not None and y is not None and x > y

def pin_entry(ident, spec, old=None):
    name, repo, tag, asset, digest, date, category = spec
    url = f'https://github.com/{repo}/releases/download/{tag}/{asset}'
    out = dict(old or {})
    # Versionar el nombre local de las alternativas KStuff para que no colisionen.
    filename = f'kstuff-lite-{tag.lstrip("v")}.elf' if ident.startswith('kstuff-lite') else asset
    out.update(id=ident, icon_key=out.get('icon_key') or ident, name=name,
               version=tag, filename=filename, url=url, source_direct=url,
               source=f'https://github.com/{repo}/releases', checksum=digest,
               last_update=date, category=category)
    return out

def release_json(repo):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'HiddenKernelLab-PLM/2026-11-26',
               'X-GitHub-Api-Version': '2022-11-28'}
    token = os.getenv('GITHUB_TOKEN', '').strip()
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(f'https://api.github.com/repos/{repo}/releases?per_page=10', headers=headers)
    with urllib.request.urlopen(req, timeout=9) as response:
        result = json.load(response)
    if not isinstance(result, list):
        raise ValueError('Respuesta inesperada de GitHub')
    return result

def candidate_names(item, tag):
    oldurl = str(item.get('url', ''))
    name = urlsplit(oldurl).path.rsplit('/', 1)[-1]
    oldtag = str(item.get('version', ''))
    if '/releases/download/' in oldurl:
        oldtag = oldurl.split('/releases/download/', 1)[1].split('/', 1)[0]
    names = {name}
    for old, new in ((oldtag, tag), (oldtag.lstrip('v'), tag.lstrip('v'))):
        if old and old in name:
            names.add(name.replace(old, new, 1))
    special = {'payload-manager': f'pldmgr_{tag}.elf', 'ps5upload': f'ps5upload-{tag.lstrip("v")}.elf',
               'patchdl': f'patchdl_{tag.lstrip("v")}.elf', 'shadowmountplus': 'shadowmountplus.elf',
               'kstuff-lite': 'kstuff.elf', 'kraken-mount': 'kraken-mount.elf'}
    if item['id'] in special:
        names.add(special[item['id']])
    return {n for n in names if n.lower().endswith('.elf')}

def refresh(item, cache):
    ident = item['id']
    # KStuff se revisa manualmente por compatibilidad: no promocionar una
    # beta nueva automáticamente aunque GitHub la etiquete como estable.
    if ident in MANUAL or ident == 'kstuff-lite':
        return item
    m = REPO.fullmatch(str(item.get('source', '')))
    if not m:
        return item
    repo = m[1]
    oldurl = str(item.get('url', ''))
    # Un espejo no se convierte genéricamente en otro binario. ShadowMount
    # ya se migra al origen oficial mediante su pin; otras excepciones se conservan.
    if not oldurl.startswith(f'https://github.com/{repo}/releases/download/'):
        return item
    if repo not in cache:
        try:
            cache[repo] = release_json(repo)
        except (OSError, ValueError) as exc:
            print(f'AVISO: {repo}: {exc}; se conserva la versión actual')
            cache[repo] = []
    choices = []
    for rel in cache[repo]:
        tag = str(rel.get('tag_name', ''))
        if not TAG.fullmatch(tag) or rel.get('draft') or not newer(tag, item.get('version')):
            continue
        key = version_key(tag)
        if key is None:
            continue
        # Sólo ShadowMountPlus puede avanzar automáticamente entre betas
        # oficiales; no significa que sus betas sean estables.
        if ident == 'shadowmountplus':
            if key[4] == 0:
                continue
        elif rel.get('prerelease') or key[4] != 3:
            continue
        names = candidate_names(item, tag)
        matches = []
        for asset in rel.get('assets', []):
            name = str(asset.get('name', ''))
            digest = str(asset.get('digest', ''))
            url = str(asset.get('browser_download_url', ''))
            if (name in names and asset.get('state') == 'uploaded' and asset.get('size', 0) > 0
                    and digest.startswith('sha256:') and SHA.fullmatch(digest[7:])
                    and url == f'https://github.com/{repo}/releases/download/{tag}/{name}'):
                matches.append((name, digest[7:], url))
        if len(matches) == 1:
            date = str(rel.get('published_at') or '')[:10]
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
                choices.append((key, tag, date, matches[0]))
    if not choices:
        return item
    _, tag, date, (name, digest, url) = max(choices, key=lambda x: x[0])
    out = dict(item, version=tag, filename=name, url=url, source_direct=url,
               checksum=digest, last_update=date)
    if NOTICE not in str(out.get('description', '')):
        out['description'] = str(out.get('description', '')).strip() + ' ' + NOTICE
    print(f'ACTUALIZADO {ident}: {item["version"]} -> {tag} (digest publicado por GitHub)')
    return out

def clean_description(item):
    ident, version = item['id'], str(item.get('version', ''))
    d = OLD_NOTICE.sub('', str(item.get('description', ''))).strip()
    if ident == 'kstuff-lite':
        d = ('KStuff Lite de EchoStretch. v1.11: firmware 1.00-13.60 declarado por el autor; '
             'no equivale a compatibilidad universal de aplicaciones. BETA. '
             'No ejecutar dos versiones de KStuff ni combinar con un HEN que ya lo cargue. '
             'Para diagnosticar fallos, probar por separado en una sesión limpia, sin autoload. '
             'No sustituye a un gestor de montaje. Rama Drakmor 1.15 Test3 NO recomendada: '
             'reportes de kernel panic y corrupción de almacenamiento; sin validación propia.')
    elif ident == 'kstuff-lite-110':
        d = ('Alternativa oficial anterior de EchoStretch; v1.10 Beta, firmware 3.00-12.70 '
             'declarado por el autor. Sólo alternativa de diagnóstico si 1.11 resulta inestable. '
             'No garantiza compatibilidad de aplicaciones. No ejecutar junto a otro KStuff '
             'ni a un HEN que lo incorpore. No autocargar sin prueba.')
    elif ident == 'kstuff-dr-experimental':
        d = ('EXPERIMENTAL, NO AUTOCARGAR. Binario de pruebas de Drakmor distribuido fuera de sus releases; '
             'copia de Wamphyre fijada por commit. SHA-256 coincidente con el ELF aportado por el usuario. '
             'El nombre stable no implica estabilidad. Reportes de KP en FW 12.20 y de corrupción '
             'de almacenamiento; no recomendado para uso habitual. No duplicar KStuff ni usar junto '
             'con un HEN que ya lo cargue. Para diagnóstico, aislar otros payloads y gestores de montaje; '
             'no está demostrada una incompatibilidad universal con ShadowMountPlus o Kraken. '
             'Detener las pruebas si aparece KP. No sustituye a un gestor de montaje. '
             'Compatibilidad y autenticidad del autor no verificadas de forma independiente.')
    elif ident == 'shadowmountplus':
        d = (f'ShadowMountPlus {version}, gestor de montaje y biblioteca para PS5. '
             'Desde 1.7beta12: migración de configuración a v2, perfiles separados, '
             'recuperación de montaje y mejoras de escaneo y M.2. '
             'Fuente oficial de Drakmor. Beta: no confundir publicación con estabilidad. '
             'No ejecutar a la vez que Kraken Mount u otro gestor equivalente sin validación. '
             'No se ha demostrado incompatibilidad universal con KStuff; si hay KP, '
             'evitar repetir pruebas y no activar autoload. API LAN: sólo red de confianza. '
             'Hacer copia de seguridad antes de cambiar de versión.')
    elif ident == 'kraken-mount':
        d = (f'Kraken Mount {version}, gestor de biblioteca y montaje. Desde v0.4.0: '
             'biblioteca de aplicaciones instaladas, mejoras de interfaz y gestión de compatibilidad. '
             'No ejecutar simultáneamente con ShadowMountPlus u otro gestor equivalente '
             'sin validación. Requiere entorno homebrew y elfldr. No autocargar sin prueba.')
    elif ident == 'onionhen':
        d = ('OnionHEN: HEN con Toolbox, overlay y servicios. La v0.9.0 incorpora KStuff Lite '
             '1.11 y declara compatibilidad ampliada hasta 13.60. No cargar otro KStuff '
             'si el integrado está activo. No combinar con otros HEN o inyectores de atajos. '
             'No relanzar en la misma sesión. Verificar compatibilidad de la versión actual.')
    elif ident == 'pizza-hen':
        d = ('HEN AIO con KStuff, ShadowMount, Toolbox, FTP, ps5debug-NG e instalador de PKG. '
             'Algunas funciones experimentales. No duplicar los componentes integrados '
             'con payloads independientes; no autocargar sin prueba.')
    elif ident == 'ps5-webkit-autoloader':
        d = ('Autoloader WebKit oficial de itsPLK; consultar los firmwares y exploits admitidos '
             'por la release actual. No trasladar automáticamente compatibilidad de ramas '
             'anteriores ni autocargar payloads experimentales.')
    elif ident == 'payload-manager':
        d = ('Gestor oficial de payloads con tienda, búsqueda, detalles, favoritos y autoload. '
             'Distinto de HK-PLDMGR-Install-Update. Revisar la configuración de autoload '
             'local al cambiar de versión; actualizar el catálogo no elimina archivos instalados.')
    elif ident == 'ps5-library':
        d = ('Biblioteca y gestor de descargas/descompresión para PS5. Las notas de v0.7.32 '
             'documentaban resolución DNS alternativa (puede eludir bloqueos DNS intencionados) '
             'y modo reposo sólo con SSD interno, no USB/exFAT. En el catálogo anterior '
             'requería KStuff y ShadowMountPlus; verificar dependencias actuales. '
             'No confundir con el agente de rdiol12.')
    elif ident == 'hearbridge':
        d = ('Puente de audio PS5 a auriculares Bluetooth A2DP, panel web y perfiles. '
             'Posibles conflictos de reconexión con mandos y cortes de audio; no autocargar '
             'hasta confirmar estabilidad. Alternativa a FGG PlayPods.')
    elif ident == 'fbneo-ps5':
        d = ('Emulador arcade nativo PS5. Desde v1.9, ID PPSA99924; conserva datos en '
             '/data/fbneo. Si existe el antiguo PPSA99012, identificarlo antes de borrar. '
             'El catálogo anterior requiere elfldr y ShadowMountPlus; verificar dependencias '
             'y compatibilidad de la release actual.')
    elif ident == 'genesis-plus-gx-ps5':
        d = ('Emulador nativo Mega Drive, Sega CD, Master System y Game Gear. '
             'Incluye instalador y helper. El catálogo anterior requiere KStuff y ShadowMountPlus; '
             'verificar dependencias actuales. No autocargar sin prueba.')
    elif ident == 'ps5upload':
        d = ('Servidor de transferencias y gestión remota: reanudación, extracción RAR '
             'y gestión de payloads. Usar versiones compatibles de cliente y helper. '
             'Desde v7.0.34 corrige problemas de mayúsculas/minúsculas; desde v7.1.13 '
             'incluye envío de ELF con confirmación explícita y mejoras SMB. Revisar cambios upstream.')
    elif ident == 'ps5-dump-forge':
        d = ('Gestor de archivos e imágenes para copias de seguridad propias en PS5. '
             'Ediciones o conversiones pueden ser irreversibles; verificar respaldos '
             'y espacio libre. No autocargar.')
    elif ident == 'romm-sync':
        d = ('Cliente RomM para sincronizar biblioteca, partidas y savestates con un servidor '
             'propio. ELF independiente; app nativa opcional. Verificar restauraciones.')
    elif ident == 'ps5-signal':
        d = ('Personaliza LED y pitidos; API local 127.0.0.1:9150. No usar ps5-signal-dev.elf. '
             'La rama 0.2 corrigió problemas de reposo y pitidos; compatibilidad por firmware '
             'pendiente de verificar en cada consola. No autocargar sin prueba.')
    else:
        # No eliminar advertencias de seguridad ni inventar changelogs.
        # Eliminar sólo el aviso automático repetitivo, conservando el resto.
        d = re.sub(r'(?:\s*' + re.escape(NOTICE) + r')+', '', d).strip()
        if OLD_NOTICE.search(str(item.get('description', ''))) or NOTICE in str(item.get('description', '')):
            d = (d + ' ' + NOTICE).strip()
    item['description'] = d

def icon_fallback():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect width="128" height="128" rx="22" fill="#253d68"/><rect x="31" y="31" width="66" height="66" rx="10" fill="none" stroke="white" stroke-width="6"/><path d="M49 64h30M64 49v30" stroke="white" stroke-width="7" stroke-linecap="round"/></svg>'
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode()

def validate(catalog, icons):
    items = catalog.get('payloads')
    if not isinstance(items, list) or not items:
        raise ValueError('Catálogo vacío')
    ids, keys = set(), set()
    for x in items:
        ident, key = x.get('id'), x.get('icon_key')
        if not isinstance(ident, str) or not ident or ident in ids:
            raise ValueError(f'ID inválido/duplicado: {ident}')
        if not isinstance(key, str) or not key or key in keys:
            raise ValueError(f'icon_key inválido/duplicado: {key}')
        ids.add(ident); keys.add(key)
        if x.get('category') not in CATEGORIES or not SHA.fullmatch(str(x.get('checksum', ''))):
            raise ValueError(f'Categoría o SHA-256 inválidos: {ident}')
        for field in ('url', 'source_direct'):
            u = urlsplit(str(x.get(field, '')))
            if u.scheme != 'https' or not u.hostname or u.username or u.password:
                raise ValueError(f'URL inválida: {ident}/{field}')
        if not x.get('name') or not x.get('filename') or not x.get('version'):
            raise ValueError(f'Metadatos incompletos: {ident}')
        if key not in icons['icons']:
            raise ValueError(f'Icono ausente: {ident}')
    required = {'nanodns', 'payload-manager', 'apr-emu-updater', 'ftpsrv', *PINS, EXPERIMENTAL['id']}
    if not required.issubset(ids) or RETIRED & ids:
        raise ValueError(f'Entradas esenciales ausentes o retiradas presentes: {required-ids}')
    if len(json.dumps(icons, ensure_ascii=False).encode()) > 4*1024*1024:
        raise ValueError('icons.json supera 4 MiB')

def transform(catalog, icon_data, offline=False):
    out = copy.deepcopy(catalog); icon_out = copy.deepcopy(icon_data)
    items = out.get('payloads'); images = icon_out.get('icons')
    if not isinstance(items, list) or not items or not isinstance(images, dict):
        raise ValueError('Formato de catálogo o iconos inesperado')
    entries = {}
    for x in items:
        ident = x.get('id')
        if not isinstance(ident, str) or not ident or ident in entries:
            raise ValueError(f'ID vacío o duplicado: {ident}')
        entries[ident] = x
    for ident in RETIRED:
        entries.pop(ident, None)
    old = entries.get('kstuff-fpkg')
    old_icon = images.get(old.get('icon_key', 'kstuff-fpkg')) if old else None
    if old and str(old.get('version', '')).lower() in {'1.13-dr-test5', '1.13-fpkg-dr-test5'}:
        # Retirar una build antigua con discrepancia test3/test5 en el espejo.
        # Nuevo ID para evitar que los favoritos/autoload la sustituyan en silencio.
        del entries['kstuff-fpkg']
        print('RETIRADO: KStuff FPKG 1.13 Test5 del catálogo principal')
    # Si alguien añadió manualmente una rama posterior, no sustituirla por otra.
    elif old:
        warning = (' EXPERIMENTAL: no autocargar; no duplicar KStuff. '
                   'No se garantiza compatibilidad ni estabilidad; detener pruebas si hay KP.')
        if warning not in str(old.get('description', '')):
            old['description'] = str(old.get('description', '')).strip() + warning
    for ident, spec in PINS.items():
        previous = entries.get(ident)
        if previous:
            tag = str(previous.get('version', ''))
            if tag != spec[2] and (newer(tag, spec[2]) or version_key(tag) is None):
                continue  # No retroceder ni reemplazar una rama desconocida.
        entries[ident] = pin_entry(ident, spec, previous)
    # Entrada separada: no reutilizar el ID de un KStuff previamente autocargado.
    exp_id = EXPERIMENTAL['id']
    if exp_id not in entries:
        entries[exp_id] = dict(EXPERIMENTAL)
    elif entries[exp_id].get('version') == EXPERIMENTAL['version']:
        entries[exp_id].update(EXPERIMENTAL)
    cache = {}
    for ident, x in list(entries.items()):
        if not offline:
            x = refresh(x, cache)
        x.setdefault('icon_key', ident)
        clean_description(x)
        entries[ident] = x
    order = {c:i for i,c in enumerate(CATEGORIES)}
    out['payloads'] = sorted(entries.values(), key=lambda x:(order.get(x.get('category'),999), str(x.get('name','')).casefold()))
    out['icons_url'] = 'icons.json'
    # Preservar iconos existentes; sólo quitar los que correspondan a entradas
    # retiradas, no eliminar metadatos ajenos al catálogo ni imágenes sin identificar.
    for x in out['payloads']:
        key = x['icon_key']
        if not images.get(key):
            images[key] = (old_icon if x['id'].startswith('kstuff-lite') and old_icon else icon_fallback())
    if old and 'kstuff-fpkg' not in entries:
        old_key = old.get('icon_key', 'kstuff-fpkg')
        if not any(x['icon_key'] == old_key for x in out['payloads']):
            images.pop(old_key, None)
    validate(out, icon_out)
    return out, icon_out

def rendered(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

def atomic_bytes(path, data):
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.'+path.name+'.', delete=False) as f:
        temp = Path(f.name)
        try:
            f.write(data); f.flush(); os.fsync(f.fileno())
        except BaseException:
            temp.unlink(missing_ok=True); raise
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--offline', action='store_true', help='Aplicar migraciones verificadas sin API')
    ap.add_argument('--dry-run', action='store_true', help='Validar y mostrar cambios sin escribir')
    args = ap.parse_args()
    try:
        oldcat = CATALOG.read_bytes(); oldicons = ICONS.read_bytes()
        cat, icons = json.loads(oldcat), json.loads(oldicons)
        newcat, newicons = transform(cat, icons, args.offline)
        changes = [(p, old, rendered(new)) for p, old, new in ((CATALOG, oldcat, newcat), (ICONS, oldicons, newicons))
                   if json.loads(old) != new]
        print(f'HiddenKernel: {len(cat["payloads"])} -> {len(newcat["payloads"])} entradas; archivos a modificar: '+
              (', '.join(p.name for p,_,_ in changes) or 'ninguno'))
        if args.dry_run:
            return 0
        done = []
        try:
            for path, old, new in changes:
                if path.read_bytes() != old:
                    raise RuntimeError(f'{path.name} cambió durante la ejecución')
                atomic_bytes(path, new); done.append((path, old, new))
        except BaseException:
            for path, old, new in reversed(done):
                if path.read_bytes() == new:
                    atomic_bytes(path, old)
            raise
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
