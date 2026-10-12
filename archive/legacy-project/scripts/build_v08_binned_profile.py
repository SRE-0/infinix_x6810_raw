"""Experimental front binned profile: filter oversize streams and durations together.

At 0x7eacc, x21 is MetadataProvider (openId at +0x10, constructor
0x8174c), x7 is candidate width, x10 points to the candidate record.
No image copying, DMA bounds or active-array metadata are modified.
"""
from build_raw_patch import *
from build_v06_raw_patch import b_cond
from build_v07_sensor_policy import build as build_policy

DEST=ROOT/'patches/front-v0.8-binned'
HOOK=0x7eacc

def main():
    a=parse_elf((ROOT/'patches/front-v0.7/libmtkcam_metastore.so').read_bytes())
    assert a.sha256=='2b3bca8dfa83ea01c3f210b1b187c173a453665f3373afe9e8d17614b0fe95df'
    assert a.data[HOOK:HOOK+4]==bytes.fromhex('48100034')
    b=bytearray(a.data);rx=a.executable_load;start=(rx.p_offset+rx.p_filesz+15)&~15
    code=bytearray();fallback_checks=[]
    code+=word(0xb94012ab)  # ldr w11,[x21,#0x10]
    code+=word(0x7100057f)  # cmp w11,#1
    fallback_checks.append(len(code));code+=bytes(4)
    # Pixel-array bounds from the original routine, extra sensor-specific guard.
    code+=mov32(9,4640)+word(0xeb09039f)  # cmp x28,x9
    fallback_checks.append(len(code));code+=bytes(4)
    code+=word(0xf94023eb)+mov32(9,3488)+word(0xeb09017f)
    fallback_checks.append(len(code));code+=bytes(4)
    code+=mov32(9,2320)+word(0xeb0900ff) # cmp x7,x9
    code+=b_cond(start+len(code),0x7ecec,12) # gt skip entire tuple and its durations
    code+=word(0xf940094b)+mov32(9,1744)+word(0xeb09017f)
    code+=b_cond(start+len(code),0x7ecec,12)
    fallback=start+len(code)
    # Relocate original cbz w8,0x7ecd4; preserve original flag-dependent path.
    delta=(0x7ecd4-fallback)//4
    code+=word(0x34000008|((delta&0x7ffff)<<5))
    code+=branch(start+len(code),HOOK+4)
    for off in fallback_checks:code[off:off+4]=b_cond(start+off,fallback,1)
    end=start+len(code)
    assert not any(a.data[start:end])
    assert end<=min(p.p_offset for p in a.load_segments if p.p_offset>rx.p_offset)
    for sec in a.sections.values():assert not(sec.size and sec.offset<end and start<sec.offset+sec.size)
    changes=[]
    def change(off,new):
        changes.append(dict(offset=hex(off),old=a.data[off:off+len(new)].hex(),new=new.hex()))
        b[off:off+len(new)]=new
    change(HOOK,branch(HOOK,start));change(start,code)
    ph=struct.unpack_from('<Q',b,32)[0]+rx.index*struct.unpack_from('<H',b,54)[0]
    for field in (32,40):change(ph+field,struct.pack('<Q',end-rx.p_offset))
    DEST.mkdir(exist_ok=True)
    (DEST/'libmtkcam_metastore.so').write_bytes(b)
    (DEST/'metastore-manifest.json').write_text(json.dumps(dict(input_sha256=a.sha256,
        output_sha256=hashlib.sha256(b).hexdigest(),changes=changes,hook=hex(HOOK),
        cave_start=hex(start),cave_end=hex(end),hardware_test=False,
        scope='openId=1 AND pixelArray=4640x3488; omit candidates width>2320 OR height>1744',
        limitation='Front high-resolution processed outputs unavailable while enabled'),indent=2))
    (DEST/'stream-filter.asm.txt').write_text('\n'.join(disasm(parse_elf(bytes(b)),start,len(code))))
    build_policy(preserve_size_checks=True,destination=DEST)
    print('metastore',hashlib.sha256(b).hexdigest())

if __name__=='__main__':main()
