"""Hash-locked capture-only duty cap over RAW/OIS v0.12; no device writes."""
import hashlib, json, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'dist/python-deps'),str(ROOT/'scripts')]
from build_raw_patch import parse_elf, branch, disasm
from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN
SOURCE=ROOT/'archive/modules/x6810_raw_v012/system/vendor/lib64/libcam.hal3a.v3.so'
DEST=ROOT/'patches/flash-capture'
EXPECTED='7aeeb34cb3ec38bddb695effb1a4f1c0ab8aa39b447e12781579025cdffc3d6e'
HOOK=0x229140
PROPERTY='vendor.debug.x6810.flashcap'

def build():
    e=parse_elf(SOURCE.read_bytes())
    if e.sha256 != EXPECTED: raise ValueError('Requires exact v0.12 HAL')
    rx=e.executable_load
    start=(rx.p_offset+rx.p_filesz+15)&~15
    assert rx.p_offset==rx.p_vaddr
    # FlashHalInfo is passed in x1/x2: duty, second duty, timeout, second timeout.
    # Override only a positive, already-bounded photographic flash on main sensor.
    # Never raise the OEM-selected duty, enable a light, or alter ON/OFF timing.
    asm=f'''
    ldr w8,[x0,#0x30]
    cmp w8,#1
    b.ne original
    sub w8,w2,#1
    cmp w8,#299
    b.hi original
    sub w8,w1,#9
    cmp w8,#20
    b.hi original
    stp x0,x1,[sp,#-48]!
    stp x2,x3,[sp,#16]
    str x30,[sp,#32]
    adr x0,property_name
    mov w1,wzr
    bl 0x2cebd0
    mov w8,w0
    ldp x0,x1,[sp]
    ldp x2,x3,[sp,#16]
    ldr x30,[sp,#32]
    add sp,sp,#48
    sub w9,w8,#9
    cmp w9,#20
    b.hi original
    cmp w8,w1
    b.hi original
    bfi x1,x8,#0,#32
    original:
    sub sp,sp,#0x70
    b {HOOK+4}
    property_name:
    .byte {','.join(str(c) for c in PROPERTY.encode()+bytes([0]))}
    '''
    code=bytes(Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN).asm(asm,addr=start)[0])
    end=start+len(code)
    assert not any(e.data[start:end])
    assert end<=min(p.p_offset for p in e.load_segments if p.p_offset>rx.p_offset)
    assert not any(s.size and s.offset<end and start<s.offset+s.size for s in e.sections.values())
    assert e.data[HOOK:HOOK+4]==bytes.fromhex('ffc301d1')
    b=bytearray(e.data); changes=[]
    def change(off,new):
        changes.append(dict(offset=hex(off),old=b[off:off+len(new)].hex(),new=new.hex()))
        b[off:off+len(new)]=new
    change(HOOK,branch(HOOK,start)); change(start,code)
    ph=struct.unpack_from('<Q',b,32)[0]+rx.index*struct.unpack_from('<H',b,54)[0]
    for off in (32,40): change(ph+off,struct.pack('<Q',end-rx.p_offset))
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/SOURCE.name).write_bytes(b)
    manifest=dict(input_sha256=e.sha256,output_sha256=hashlib.sha256(b).hexdigest(),
                  hook=hex(HOOK),cave_start=hex(start),cave_end=hex(end),
                  property=PROPERTY,changes=changes,hardware_validated=False,
                  scope='Main sensor, OEM photographic duty 9..29, timeout 1..300 ms; downward cap only; no official API advertisement')
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (DEST/'capture.asm.txt').write_text(asm+'\n'+'\n'.join(disasm(parse_elf(bytes(b)),start,len(code))))
    print(json.dumps({k:v for k,v in manifest.items() if k!='changes'},indent=2))
    return bytes(b),manifest
if __name__=='__main__':build()
