"""Append 12MP processed streams and the Transsion 48MP JPEG size to v0.12.2."""
from build_raw_patch import ROOT, OUT, parse_elf, emulate, plt_symbols, branch, trampoline, disasm
import json
import struct

BASE_SHA = 'a7f9b751cb73f4bc567f8db89b53b8e3a143d64ed605764e34a3abd719007b35'
SYMBOL = 'constructCustStaticMetadata_PLATFORM_PROJECT_SENSOR_DRVNAME_S5KGM1ST_MIPI_RAW'
DEST = ROOT / 'patches/v0122_x6810_raw_hd48_12mp'
ADDED = [
    33, 4000, 3000, 0, 50000000, 33333333,  # JPEG 12MP
    35, 4000, 3000, 0, 50000000, 0,         # YUV 12MP
    33, 8000, 6000, 0, 100000000, 100000000, # JPEG HD, provisional timing
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build():
    source = ROOT / 'archive/modules/x6810_raw_v012_native_torch/system/vendor/lib64/libmtkcam_metastore.so'
    image = parse_elf(source.read_bytes())
    require(image.sha256 == BASE_SHA, 'Expected the exact v0.12.2 metastore')
    symbol = next(s for s in image.symbols if s.name == SYMBOL)
    before = emulate(image, symbol, True)
    require(not before['error'], str(before['error']))
    stream = before['metadata']['0xd0012']
    tuples = [stream['values'][i:i+6] for i in range(0, len(stream['values']), 6)]
    require(not any(t[:3] in ([33, 4000, 3000], [35, 4000, 3000], [33, 8000, 6000]) for t in tuples),
            'Resolution tuple already exists')
    hook = int(stream['sites'][-1], 16)
    helper = next(k for k, v in plt_symbols(image).items() if 'IEntry9push_backERKl' in v)
    require(image.data[hook:hook+4] == branch(hook, helper, True), 'Unexpected original call')
    rx = image.executable_load
    require(rx.p_vaddr == rx.p_offset, 'Unexpected RX mapping')
    start = (rx.p_offset + rx.p_filesz + 15) & ~15
    code = trampoline(start, helper, ADDED, False)
    end = start + len(code)
    require(not any(image.data[start:end]), 'Code cave is not empty')
    require(end <= min(p.p_offset for p in image.load_segments if p.p_offset > rx.p_offset), 'Cave overlaps next segment')
    for section in image.sections.values():
        require(not (section.size and section.offset < end and start < section.offset + section.size),
                'Cave overlaps section ' + section.name)
    patched = bytearray(image.data)
    changes = []

    def change(offset, data):
        changes.append(dict(offset=hex(offset), old=image.data[offset:offset+len(data)].hex(), new=data.hex()))
        patched[offset:offset+len(data)] = data

    change(hook, branch(hook, start, True))
    change(start, code)
    ph = struct.unpack_from('<Q', patched, 32)[0] + rx.index * struct.unpack_from('<H', patched, 54)[0]
    for field in (32, 40):
        change(ph + field, struct.pack('<Q', end - rx.p_offset))
    result = parse_elf(bytes(patched))
    checked = 0
    for other in image.symbols:
        if not other.name.startswith('constructCustStaticMetadata_PLATFORM_PROJECT_'):
            continue
        old, new = emulate(image, other, True), emulate(result, other, True)
        require(not old['error'] and not new['error'], 'Emulation error: ' + other.name)
        if other.name == SYMBOL:
            require(old['metadata'].keys() == new['metadata'].keys(), 'Unexpected metadata tags')
            for tag, entry in old['metadata'].items():
                require(new['metadata'][tag]['values'] == entry['values'] + (ADDED if tag == '0xd0012' else []),
                        'Unexpected metadata change: ' + tag)
        else:
            require(old == new, 'Other sensor constructor changed: ' + other.name)
        checked += 1
    restored = bytearray(patched)
    for item in reversed(changes):
        offset = int(item['offset'], 16)
        old, new = bytes.fromhex(item['old']), bytes.fromhex(item['new'])
        require(restored[offset:offset+len(new)] == new, 'Overlapping manifest edits')
        restored[offset:offset+len(old)] = old
    require(restored == image.data and len(patched) == len(image.data), 'Patch does not reverse exactly')
    manifest = dict(
        input_sha256=image.sha256, output_sha256=result.sha256,
        scope='v0.12.2 S5KGM1ST: JPEG/YUV 4000x3000 plus JPEG 8000x6000',
        hardware_validated=True, constructors_verified=checked,
        native_48mp_verified=False,
        observed_device_result='Direct JPEG 8000x6000 was produced from 4000x3000 sensor/IMGO; Transsion 48M combined eight 4000x3000 frames.',
        timing_note='12MP stock convention; 48MP JPEG 100ms provisional and not throughput-calibrated',
        hook=hex(hook), cave_start=hex(start), cave_end=hex(end),
        added_tuples=[ADDED[i:i+6] for i in range(0, len(ADDED), 6)], changes=changes)
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / 'libmtkcam_metastore.so').write_bytes(patched)
    (DEST / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (DEST / 'trampoline.asm.txt').write_text('\n'.join(disasm(result, start, len(code))) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'changes'}, indent=2))
    return manifest


if __name__ == '__main__':
    build()
