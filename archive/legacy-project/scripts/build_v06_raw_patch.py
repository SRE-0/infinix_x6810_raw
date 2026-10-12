"""Build X6810 RAW v0.6: valid HI1631Q size plus front-only remosaic defaults.

The patch is always reconstructed from the exact stock ELF.  Rear-camera
trampolines are required to remain byte-identical to the owner-tested v0.2.
"""
from build_raw_patch import *

PREFIX = 'constructCustStaticMetadata_PLATFORM_PROJECT_SENSOR_DRVNAME_'
PROFILES = [
    ('S5KGM1ST_MIPI_RAW', [32, 4000, 3000, 0, 50000000, 33333333],
     'main; functional RAW reported by owner with v0.1'),
    ('OV08A10_MIPI_RAW', [32, 3264, 2448, 0, 33333333, 33333333],
     'telephoto; functional RAW reported by owner with v0.2'),
    ('HI1631Q_MIPI_RAW', [32, 4640, 3488, 0, 100000000, 33333333],
     'front; full sensor capture mode only; 2320x1744 is invalid for RAW16'),
]
DEST = ROOT/'patches/front-v0.6'
TEMPLATE_UPDATE = 0xb9804
REMOSAIC_ENABLE = 0x800b0006
PROCESS_RAW_ENABLE = 0x800b0019


