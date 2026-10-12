"""Independent byte/ELF/branch verification, no disassembler dependency."""
from pathlib import Path
import hashlib,json,struct
ROOT=Path(__file__).resolve().parents[1]
a=(ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes()
b=(ROOT/'patches/libmtkcam_metastore.so').read_bytes()
m=json.loads((ROOT/'patches/patch-manifest.json').read_text())
assert hashlib.sha256(a).hexdigest()==m['input_sha256']
assert hashlib.sha256(b).hexdigest()==m['output_sha256']
assert len(a)==len(b)==m['size']
replay=bytearray(a);reverse=bytearray(b);occupied=set()
for c in m['changes']:
    off=int(c['offset'],16);old=bytes.fromhex(c['old']);new=bytes.fromhex(c['new'])
    assert len(old)==len(new) and a[off:off+len(old)]==old and b[off:off+len(new)]==new
    region=set(range(off,off+len(old)));assert not occupied&region;occupied|=region
    replay[off:off+len(new)]=new;reverse[off:off+len(old)]=old
assert bytes(replay)==b and bytes(reverse)==a
phoff=struct.unpack_from('<Q',b,32)[0]
entsize,n=struct.unpack_from('<HH',b,54)
loads=[]
for i in range(n):
    typ,flags,off,va,pa,filesz,memsz,align=struct.unpack_from('<IIQQQQQQ',b,phoff+i*entsize)
    if typ!=1:continue
    assert filesz<=memsz and off+filesz<=len(b)
    assert (off-va)%align==0
    assert flags!=7
    loads.append((off,va,filesz,flags))
cave=next(c for c in m['changes'] if c['reason'].startswith('AAPCS'))
cavestart=int(cave['offset'],16);caveend=cavestart+len(bytes.fromhex(cave['new']))
assert set(bytes.fromhex(cave['old']))=={0}
assert any(off<=cavestart<caveend<=off+sz and flags==5 for off,va,sz,flags in loads)
for c in m['changes'][:2]:
    off=int(c['offset'],16);w=struct.unpack_from('<I',b,off)[0]
    assert w>>26==0b100101
    imm=w&0x3ffffff
    if imm&(1<<25):imm-=1<<26
    target=off+imm*4
    assert cavestart<=target<caveend
# The three problematic original-module changes are absent.
for off in (0x54a64,0x7cfd0,0x7cfec,0x2bcc8):assert b[off:off+4]==a[off:off+4]
assert sum(x!=y for x,y in zip(a,b))==m['changed_bytes']
print('PASS: hashes, exact replay/reversal, non-overlap, ELF load bounds/alignment/W^X, branch targets, stock checks preserved.')
