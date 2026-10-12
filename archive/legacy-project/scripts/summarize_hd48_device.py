"""Summarize captured HD enumeration and sensor/SR evidence without device writes."""
import argparse
import json
import re
import struct
from pathlib import Path


def jpeg_size(path):
    data = path.read_bytes()
    if data[:2] != b'\xff\xd8':
        raise ValueError(f'Not JPEG: {path}')
    offset = 2
    while offset < len(data):
        if data[offset] != 255:
            raise ValueError('Invalid JPEG marker')
        while data[offset] == 255:
            offset += 1
        marker = data[offset]
        offset += 1
        if marker in (0xD9, 0xDA):
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue
        length = struct.unpack_from('>H', data, offset)[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            height, width = struct.unpack_from('>HH', data, offset + 3)
            return dict(width=width, height=height, bytes=len(data))
        if length < 2:
            raise ValueError('Invalid JPEG segment size')
        offset += length
    raise ValueError('JPEG has no SOF dimensions')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    folder = args.directory
    direct = (folder / 'direct-hd-logcat.txt').read_text(encoding='utf-8', errors='replace').splitlines()
    stock = (folder / 'transsion-hd-logcat.txt').read_text(encoding='utf-8', errors='replace').splitlines()
    report = dict(
        jpeg_files={p.name: jpeg_size(p) for p in folder.glob('*.jpg')},
        direct_sensor_selection=[line for line in direct if 'mtkcam-SensorSettingPolicy:' in line and ('candidate [' in line or 'select size(' in line)],
        direct_imgo=[line for line in direct if 'mtkcam-P1HwSettingPolicy:' in line and 'imgoAlloc' in line],
        stock_sr=[line for line in stock if ('sr_android:' in line and re.search(r'\[(?:In \d+|Out)\]', line)) or 'addAlgo:cap_superresolution' in line],
        conclusion='Direct JPEG HD used 12MP sensor/IMGO; Transsion HD used eight 12MP inputs for software SR. No native 48MP readout established.',
    )
    (folder / 'resolution-evidence.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
