"""Emulate native torch bridge boundaries, metadata and failure cleanup."""
import itertools,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_native_torch_patch import build_hal,build_device,build_framework,OUT
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm64_const import *
END=0x700000;SELF=0x500000;STACK=0x60ff00
def machine(name):
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0,0x800000)
 u.mem_write(0,(OUT/name).read_bytes());u.reg_write(UC_ARM64_REG_SP,STACK)
 u.reg_write(UC_ARM64_REG_X0,SELF);u.reg_write(UC_ARM64_REG_X30,END)
 return u
def r(u,i):return u.reg_read(UC_ARM64_REG_X0+i)
def w(u,i,v):u.reg_write(UC_ARM64_REG_X0+i,v&0xffffffffffffffff)
def ret(u,value):w(u,0,value);u.reg_write(UC_ARM64_REG_PC,u.reg_read(UC_ARM64_REG_X30))
def put(u,addr,value,size=4):u.mem_write(addr,(value&((1<<(size*8))-1)).to_bytes(size,'little'))
count=0
h=build_hal();d=build_device();f=build_framework()
for sensor,torch,timeout,level in itertools.product([1,2,4],[0,1],[0,1,300],[-1,0,1,5,9,10]):
 u=machine('libcam.hal3a.v3.so');put(u,SELF+0x30,sensor);put(u,SELF+0xbc,torch)
 put(u,int(h['context_cell'],16),level);w(u,1,0xffffffff00000006);w(u,2,timeout)
 u.emu_start(0x229140,0x2d79e0,count=100)
 expected=level-1 if sensor==1 and torch==1 and timeout==0 and 1<=level<=9 else 6
 assert r(u,1)==0xffffffff00000000+expected
 assert r(u,0)==SELF and r(u,2)==timeout and u.reg_read(UC_ARM64_REG_SP)==STACK
 count+=1
for main,level,result in itertools.product([False,True],[-1,0,1,5,9,10],[0,-16]):
 u=machine('cameraserver');put(u,SELF+0x20,0x3002 if main else 0x3102);put(u,SELF+0xb8,7)
 w(u,1,level);calls=[]
 def hook(uc,addr,size,data):
  if addr==int(f['blocks']['original_set_torch']['address'],16):
   calls.append(r(uc,1));ret(uc,result)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x14f2ec,END,count=100)
 valid=main and 1<=level<=9
 assert calls==([0x100+level] if valid else [])
 assert r(u,0)&0xffffffff==((result if valid else -22 if main else -38)&0xffffffff)
 assert int.from_bytes(u.mem_read(SELF+0xb8,4),'little')==(level if valid and result==0 else 7)
 assert u.reg_read(UC_ARM64_REG_SP)==STACK
 count+=1
for level in [0,1,5,9,10]:
 u=machine('cameraserver');put(u,SELF+0x20,0x3002);put(u,SELF+0xb8,level);w(u,1,SELF+0x400)
 u.emu_start(0x14f31c,END,count=100)
 assert r(u,0)==0 and int.from_bytes(u.mem_read(SELF+0x400,4),'little')==(level if 1<=level<=9 else 7)
 count+=1
# Every loader/driver error preserves status and balances the temporary context.
for mode,failure in itertools.product([0,1,0x101,0x105,0x109],['none','dlopen','getter','control','instance','context','on','apply']):
 u=machine('libmtkcam_device3_hal.so');w(u,1,mode);events=[]
 original=int(d['blocks']['original_set_torch']['address'],16)
 def hook(uc,addr,size,data):
  if addr==original:events.append(('mode',r(uc,1)));ret(uc,-16 if failure=='on' else 0)
  elif addr==0x37c90:events.append(('open',));ret(uc,0 if failure=='dlopen' else 0x510000)
  elif addr==0x37ca0:
   name=bytes(uc.mem_read(r(uc,1),64)).split(b'\0')[0];kind='getter' if b'getInstance' in name else 'control'
   events.append((kind,));ret(uc,0 if failure==kind else 0x710000 if kind=='getter' else 0x710004)
  elif addr==0x710000:ret(uc,0 if failure=='instance' else 0x520000)
  elif addr==0x710004:
   events.append(('custom',r(uc,1),r(uc,2)))
   ret(uc,-22 if (failure=='context' and r(uc,1)==0x6810 and r(uc,2)) or (failure=='apply' and r(uc,1)==0x6811) else 0)
  elif addr==0x37cc0:events.append(('close',));ret(uc,0)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x194d0,END,count=250)
 assert u.reg_read(UC_ARM64_REG_SP)==STACK
 if mode in (0,1):assert events==[('mode',mode)]
 else:
  assert (('close',) in events)==(failure!='dlopen')
  if failure in ('none','on','apply'):assert ('custom',0x6810,0) in events
  if failure=='apply':assert ('mode',0) in events
  expected=0 if failure=='none' else -16 if failure=='on' else -22 if failure in ('context','apply') else -38
  assert r(u,0)&0xffffffff==expected&0xffffffff,(mode,failure,events,r(u,0))
 count+=1
print('PASS',count,'native instruction cases (boundary routing, register/stack preservation, status and cleanup)')
