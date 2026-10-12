from emulate_metadata import *
import json

p=ROOT/'patches/front-v0.7'
m=json.loads((p/'policy-manifest.json').read_text())
stock=(ROOT/'stock-binaries/libmtkcam_pipelinepolicy.so').read_bytes()
data=(p/'libmtkcam_pipelinepolicy.so').read_bytes();a=parse_elf(data)
assert hashlib.sha256(stock).hexdigest()==m['input_sha256']
assert hashlib.sha256(data).hexdigest()==m['output_sha256']
replay=bytearray(stock);touched=set()
for c in m['changes']:
    off=int(c['offset'],16);old=bytes.fromhex(c['old']);new=bytes.fromhex(c['new'])
    assert len(old)==len(new) and stock[off:off+len(old)]==old
    idx=set(range(off,off+len(old)));assert not idx&touched;touched|=idx
    replay[off:off+len(new)]=new
assert replay==data
cases=[]
for camera,mode,w,h in [(1,0,2320,1744),(0,0,2320,1744),(2,0,2320,1744),
                       (1,1,2320,1744),(1,0,4640,3488),(1,0,2320,1745),(1,0,2321,1744)]:
    u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0,0x200000)
    for ph in a.load_segments:u.mem_write(ph.p_vaddr,data[ph.p_offset:ph.p_offset+ph.p_filesz])
    u.mem_map(0x1000000,0x10000)
    u.reg_write(UC_ARM64_REG_X0,0x1001000);u.reg_write(UC_ARM64_REG_X22,0x1002000)
    u.reg_write(UC_ARM64_REG_X21,mode);u.reg_write(UC_ARM64_REG_X29,0x1004000)
    u.reg_write(UC_ARM64_REG_SP,0x1003000)
    u.mem_write(0x1002000,struct.pack('<I',camera))
    u.mem_write(0x100101c,struct.pack('<II',w,h))
    u.mem_write(0x1003f80,struct.pack('<I',mode))
    ends=[]
    def stop(uc,pc,size,_):
        if pc in (0x489ac,0x488a8):ends.append(pc);uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,stop);u.emu_start(0x488a4,0,count=100)
    expected=0x489ac if (camera,mode,w,h)==(1,0,2320,1744) else 0x488a8
    assert ends==[expected],(camera,mode,w,h,ends)
    assert u.reg_read(UC_ARM64_REG_X0)==0x1001000
    assert u.reg_read(UC_ARM64_REG_SP)==0x1003000
    if expected==0x488a8:assert u.reg_read(UC_ARM64_REG_W8)==mode
    cases.append(dict(camera=camera,mode=mode,size=[w,h],exit=hex(expected)))
(ROOT/'dist/verification/front-v0.7-policy.json').write_text(json.dumps(dict(cases=cases,manifest_replay=True,hardware_test=False),indent=2)+'\n')
print('PASS: 7 policy guard paths and exact manifest replay')
