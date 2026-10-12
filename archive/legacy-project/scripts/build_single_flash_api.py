"""Build the exact-build Camera2 SINGLE bridge. No device writes.

Levels 1..30 map to duties 0..29; levels 10..30 select photographic currents.
The software timeout remains 300 ms. OEM
SINGLE scheduling and OFF remain in charge; no autonomous driver commands.
"""
import json, struct
from pathlib import Path
import build_native_torch_patch as common
from build_raw_patch import branch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'patches/single-flash-api'
BASE=ROOT/'modules/v000_x6810_GL_raw_hd48_12mp_torch_changes/system'

def build():
    common.OUT=OUT
    p=common.Patch(BASE/'vendor/lib64/libcam.hal3a.v3.so',
                  '0669ac8e0f329e941ead3098a3ea0828597f8ce68c40a6ec7bef4607d6bbbecd')
    last=max(p.elf.load_segments,key=lambda s:s.p_vaddr)
    cell=(last.p_vaddr+last.p_memsz+15)&~15
    p.put(p.ph(last)+40,struct.pack('<Q',cell+16+256*24-last.p_vaddr))
    # Bounded, locked frame correlation. Exact owner+magic match; collisions
    # fail closed. No native calls or blocking I/O while holding the lock.
    ring=p.asm('frame_strength_ring',f'''
        adrp x8,{cell&~4095}
        add x8,x8,#{cell&4095}
    lock:
        ldaxr w9,[x8]
        cbnz w9,lock
        mov w9,#1
        stxr w10,w9,[x8]
        cbnz w10,lock
        and w9,w1,#255
        mov w10,#24
        madd x9,x9,x10,x8
        add x9,x9,#16
        cbz w3,read
        str x0,[x9]
        str w1,[x9,#8]
        str w2,[x9,#12]
        mov w0,wzr
        b unlock
    read:
        ldr x10,[x9]
        cmp x10,x0
        b.ne missing
        ldr w10,[x9,#8]
        cmp w10,w1
        b.ne missing
        ldr w0,[x9,#12]
        b unlock
    missing:
        mov w0,wzr
    unlock:
        stlr wzr,[x8]
        ret
    ''')
    # At this call site x28 is MetaSet.appMeta; x19 is Hal3AAdapter3.
    parse=p.asm('parse_private_single', f'''
        stp x29,x30,[sp,#-112]!
        stp x0,x1,[sp,#16]
        stp x2,x8,[sp,#32]
        str wzr,[x19,#0x3fc]
        add x8,sp,#48
        stp xzr,xzr,[x8]
        stp xzr,xzr,[x8,#16]
        stp xzr,xzr,[x8,#32]
        stp xzr,xzr,[x8,#48]
        mov x0,x28
        mov w1,#0x8c
        movk w1,#0xc000,lsl #16
        mov w2,wzr
        bl 0x2d06a0
        add x0,sp,#48
        bl 0x2d06c0
        cbnz w0,destruct
        add x0,sp,#48
        mov w1,wzr
        bl 0x2d48f0
        mov w8,#0x6810
        lsl w8,w8,#16
        sub w9,w0,w8
        sub w9,w9,#1
        cmp w9,#29
        b.hi destruct
        str w0,[x19,#0x3fc]
    destruct:
        add x0,sp,#48
        bl 0x2cfbb0
        ldr w8,[x19,#0x28]
        cmp w8,#1
        b.ne restored
        ldr x8,[sp,#0x180]
        ldr w1,[x8,#0x28]
        mov x0,x19
        ldr w2,[x19,#0x3fc]
        mov w3,#1
        bl {ring}
    restored:
        ldp x2,x8,[sp,#32]
        ldp x0,x1,[sp,#16]
        ldp x29,x30,[sp],#112
        mov x0,x19
        b 0x24ff94
    ''')
    p.hook(0x24ff90,parse)
    transfer=p.asm('params_under_mutex','''
        ldr w8,[x21,#0x30c]
        str w8,[x20,#0x484]
        mov x27,x20
        b 0x101014
    ''')
    p.hook(0x101010,transfer)
    gate=p.asm('single_scenario_duty','''
        ldr w8,[x19,#0xc4]
        cmp w8,#1
        b.ne original
        ldr w8,[x19,#0x484]
        mov w9,#0x6810
        lsl w9,w9,#16
        sub w8,w8,w9
        sub w8,w8,#1
        cmp w8,#29
        b.hi original
        stp x0,x30,[sp,#-48]!
        ldur x9,[x0,#0x8c]
        ldur x10,[x0,#0x94]
        stp x9,x10,[sp,#16]
        mov w2,w8
        movk x2,#0xffff,lsl #32
        movk x2,#0xffff,lsl #48
        mov x3,#300
        mov w1,#4
        bl 0x228900
        ldr x0,[sp]
        mov w8,#300
        str w8,[x0,#0x94]
        mov w1,#1
        mov w2,#4
        bl 0x2cedf0
        ldr x9,[sp]
        ldp x10,x11,[sp,#16]
        stur x10,[x9,#0x8c]
        stur x11,[x9,#0x94]
        ldr x30,[sp,#8]
        add sp,sp,#48
        b 0x1038bc
    original:
        bl 0x2cedf0
        b 0x1038bc
    ''')
    p.hook(0x1038b8,gate)
    result=p.asm('single_result_by_frame',f'''
        cmp w19,#1
        b.ne original
        ldr w8,[x25,#0x28]
        cmp w8,#1
        b.ne original
        stp x29,x30,[sp,#-96]!
        mov x0,x25
        mov w1,w22
        mov w3,wzr
        bl {ring}
        mov w8,#0x6810
        lsl w8,w8,#16
        sub w9,w0,w8
        sub w9,w9,#1
        cmp w9,#29
        b.hi done
        str w0,[sp,#80]
        add x0,sp,#16
        mov w1,#0x8c
        movk w1,#0xc000,lsl #16
        bl 0x2cfb80
        add x0,sp,#16
        add x1,sp,#80
        bl 0x2d0670
        add x0,x24,#0x30
        mov w1,#0x8c
        movk w1,#0xc000,lsl #16
        add x2,sp,#16
        bl 0x2cfba0
        add x0,sp,#16
        bl 0x2cfbb0
    done:
        ldp x29,x30,[sp],#96
    original:
        mov w0,w19
        b 0x25f2d0
    ''')
    p.hook(0x25f2cc,result)
    hal=p.finish()

    p=common.Patch(BASE/'bin/cameraserver',
                  '2f361a730064a2e8ccab8a3cd7fce8854f30dfffa141e7888f0f3b91b8aa867c')
    # CameraMetadata's buffer pointer is +8, confirmed by the existing probe.
    lookup=p.asm('lookup_inline_scalar','''
        ldr x8,[x0,#8]
        cbz x8,missing
        ldr w9,[x8,#12]
        cmp w9,#4096
        b.hi missing
        ldr w10,[x8,#20]
        add x8,x8,x10
    loop:
        cbz w9,missing
        ldr w10,[x8]
        cmp w10,w1
        b.eq found
        add x8,x8,#16
        sub w9,w9,#1
        b loop
    found:
        ldr w10,[x8,#4]
        cmp w10,#1
        b.ne missing
        ldrb w10,[x8,#12]
        cbz w10,byte_value
        cmp w10,#1
        b.ne missing
        ldr w0,[x8,#8]
        ret
    byte_value:
        ldrb w0,[x8,#8]
        ret
    missing:
        mov w0,#-1
        ret
    ''')
    bridge=p.asm('request_before_vndk_filter',f'''
        stp x29,x30,[sp,#-80]!
        stp x19,x20,[sp,#16]
        stp x0,x1,[sp,#32]
        stp x2,x3,[sp,#48]
        mov x19,x1
        ldrh w8,[x22]
        mov w9,#0x3002
        cmp w8,w9
        b.ne original
        mov x0,x19
        mov w1,#2
        movk w1,#4,lsl #16
        bl {lookup}
        cmp w0,#1
        b.ne original
        mov x0,x19
        mov w1,#3
        movk w1,#1,lsl #16
        bl {lookup}
        cmp w0,#1
        b.hi original
        mov x0,x19
        mov w1,#6
        movk w1,#4,lsl #16
        bl {lookup}
        cmn w0,#1
        b.ne explicit
        mov w0,#7
    explicit:
        sub w8,w0,#1
        cmp w8,#29
        b.hi invalid
        mov w8,#0x6810
        lsl w8,w8,#16
        add w8,w8,w0
        str w8,[sp,#64]
        mov x0,x19
        mov w1,#0x8c
        movk w1,#0xc000,lsl #16
        add x2,sp,#64
        mov w3,#1
        bl 0x377030
        cbnz w0,invalid
    original:
        ldp x2,x3,[sp,#48]
        ldp x0,x1,[sp,#32]
        ldp x19,x20,[sp,#16]
        ldp x29,x30,[sp],#80
        bl 0x2ac57c
        b 0x2198c8
    invalid:
        ldp x19,x20,[sp,#16]
        ldp x29,x30,[sp],#80
        mov w0,#-22
        b 0x2198c8
    ''')
    p.hook(0x2198c4,bridge)
    result=p.asm('decode_result_strength',f'''
        stp x29,x30,[sp,#-16]!
        mov x0,x19
        mov w1,#0x8c
        movk w1,#0xc000,lsl #16
        bl {lookup}
        mov w8,#0x6810
        lsl w8,w8,#16
        sub w8,w0,w8
        sub w9,w8,#1
        cmp w9,#29
        mov w9,#1
        csel w8,w8,w9,ls
        ldp x29,x30,[sp],#16
        str w8,[sp,#0xc]
        ldr x1,[x19]
        mov x0,x20
        b 0x243538
    ''')
    p.hook(0x24352c,result)
    append=p.asm('append_metadata_key','''
        stp x29,x30,[sp,#-112]!
        stp x19,x20,[sp,#16]
        stp x21,x22,[sp,#32]
        mov x29,sp
        mov x19,x0
        mov w20,w1
        mov w21,w2
        add x8,sp,#48
        bl 0x376fd0
        ldr x22,[sp,#64]
        ldr x10,[sp,#72]
        cmp x22,#1023
        b.hi invalid
        mov x9,xzr
    scan:
        cmp x9,x22
        b.hs allocate
        ldr w8,[x10,x9,lsl #2]
        cmp w8,w21
        b.eq exists
        add x9,x9,#1
        b scan
    allocate:
        sub sp,sp,#0x1000
        mov x9,xzr
    copy:
        cmp x9,x22
        b.hs append
        ldr w8,[x10,x9,lsl #2]
        str w8,[sp,x9,lsl #2]
        add x9,x9,#1
        b copy
    append:
        str w21,[sp,x22,lsl #2]
        mov x0,x19
        mov w1,w20
        mov x2,sp
        add x3,x22,#1
        bl 0x377030
        add sp,sp,#0x1000
        b done
    invalid:
        mov w0,#-22
        b done
    exists:
        mov w0,wzr
    done:
        ldp x21,x22,[sp,#32]
        ldp x19,x20,[sp,#16]
        ldp x29,x30,[sp],#112
        ret
    ''')
    static_source='''
        cbnz w0,done
        ldr w8,[x19,#0x20]
        mov w9,#0x3002
        cmp w8,w9
        b.ne done
        stp x29,x30,[sp,#-32]!
    '''
    for tag,value in [(0x40007,30),(0x40008,7)]:
        static_source+=f'''
        mov w8,#{value}
        str w8,[sp,#16]
        add x0,x19,#0x130
        mov w1,#{tag&65535}
        movk w1,#{tag>>16},lsl #16
        add x2,sp,#16
        mov w3,#1
        bl 0x377030
        cbnz w0,restore
        '''
    for tag,key in [(0xc000d,0x40006),(0xc000e,0x40006),(0xc000f,0x40007),(0xc000f,0x40008)]:
        static_source+=f'''
        add x0,x19,#0x130
        mov w1,#{tag&65535}
        movk w1,#{tag>>16},lsl #16
        mov w2,#{key&65535}
        movk w2,#{key>>16},lsl #16
        bl {append}
        cbnz w0,restore
        '''
    static_source+='''
    restore:
        ldp x29,x30,[sp],#32
    done:
        ldp x20,x19,[sp,#0x80]
        b 0x13f2ac
    '''
    p.hook(0x13f2a8,p.asm('single_characteristics',static_source))
    framework=p.finish()
    print(json.dumps({n:m['output_sha256'] for n,m in [('hal',hal),('framework',framework)]},indent=2))

if __name__=='__main__': build()
