"""Verify stream skip/retain behavior, fallback flags and register preservation."""
from emulate_metadata import *
import itertools,json

p=ROOT/'patches/front-v0.8-binned'
m=json.loads((p/'metastore-manifest.json').read_text())
data=(p/'libmtkcam_metastore.so').read_bytes();a=parse_elf(data)
stock=(ROOT/'patches/front-v0.7/libmtkcam_metastore.so').read_bytes()
assert hashlib.sha256(data).hexdigest()==m['output_sha256']
replay=bytearray(stock)
for c in m['changes']:
    off=int(c['offset'],16);old=bytes.fromhex(c['old']);new=bytes.fromhex(c['new'])
    assert stock[off:off+len(old)]==old
    replay[off:off+len(new)]=new
assert replay==data
cases=[]
for camera,(pw,ph),(w,h),flag in itertools.product([0,1,2],[(4640,3488),(4000,3000)],
    [(2320,1744),(1920,1080),(3456,3456),(2321,1744),(2320,1745)], [0,1]):
    u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0,0x200000)
    for seg in a.load_segments:u.mem_write(seg.p_vaddr,data[seg.p_offset:seg.p_offset+seg.p_filesz])
    u.mem_map(0x1000000,0x10000)
    regs={UC_ARM64_REG_X21:0x1001000,UC_ARM64_REG_X10:0x1002000,
          UC_ARM64_REG_SP:0x1003000,UC_ARM64_REG_X28:pw,UC_ARM64_REG_X7:w,UC_ARM64_REG_X8:flag}
    for reg,val in regs.items():u.reg_write(reg,val)
    u.mem_write(0x1001010,struct.pack('<I',camera))
    u.mem_write(0x1002010,struct.pack('<Q',h))
    u.mem_write(0x1003040,struct.pack('<Q',ph))
    ends=[]
    def stop(uc,pc,size,_):
        if pc in (0x7ecec,0x7ead0,0x7ecd4):ends.append(pc);uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,stop);u.emu_start(0x7eacc,0,count=100)
    skip=camera==1 and (pw,ph)==(4640,3488) and (w>2320 or h>1744)
    expected=0x7ecec if skip else 0x7ead0 if flag else 0x7ecd4
    assert ends==[expected],(camera,pw,ph,w,h,flag,ends)
    for reg,val in regs.items():assert u.reg_read(reg)==val
    cases.append(dict(camera=camera,pixel_array=[pw,ph],size=[w,h],flag=flag,exit=hex(expected)))
(ROOT/'dist/verification/front-v0.8-stream-filter.json').write_text(json.dumps(dict(cases=cases,manifest_replay=True),indent=2))
print('PASS: 60 stream-filter paths, register preservation, exact manifest replay')
