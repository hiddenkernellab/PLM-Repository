#!/usr/bin/env python3
"""HiddenKernel updater - resilient repair, 2026-10-12.

Uses the pinned upstream generator when available. If an upstream fails, keeps
existing verified catalog intact rather than aborting or publishing empty JSON.
Never pushes to GitHub.
"""
import hashlib
import json
import re
import urllib.request
from pathlib import Path

MAIN_COMMIT = 'af8eb2eafe345979bab15d86acbf78543b48567c'
MAIN_BLOB_SHA = 'aaed504fe6db9c9149a2e8c94354ba5db0e01ac6'
MAIN_URL = ('https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/'
            + MAIN_COMMIT + '/actualizador.py')
CATALOG = Path('payloads.json')


def read_catalog(path=CATALOG):
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('payloads'), list):
        raise ValueError('payloads.json no tiene una lista payloads valida')
    return data


def write_catalog(data, path=CATALOG):
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    tmp.replace(path)


def run_pinned_main():
    req = urllib.request.Request(MAIN_URL, headers={'User-Agent': 'HiddenKernel-Updater/2026-10-12'})
    with urllib.request.urlopen(req, timeout=25) as response:
        source = response.read()
    blob = b'blob ' + str(len(source)).encode() + b'\0' + source
    if hashlib.sha1(blob).hexdigest() != MAIN_BLOB_SHA:
        raise ValueError('SHA del main no coincide: no se ejecuta codigo alterado')
    ns = {'__name__': '__hiddenkernel_pinned__'}
    exec(compile(source, MAIN_URL, 'exec'), ns, ns)
    ns['main']()
    read_catalog()  # Verify before accepting output.


def maintain_catalog(path=CATALOG):
    data = read_catalog(path)
    entries = data['payloads']
    # Remove exact duplicate names + versions + filenames, preserve distinct variants.
    seen, cleaned = set(), []
    for item in entries:
        if not isinstance(item, dict):
            continue
        key = tuple(str(item.get(k, '')).casefold() for k in ('name', 'version', 'filename'))
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    for item in cleaned:
        if str(item.get('name', '')).casefold() != 'ps5upload':
            continue
        version = tuple(int(n) for n in re.findall(r'\d+', str(item.get('version', '')))[:3])
        if version >= (7, 0, 17) and re.fullmatch(r'[0-9a-f]{64}', str(item.get('checksum', ''))):
            item['category'] = 'ARCHIVOS / RED'
            item['description'] = ('Servidor ELF para PS5Upload y transferencias remotas. '
                'Version 7.0.17: gestion de partidas PS5 desde el cliente compatible; '
                'hacer copia de seguridad antes de editar. ESTADO: EN PRUEBAS.')
    data['payloads'] = cleaned
    write_catalog(data, path)
    return len(cleaned)


def main():
    # Keep a copy so a failing upstream cannot corrupt the published catalog.
    backup = CATALOG.read_bytes() if CATALOG.exists() else None
    updated = False
    try:
        run_pinned_main()
        updated = True
    except Exception as exc:
        if backup is not None:
            CATALOG.write_bytes(backup)
            print(f'AVISO: generador upstream fallo ({type(exc).__name__}: {exc}).')
            print('Se conserva el catalogo existente; no se anuncian versiones nuevas.')
        else:
            raise RuntimeError('Fallo upstream y no existe catalogo previo para conservar') from exc
    total = maintain_catalog()
    print(f'HiddenKernel: {total} entradas validas; generacion upstream: {"OK" if updated else "SIN ACTUALIZAR"}')


if __name__ == '__main__':
    main()
