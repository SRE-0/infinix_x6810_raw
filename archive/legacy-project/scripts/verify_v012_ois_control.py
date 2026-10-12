"""Execute the OIS request bridge with ABI clobbering and mocked vendor boundaries."""
from build_v012_ois import *
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm64_const import *
a=parse_elf((DEST/'libcam.hal3a.v3.so').read_bytes())
def case(sensor,mode,current,fd=63,number=1):
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0,0x400000)
 for h in a.load_segments:u.mem_write(h.p_vaddr,a.data[h.p_offset:h.p_offset+h.p_filesz])
 u.mem_map(0x1000000,0x200000);sp=0x1100000;obj=0x1001000;ois=0x1010000;vt=0x1020000;command=0x1030000
 def put(addr,n,fmt='<I'):u.mem_write(addr,struct.pack(fmt,n))
 put(obj+0x28,sensor);put(obj+0x344,current);put(obj+0xe0,ois,'<Q');put(ois,vt,'<Q');put(ois+8,fd,'<i');put(ois+0xc8,number);put(vt+0xb8,command,'<Q')
 u.reg_write(UC_ARM64_REG_SP,sp);u.reg_write(UC_ARM64_REG_X20,obj);u.reg_write(UC_ARM64_REG_X21,0x1040000);u.reg_write(UC_ARM64_REG_X19,0x123456);u.reg_write(UC_ARM64_REG_LR,0x234568)
 calls=[]
 def hook(uc,pc,size,data):
  if pc in (0x25cd74,0x25c9e4):uc.emu_stop();return
  if pc not in (0x2d06a0,0x2d06c0,0x2d0720,0x2cfbb0,command):return
  x0=uc.reg_read(UC_ARM64_REG_X0);x1=uc.reg_read(UC_ARM64_REG_X1)
  result=0
  if pc==0x2d06a0:assert x1==0x80004
  elif pc==0x2d06c0:result=int(mode is None)
  elif pc==0x2d0720:result=mode
  elif pc==command:assert x0==ois;calls.append(x1);result=1
  for i in range(1,18):uc.reg_write(globals()['UC_ARM64_REG_X'+str(i)],0xDEAD0000+i*16)
  uc.reg_write(UC_ARM64_REG_X0,result);uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_LR))
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x25c9e0,0x3ffff0,count=1000)
 assert u.reg_read(UC_ARM64_REG_SP)==sp
 assert u.reg_read(UC_ARM64_REG_X19)==0x123456
 assert u.reg_read(UC_ARM64_REG_X20)==obj
 assert u.reg_read(UC_ARM64_REG_X21)==0x1040000
 assert u.reg_read(UC_ARM64_REG_LR)==0x234568
 desired=3 if mode==1 else 1
 expected=[] if sensor!=4 or current==desired or fd<0 or number!=1 else [1 if mode==1 else 2]
 assert calls==expected,(sensor,mode,current,fd,number,calls,expected)
 assert u.reg_read(UC_ARM64_REG_PC)==(0x25cd74 if sensor==4 else 0x25c9e4)
 return 1
count=sum(case(s,m,c,f,n) for s in [1,2,4,8] for m in [None,0,1,2] for c in [0,1,3] for f in [-1,63] for n in [0,1])
print('PASS',count,'control cases, OFF/ON, missing key, other sensors, invalid fd, OIS count and ABI preservation')
