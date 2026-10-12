"""Hash-locked CameraService -> MTK native torch-strength bridge.

No device writes. API levels 1..9 map to AW36515 duties 0..8. Private HIDL
transport is valid ONLY with all three exact companion binaries installed.
SINGLE metadata is deliberately untouched until its request path is implemented.
"""
import hashlib, json, struct, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from build_raw_patch import parse_elf, branch, disasm
from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN
OUT = ROOT/'patches/native-torch'
KS = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)

class Patch:
    def __init__(self, path, digest):
        self.path = path
        self.elf = parse_elf(path.read_bytes())
        if self.elf.sha256 != digest: raise ValueError(f'Unexpected input: {path}')
        self.data = bytearray(self.elf.data)
        self.rx = self.elf.executable_load
        assert self.rx.p_offset == self.rx.p_vaddr
        self.start = self.end = (self.rx.p_offset+self.rx.p_filesz+15)&~15
        self.changes = []; self.blocks = {}
    def put(self, off, data):
        old = self.data[off:off+len(data)]
        self.changes.append(dict(offset=hex(off),old=old.hex(),new=data.hex()))
        self.data[off:off+len(data)] = data
    def asm(self, name, source):
        addr = self.end
        code = bytes(KS.asm(source, addr=addr)[0])
        self.end += len(code)
        self.end = (self.end+3)&~3
        self.blocks[name] = dict(address=hex(addr),size=len(code),source=source)
        assert not any(self.elf.data[addr:self.end]), name
        assert self.end <= min(p.p_offset for p in self.elf.load_segments if p.p_offset>self.rx.p_offset)
        assert not any(s.size and s.offset<self.end and addr<s.offset+s.size for s in self.elf.sections.values())
        self.put(addr,code)
        return addr
    def ph(self, segment):
        return struct.unpack_from('<Q',self.data,32)[0]+segment.index*struct.unpack_from('<H',self.data,54)[0]
    def bss(self):
        last = max(self.elf.load_segments,key=lambda p:p.p_vaddr)
        addr = (last.p_vaddr+last.p_memsz+7)&~7
        self.put(self.ph(last)+40,struct.pack('<Q',addr+8-last.p_vaddr))
        return addr
    def hook(self, at, target): self.put(at,branch(at,target))
    def finish(self):
        for field in (32,40): self.put(self.ph(self.rx)+field,struct.pack('<Q',self.end-self.rx.p_offset))
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/self.path.name).write_bytes(self.data)
        manifest = dict(input_sha256=self.elf.sha256,output_sha256=hashlib.sha256(self.data).hexdigest(),
                        cave_start=hex(self.start),cave_end=hex(self.end),blocks=self.blocks,changes=self.changes,
                        hardware_validated=False)
        (OUT/(self.path.name+'.json')).write_text(json.dumps(manifest,indent=2)+'\n')
        (OUT/(self.path.name+'.asm.txt')).write_text('\n'.join(disasm(parse_elf(bytes(self.data)),self.start,self.end-self.start)))
        return manifest

