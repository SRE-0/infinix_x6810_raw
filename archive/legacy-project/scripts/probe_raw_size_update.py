"""Isolated emulation of stock updateRawCapability stream-size replacement block.

Starts at 0x7d1dc AFTER acquisition of the active rectangle, with that size
explicitly supplied on the stack. Does not emulate a complete provider/camera.
"""
from emulate_metadata import *


def probe(width,height, original=None, image_data=None, preserve_binned=False):
    a=parse_elf(image_data if image_data is not None else (ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes())
    u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0,0x200000)
    for ph in a.load_segments:u.mem_write(ph.p_vaddr,a.data[ph.p_offset:ph.p_offset+ph.p_filesz])
    u.mem_map(0x1000000,0x200000)
    sp=0x1100000;u.reg_write(UC_ARM64_REG_SP,sp)
    u.reg_write(UC_ARM64_REG_X19,0x1001000)
    u.reg_write(UC_ARM64_REG_X25,0x1003000) # zero logging threshold, avoids logging-only branches
    u.mem_write(sp+0x18,struct.pack('<II',height,width))
    # Six-int stride is from this vendor routine, not the public Camera2 quad layout.
    original=original or [33,640,480,0,0,0,32,1112,834,0,0,0]
    entries={};result={};plt=plt_symbols(a)
    def hook(uc,pc,size,unused):
        if pc not in plt:return
        name=plt[pc];x0=uc.reg_read(UC_ARM64_REG_X0);x1=uc.reg_read(UC_ARM64_REG_X1);x2=uc.reg_read(UC_ARM64_REG_X2)
        ret=0
        if 'IMetadata8entryFor' in name:
            assert x1==0xd000a
            entries[uc.reg_read(UC_ARM64_REG_X8)]=list(original)
        elif 'IEntry5count' in name:ret=len(entries[x0])
        elif 'IEntry6itemAt' in name:ret=entries[x0][x1]
        elif 'IEntry13replaceItemAt' in name:entries[x0][x1]=int.from_bytes(uc.mem_read(x2,4),'little')
        elif 'IEntry3tag' in name:ret=0xd000a
        elif 'IMetadata6update' in name:result[x1]=list(entries[x2])
        else:raise ValueError('Unmodelled call '+name)
        for r in range(1,18):uc.reg_write(globals()['UC_ARM64_REG_X'+str(r)],0xDEAD0000+r*0x100)
        uc.reg_write(UC_ARM64_REG_X0,ret);uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_LR))
    u.hook_add(UC_HOOK_CODE,hook)
    u.emu_start(0x7d1dc,0x7d4d4,count=10000)
    assert u.reg_read(UC_ARM64_REG_PC)==0x7d4d4
    expected=original[:]
    first_raw=next(i for i in range(0,len(expected),6) if expected[i]==32)
    if not preserve_binned:
        expected[first_raw+1:first_raw+3]=[width,height]
    assert result[0xd000a]==expected
    return dict(active_size_supplied=[width,height],before=original,after=result[0xd000a],passed=True)

if __name__=='__main__':
    output=dict(scope='Isolated block 0x7d1dc..0x7d4d4; synthetic vendor entry and active dimensions. No hardware or full HAL test.',
                tests=[probe(3264,2448),probe(4608,3456),probe(4672,3504),
                       probe(4640,3488,[32,4640,3488,0,100000000,33333333,
                                        32,2320,1744,0,33333333,33333333])])
    (OUT/'aux-raw-size-normalization.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))
