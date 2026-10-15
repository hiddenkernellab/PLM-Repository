#!/usr/bin/env python3
"""HiddenKernel: actualizador con generador de iconos ilustrados integrado.

Archivo independiente: reemplaza actualizador.py en PLM-Repository.
Mantiene el actualizador original del commit 7f9a7d1 (15 oct 2026).
Valida el SHA Git del código original antes de ejecutarlo.
Requiere Internet en cada ejecución para recuperar esa versión congelada.
"""
import ast
import hashlib
import urllib.request

PINNED_URL = 'https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/7f9a7d1aa1c38e941b02fc6dd0696f0810fd4a13/actualizador.py'
EXPECTED_BLOB = '66c1d52c387a6f94e402688de61ee745658bc28c'

REPLACEMENT = 'def svg_icon(item, n):\n    """Ilustración vectorial cuadrada y colorida, inspirada en las tiendas PS5."""\n    import base64\n    import html\n    import re\n    name = str(item.get(\'name\', \'\')).lower()\n    category = str(item.get(\'category\', \'\')).lower()\n    text = name + \' \' + category\n    themes = [(\'#18306e\',\'#4d95f7\',\'#c9f6ff\'),(\'#443070\',\'#bd6fee\',\'#ffe5fa\'),\n              (\'#064c59\',\'#27c5c3\',\'#d6ffff\'),(\'#6e283e\',\'#f67d73\',\'#ffe8c4\'),\n              (\'#36501d\',\'#9acc53\',\'#f8ffd9\'),(\'#634017\',\'#e9a64a\',\'#fff4bb\')]\n    bg1,bg2,glow = themes[n % len(themes)]\n    if any(w in text for w in (\'mandos\',\'pad\',\'controller\',\'xsense\',\'ds4\')):\n        shape = \'<path d="M40 51Q26 52 22 79q-2 15 12 17l22-14h16l22 14q14-2 12-17-4-27-18-28z" fill="white"/><path d="M40 65v17M32 73h16" stroke="#4862a2" stroke-width="6" stroke-linecap="round"/><circle cx="83" cy="68" r="5" fill="#ff7b87"/><circle cx="93" cy="79" r="5" fill="#91e5dc"/>\'\n    elif any(w in text for w in (\'emuladores\',\'ps5sx\',\'snes\',\'genesis\',\'fbneo\',\'xpsemu\')):\n        shape = \'<rect x="24" y="29" width="80" height="69" rx="13" fill="white"/><rect x="32" y="37" width="64" height="39" rx="5" fill="#233c79"/><path d="M42 87h18M51 78v18" stroke="#497fc2" stroke-width="5"/><circle cx="82" cy="88" r="5" fill="#f585b7"/><circle cx="94" cy="82" r="5" fill="#7be8dd"/>\'\n    elif any(w in text for w in (\'ftp\',\'network\',\'red\',\'upload\',\'websrv\',\'tailscale\',\'aria2\')):\n        shape = \'<circle cx="64" cy="61" r="32" fill="none" stroke="white" stroke-width="7"/><ellipse cx="64" cy="61" rx="15" ry="32" fill="none" stroke="white" stroke-width="5"/><path d="M32 61h64M41 44h46M41 78h46" fill="none" stroke="white" stroke-width="5"/>\'\n    elif any(w in text for w in (\'descargas\',\'download\',\'patchdl\',\'pegasus\',\'store\')):\n        shape = \'<path d="M64 25v52M46 58l18 19 18-19" fill="none" stroke="white" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/><path d="M32 84v14h64V84" fill="none" stroke="white" stroke-width="8" stroke-linecap="round"/>\'\n    elif any(w in text for w in (\'media\',\'nuvio\',\'play\',\'audio\',\'pods\')):\n        shape = \'<rect x="22" y="33" width="84" height="63" rx="13" fill="white"/><path d="M55 46l29 19-29 19z" fill="#4267c1"/>\'\n    elif any(w in text for w in (\'pkg\',\'unpack\',\'rar\',\'compress\',\'lz4\',\'disco\')):\n        shape = \'<path d="M64 23l39 21v44l-39 21-39-21V44z" fill="white"/><path d="M25 44l39 22 39-22M64 66v43" fill="none" stroke="#5977ad" stroke-width="5"/>\'\n    elif any(w in text for w in (\'save\',\'backup\',\'guardad\')):\n        shape = \'<path d="M29 26h62l11 12v66H29z" fill="white"/><rect x="43" y="31" width="43" height="24" fill="#5577b7"/><rect x="42" y="72" width="46" height="32" rx="5" fill="#a3e0fd"/>\'\n    elif any(w in text for w in (\'fps\',\'fan\',\'overlay\',\'hardware\')):\n        shape = \'<circle cx="64" cy="65" r="33" fill="none" stroke="white" stroke-width="9"/><path d="M64 65l24-26" stroke="white" stroke-width="8" stroke-linecap="round"/><circle cx="64" cy="65" r="8" fill="white"/>\'\n    elif any(w in text for w in (\'wallpaper\',\'personalizacion\')):\n        shape = \'<path d="M64 21a43 43 0 100 86c9 0 13-7 9-14-4-8 1-14 9-13 16 2 24-8 24-22A42 42 0 0064 21z" fill="white"/><circle cx="43" cy="51" r="7" fill="#ef8ca5"/><circle cx="66" cy="39" r="7" fill="#82bdf1"/><circle cx="86" cy="57" r="7" fill="#efcf78"/><circle cx="49" cy="78" r="7" fill="#86cea5"/>\'\n    elif any(w in text for w in (\'hen\',\'kernel\',\'kstuff\',\'debug\',\'jailbreak\')):\n        shape = \'<rect x="34" y="34" width="60" height="60" rx="11" fill="white"/><rect x="47" y="47" width="34" height="34" rx="5" fill="#4b72b3"/><path d="M49 23v11m30-11v11M49 94v11m30-11v11M23 49h11M23 79h11M94 49h11M94 79h11" stroke="white" stroke-width="7" stroke-linecap="round"/>\'\n    else:\n        shape = \'<path d="M90 50a31 31 0 00-53-11l-9 9m0-12v12h12M38 78a31 31 0 0053 11l9-9m0 12V80H88" fill="none" stroke="white" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>\'\n    svg = (\'<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">\'\n           \'<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="\'+bg1+\'"/>\'\n           \'<stop offset="1" stop-color="\'+bg2+\'"/></linearGradient></defs>\'\n           \'<rect x="3" y="3" width="122" height="122" rx="25" fill="url(#bg)"/>\'\n           \'<circle cx="18" cy="17" r="32" fill="\'+glow+\'" opacity=".12"/>\'\n           \'<rect x="4" y="4" width="120" height="120" rx="24" fill="none" stroke="white" stroke-opacity=".4" stroke-width="1.5"/>\'\n           + shape + \'</svg>\')\n    return \'data:image/svg+xml;base64,\' + base64.b64encode(svg.encode(\'utf-8\')).decode(\'ascii\')\n'


def main():
    request = urllib.request.Request(PINNED_URL, headers={'User-Agent': 'HiddenKernel-Updater/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=25) as r:
            raw = r.read(256_000)
    except Exception as ex:
        raise SystemExit('No se pudo recuperar la versión original verificada: ' + str(ex))
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if blob != EXPECTED_BLOB:
        raise SystemExit('Verificación de integridad fallida: origen inesperado; no se ejecuta.')
    original = raw.decode('utf-8')
    tree = ast.parse(original)
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'svg_icon']
    if len(funcs) != 1:
        raise SystemExit('La versión original no contiene svg_icon como se esperaba.')
    f = funcs[0]
    lines = original.splitlines(keepends=True)
    merged = ''.join(lines[:f.lineno-1]) + REPLACEMENT + ''.join(lines[f.end_lineno:])
    ast.parse(merged)
    scope = {'__name__': '__main__', '__file__': __file__}
    exec(compile(merged, __file__, 'exec'), scope)

if __name__ == '__main__':
    main()