def build_hal():
    p=Patch(ROOT/'patches/flash-capture/libcam.hal3a.v3.so','4d5a62e26aa736cc9b7632ba6b9ee6f63904f5d248ec3bfeece87fe80dcd15d2')
    cell=p.bss()
    ctx=f'adrp x9, {cell&~4095}; add x9,x9,#{cell&4095}'
    entry=p.asm('torch_before_on',f'''
        ldr w8,[x0,#0x30]
        cmp w8,#1
        b.ne original
        ldr w8,[x0,#0xbc]
        cmp w8,#1
        b.ne original
        cbnz w2,original
        {ctx}
        ldr w8,[x9]
        sub w8,w8,#1
        cmp w8,#8
        b.hi original
        bfi x1,x8,#0,#32
    original:
        b 0x2d79e0
    ''')
    p.hook(0x229140,entry)
    custom=p.asm('custom_strength_context',f'''
        mov w8,#0x6810
        cmp w1,w8
        b.eq context
        add w8,w8,#1
        cmp w1,w8
        b.eq apply
        stp x29,x30,[sp,#-0x20]!
        b 0x229eb4
    context:
        ldr w8,[x0,#0x30]
        cmp w8,#1
        b.ne unsupported
        cmp x2,#9
        b.hi invalid
        {ctx}
        str w2,[x9]
        mov w0,#0
        ret
    apply:
        ldr w8,[x0,#0x30]
        cmp w8,#1
        b.ne unsupported
        sub x8,x2,#1
        cmp x8,#8
        b.hi invalid
        ldr w9,[x0,#0xbc]
        cmp w9,#1
        b.ne unavailable
        ldr x0,[x0,#0x2a8]
        cbz x0,unavailable
        ldr x9,[x0]
        ldr x9,[x9,#0x38]
        mov w1,w8
        br x9
    invalid: mov w0,#-22; ret
    unsupported: mov w0,#-38; ret
    unavailable: mov w0,#-19; ret
    ''')
    p.hook(0x229eb0,custom)
    m=p.finish(); m['context_cell']=hex(cell)
    return m

def bytestring(s): return '.byte '+','.join(str(x) for x in s.encode()+b'\0')

def build_device():
    p=Patch(ROOT/'.local-private/hal-review-20261003/binaries/libmtkcam_device3_hal.so',
            '0333ea749a9b15eb9ecf21215a2ebea11c5d3fbff247acd7ec93022256d544b1')
    original=p.asm('original_set_torch', '''
        ldp x8,x9,[x0,#0x10]
        mov w2,w1
        ldr x10,[x8]
        mov x0,x8
        mov x1,x9
        ldr x3,[x10,#0x58]
        br x3
    ''')
    entry=p.asm('encoded_torch',f'''
        sub w8,w1,#0x101
        cmp w8,#8
        b.ls encoded
        b {original}
    encoded:
        stp x29,x30,[sp,#-80]!
        stp x19,x20,[sp,#16]
        stp x21,x22,[sp,#32]
        stp x23,x24,[sp,#48]
        mov x29,sp
        mov x19,x0
        add w20,w8,#1
        adr x0,library
        mov w1,#2
        bl 0x37c90
        mov x21,x0
        cbz x0,nohandle
        adr x1,getter
        bl 0x37ca0
        cbz x0,nosymbol
        mov x24,x0
        mov x0,x21
        adr x1,control
        bl 0x37ca0
        cbz x0,nosymbol
        mov x23,x0
        mov w0,#1
        blr x24
        mov x22,x0
        cbz x0,nosymbol
        mov w1,#0x6810
        mov w2,w20
        mov x3,xzr
        blr x23
        mov w24,w0
        cbnz w0,close
        mov x0,x19
        mov w1,#1
        bl {original}
        mov w24,w0
        cbnz w0,clear
        mov x0,x22
        mov w1,#0x6811
        mov w2,w20
        mov x3,xzr
        blr x23
        mov w24,w0
        cbz w0,clear
        mov x0,x19
        mov w1,#0
        bl {original}
    clear:
        mov x0,x22
        mov w1,#0x6810
        mov x2,xzr
        mov x3,xzr
        blr x23
        b close
    nosymbol:
        mov w24,#-38
    close:
        mov x0,x21
        bl 0x37cc0
        mov w0,w24
        b done
    nohandle:
        mov w0,#-38
    done:
        ldp x23,x24,[sp,#48]
        ldp x21,x22,[sp,#32]
        ldp x19,x20,[sp,#16]
        ldp x29,x30,[sp],#80
        ret
    library: {bytestring('libcam.hal3a.v3.so')}
    getter: {bytestring('_ZN8FlashHal11getInstanceEi')}
    control: {bytestring('_ZN8FlashHal16sendCustom3ACtrlEN6NS3Av315ECustom3ACtrl_TEll')}
    ''')
    p.hook(0x194d0,entry)
    return p.finish()

