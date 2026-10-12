"""Paired experimental policy: accept the real front PREVIEW sensor mode for RAW.

Use only with v0.7 binned-only metastore. Never bypass ISP buffer validation.
"""
from build_raw_patch import ROOT, parse_elf, branch, word, mov32, disasm
from build_v06_raw_patch import b_cond
import json
import struct
import hashlib

STOCK='47924889f98b5e01c3220eb69235df8580d597172faa439cd71beb0f8f41d7bd'
DEST=ROOT/'patches/front-v0.7'
HOOK=0x488a4


def build(*, preserve_size_checks=False, destination=None):
    dest = destination or DEST
    a=parse_elf((ROOT/'stock-binaries/libmtkcam_pipelinepolicy.so').read_bytes())
    assert a.sha256==STOCK
    b=bytearray(a.data);rx=a.executable_load;start=(rx.p_offset+rx.p_filesz+15)&~15
    code=bytearray();jumps=[]
    def check(reg,value):
        code.extend(mov32(9,value));code.extend(word(0x6b09001f|reg<<5))
        jumps.append(len(code));code.extend(b'\0'*4)
    code.extend(bytes.fromhex('c80240b9'))  # ldr w8,[x22] current open id
    check(8,1)
    check(21,0)  # eMode PREVIEW candidate
    code.extend(bytes.fromhex('081c40b9'))  # candidate width [node+0x1c]
    check(8,2320)
    code.extend(bytes.fromhex('082040b9'))  # candidate height [node+0x20]
    check(8,1744)
    code.extend(branch(start+len(code),0x48988 if preserve_size_checks else 0x489ac))
    fallback=start+len(code)
    original=bytes.fromhex('a80358b8') # ldur w8,[x29,#-0x80]
    assert a.data[HOOK:HOOK+4]==original
    code.extend(original);code.extend(branch(start+len(code),HOOK+4))
    for off in jumps:code[off:off+4]=b_cond(start+off,fallback,1)
    end=start+len(code)
    assert not any(a.data[start:end])
    assert end<=min(p.p_offset for p in a.load_segments if p.p_offset>rx.p_offset)
    for sec in a.sections.values():assert not (sec.size and sec.offset<end and start<sec.offset+sec.size)
    changes=[]
    def change(off,new):
        changes.append(dict(offset=hex(off),old=a.data[off:off+len(new)].hex(),new=new.hex()))
        b[off:off+len(new)]=new
    change(HOOK,branch(HOOK,start));change(start,code)
    ph=struct.unpack_from('<Q',b,32)[0]+rx.index*struct.unpack_from('<H',b,54)[0]
    for f in (32,40):change(ph+f,struct.pack('<Q',end-rx.p_offset))
    m=dict(input_sha256=STOCK,output_sha256=hashlib.sha256(b).hexdigest(),
           size=len(b),hook=hex(HOOK),cave_start=hex(start),cave_end=hex(end),changes=changes,
           guard='openId=1 AND candidate=PREVIEW AND sensor size=2320x1744',
           paired_metastore='front-v0.7; only 2320x1744 front RAW',hardware_test=False,
           preserve_original_requested_size_checks=preserve_size_checks)
    dest.mkdir(exist_ok=True)
    (dest/'libmtkcam_pipelinepolicy.so').write_bytes(b)
    (dest/'policy-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    (dest/'sensor-policy-guard.asm.txt').write_text('\n'.join(disasm(parse_elf(bytes(b)),start,len(code)))+'\n')
    print('policy',m['output_sha256']);return m


if __name__=='__main__':build()
