#!/usr/bin/env python3
"""Actualiza los iconos del catálogo HiddenKernel sin borrar sus actualizaciones.

Colocar junto a actualizador.py y payloads.json y ejecutar:
    python HiddenKernel_Actualizador_Iconos.py

Crea copias .bak del código y JSON antes de modificar. Funciona sin Internet.
Los diseños son originales; NO afirma descargar logotipos oficiales.
"""
import ast
import base64
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPDATER = ROOT / 'actualizador.py'
CATALOG = ROOT / 'payloads.json'
ICONS = ROOT / 'icons.json'

# Esta función sustituye exclusivamente a svg_icon() en el actualizador
# existente. Así, al volver a ejecutar actualizador.py NO reaparecen
# los antiguos iconos etiquetados FTP / CODE / ELF.
REPLACEMENT = '''def svg_icon(item, n):
    """Ilustración vectorial cuadrada y colorida, inspirada en las tiendas PS5."""
    import base64
    import html
    import re
    name = str(item.get('name', '')).lower()
    category = str(item.get('category', '')).lower()
    text = name + ' ' + category
    themes = [('#18306e','#4d95f7','#c9f6ff'),('#443070','#bd6fee','#ffe5fa'),
              ('#064c59','#27c5c3','#d6ffff'),('#6e283e','#f67d73','#ffe8c4'),
              ('#36501d','#9acc53','#f8ffd9'),('#634017','#e9a64a','#fff4bb')]
    bg1,bg2,glow = themes[n % len(themes)]
    if any(w in text for w in ('mandos','pad','controller','xsense','ds4')):
        shape = '<path d="M40 51Q26 52 22 79q-2 15 12 17l22-14h16l22 14q14-2 12-17-4-27-18-28z" fill="white"/><path d="M40 65v17M32 73h16" stroke="#4862a2" stroke-width="6" stroke-linecap="round"/><circle cx="83" cy="68" r="5" fill="#ff7b87"/><circle cx="93" cy="79" r="5" fill="#91e5dc"/>'
    elif any(w in text for w in ('emuladores','ps5sx','snes','genesis','fbneo','xpsemu')):
        shape = '<rect x="24" y="29" width="80" height="69" rx="13" fill="white"/><rect x="32" y="37" width="64" height="39" rx="5" fill="#233c79"/><path d="M42 87h18M51 78v18" stroke="#497fc2" stroke-width="5"/><circle cx="82" cy="88" r="5" fill="#f585b7"/><circle cx="94" cy="82" r="5" fill="#7be8dd"/>'
    elif any(w in text for w in ('ftp','network','red','upload','websrv','tailscale','aria2')):
        shape = '<circle cx="64" cy="61" r="32" fill="none" stroke="white" stroke-width="7"/><ellipse cx="64" cy="61" rx="15" ry="32" fill="none" stroke="white" stroke-width="5"/><path d="M32 61h64M41 44h46M41 78h46" fill="none" stroke="white" stroke-width="5"/>'
    elif any(w in text for w in ('descargas','download','patchdl','pegasus','store')):
        shape = '<path d="M64 25v52M46 58l18 19 18-19" fill="none" stroke="white" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/><path d="M32 84v14h64V84" fill="none" stroke="white" stroke-width="8" stroke-linecap="round"/>'
    elif any(w in text for w in ('media','nuvio','play','audio','pods')):
        shape = '<rect x="22" y="33" width="84" height="63" rx="13" fill="white"/><path d="M55 46l29 19-29 19z" fill="#4267c1"/>'
    elif any(w in text for w in ('pkg','unpack','rar','compress','lz4','disco')):
        shape = '<path d="M64 23l39 21v44l-39 21-39-21V44z" fill="white"/><path d="M25 44l39 22 39-22M64 66v43" fill="none" stroke="#5977ad" stroke-width="5"/>'
    elif any(w in text for w in ('save','backup','guardad')):
        shape = '<path d="M29 26h62l11 12v66H29z" fill="white"/><rect x="43" y="31" width="43" height="24" fill="#5577b7"/><rect x="42" y="72" width="46" height="32" rx="5" fill="#a3e0fd"/>'
    elif any(w in text for w in ('fps','fan','overlay','hardware')):
        shape = '<circle cx="64" cy="65" r="33" fill="none" stroke="white" stroke-width="9"/><path d="M64 65l24-26" stroke="white" stroke-width="8" stroke-linecap="round"/><circle cx="64" cy="65" r="8" fill="white"/>'
    elif any(w in text for w in ('wallpaper','personalizacion')):
        shape = '<path d="M64 21a43 43 0 100 86c9 0 13-7 9-14-4-8 1-14 9-13 16 2 24-8 24-22A42 42 0 0064 21z" fill="white"/><circle cx="43" cy="51" r="7" fill="#ef8ca5"/><circle cx="66" cy="39" r="7" fill="#82bdf1"/><circle cx="86" cy="57" r="7" fill="#efcf78"/><circle cx="49" cy="78" r="7" fill="#86cea5"/>'
    elif any(w in text for w in ('hen','kernel','kstuff','debug','jailbreak')):
        shape = '<rect x="34" y="34" width="60" height="60" rx="11" fill="white"/><rect x="47" y="47" width="34" height="34" rx="5" fill="#4b72b3"/><path d="M49 23v11m30-11v11M49 94v11m30-11v11M23 49h11M23 79h11M94 49h11M94 79h11" stroke="white" stroke-width="7" stroke-linecap="round"/>'
    else:
        shape = '<path d="M90 50a31 31 0 00-53-11l-9 9m0-12v12h12M38 78a31 31 0 0053 11l9-9m0 12V80H88" fill="none" stroke="white" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>'
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">'
           '<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="'+bg1+'"/>'
           '<stop offset="1" stop-color="'+bg2+'"/></linearGradient></defs>'
           '<rect x="3" y="3" width="122" height="122" rx="25" fill="url(#bg)"/>'
           '<circle cx="18" cy="17" r="32" fill="'+glow+'" opacity=".12"/>'
           '<rect x="4" y="4" width="120" height="120" rx="24" fill="none" stroke="white" stroke-opacity=".4" stroke-width="1.5"/>'
           + shape + '</svg>')
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode('utf-8')).decode('ascii')
'''

