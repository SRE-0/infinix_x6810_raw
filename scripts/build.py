"""Build the two pinned X6810 camera modules (Python 3.11+, no device access)."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / 'archive/legacy-project'
ID = 'x6810_raw12mp'
VERSION = '1.1.0'
VENDOR = 'system/vendor/lib64/'
META = VENDOR + 'libmtkcam_metastore.so'
POLICY = VENDOR + 'libmtkcam_pipelinepolicy.so'
HAL3A = VENDOR + 'libcam.hal3a.v3.so'
DEVICE = VENDOR + 'libmtkcam_device3_hal.so'
SERVER = 'system/bin/cameraserver'
STOCK = {
    META: 'dbd740c5c7ba3081fb9d38b68b2f9975e19d6faad41dd5f87ce75f3c7d7be485',
    POLICY: '47924889f98b5e01c3220eb69235df8580d597172faa439cd71beb0f8f41d7bd',
    HAL3A: '93ae38c9efcbfeffc0fe1e9a0c16c472a8b782f18b4a7fc01e32ca1e12ed2b0b',
    DEVICE: '0333ea749a9b15eb9ecf21215a2ebea11c5d3fbff247acd7ec93022256d544b1',
    SERVER: '0e61fed272068a7855e236f9fb23d3e07e46bc1ba5588f92398c1a789e457f0c',
}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def payload(flavor: str) -> dict[str, bytes]:
    directory = ROOT / 'payloads' / flavor
    expected = json.loads((directory / 'SHA256SUMS.json').read_text(encoding='utf-8'))
    required = {META, POLICY, HAL3A} if flavor == 'raw' else set(STOCK)
    if set(expected) != required:
        raise ValueError(f'Unexpected payload paths: {flavor}')
    files = {rel: (directory / Path(rel).name).read_bytes() for rel in expected}
    for rel, data in files.items():
        if digest(data) != expected[rel]:
            raise ValueError(f'Payload checksum mismatch: {flavor}/{rel}')
        if data[:5] != b'\x7fELF\x02' or data[5] != 1 or int.from_bytes(data[18:20], 'little') != 183:
            raise ValueError(f'Expected little-endian ELF64 AArch64: {rel}')
    return files

def live_path(rel: str) -> str:
    return '/' + rel.removeprefix('system/') if rel.startswith(VENDOR) else '/' + rel

def accepted_states(flavor: str) -> list[dict[str, str]]:
    raw = {p: digest(b) for p, b in payload('raw').items()}
    flash = {p: digest(b) for p, b in payload('raw-flash').items()}
    torch = json.loads((LEGACY / 'modules/v000_x6810_GL_raw_hd48_12mp_torch_changes/payload-sha256.json').read_text())
    raw12 = json.loads((LEGACY / 'archive/modules/x6810_raw_v012/payload-sha256.json').read_text())
    if flavor == 'raw':
        raw11 = json.loads((LEGACY / 'archive/modules/x6810_raw_v011/payload-sha256.json').read_text())
        return [{p: state[p] for p in raw} for state in (STOCK, {**STOCK, **raw11}, raw12, raw, torch, flash)]
    # Each row is a complete coherent tuple; mixed independent hashes are rejected.
    return [STOCK, {**STOCK, **raw12}, {**STOCK, **raw}, torch, flash]

def installer(flavor: str, hashes: dict[str, str]) -> str:
    text = '''#!/system/bin/sh
SKIPUNZIP=0
command -v sha256sum >/dev/null 2>&1 || abort "sha256sum required"
file_sha() { sha256sum "$1" 2>/dev/null | cut -d ' ' -f 1; }
DEVICE_OK=0
for prop in ro.product.device ro.product.vendor.device ro.product.system.device; do
 case "$(getprop "$prop")" in Infinix-X6810|Infinix-X6810-GL|X6810|X6810-GL) DEVICE_OK=1 ;; esac
done
[ "$DEVICE_OK" = 1 ] || abort "Infinix X6810-GL required"
case "$(getprop ro.product.cpu.abilist)" in *arm64-v8a*) ;; *) abort "ARM64 required" ;; esac
SDK=$(getprop ro.build.version.sdk)
case "$SDK" in ''|*[!0-9]*) abort "Invalid Android SDK" ;; esac
'''
    text += ('[ "$SDK" -ge 30 ] || abort "Android 11/API 30 or newer required"\n' if flavor == 'raw'
             else '[ "$SDK" = 36 ] || abort "This flash framework profile requires Android 16/API 36"\n')
    text += '[ "$(file_sha /vendor/lib64/libtran_oismgr.so)" = b061c7e672e285e7933053874c6892360b7bb9585a4982a4ff64624c4cd650b7 ] || abort "Unknown OIS manager dependency"\n'
    paths = list(hashes)
    for i, rel in enumerate(paths):
        text += f'S{i}=$(file_sha {live_path(rel)})\n'
    tuples = sorted({':'.join(state[p] for p in paths) for state in accepted_states(flavor)})
    text += 'case "' + ':'.join(f'$S{i}' for i in range(len(paths))) + '" in\n '
    text += '|'.join(tuples) + ') ;;\n *) abort "Unsupported camera binary set; do not bypass hashes" ;;\nesac\n'
    for rel, expected in hashes.items():
        text += f'[ "$(file_sha "$MODPATH/{rel}")" = {expected} ] || abort "Payload mismatch: {rel}"\n'
    text += '''# Reject active and pending overlays, including direct vendor layouts.
for base in /data/adb/modules /data/adb/modules_update; do
 for other in "$base"/*; do
  [ -d "$other" ] || continue
  [ "${other##*/}" = x6810_raw12mp ] && continue
  [ -e "$other/disable" ] && continue
  [ -e "$other/remove" ] && continue
  for rel in system/bin/cameraserver system/vendor/lib64/libmtkcam_metastore.so system/vendor/lib64/libmtkcam_pipelinepolicy.so system/vendor/lib64/libcam.hal3a.v3.so system/vendor/lib64/libmtkcam_device3_hal.so; do
   [ ! -f "$other/$rel" ] && [ ! -f "$other/${rel#system/}" ] || abort "Conflicting camera overlay: ${other##*/}"
  done
 done
done
mkdir -p "$MODPATH/backup" || abort "Cannot create backup"
'''
    for rel in paths:
        text += f'cp -p {live_path(rel)} "$MODPATH/backup/{Path(rel).name}" || abort "Backup failed"\n'
    text += '''set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/vendor" 0 0 0755 0644 u:object_r:vendor_file:s0
for script in post-fs-data.sh service.sh boot-completed.sh; do set_perm "$MODPATH/$script" 0 0 0755; done
'''
    if SERVER in hashes:
        text += 'set_perm "$MODPATH/system/bin/cameraserver" 0 2000 0755 u:object_r:cameraserver_exec:s0\n'
    text += f'ui_print "X6810 {flavor} {VERSION}: binary checks passed. Reboot required."\n'
    return text

def module_files(flavor: str) -> dict[str, bytes]:
    files = payload(flavor)
    hashes = {p: digest(b) for p, b in files.items()}
    description = ('RAW16, processed JPEG HD48 and telephoto OIS; vendor-only, Android 11+ with known binaries.'
                   if flavor == 'raw' else 'RAW/OIS/HD48 plus TORCH/SINGLE bridge; exact Android 16 GSI framework profile.')
    files['module.prop'] = (f'id={ID}\nname=X6810 {flavor}\nversion={VERSION}\nversionCode=10100\nauthor=SRE-0\ndescription={description}\n').encode()
    files['customize.sh'] = installer(flavor, hashes).encode()
    files['payload-sha256.json'] = (json.dumps(hashes, indent=2)+'\n').encode()
    files['compatibility.json'] = (json.dumps({'flavor': flavor, 'min_sdk': 30 if flavor == 'raw' else 36,
        'exact_sdk': None if flavor == 'raw' else 36,
        'public_feature_min_sdk': 30 if flavor == 'raw' else 35,
        'ois_validation': 'Owner confirms working telephoto OIS on Android 16 GSI; no new device test in this revision',
        'accepted_binary_sets': accepted_states(flavor),
        'hardware_validation': 'Historical Android 16 GSI only; new packaging not device-tested'}, indent=2)+'\n').encode()
    files['README.md'] = (f'# X6810 {flavor}\n\n{description}\n\n'
        'Install through APatch; same ID for both variants. Switch by updating and rebooting. '
        'Disable/remove the module and reboot to recover. Backups contain the previous visible overlay, not necessarily stock.\n\n'
        'Any compatible external GCam can be installed; the GCam system module is optional. '
        'The owner confirms working telephoto OIS and BSG V32 with the recommended V32 XML on Android 16 GSI. '
        'Processed HD48 JPEG does not mean native 48MP RAW.\n\n'
        'Docs: https://github.com/SRE-0/infinix_x6810_raw\n'
        'GCam: https://github.com/SRE-0/infinix_x6810_gcam_port\n').encode()
    files['system.prop'] = b'vendor.camera.tran.nums=3\n'
    for name in ('post-fs-data.sh', 'boot-completed.sh'):
        files[name] = (ROOT / 'module/common' / name).read_bytes()
    service = '#!/system/bin/sh\nMODDIR=${0%/*}\n'
    if flavor == 'raw-flash':
        service += f'''setprop vendor.debug.x6810.flashcap 0
if [ "$(sha256sum /system/bin/cameraserver | cut -d ' ' -f 1)" = {hashes[SERVER]} ]; then
 mount -o remount,bind,suid /system/bin/cameraserver
 [ "$(getprop init.svc.cameraserver)" = running ] || start cameraserver
fi
'''
    service += '''TRIES=0
while [ "$(getprop sys.boot_completed)" != 1 ] && [ "$TRIES" -lt 120 ]; do
 sleep 5
 TRIES=$((TRIES + 1))
done
[ "$(getprop sys.boot_completed)" = 1 ] && sh "$MODDIR/boot-completed.sh"
exit 0
'''
    files['service.sh'] = service.encode()
    for name in ('update-binary', 'updater-script'):
        rel = 'META-INF/com/google/android/' + name
        files[rel] = (ROOT / 'module/common' / name).read_bytes()
    return files

def write_zip(path: Path, files: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w') as archive:
        for rel, data in sorted(files.items()):
            info = zipfile.ZipInfo(rel, (2026, 10, 12, 0, 0, 0))
            info.create_system = 3
            executable = rel.endswith('.sh') or rel.endswith('update-binary') or rel == SERVER
            info.external_attr = (0o100755 if executable else 0o100644) << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f'Invalid archive: {path}')

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=('raw', 'raw-flash', 'all'), default='all')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/releases')
    args = parser.parse_args()
    variants = ('raw', 'raw-flash') if args.variant == 'all' else (args.variant,)
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for flavor in variants:
        path = args.output / f'x6810-{flavor}-{VERSION}.zip'
        write_zip(path, module_files(flavor))
        records.append({'file': path.name, 'sha256': digest(path.read_bytes()), 'variant': flavor})
    (args.output / 'SHA256SUMS.txt').write_text(''.join(f'{r["sha256"]}  {r["file"]}\n' for r in records), encoding='ascii', newline='\n')
    (args.output / 'releases.json').write_text(json.dumps(records, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(records, indent=2))

if __name__ == '__main__':
    main()
