"""Repackage historic builds without altering their camera payloads.

Every accepted hash is reconstructed from the exact stock and a checked manifest.
Run this AFTER any version-specific package script to refresh all compatible ZIPs.
Old archives remain untouched. No device operations.
"""
from pathlib import Path
import hashlib
import json
import re
import zipfile
from module_template import TEMPLATE, style_customize_text

ROOT = Path(__file__).resolve().parents[1]
STOCK_SHA = 'dbd740c5c7ba3081fb9d38b68b2f9975e19d6faad41dd5f87ce75f3c7d7be485'
LIB = 'system/vendor/lib64/libmtkcam_metastore.so'


def registry():
    stock = (ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes()
    assert hashlib.sha256(stock).hexdigest() == STOCK_SHA
    result = {STOCK_SHA: 'stock'}
    for path in sorted((ROOT/'patches').rglob('patch-manifest.json')):
        m = json.loads(path.read_text())
        if m.get('input_sha256') != STOCK_SHA:
            raise ValueError(f'Unexpected original: {path}')
        rebuilt = bytearray(stock)
        occupied = set()
        for c in m['changes']:
            off = int(c['offset'], 16)
            old, new = bytes.fromhex(c['old']), bytes.fromhex(c['new'])
            assert len(old) == len(new) and 0 <= off <= len(stock)-len(old)
            assert stock[off:off+len(old)] == old, path
            indices = set(range(off, off+len(old)))
            assert not occupied.intersection(indices), path
            occupied.update(indices)
            rebuilt[off:off+len(new)] = new
        actual = (path.parent/'libmtkcam_metastore.so').read_bytes()
        assert actual == rebuilt, path
        assert hashlib.sha256(actual).hexdigest() == m['output_sha256'], path
        result[m['output_sha256']] = m['profile']
    return result


def installer(old, hashes):
    # Preserve payload checksum, permissions, backup and conflict checks.
    pattern = r'case "\$LIVE_SHA" in\n.*?\nesac'
    replacement = ('case "$LIVE_SHA" in\n  '+ '|'.join(sorted(hashes)) +
        ') ;;\n  *) abort "! Unsupported vendor library hash: $LIVE_SHA" ;;\nesac')
    new, count = re.subn(pattern, lambda _: replacement, old, count=1, flags=re.S)
    if not count:
        new, count = re.subn(r'(?m)^\[ "\$LIVE_SHA" = "\$STOCK_SHA" \] \|\| abort [^\n]+',
                            lambda _: replacement, old, count=1)
    assert count == 1, 'Unrecognized installer: refuse blind rewrite'
    new = new.replace('libmtkcam_metastore.stock.so', 'libmtkcam_metastore.previous.so')
    return new


def write_zip(path, files):
    with zipfile.ZipFile(path, 'w') as z:
        for rel, data in sorted(files.items()):
            info = zipfile.ZipInfo(rel, date_time=(2026, 9, 13, 0, 0, 0))
            info.create_system = 3
            executable = rel.endswith('.sh') or rel.endswith('update-binary')
            info.external_attr = (0o100755 if executable else 0o100644) << 16
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert z.read(LIB) == files[LIB]


def main():
    hashes = registry()
    dest = ROOT/'dist/compatible'; dest.mkdir(exist_ok=True)
    reports = []
    for original in sorted((ROOT/'dist').glob('*.zip')):
        with zipfile.ZipFile(original) as z:
            files = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
        payload_hash = hashlib.sha256(files[LIB]).hexdigest()
        assert payload_hash in hashes
        original_installer = files['customize.sh'].decode().replace('\r\n', '\n')
        compatible_installer = installer(original_installer, hashes)
        prop = files['module.prop'].decode().replace('\r\n', '\n')
        assert 'id=x6810_raw12mp\n' in prop
        prop = re.sub(r'(?m)^(version=.*)$', r'\1-compat1', prop)
        files['module.prop'] = prop.encode()
        files['customize.sh'] = style_customize_text(compatible_installer, prop).encode()
        # v0.1-v0.3 did not ship auxiliary properties. Retain all historic
        # properties when present, so a rollback does not change two variables.
        if 'system.prop' not in files:
            files['system.prop'] = b'vendor.camera.tran.nums=3\n'
        for name in ('post-fs-data.sh', 'service.sh', 'README.md'):
            files.setdefault(name, (TEMPLATE / name).read_bytes())
        files['compatibility.json'] = (json.dumps(hashes, indent=2)+'\n').encode()
        files['COMPATIBILITY.md'] = (
            '# Instalador compatible\n\n'
            'Biblioteca identica a la version historica; no corrige su color ni sus crashes.\n'
            'Acepta stock y todas las revisiones verificadas del registro incluido.\n'
            'Instala este ZIP desde APatch sobre el modulo existente y reinicia una vez.\n'
            'No requiere desinstalar previamente. Conserva id=x6810_raw12mp.\n'
            'Los ZIP antiguos sin compat1 mantienen sus restricciones originales.\n'
            'Versiones futuras requieren regenerar esta coleccion con el script comun.\n'
            'v0.6 tiene una regresion reportada; se conserva solo para reproducibilidad.\n'
        ).encode()
        output = dest/(original.stem+'-compat1.zip')
        write_zip(output, files)
        reports.append(dict(file=output.name, original=original.name, payload_sha256=payload_hash,
                            sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
    (dest/'index.json').write_text(json.dumps(reports, indent=2)+'\n')
    (dest/'SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['file']+'\n' for r in reports))
    print(f'{len(reports)} compatible ZIPs; {len(hashes)} verified base hashes')


if __name__ == '__main__': main()
