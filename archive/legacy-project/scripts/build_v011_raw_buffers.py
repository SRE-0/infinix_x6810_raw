"""Raise the normal RAW16 output collection buffer floor, preserving larger limits.

Reproducible exact-firmware patch on the v0.10 policy, including its front fix.
No metadata, image sizes, sensor mode or processing algorithm changes.
"""
from build_raw_patch import ROOT, parse_elf, branch, word, mov32, disasm
import hashlib
import json
import struct

SOURCE_SHA = '40360af0dc17d589cdf36b5388b642200093511815e00d702f5d02e612333c47'
HOOK = 0x5a0b8
DEST = ROOT / 'patches/v0.11-raw-buffers'


def build():
    a = parse_elf((ROOT / 'patches/front-v0.10-full-binned/libmtkcam_pipelinepolicy.so').read_bytes())
    assert a.sha256 == SOURCE_SHA
    off = a.va_to_offset(HOOK)
    assert a.data[off:off+4] == bytes.fromhex('e10313aa')  # mov x1,x19
    rx = a.executable_load
    start = (rx.p_offset + rx.p_filesz + 15) & ~15
    # x19 is the existing capture policy count (2 in the measured BSG session).
    # Only x1 and NZCV are changed; no later conditional consumes these flags
    # before the original virtual setter call, which may itself clobber NZCV.
    code = mov32(1, 6)
    code += word(0xf100001f | (6 << 10) | (19 << 5))  # cmp x19,#6
    code += word(0x9a800000 | (1 << 16) | (2 << 12) | (19 << 5) | 1)  # csel x1,x19,x1,hs
    code += branch(start + len(code), HOOK + 4)
    end = start + len(code)
    assert a.offset_to_va(off) == off and a.offset_to_va(rx.p_offset) == rx.p_offset
    assert not any(a.data[start:end])
    assert end <= min(p.p_offset for p in a.load_segments if p.p_offset > rx.p_offset)
    for s in a.sections.values():
        assert not (s.size and s.offset < end and start < s.offset + s.size)
    b = bytearray(a.data)
    changes = []
    def change(offset, new):
        changes.append(dict(offset=hex(offset), old=a.data[offset:offset+len(new)].hex(), new=new.hex()))
        b[offset:offset+len(new)] = new
    change(off, branch(HOOK, start))
    change(start, code)
    ph = struct.unpack_from('<Q', b, 32)[0] + rx.index * struct.unpack_from('<H', b, 54)[0]
    for field in (32, 40):
        change(ph + field, struct.pack('<Q', end - rx.p_offset))
    manifest = dict(input_sha256=SOURCE_SHA, output_sha256=hashlib.sha256(b).hexdigest(),
                    hook=hex(HOOK), cave_start=hex(start), cave_end=hex(end),
                    behavior='RAW16 output collection: max(original capture-policy count, 6)',
                    scope='Default policy, collection root ParsedAppImageStreamInfo+0x50; all camera IDs',
                    changes=changes, size=len(b))
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / 'libmtkcam_pipelinepolicy.so').write_bytes(b)
    (DEST / 'raw-buffers-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (DEST / 'raw-buffers.asm.txt').write_text('\n'.join(disasm(parse_elf(bytes(b)), start, len(code)))+'\n')
    print(json.dumps(manifest, indent=2))
    return manifest


if __name__ == '__main__':
    build()
