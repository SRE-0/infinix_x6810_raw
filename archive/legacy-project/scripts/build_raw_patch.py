"""Reproducible X6810 S5KGM1ST RAW12 candidate. No device writes.

Append RAW and a 4000x3000 RAW16 stream, preserving every stock entry.
Only accepts the exact supplied stock library. Trampolines occupy verified
zero padding AFTER .plt; no log/error paths or PLT resolver are overwritten.
"""
from emulate_metadata import *
import argparse

STOCK_SHA='dbd740c5c7ba3081fb9d38b68b2f9975e19d6faad41dd5f87ce75f3c7d7be485'
SYMBOL='constructCustStaticMetadata_PLATFORM_PROJECT_SENSOR_DRVNAME_S5KGM1ST_MIPI_RAW'
RAW_STREAM=[32,4000,3000,0,50000000,33333333]

def word(v): return struct.pack('<I',v)
def branch(src,dst,link=False):
    d=dst-src
    if d%4 or not -(1<<27)<=d<(1<<27): raise ValueError('Branch out of range/alignment')
    return word((0x94000000 if link else 0x14000000)|((d//4)&0x3ffffff))
def mov32(reg,value):
    if not 0<=value<2**32: raise ValueError('Not uint32')
    out=word(0x52800000|((value&0xffff)<<5)|reg)
    if value>>16: out+=word(0x72a00000|((value>>16)<<5)|reg)
    return out
def trampoline(base,target,values,byte):
    # Save callee-saved x19 and hook LR, use 16-byte-aligned 32-byte frame.
    code=bytearray.fromhex('f37bbea9 f30300aa') # stp x19,x30,[sp,#-32]!; mov x19,x0
    code+=branch(base+len(code),target,True) # perform original push with original x0/x1
    for value in values:
        code+=mov32(8,value)
        code+=bytes.fromhex('e8430039' if byte else 'e80b00f9') # str[b] x8/[w8],sp+16
        code+=bytes.fromhex('e00313aa e1430091') # x0=entry, x1=sp+16
        code+=branch(base+len(code),target,True)
    code+=bytes.fromhex('f37bc2a8 c0035fd6') # restore x19/LR/SP; ret
    return bytes(code)

def build():
    source=ROOT/'stock-binaries/libmtkcam_metastore.so'
    a=parse_elf(source.read_bytes())
    if a.sha256!=STOCK_SHA: raise ValueError('Stock SHA-256 mismatch; refusing patch')
    if a.data[4:6]!=bytes([2,1]) or struct.unpack_from('<H',a.data,18)[0]!=183: raise ValueError('Need LE AArch64 ELF64')
    s=next(s for s in a.symbols if s.name==SYMBOL)
    before=emulate(a,s,True)
    if before['error']: raise ValueError(before['error'])
    cap=before['metadata']['0xc000c']; stream=before['metadata']['0xd0012']
    if 3 in cap['values']: raise ValueError('Already RAW')
    plt=plt_symbols(a)
    pushbyte=next(k for k,v in plt.items() if 'IEntry9push_backERKh' in v)
    pushlong=next(k for k,v in plt.items() if 'IEntry9push_backERKl' in v)
    rx=a.executable_load
    start=(rx.p_offset+rx.p_filesz+15)&~15
    # This known file maps RX virtual addresses identically to file offsets.
    if rx.p_vaddr!=rx.p_offset: raise ValueError('Unexpected VA/file mapping')
    capcode=trampoline(start,pushbyte,[3],True)
    streamstart=start+len(capcode)
    streamcode=trampoline(streamstart,pushlong,RAW_STREAM,False)
    cave=capcode+streamcode
    end=start+len(cave)
    if any(a.data[start:end]): raise ValueError('Cave is not zero-filled')
    for sec in a.sections.values():
        if sec.size and sec.offset<end and start<sec.offset+sec.size: raise ValueError('Cave overlaps '+sec.name)
    nextload=min(p.p_offset for p in a.load_segments if p.p_offset>rx.p_offset)
    if end>nextload: raise ValueError('Cave overlaps next LOAD')
    b=bytearray(a.data); changes=[]
    def change(off,new,reason):
        old=a.data[off:off+len(new)]
        if bytes(b[off:off+len(new)])!=old: raise ValueError('Overlapping patch')
        b[off:off+len(new)]=new
        changes.append(dict(offset=hex(off),old=old.hex(),new=new.hex(),reason=reason))
    for hook,dst,target in [(int(cap['sites'][-1],16),start,pushbyte),(int(stream['sites'][-1],16),streamstart,pushlong)]:
        if a.data[hook:hook+4]!=branch(hook,target,True): raise ValueError('Unexpected original BL')
        change(hook,branch(hook,dst,True),'Append RAW capability' if dst==start else 'Append RAW16 stream tuple')
    change(start,cave,'AAPCS64 trampolines in trailing zero padding')
    phoff=struct.unpack_from('<Q',a.data,0x20)[0]+rx.index*struct.unpack_from('<H',a.data,0x36)[0]
    for field in (32,40): change(phoff+field,struct.pack('<Q',end-rx.p_offset),'Extend executable PT_LOAD size')
    patched=parse_elf(bytes(b))
    after=emulate(patched,s,True)
    if after['error']: raise ValueError(after['error'])
    for tag,e in before['metadata'].items():
        expected=e['values']+([3] if tag=='0xc000c' else RAW_STREAM if tag=='0xd0012' else [])
        if after['metadata'][tag]['values']!=expected: raise ValueError('Metadata mismatch '+tag)
    # All other PROJECT constructors must produce identical metadata under ABI clobbering.
    checked=0
    for other in a.symbols:
        if not other.name.startswith('constructCustStaticMetadata_PLATFORM_PROJECT_') or other.name==SYMBOL: continue
        x,y=emulate(a,other,True),emulate(patched,other,True)
        if x!=y or x['error']: raise ValueError('Other constructor regression: '+other.name)
        checked+=1
    allowed=set()
    for c in changes:
        off=int(c['offset'],16); allowed.update(range(off,off+len(bytes.fromhex(c['new']))))
    actual={i for i,(x,y) in enumerate(zip(a.data,b)) if x!=y}
    if not actual<=allowed or len(b)!=len(a.data): raise ValueError('Unexpected file mutation')
    output=ROOT/'patches/libmtkcam_metastore.so'
    output.write_bytes(b)
    manifest=dict(profile='x6810-s5kgm1st-raw16-12mp-experimental',input_sha256=a.sha256,output_sha256=patched.sha256,size=len(b),changed_bytes=len(actual),target_symbol=SYMBOL,raw_stream=RAW_STREAM,changes=changes,capabilities_before=cap['values'],capabilities_after=after['metadata']['0xc000c']['values'],other_constructors_verified=checked,device_tested=False)
    (ROOT/'patches/patch-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'patched-trampolines.asm.txt').write_text('\n'.join(disasm(patched,start,len(cave)))+'\n')
    (OUT/'patched-constructor.json').write_text(json.dumps(after,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='changes'},indent=2))
    return manifest
if __name__=='__main__': build()
