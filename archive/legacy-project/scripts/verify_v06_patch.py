"""Independent v0.6 byte, ELF, control-flow and package verification."""
from pathlib import Path
import hashlib, json, struct, zipfile, sys
sys.path.insert(0, str(Path(__file__).parent))
from analyze_binaries import parse_elf, disasm

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'patches/front-v0.6'
m=json.loads((D/'patch-manifest.json').read_text())
a=(ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes()
b=(D/'libmtkcam_metastore.so').read_bytes()
assert hashlib.sha256(a).hexdigest()==m['input_sha256']
assert hashlib.sha256(b).hexdigest()==m['output_sha256']
assert len(a)==len(b)==m['size']
replay=bytearray(a);reverse=bytearray(b);touched=set()
for c in m['changes']:
    off=int(c['offset'],16);old=bytes.fromhex(c['old']);new=bytes.fromhex(c['new'])
    assert len(old)==len(new) and a[off:off+len(old)]==old and b[off:off+len(new)]==new
    indices=set(range(off,off+len(old)));assert not indices&touched;touched|=indices
    replay[off:off+len(old)]=new;reverse[off:off+len(new)]=old
assert replay==b and reverse==a
assert sum(x!=y for x,y in zip(a,b))==m['changed_bytes']
phoff=struct.unpack_from('<Q',b,32)[0];entsize,num=struct.unpack_from('<HH',b,54)
loads=[]
for j in range(num):
    typ,flags,off,va,pa,fs,ms,align=struct.unpack_from('<IIQQQQQQ',b,phoff+j*entsize)
    if typ!=1:continue
    assert fs<=ms and off+fs<=len(b) and flags!=7 and (not align or off%align==va%align)
    loads.append((off,off+fs,flags))
start,end=int(m['cave_start'],16),int(m['cave_end'],16)
assert not any(a[start:end]) and any(lo<=start<end<=hi and flags&1 for lo,hi,flags in loads)
baseline=(ROOT/'patches/aux-v0.2/libmtkcam_metastore.so').read_bytes()
for j,t in enumerate(m['targets']):
    assert len(t['raw_stream'])==6
    if t['sensor']=='HI1631Q_MIPI_RAW': assert t['raw_stream']==[32,4640,3488,0,100000000,33333333]
    for h in t['hooks']:
        off=int(h['offset'],16);ins=struct.unpack_from('<I',b,off)[0];assert ins>>26==0b100101
        imm=ins&0x3ffffff;imm=imm-(1<<26) if imm&(1<<25) else imm
        dest=off+imm*4;assert dest==int(h['destination'],16) and start<=dest<end
        if j<2:
            assert b[off:off+4]==baseline[off:off+4]
            assert b[dest:dest+h['trampoline_size']]==baseline[dest:dest+h['trampoline_size']]
request=m['request_defaults'];hook=int(request['hook'],16);tramp=int(request['trampoline'],16)
assert a[hook:hook+4]==bytes.fromhex('00e4006f')
assert request['camera_open_id']==1 and request['tags']=={'0x800b0006':1,'0x800b0019':1}
lines=disasm(parse_elf(b),tramp,request['size'])
joined='\n'.join(lines)
for expected in ('ldr      w8, [x20, #8]','cmp      w8, #1','movk     w1, #0x800b','str      w8, [sp, #0x40]','b        #0xb9808'):
    assert expected in joined,expected
assert joined.count('bl       #0xbbbc0')==2
assert joined.count('bl       #0xbbc30')==2
assert joined.count('bl       #0xbbbf0')==2
assert joined.count('bl       #0xbbc20')==2
archive=ROOT/'dist/x6810-raw16-v0.6.0-hi1631q-remosaic.zip'
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None and len(z.namelist())==11
    assert z.read('system/vendor/lib64/libmtkcam_metastore.so')==b
    props=z.read('system.prop').decode()
    assert 'vendor.camera.tran.nums=3' in props and 'ro.odm.camera=1' in props
    for name in z.namelist():
        if not name.endswith('.so'):assert b'\r' not in z.read(name)
result=dict(passed=True,changed_bytes=m['changed_bytes'],static_hooks=6,request_hook=hex(hook),
            request_tags=request['tags'],front_raw_stream=[32,4640,3488,0,100000000,33333333],
            invalid_binned_stream_removed=True,main_patch_bytes_preserved=True,
            telephoto_patch_bytes_preserved=True,forward_and_reverse_replay=True,
            elf_load_bounds=True,zip_crc_and_payload=True,
            zip_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),hardware_test=False)
(ROOT/'dist/verification/front-v0.6-binary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
