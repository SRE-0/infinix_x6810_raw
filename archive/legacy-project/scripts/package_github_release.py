"""Build complete GitHub release assets from the versioned project sources."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW_MODULES = {
    'v000': 'v000_x6810_GL_raw_hd48_12mp_torch_changes',
    'v001': 'v001_x6810_GL_raw_hd48_12mp_torch_single_flash_apis_changes',
}
GCAM_DIR = ROOT / 'gcam/apatch-startup'
GCAM_NATIVE = GCAM_DIR / 'payload/libgcastartup-cache.so'
GCAM_XML = ROOT / 'profiles/x6810-gcam-bsg-v18-recommended.xml'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def package_raw_module(version, output):
    source = ROOT / 'modules' / RAW_MODULES[version]
    if not source.is_dir():
        raise FileNotFoundError(f'Complete RAW module not found: {source}')
    properties = (source / 'module.prop').read_text(encoding='utf-8')
    if 'id=x6810_raw12mp' not in properties.splitlines():
        raise ValueError(f'Unexpected module ID in {source / "module.prop"}')
    files = sorted(path for path in source.rglob('*') if path.is_file())
    if not files or not (source / 'customize.sh').is_file():
        raise ValueError(f'Incomplete APatch module tree: {source}')

    with zipfile.ZipFile(output, 'w') as archive:
        for path in files:
            if path.is_symlink():
                raise ValueError(f'Symlinks are not supported in module ZIPs: {path}')
            name = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2024, 1, 1, 0, 0, 0))
            info.create_system = 3
            executable = path.suffix == '.sh' or path.name == 'update-binary'
            info.external_attr = (0o100755 if executable else 0o100644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError(f'Invalid module archive: {output}')
        if set(archive.namelist()) != {p.relative_to(source).as_posix() for p in files}:
            raise ValueError(f'Incomplete module archive: {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-version', choices=RAW_MODULES, default='v001')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--gcam-apk', type=Path,
                        default=Path.home() / 'Downloads' / 'MGC_9.7.047_V32_MGC.apk',
                        help='original, signed BSG APK with the builder-verified SHA-256')
    args = parser.parse_args()

    for path in (args.gcam_apk, GCAM_NATIVE, GCAM_XML):
        if not path.is_file():
            raise FileNotFoundError(f'Required release source is missing: {path}')
    xml = ET.parse(GCAM_XML).getroot()
    if xml.tag != 'map' or len(xml) != 16 or any(entry.tag != 'string' for entry in xml):
        raise ValueError(f'Unexpected GCam XML overlay structure: {GCAM_XML}')

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    raw_zip = output_dir / f'x6810-raw-{args.raw_version}.zip'
    gcam_properties = dict(
        line.split('=', 1) for line in (GCAM_DIR / 'module.prop').read_text(encoding='utf-8').splitlines()
        if '=' in line and not line.startswith('#')
    )
    gcam_zip = output_dir / f"x6810-gcam-system-{gcam_properties['version']}.zip"
    xml_output = output_dir / 'x6810-gcam-bsg-v18-recommended.xml'

    package_raw_module(args.raw_version, raw_zip)
    subprocess.run([
        sys.executable, str(GCAM_DIR / 'build.py'), str(args.gcam_apk), str(gcam_zip),
        '--native', str(GCAM_NATIVE),
    ], check=True)
    shutil.copyfile(GCAM_XML, xml_output)

    assets = sorted((raw_zip, gcam_zip, xml_output), key=lambda path: path.name)
    sums = ''.join(f'{sha256(path)}  {path.name}\n' for path in assets)
    (output_dir / 'SHA256SUMS.txt').write_text(sums, encoding='ascii', newline='\n')
    for path in assets:
        print(f'{path.name}: {path.stat().st_size} bytes; sha256 {sha256(path)}')
    print(f'SHA256SUMS.txt: {output_dir / "SHA256SUMS.txt"}')


if __name__ == '__main__':
    main()
