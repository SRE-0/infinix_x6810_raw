"""Offline validation: real payloads/manifests, ZIPs and isolated shell installers."""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile
from build import ROOT, LEGACY, STOCK, META, POLICY, SERVER, accepted_states, digest, module_files, write_zip

def require(condition, detail):
    if not condition:
        raise ValueError(detail)

def shell_quote(path):
    resolved = Path(path).resolve()
    value = os.path.relpath(resolved, Path.cwd()).replace('\\', '/')
    return "'" + value.replace("'", "'\\''") + "'"

def verify_manifests():
    images = {}
    for directory in (LEGACY / 'patches', LEGACY / 'stock-binaries', LEGACY / 'modules', LEGACY / 'archive/modules', ROOT / 'payloads'):
        for p in directory.rglob('*'):
            if p.is_file() and (p.suffix == '.so' or p.name == 'cameraserver'):
                images.setdefault(digest(p.read_bytes()), p)
    count = 0
    def check(m, source):
        nonlocal count
        if isinstance(m, dict):
            if {'input_sha256', 'output_sha256', 'changes'} <= m.keys():
                if m['input_sha256'] in images:
                    before = images[m['input_sha256']].read_bytes()
                else:
                    require(m['output_sha256'] in images, f'Missing both manifest images: {source}')
                    reverted = bytearray(images[m['output_sha256']].read_bytes())
                    for change in reversed(m['changes']):
                        offset = int(str(change['offset']), 0)
                        old, new = bytes.fromhex(change['old']), bytes.fromhex(change['new'])
                        require(reverted[offset:offset+len(new)] == new, f'Reverse delta mismatch: {source}')
                        reverted[offset:offset+len(old)] = old
                    before = bytes(reverted)
                    require(digest(before) == m['input_sha256'], f'Reversed input hash mismatch: {source}')
                after = bytearray(before)
                for change in m['changes']:
                    offset = int(str(change['offset']), 0)
                    old, new = bytes.fromhex(change['old']), bytes.fromhex(change['new'])
                    require(len(old) == len(new) and 0 <= offset <= len(before)-len(old), f'Invalid delta: {source}')
                    require(before[offset:offset+len(old)] == old, f'Original bytes mismatch: {source}')
                    after[offset:offset+len(new)] = new
                require(digest(after) == m['output_sha256'], f'Reconstruction mismatch: {source}')
                if m['output_sha256'] in images:
                    require(bytes(after) == images[m['output_sha256']].read_bytes(), f'Output bytes mismatch: {source}')
                count += 1
            else:
                for value in m.values():
                    check(value, source)
    for directory in (LEGACY / 'patches', LEGACY / 'modules'):
        for p in directory.rglob('*.json'):
            check(json.loads(p.read_text(encoding='utf-8')), p.relative_to(ROOT))
    return count

def verify_installers():
    shell = shutil.which('sh')
    if not shell and Path('C:/Program Files/Git/usr/bin/sh.exe').is_file():
        shell = 'C:/Program Files/Git/usr/bin/sh.exe'
    require(shell, 'POSIX sh required (Git Bash on Windows)')
    parent = ROOT / 'dist/verification'
    parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory(dir=parent, prefix='installers-') as tmp:
        temp = Path(tmp)
        for variant in ('raw', 'raw-flash'):
            files = module_files(variant)
            for sdk in (29, 30, 31, 33, 35, 36, 37, 99):
                rows.append(run_case(temp, shell, variant, files, f'api-{sdk}', sdk=sdk))
            for i, state in enumerate(accepted_states(variant)):
                rows.append(run_case(temp, shell, variant, files, f'state-{i}', state=state))
            for case in ('wrong-device', 'wrong-abi', 'unknown', 'mixed', 'corrupt', 'conflict', 'pending', 'direct-vendor', 'disabled', 'remove', 'bad-sdk', 'backup-failure', 'bad-ois'):
                rows.append(run_case(temp, shell, variant, files, case))
            # Determinism and executable metadata must hold independent of host OS.
            a, b = temp / f'{variant}-a.zip', temp / f'{variant}-b.zip'
            write_zip(a, files); write_zip(b, files)
            require(a.read_bytes() == b.read_bytes(), f'Non-deterministic ZIP: {variant}')
            with zipfile.ZipFile(a) as archive:
                for name in archive.namelist():
                    expected = 0o755 if name.endswith('.sh') or name.endswith('update-binary') or name == SERVER else 0o644
                    require((archive.getinfo(name).external_attr >> 16) & 0o777 == expected, f'ZIP mode: {name}')
                if variant == 'raw':
                    require(SERVER not in archive.namelist(), 'RAW must not replace framework')
                    require('flashcap' not in archive.read('service.sh').decode(), 'RAW must not run flash service')
    (parent / 'installers.json').write_text(json.dumps(rows, indent=2)+'\n', encoding='utf-8')
    return len(rows)

