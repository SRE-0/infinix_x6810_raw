"""Execute candidate instructions across the observed FlashHalInfo ABI boundaries."""
import itertools, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'dist/python-deps'),str(ROOT/'scripts')]
from build_flash_capture_patch import build,HOOK
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm64_const import *
b,m=build();total=0
for sensor,duty,timeout,cap in itertools.product([1,2,4],[-1,0,4,8,9,15,29,30],[0,1,135,300,301],[-1,0,8,9,15,29,30,100]):
    u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
    u.mem_map(0,0x400000);u.mem_write(0,b)
    u.mem_map(0x500000,0x10000);u.mem_map(0x600000,0x10000)
    original=(0xffffffff<<32)|(duty&0xffffffff)
    u.reg_write(UC_ARM64_REG_X0,0x500000);u.mem_write(0x500030,sensor.to_bytes(4,'little'))
    u.reg_write(UC_ARM64_REG_X1,original);u.reg_write(UC_ARM64_REG_X2,timeout)
    u.reg_write(UC_ARM64_REG_X3,123);u.reg_write(UC_ARM64_REG_X30,0x123456)
    u.reg_write(UC_ARM64_REG_SP,0x60fff0)
    def hook(uc,addr,size,data):
        if addr==0x2cebd0:
            assert bytes(uc.mem_read(uc.reg_read(UC_ARM64_REG_X0),28)).split(b'\0')[0]==b'vendor.debug.x6810.flashcap'
            uc.reg_write(UC_ARM64_REG_X0,cap&0xffffffffffffffff)
            uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(HOOK,HOOK+4,count=100)
    changed=sensor==1 and 1<=timeout<=300 and 9<=duty<=29 and 9<=cap<=duty
    expected=(0xffffffff<<32)|((cap if changed else duty)&0xffffffff)
    assert u.reg_read(UC_ARM64_REG_X1)==expected,(sensor,duty,timeout,cap)
    assert u.reg_read(UC_ARM64_REG_X0)==0x500000
    assert u.reg_read(UC_ARM64_REG_X2)==timeout and u.reg_read(UC_ARM64_REG_X3)==123
    assert u.reg_read(UC_ARM64_REG_X30)==0x123456
    assert u.reg_read(UC_ARM64_REG_SP)==0x60fff0-0x70
    total+=1
print('PASS',total,'ABI, sensor, timeout, duty-cap and register-preservation cases')
