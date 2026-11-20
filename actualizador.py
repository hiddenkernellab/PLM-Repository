#!/usr/bin/env python3
"""HiddenKernel: actualizador acumulativo basado en main verificado el 19-11-2026.
Conserva el actualizador publicado ejecutando una copia exacta fijada por SHA,
y añade Kraken Mount v0.3.0 sin duplicados. No realiza push a GitHub.
Requiere Internet para recuperar el actualizador original de main.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parent
UPSTREAM = 'https://raw.githubusercontent.com/hiddenkernellab/PLM-Repository/d1df14fc26042548246f8b345f02b511e95a40a7/actualizador.py'
UPSTREAM_SHA = '13ee24a5aeed710d0933693454c4b80ff19eabc0'  # Git blob SHA, no SHA256
CATALOG = ROOT / 'payloads.json'
KRAKEN = {
    'id': 'kraken-mount', 'name': 'Kraken Mount', 'filename': 'kraken-mount.elf',
    'version': 'v0.3.0', 'category': 'JUEGOS / COMPATIBILIDAD',
    'url': 'https://github.com/quer3q/kraken-mount/releases/download/v0.3.0/kraken-mount.elf',
    'source_direct': 'https://github.com/quer3q/kraken-mount/releases/download/v0.3.0/kraken-mount.elf',
    'source': 'https://github.com/quer3q/kraken-mount/releases',
    'description': 'Monta FPKG y carpetas de juegos sin instalacion convencional. v0.3.0 corrige guardados, DLC/PlayGo, montaje de PKG y retirada segura de USB. Requiere entorno homebrew y elfldr 9021. No autocargar.',
    'last_update': '2026-11-18',
    'checksum': '092623a204b707b89d0867a0087f9dd1c430eef6a22db497f03b59aaf1297bfe',
    'icon_key': 'kraken-mount',
}

def git_blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def main():
    with urllib.request.urlopen(UPSTREAM, timeout=30) as response:
        original = response.read()
    if git_blob_sha(original) != UPSTREAM_SHA:
        raise RuntimeError('El actualizador upstream no coincide con el main verificado: no se ejecuta.')
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', prefix='.hkl_base_', dir=ROOT, delete=False) as f:
        tmp = Path(f.name)
        f.write(original)
    try:
        completed = subprocess.run([sys.executable, str(tmp), *sys.argv[1:]], cwd=ROOT)
    finally:
        tmp.unlink(missing_ok=True)
    if completed.returncode:
        return completed.returncode
    data = json.loads(CATALOG.read_text(encoding='utf-8'))
    items = data['payloads']
    matches = [i for i, x in enumerate(items) if x.get('id') == 'kraken-mount' or x.get('name', '').lower() == 'kraken mount']
    if len(matches) > 1:
        raise RuntimeError('Hay entradas duplicadas de Kraken Mount; se requiere revision manual.')
    if matches and items[matches[0]].get('version') == KRAKEN['version']:
        print('Kraken Mount v0.3.0: ya incorporado.')
        return 0
    if matches and items[matches[0]].get('version', '').lstrip('v') > '0.3.0':
        print('Kraken Mount: version mas reciente presente; sin cambios.')
        return 0
    if matches:
        items[matches[0]] = {**items[matches[0]], **KRAKEN}
    else:
        items.append(KRAKEN.copy())
    items.sort(key=lambda x: (str(x.get('category','')), str(x.get('name','')).casefold()))
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=ROOT, prefix='.payloads_', delete=False) as f:
        f.write(rendered)
        replacement = Path(f.name)
    os.replace(replacement, CATALOG)
    print('Kraken Mount v0.3.0: incorporado al catalogo local (sin push).')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