def run_case(temp, shell, variant, files, case, sdk=36, state=None):
    root = temp / variant / case
    mod, live, active, pending = (root / name for name in ('module', 'live', 'active', 'pending'))
    for p in (mod, live, active, pending):
        p.mkdir(parents=True)
    for rel, data in files.items():
        p = mod / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
    paths = json.loads(files['payload-sha256.json'])
    state = dict(state or accepted_states(variant)[0])
    if case == 'unknown':
        state[META] = '0' * 64
    if case == 'mixed':
        state[META] = accepted_states(variant)[-1][META]
        state[POLICY] = STOCK[POLICY]
    mocks = []
    for rel in paths:
        actual = '/' + rel.removeprefix('system/') if rel.startswith('system/vendor/') else '/' + rel
        p = live / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(f'previous:{rel}'.encode())
        mocks.append(f' {shell_quote(p)}) echo {state[rel]} ;;')
    ois = root / 'ois.so'; ois.write_bytes(b'previous-ois')
    mocks.append(f' {shell_quote(ois)}) echo ' + ('0'*64 if case == 'bad-ois' else 'b061c7e672e285e7933053874c6892360b7bb9585a4982a4ff64624c4cd650b7') + ' ;;')
    if case == 'corrupt':
        (mod / META).write_bytes(b'corrupt')
    if case in ('conflict', 'pending', 'direct-vendor', 'disabled', 'remove'):
        other = (pending if case == 'pending' else active) / 'other'
        p = other / (META.removeprefix('system/') if case == 'direct-vendor' else META)
        p.parent.mkdir(parents=True); p.write_bytes(b'conflict')
        if case in ('disabled', 'remove'):
            (other / ('disable' if case == 'disabled' else 'remove')).touch()
    script = files['customize.sh'].decode()
    script = script.replace('file_sha() { sha256sum "$1" 2>/dev/null | cut -d \' \' -f 1; }',
        'file_sha() { case "$1" in\n'+'\n'.join(mocks)+'\n *) sha256sum "$1" | cut -d \' \' -f 1 ;;\nesac; }')
    # Only literal live paths are redirected; module payload checks remain real SHA-256.
    for rel in paths:
        actual = '/' + rel.removeprefix('system/') if rel.startswith('system/vendor/') else '/' + rel
        script = script.replace('file_sha '+actual+')', 'file_sha '+shell_quote(live / rel)+')')
        script = script.replace('cp -p '+actual+' ', 'cp -p '+shell_quote(live / rel)+' ')
    script = script.replace('file_sha /vendor/lib64/libtran_oismgr.so)', 'file_sha '+shell_quote(ois)+')')
    script = script.replace('/data/adb/modules /data/adb/modules_update', shell_quote(active)+' '+shell_quote(pending))
    sdk_value = 'invalid' if case == 'bad-sdk' else str(sdk)
    stubs = f'''abort() {{ echo "$*"; exit 91; }}
ui_print() {{ :; }}
set_perm() {{ :; }}
set_perm_recursive() {{ :; }}
getprop() {{ case "$1" in
 ro.product.device) echo {'wrong' if case == 'wrong-device' else 'Infinix-X6810'} ;;
 ro.product.cpu.abilist) echo {'armeabi-v7a' if case == 'wrong-abi' else 'arm64-v8a,armeabi-v7a'} ;;
 ro.build.version.sdk) echo {sdk_value} ;;
esac; }}
'''
    if case == 'backup-failure':
        stubs += 'cp() { return 1; }\n'
    harness = root / 'run.sh'
    harness.write_text('PATH=/usr/bin:$PATH\nMODPATH='+shell_quote(mod)+'\n'+stubs+script, encoding='utf-8', newline='\n')
    subprocess.run([shell, '-n', str(harness)], check=True, capture_output=True)
    result = subprocess.run([shell, str(harness)], capture_output=True, text=True, timeout=20)
    accepted = (sdk >= 30 if variant == 'raw' else sdk == 36) and case not in {
        'wrong-device', 'wrong-abi', 'unknown', 'mixed', 'corrupt', 'conflict', 'pending', 'direct-vendor', 'bad-sdk', 'backup-failure'}
    if case == 'bad-ois':
        accepted = False
    require(result.returncode == (0 if accepted else 91), f'{variant}/{case}: {result.stdout} {result.stderr}')
    if accepted:
        for rel in paths:
            require((mod / 'backup' / Path(rel).name).read_bytes() == (live / rel).read_bytes(), f'Backup: {case}')
    return {'variant': variant, 'case': case, 'sdk': sdk_value, 'accepted': accepted}

def main():
    for p in (ROOT / 'scripts').glob('*.py'):
        ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
    manifests = verify_manifests()
    installers = verify_installers()
    print(f'PASS: {manifests} binary manifests reconstructed; {installers} isolated installer cases; deterministic ZIPs and permissions')
    print('Offline fixtures do not establish real-device/API compatibility.')

if __name__ == '__main__':
    main()