def build_framework():
    p=Patch(ROOT/'.local-private/flash-api-20261003/cameraserver',
            '0e61fed272068a7855e236f9fb23d3e07e46bc1ba5588f92398c1a789e457f0c')
    original=p.asm('original_set_torch','sub sp,sp,#0x100; b 0x14ee38')
    ordinary=p.asm('ordinary_torch_reset',f'''
        stp x19,x30,[sp,#-32]!
        str x20,[sp,#16]
        mov x19,x0
        mov w20,w1
        cmp w1,#1
        b.ne call_original
        ldr w8,[x19,#0x20]
        mov w9,#0x3002
        cmp w8,w9
        b.ne call_original
        mov w1,#0x107
    call_original:
        bl {original}
        cbnz w0,done
        cmp w20,#1
        b.hi done
        ldr w8,[x19,#0x20]
        mov w9,#0x3002
        cmp w8,w9
        b.ne done
        mov w8,#7
        str w8,[x19,#0xb8]
    done:
        ldr x20,[sp,#16]
        ldp x19,x30,[sp],#32
        ret
    ''')
    p.hook(0x14ee34,ordinary)
    setter=p.asm('strength_setter',f'''
        ldr w8,[x0,#0x20]
        mov w9,#0x3002
        cmp w8,w9
        b.ne unsupported
        sub w8,w1,#1
        cmp w8,#8
        b.hi invalid
        stp x19,x30,[sp,#-32]!
        str x20,[sp,#16]
        mov x19,x0
        mov w20,w1
        add w1,w1,#0x100
        bl {original}
        cbnz w0,done
        str w20,[x19,#0xb8]
    done:
        ldr x20,[sp,#16]
        ldp x19,x30,[sp],#32
        ret
    unsupported: mov w0,#-38; ret
    invalid: mov w0,#-22; ret
    ''')
    getter=p.asm('strength_getter','''
        ldr w8,[x0,#0x20]
        mov w9,#0x3002
        cmp w8,w9
        b.ne unsupported
        cbz x1,invalid
        ldr w8,[x0,#0xb8]
        sub w9,w8,#1
        cmp w9,#8
        mov w9,#7
        csel w8,w8,w9,ls
        str w8,[x1]
        mov w0,#0
        ret
    unsupported: mov w0,#-38; ret
    invalid: mov w0,#-22; ret
    ''')
    p.hook(0x14f2ec,setter); p.hook(0x14f31c,getter)
    p.put(0x14f208,bytes(KS.asm('mov w1,w19')[0]))
    fixup=p.asm('strength_characteristics','''
        cbnz w21,done
        ldr w8,[x19,#0x20]
        mov w9,#0x3002
        cmp w8,w9
        b.ne done
        mov w8,#9
        str w8,[sp,#0xc]
        add x0,x19,#0x130
        mov w1,#2
        movk w1,#5,lsl #16
        add x2,sp,#0xc
        mov w3,#1
        bl 0x377030
        mov w21,w0
        cbnz w0,done
        mov w8,#7
        str w8,[sp,#0xc]
        add x0,x19,#0x130
        mov w1,#3
        movk w1,#5,lsl #16
        add x2,sp,#0xc
        mov w3,#1
        bl 0x377030
        mov w21,w0
        cbnz w0,done
        mov w8,#7
        str w8,[x19,#0xb8]
        str w8,[x19,#0xbc]
        mov w8,#9
        str w8,[x19,#0xc0]
    done:
        mov w0,w21
        b 0x13f2a8
    ''')
    p.hook(0x13f2a4,fixup)
    return p.finish()

if __name__=='__main__':
    result={'hal':build_hal(),'device':build_device(),'framework':build_framework()}
    print(json.dumps({k:{n:v for n,v in m.items() if n not in ('changes','blocks')} for k,m in result.items()},indent=2))
