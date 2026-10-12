"""Emulate the guard AND original size comparisons, including oversized requests."""
from emulate_metadata import *
import json

p=ROOT/'patches/front-v0.8-trial'
m=json.loads((p/'policy-manifest.json').read_text())
data=(p/'libmtkcam_pipelinepolicy.so').read_bytes()
stock=(ROOT/'stock-binaries/libmtkcam_pipelinepolicy.so').read_bytes()
assert hashlib.sha256(stock).hexdigest()==m['input_sha256']
assert hashlib.sha256(data).hexdigest()==m['output_sha256']
replay=bytearray(stock)
for c in m['changes']:
    off=int(c['offset'],16);old=bytes.fromhex(c['old']);new=bytes.fromhex(c['new'])
    assert stock[off:off+len(old)]==old
    replay[off:off+len(new)]=new
assert replay==data
a=parse_elf(data);cases=[]
for camera,mode,w,h,rw,rh in [(1,0,2320,1744,2320,1744),
    (1,0,2320,1744,1728,1728),(1,0,2320,1744,3456,3456),
    (1,0,2320,1744,2321,1744),(1,0,2320,1744,2320,1745),
    (0,0,2320,1744,1728,1728),(2,0,2320,1744,1728,1728),
    (1,1,2320,1744,1728,1728),(1,0,4640,3488,1728,1728)]:
    u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0,0x200000)
    for ph in a.load_segments:u.mem_write(ph.p_vaddr,data[ph.p_offset:ph.p_offset+ph.p_filesz])
    u.mem_map(0x1000000,0x10000)
    for reg,value in [(UC_ARM64_REG_X0,0x1001000),(UC_ARM64_REG_X22,0x1002000),
        (UC_ARM64_REG_X21,mode),(UC_ARM64_REG_X29,0x1004000),
        (UC_ARM64_REG_SP,0x1003000),(UC_ARM64_REG_X20,0x1005000)]:u.reg_write(reg,value)
    u.mem_write(0x1002000,struct.pack('<I',camera))
    u.mem_write(0x100101c,struct.pack('<II',w,h))
    u.mem_write(0x1003f80,struct.pack('<I',mode))
    u.mem_write(0x1005000,struct.pack('<Q',0x1006000))
    u.mem_write(0x1006144,struct.pack('<II',rw,rh))
    ends=[]
    def stop(uc,pc,size,_):
        if pc in (0x489ac,0x488a8,0x48878):ends.append(pc);uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,stop);u.emu_start(0x488a4,0,count=100)
    expected=0x488a8
    if (camera,mode,w,h)==(1,0,2320,1744):expected=0x489ac if rw<=w and rh<=h else 0x48878
    assert ends==[expected],(camera,mode,w,h,rw,rh,ends)
    assert u.reg_read(UC_ARM64_REG_X0)==0x1001000
    assert u.reg_read(UC_ARM64_REG_SP)==0x1003000
    cases.append(dict(camera=camera,mode=mode,candidate=[w,h],requested=[rw,rh],exit=hex(expected)))
(ROOT/'dist/verification/front-v0.8-policy.json').write_text(json.dumps(dict(cases=cases,manifest_replay=True),indent=2))
print('PASS: 9 guard/size paths, oversized dimensions rejected, exact replay')
