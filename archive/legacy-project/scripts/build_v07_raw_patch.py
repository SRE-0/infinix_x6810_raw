"""Experimental HI1631Q binned-only RAW with guarded size normalization.

Does not enable remosaic request defaults. Must be validated on hardware.
"""
import build_v04_raw_patch as base
from build_raw_patch import ROOT, parse_elf, branch, word, mov32, disasm
from build_v06_raw_patch import b_cond
import hashlib
import json
import struct

DEST = ROOT/'patches/front-v0.7'
HOOK = 0x7d3b8


def guard(start):
    code = bytearray(bytes.fromhex('f503002a'))  # original mov w21,w0 (old height)
    mismatches = []
    def check(reg, value):
        code.extend(mov32(8, value))
        code.extend(word(0x6b08001f | reg << 5))  # cmp wREG,w8
        mismatches.append(len(code)); code.extend(b'\0'*4)
    check(20, 2320)
    check(21, 1744)
    code.extend(bytes.fromhex('e91f40b9'))  # ldr w9,[sp,#0x1c] active width
    check(9, 4640)
    code.extend(bytes.fromhex('e91b40b9'))  # ldr w9,[sp,#0x18] active height
    check(9, 3488)
    # Only this exact binned tuple/active-size pair bypasses replacement.
    code.extend(branch(start+len(code), 0x7d4bc))
    fallback = start+len(code)
    code.extend(branch(fallback, HOOK+4))
    for off in mismatches: code[off:off+4] = b_cond(start+off, fallback, 1)
    return bytes(code)


def build():
    # Reuse the previously emulated static constructor builder in an isolated
    # output directory. Historic files and the original ELF remain untouched.
    saved = base.PROFILES, base.DEST, base.OUT
    try:
        base.PROFILES = saved[0][:2]+[('HI1631Q_MIPI_RAW',
            [32,2320,1744,0,33333333,33333333], 'Experimental binned-only; hardware validation pending')]
        base.DEST = DEST
        base.OUT = ROOT/'dist/analysis/v07'; base.OUT.mkdir(exist_ok=True)
        base.build_front()
    finally:
        base.PROFILES, base.DEST, base.OUT = saved
    m = json.loads((DEST/'patch-manifest.json').read_text())
    stock = (ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes()
    data = bytearray((DEST/'libmtkcam_metastore.so').read_bytes())
    assert stock[HOOK:HOOK+4] == bytes.fromhex('f503002a')
    start = int(m['cave_end'],16)
    code = guard(start); end = start+len(code)
    assert not any(stock[start:end])
    a = parse_elf(stock)
    assert end <= min(p.p_offset for p in a.load_segments if p.p_offset>a.executable_load.p_offset)
    for sec in a.sections.values():
        assert not (sec.size and sec.offset<end and start<sec.offset+sec.size)
    data[HOOK:HOOK+4] = branch(HOOK,start)
    data[start:end] = code
    m['changes'].append(dict(offset=hex(HOOK),old=stock[HOOK:HOOK+4].hex(),
        new=data[HOOK:HOOK+4].hex(),reason='Guard binned HI1631Q RAW-size normalization'))
    # Extend existing cave and LOAD records rather than overlapping manifests.
    for c in m['changes']:
        off = int(c['offset'],16)
        if off == int(m['cave_start'],16):
            c['old'] = stock[off:end].hex(); c['new'] = data[off:end].hex()
        elif off in (0xd0,0xd8):
            data[off:off+8] = struct.pack('<Q',end-a.executable_load.p_offset)
            c['new'] = data[off:off+8].hex()
    m.update(profile='x6810-hi1631q-binned-normalization-v0.7-experimental',
        output_sha256=hashlib.sha256(data).hexdigest(),cave_end=hex(end),
        changed_bytes=sum(x!=y for x,y in zip(stock,data)),device_tested=False,
        normalization_guard=dict(hook=hex(HOOK),trampoline=hex(start),
            match_raw_size=[2320,1744],match_active_size=[4640,3488],
            scope='Dimension guard; this tuple is introduced only for HI1631Q by this build'),
        validation='Static constructors plus normalization block emulation; sensor mode, CFA, color and GCam pending')
    assert data[0xb9804:0xb9808] == stock[0xb9804:0xb9808]  # no v0.6 request hook
    (DEST/'libmtkcam_metastore.so').write_bytes(data)
    (DEST/'patch-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    (ROOT/'dist/analysis/v07/normalization-guard.asm.txt').write_text('\n'.join(disasm(parse_elf(bytes(data)),start,len(code)))+'\n')
    print('v0.7 EXPERIMENTAL',m['output_sha256'])
    return m


if __name__ == '__main__': build()
