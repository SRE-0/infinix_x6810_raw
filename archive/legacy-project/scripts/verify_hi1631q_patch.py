"""Independent byte/ELF verification, without importing the patch builder."""
from pathlib import Path
import hashlib, json, struct, zipfile

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'patches/front-v0.3'
m=json.loads((D/'patch-manifest.json').read_text())
a=(ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes()
b=(D/'libmtkcam_metastore.so').read_bytes()
assert hashlib.sha256(a).hexdigest()==m['input_sha256']
assert hashlib.sha256(b).hexdigest()==m['output_sha256']
assert len(a)==len(b)==m['size']
replay=bytearray(a); reverse=bytearray(b); touched=set()
for c in m['changes']:
    off=int(c['offset'],16);old=bytes.fromhex(c['old']);new=bytes.fromhex(c['new'])
    assert len(old)==len(new) and a[off:off+len(old)]==old and b[off:off+len(new)]==new
    indices=set(range(off,off+len(old)));assert not indices & touched;touched |= indices
    replay[off:off+len(old)]=new;reverse[off:off+len(new)]=old
assert replay==b and reverse==a
previous=(ROOT/'patches/aux-v0.2/libmtkcam_metastore.so').read_bytes()
expected_delta={i for off in (0x381ec,0x38624,0x4e26c,0x4e688) for i in range(off,off+4)}
assert {i for i,(x,y) in enumerate(zip(previous,b)) if x!=y} <= expected_delta
assert sum(x!=y for x,y in zip(a,b))==m['changed_bytes']
phoff=struct.unpack_from('<Q',b,32)[0];entsize,num=struct.unpack_from('<HH',b,54)
loads=[]
for j in range(num):
    typ,flags,off,va,pa,fs,ms,align=struct.unpack_from('<IIQQQQQQ',b,phoff+j*entsize)
    if typ!=1:continue
    assert fs<=ms and off+fs<=len(b) and flags!=7
    assert not align or off%align==va%align
    loads.append((off,off+fs,va,flags))
start,end=int(m['cave_start'],16),int(m['cave_end'],16)
assert not any(a[start:end]) and any(lo<=start<end<=hi and flags&1 for lo,hi,va,flags in loads)
baseline=(ROOT/'patches/aux-v0.2/libmtkcam_metastore.so').read_bytes()
assert hashlib.sha256(baseline).hexdigest()=='7a41b870658b2eeea8eb0a612219ca6e73de90b78b6b27a74d778d2804e43f5b'
for j,t in enumerate(m['targets']):
    for h in t['hooks']:
        off=int(h['offset'],16);word=struct.unpack_from('<I',b,off)[0]
        assert word>>26==0b100101
        imm=word&0x3ffffff;imm=imm-(1<<26) if imm&(1<<25) else imm
        dest=off+imm*4
        assert dest==int(h['destination'],16) and start<=dest<end
        if j<2:
            assert b[off:off+4]==baseline[off:off+4]
            assert b[dest:dest+h['trampoline_size']]==baseline[dest:dest+h['trampoline_size']]
for off in (0x2bcc8,0x54a64,0x7cfd0,0x7cfec,0x381ec,0x38624):assert a[off:off+4]==b[off:off+4]
archive=ROOT/'dist/x6810-raw16-v0.3.0-hi1631q-experimental.zip'
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert z.read('system/vendor/lib64/libmtkcam_metastore.so')==b
    assert len(z.namelist())==10
    for name in z.namelist():
        if not name.endswith('.so'):assert b'\r' not in z.read(name)
result=dict(passed=True,changed_bytes=m['changed_bytes'],hooks=6,main_patch_bytes_preserved=True,telephoto_patch_bytes_preserved=True,
            forward_and_reverse_replay=True,elf_load_bounds=True,zip_crc_and_payload=True,
            zip_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),hardware_test=False)
(ROOT/'dist/verification/front-v0.3-binary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