def b_cond(src, dst, cond):
    delta = dst-src
    if delta % 4 or not -(1 << 20) <= delta < (1 << 20):
        raise ValueError('Conditional branch out of range/alignment')
    return word(0x54000000 | (((delta//4) & 0x7ffff) << 5) | cond)


def request_defaults_trampoline(base, ctor, push_int, update, destroy):
    """Set int32 vendor request tags only when this->openId is camera 1."""
    code = bytearray()
    code += bytes.fromhex('880a40b9')                 # ldr w8,[x20,#8]
    code += bytes.fromhex('1f050071')                 # cmp w8,#1
    branch_off = len(code)
    code += b'\0' * 4                                # b.ne skip
    code += bytes.fromhex('ff8301d1')                 # sub sp,sp,#0x60
    for tag in (REMOSAIC_ENABLE, PROCESS_RAW_ENABLE):
        code += bytes.fromhex('e0030091')             # mov x0,sp
        code += mov32(1, tag)
        code += branch(base+len(code), ctor, True)
        code += bytes.fromhex('28008052')             # mov w8,#1
        code += bytes.fromhex('e84300b9')             # str w8,[sp,#0x40]
        code += bytes.fromhex('e0030091 e1030191')    # x0=sp; x1=sp+0x40
        code += branch(base+len(code), push_int, True)
        code += bytes.fromhex('e00313aa')             # mov x0,x19 (metadata)
        code += mov32(1, tag)
        code += bytes.fromhex('e2030091')             # mov x2,sp
        code += branch(base+len(code), update, True)
        code += bytes.fromhex('e0030091')             # mov x0,sp
        code += branch(base+len(code), destroy, True)
    code += bytes.fromhex('ff830191')                 # add sp,sp,#0x60
    skip = base+len(code)
    code[branch_off:branch_off+4] = b_cond(base+branch_off, skip, 1)  # NE
    code += bytes.fromhex('00e4006f')                 # original movi v0.2d,#0
    code += branch(base+len(code), TEMPLATE_UPDATE+4, False)
    return bytes(code)


def build_front():
    a = parse_elf((ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes())
    if a.sha256 != STOCK_SHA: raise ValueError('Exact stock hash mismatch')
    if a.data[4:6] != bytes([2, 1]) or struct.unpack_from('<H', a.data, 18)[0] != 183:
        raise ValueError('Expected little-endian ELF64 AArch64')
    rx = a.executable_load
    if rx.p_vaddr != rx.p_offset: raise ValueError('Unexpected VA mapping')
    plt = plt_symbols(a)
    pb = next(k for k, v in plt.items() if 'IEntry9push_backERKh' in v)
    pl = next(k for k, v in plt.items() if 'IEntry9push_backERKl' in v)
    pi = next(k for k, v in plt.items() if 'IEntry9push_backERKi' in v)
    ctor = next(k for k, v in plt.items() if 'IEntryC1Ej' in v)
    update = next(k for k, v in plt.items() if 'IMetadata6updateEjRKNS0_6IEntryE' in v)
    destroy = next(k for k, v in plt.items() if 'IEntryD1Ev' in v)
    start = (rx.p_offset + rx.p_filesz + 15) & ~15
    code = bytearray(); b = bytearray(a.data); changes = []; targets = []

    def change(off, new, reason):
        old = a.data[off:off+len(new)]
        if len(old) != len(new): raise ValueError('Out of file')
        if any(off < int(c['offset'],16)+len(bytes.fromhex(c['new'])) and
               int(c['offset'],16) < off+len(new) for c in changes):
            raise ValueError('Overlapping changes')
        b[off:off+len(new)] = new
        changes.append(dict(offset=hex(off), old=old.hex(), new=new.hex(), reason=reason))

    for name, raw, status in PROFILES:
        s = next(s for s in a.symbols if s.name == PREFIX+name)
        before = emulate(a, s, True)
        if before['error']: raise ValueError(before['error'])
        caps = before['metadata']['0xc000c']; stream = before['metadata']['0xd0012']
        if 3 in caps['values'] or len(stream['values']) % 6: raise ValueError('Unexpected stock metadata')
        hooks = []
        for entry, values, target, byte in ((caps, [3], pb, True), (stream, raw, pl, False)):
            hook = int(entry['sites'][-1], 16); dst = start+len(code)
            if a.data[hook:hook+4] != branch(hook, target, True): raise ValueError('Original BL mismatch')
            chunk = trampoline(dst, target, values, byte)
            change(hook, branch(hook, dst, True), name+(': append RAW capability' if byte else ': append RAW16 tuple'))
            hooks.append(dict(offset=hex(hook), destination=hex(dst), helper=hex(target), trampoline_size=len(chunk)))
            code += chunk
        targets.append(dict(sensor=name, symbol=s.name, constructor=hex(s.value), raw_stream=raw,
                            status=status, capabilities_before=caps['values'], hooks=hooks))

    request_start = start+len(code)
    request_code = request_defaults_trampoline(request_start, ctor, pi, update, destroy)
    code += request_code
    if a.data[TEMPLATE_UPDATE:TEMPLATE_UPDATE+4] != bytes.fromhex('00e4006f'):
        raise ValueError('Unexpected TemplateRequest hook instruction')
    change(TEMPLATE_UPDATE, branch(TEMPLATE_UPDATE, request_start),
           'Hook default request metadata after sensor-specific merge')

    end = start+len(code)
    if any(a.data[start:end]): raise ValueError('Nonzero cave')
    for sec in a.sections.values():
        if sec.size and sec.offset < end and start < sec.offset+sec.size: raise ValueError('Section overlap: '+sec.name)
    if end > min(p.p_offset for p in a.load_segments if p.p_offset > rx.p_offset): raise ValueError('Next LOAD overlap')
    change(start, code, 'Static-metadata trampolines plus front request-tag trampoline')
    ph = struct.unpack_from('<Q', a.data, 32)[0]+rx.index*struct.unpack_from('<H', a.data, 54)[0]
    for field in (32, 40): change(ph+field, struct.pack('<Q', end-rx.p_offset), 'Extend executable PT_LOAD size')
    patched = parse_elf(bytes(b)); comparison = []; unchanged = 0
    selected = {t['symbol']: t for t in targets}
    for s in a.symbols:
        if not s.name.startswith('constructCustStaticMetadata_PLATFORM_PROJECT_'): continue
        x, y = emulate(a, s, True), emulate(patched, s, True)
        if x['error'] or y['error']: raise ValueError((s.name, x['error'], y['error']))
        if s.name in selected:
            t = selected[s.name]
            if x['metadata'].keys() != y['metadata'].keys(): raise ValueError('Tag set changed')
            for tag, entry in x['metadata'].items():
                suffix = [3] if tag == '0xc000c' else t['raw_stream'] if tag == '0xd0012' else []
                if y['metadata'][tag]['values'] != entry['values']+suffix: raise ValueError((s.name, tag))
            t['capabilities_after'] = y['metadata']['0xc000c']['values']
            comparison.append(dict(before=x, after=y))
        else:
            if x != y: raise ValueError('Unrelated constructor changed: '+s.name)
            unchanged += 1

    baseline = (ROOT/'patches/aux-v0.2/libmtkcam_metastore.so').read_bytes()
    if hashlib.sha256(baseline).hexdigest() != '7a41b870658b2eeea8eb0a612219ca6e73de90b78b6b27a74d778d2804e43f5b':
        raise ValueError('Confirmed baseline file changed')
    for h in targets[0]['hooks'] + targets[1]['hooks']:
        for off, size in ((int(h['offset'],16),4),(int(h['destination'],16),h['trampoline_size'])):
            if b[off:off+size] != baseline[off:off+size]: raise ValueError('Rear patch regression')
    actual = {i for i, (x,y) in enumerate(zip(a.data,b)) if x != y}
    allowed = {i for c in changes for i in range(int(c['offset'],16),int(c['offset'],16)+len(bytes.fromhex(c['new'])))}
    if len(b) != len(a.data) or not actual <= allowed: raise ValueError('Unexpected mutation')
    request = dict(hook=hex(TEMPLATE_UPDATE), trampoline=hex(request_start), size=len(request_code),
                   camera_open_id=1, tags={hex(REMOSAIC_ENABLE): 1, hex(PROCESS_RAW_ENABLE): 1},
                   rationale='Use existing MTK 4Cell remosaic/processed-RAW path for HI1631Q')
    manifest = dict(profile='x6810-main-tele-hi1631q-remosaic-v0.6', input_sha256=a.sha256,
                    output_sha256=patched.sha256, size=len(b), changed_bytes=len(actual),
                    cave_start=hex(start), cave_end=hex(end), targets=targets, request_defaults=request,
                    changes=changes, unchanged_project_constructors=unchanged,
                    main_patch_bytes_preserved=True, telephoto_patch_bytes_preserved=True,
                    device_tested=False,
                    validation='Static constructor emulation and binary checks; HI1631Q remosaic hardware test pending')
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST/'libmtkcam_metastore.so').write_bytes(b)
    (DEST/'patch-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (OUT/'front-v0.6-constructors.json').write_text(json.dumps(comparison,indent=2)+'\n')
    (OUT/'front-v0.6-trampolines.asm.txt').write_text('\n'.join(disasm(patched,start,len(code)))+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ('changes','targets')},indent=2))
    return manifest


if __name__ == '__main__': build_front()