def backup(path):
    if path.exists():
        target = path.with_name(path.name + '.' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.bak')
        shutil.copy2(path, target)
        print('Copia:', target.name)

def main():
    if not UPDATER.is_file() or not CATALOG.is_file():
        raise SystemExit('ERROR: Coloca este archivo junto a actualizador.py y payloads.json.')
    old = UPDATER.read_text(encoding='utf-8')
    tree = ast.parse(old)
    targets = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == 'svg_icon']
    if len(targets) != 1:
        raise SystemExit('ERROR: No se encontró una única función svg_icon en actualizador.py. Sin cambios.')
    parsed = json.loads(CATALOG.read_text(encoding='utf-8'))
    if not isinstance(parsed.get('payloads'), list):
        raise SystemExit('ERROR: Catálogo inválido. Sin cambios.')
    before = old.splitlines(keepends=True)
    target = targets[0]
    patched = ''.join(before[:target.lineno-1]) + REPLACEMENT + ''.join(before[target.end_lineno:])
    ast.parse(patched)
    backup(UPDATER)
    backup(CATALOG)
    backup(ICONS)
    UPDATER.write_text(patched, encoding='utf-8')
    # Crear iconos sin lanzar update_catalog() ni tocar versiones o URLs.
    scope = {'__name__':'hiddenkernel_icons_only'}
    exec(compile(patched, str(UPDATER), 'exec'), scope)
    scope['update_icons'](CATALOG)
    updated = json.loads(CATALOG.read_text(encoding='utf-8'))
    icon_data = json.loads(ICONS.read_text(encoding='utf-8'))
    assert len(icon_data['icons']) == len(updated['payloads'])
    print('LISTO:', len(icon_data['icons']), 'iconos ilustrados. Sube actualizador.py, icons.json y payloads.json.')
    print('AVISO: Son diseños originales, no logotipos oficiales de los autores.')

if __name__ == '__main__':
    main()
