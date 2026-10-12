"""Host checks of emitted instructions, frame isolation and pulse restoration."""
import itertools,json,struct,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm64_const import *
OUT=ROOT/'patches/single-flash-api'
STOP=0x700000; STACK=0x680000; RAW=0x500000; FLASH=0x510000
def rid(n):return UC_ARM64_REG_X29 if n==29 else UC_ARM64_REG_X30 if n==30 else UC_ARM64_REG_X0+n
def reg(u,n):return u.reg_read(rid(n))
def wr(u,n,v):u.reg_write(rid(n),v&((1<<64)-1))
def put(u,a,v,n=4):u.mem_write(a,int(v).to_bytes(n,'little'))
def machine(name):
    u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0,0x800000)
    data=(OUT/name).read_bytes(); ph=struct.unpack_from('<Q',data,32)[0]
    for i in range(struct.unpack_from('<H',data,56)[0]):
        typ,flags,off,va,pa,fs,ms,align=struct.unpack_from('<IIQQQQQQ',data,ph+i*56)
        if typ==1:u.mem_write(va,data[off:off+fs])
    u.reg_write(UC_ARM64_REG_SP,STACK);wr(u,30,STOP)
    return u
def ret(u,v=0):wr(u,0,v);u.reg_write(UC_ARM64_REG_PC,reg(u,30))
for name in ['libcam.hal3a.v3.so','cameraserver']:
    m=json.loads((OUT/(name+'.json')).read_text());data=(OUT/name).read_bytes()
    assert hashlib.sha256(data).hexdigest()==m['output_sha256']
    restored=bytearray(data)
    for c in reversed(m['changes']):
        o=int(c['offset'],16); new=bytes.fromhex(c['new']);old=bytes.fromhex(c['old'])
        assert restored[o:o+len(new)]==new
        restored[o:o+len(old)]=old
    assert hashlib.sha256(restored).hexdigest()==m['input_sha256']
h=json.loads((OUT/'libcam.hal3a.v3.so.json').read_text())
ring=int(h['blocks']['frame_strength_ring']['address'],16)
u=machine('libcam.hal3a.v3.so')
def ringcall(owner,frame,level,write):
    for n,v in enumerate([owner,frame,level,write]):wr(u,n,v)
    wr(u,30,STOP);u.emu_start(ring,STOP,count=1000);return reg(u,0)
for frame in range(1,600):
    ringcall(RAW,frame,frame%9+1,1)
    assert ringcall(RAW,frame,0,0)==frame%9+1
    assert ringcall(FLASH,frame,0,0)==0
    assert ringcall(RAW,frame+256,0,0)==0
    ringcall(RAW,frame,0,1);assert ringcall(RAW,frame,0,0)==0
cases=0
for sensor,level in itertools.product([1,2,4],[-1,0,*range(1,31),31,255]):
    u=machine('libcam.hal3a.v3.so');wr(u,19,RAW);wr(u,0,FLASH);wr(u,1,1);wr(u,2,4)
    put(u,RAW+0xc4,sensor);put(u,RAW+0x484,(0x68100000+level)&0xffffffff)
    old=struct.pack('<iiii',6,-1,0,0);u.mem_write(FLASH+0x8c,old);events=[]
    def hook(uc,addr,size,data):
        if addr==0x228900:
            events.append(('configure',reg(uc,2)&0xffffffff))
            uc.mem_write(FLASH+0x8c,struct.pack('<QQ',reg(uc,2),0));ret(uc)
        elif addr==0x2cedf0:
            events.append(('on',tuple(struct.unpack('<iiii',bytes(uc.mem_read(FLASH+0x8c,16))))));ret(uc)
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x1038b8,0x1038bc,count=300)
    valid=sensor==1 and 1<=level<=30
    assert events==([('configure',level-1),('on',(level-1,-1,300,0))] if valid else [('on',(6,-1,0,0))]),events
    assert bytes(u.mem_read(FLASH+0x8c,16))==old
    assert u.reg_read(UC_ARM64_REG_SP)==STACK
    cases+=1
f=json.loads((OUT/'cameraserver.json').read_text())
lookup=int(f['blocks']['lookup_inline_scalar']['address'],16)
for camera,ae,mode,level in itertools.product([0,1,2],[0,1,2,3],[0,1,2],[-1,0,1,2,9,10,21,30,31]):
    u=machine('cameraserver');wr(u,0,30);wr(u,1,RAW);wr(u,2,0);wr(u,22,FLASH)
    put(u,FLASH,0x3002+camera*256,2);events=[]
    def hook(uc,addr,size,data):
        if addr==lookup:ret(uc,{0x40002:mode,0x10003:ae,0x40006:level}[reg(uc,1)])
        elif addr==0x377030:
            events.append(int.from_bytes(uc.mem_read(reg(uc,2),4),'little'));ret(uc)
        elif addr==0x2ac57c:
            assert reg(uc,0)==30 and reg(uc,1)==RAW and reg(uc,2)==0
            ret(uc)
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x2198c4,0x2198c8,count=300)
    effective=7 if level==-1 else level
    valid=camera==0 and ae<=1 and mode==1 and 1<=effective<=30
    assert events==([0x68100000+effective] if valid else []),(camera,ae,mode,level,events)
    assert u.reg_read(UC_ARM64_REG_SP)==STACK
    if camera==0 and ae<=1 and mode==1 and not 1<=effective<=30:
        assert reg(u,0)&0xffffffff==0xffffffea
    cases+=1
print('PASS: manifest reversal, 599 frame isolation/overwrite cases,',cases,'pulse/request routing cases')
