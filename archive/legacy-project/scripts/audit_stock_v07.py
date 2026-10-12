"""Exhaustive byte diff and bounded execution checks of stock versus v0.7.

Reads binaries, writes dist/analysis/stock-v07-comparison only.
No build, installation, property changes, ADB, or real camera execution.
"""
import hashlib
import json
import random
import struct
import zipfile
from analyze_binaries import ROOT, parse_elf, disasm
from emulate_metadata import emulate, plt_symbols
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn import arm64_const as reg

OUT = ROOT / 'dist/analysis/stock-v07-comparison'
STOCK = ROOT / 'stock-binaries/libmtkcam_metastore.so'
PATCH = ROOT / 'patches/front-v0.7/libmtkcam_metastore.so'
SP = 0x1100000
STOP = 0x1ff000


def sha(b):
    return hashlib.sha256(b).hexdigest()


def machine(a):
    u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    u.mem_map(0, 0x200000)
    for p in a.load_segments:
        u.mem_write(p.p_vaddr, a.data[p.p_offset:p.p_offset+p.p_filesz])
    u.mem_map(0x1000000, 0x200000)
    u.reg_write(reg.UC_ARM64_REG_SP, SP)
    u.reg_write(reg.UC_ARM64_REG_LR, STOP)
    return u


def poison(u, seed):
    # Simulate legitimate destruction of caller-saved values at external calls.
    for n in range(18):
        u.reg_write(getattr(reg, 'UC_ARM64_REG_X'+str(n)), 0xDEAD00000000+seed*256+n)
    for n in [*range(8), *range(16,32)]:
        u.reg_write(getattr(reg, 'UC_ARM64_REG_Q'+str(n)), (1 << 100)+seed+n)
    u.reg_write(reg.UC_ARM64_REG_NZCV, (seed % 16) << 28)


def abi_case(a, h, values, seed):
    u = machine(a)
    rng = random.Random(seed)
    saved = {n:rng.getrandbits(64) for n in range(18,30)}
    for n,v in saved.items():
        u.reg_write(getattr(reg, 'UC_ARM64_REG_X'+str(n)), v)
    simd = {n:rng.getrandbits(128) for n in range(8,16)}
    for n,v in simd.items():
        u.reg_write(getattr(reg, 'UC_ARM64_REG_Q'+str(n)), v)
    before = b'\xa5'*64
    u.mem_write(SP, before)
    u.mem_write(SP-96, b'\x5a'*64)
    original = 0x6e if len(values)==1 else 0x1122334455667788
    u.mem_write(0x1004000, struct.pack('<Q', original))
    u.reg_write(reg.UC_ARM64_REG_X0, 0x1003000)
    u.reg_write(reg.UC_ARM64_REG_X1, 0x1004000)
    helper = int(h['helper'],16)
    observed = []
    def call(uc, pc, size, _):
        if pc != helper:
            return
        assert uc.reg_read(reg.UC_ARM64_REG_SP) == SP-32
        assert uc.reg_read(reg.UC_ARM64_REG_SP) % 16 == 0
        assert uc.reg_read(reg.UC_ARM64_REG_X0) == 0x1003000
        ptr = uc.reg_read(reg.UC_ARM64_REG_X1)
        observed.append(int.from_bytes(uc.mem_read(ptr,1 if len(values)==1 else 8),'little'))
        lr = uc.reg_read(reg.UC_ARM64_REG_LR)
        poison(uc, seed+len(observed))
        uc.reg_write(reg.UC_ARM64_REG_X0, 0xACED+len(observed))
        uc.reg_write(reg.UC_ARM64_REG_PC, lr)
    u.hook_add(UC_HOOK_CODE, call)
    u.emu_start(int(h['destination'],16), STOP, count=1000)
    assert u.reg_read(reg.UC_ARM64_REG_PC) == STOP
    assert observed == [original]+values
    assert u.reg_read(reg.UC_ARM64_REG_SP) == SP
    assert u.reg_read(reg.UC_ARM64_REG_LR) == STOP
    assert bytes(u.mem_read(SP,64)) == before
    assert bytes(u.mem_read(SP-96,64)) == b'\x5a'*64
    for n,v in saved.items():
        assert u.reg_read(getattr(reg,'UC_ARM64_REG_X'+str(n))) == v
    for n,v in simd.items():
        assert u.reg_read(getattr(reg,'UC_ARM64_REG_Q'+str(n))) == v
    return dict(destination=h['destination'], seed=seed, values=observed,
        stack_restored=True, callee_saved_preserved=True, original_push_preserved=True)


def normalization(a, active, values, log_level):
    u = machine(a)
    u.reg_write(reg.UC_ARM64_REG_X19,0x1001000)
    u.reg_write(reg.UC_ARM64_REG_X25,0x1003000)
    u.mem_write(0x1003000,struct.pack('<I',log_level))
    u.mem_write(SP+0x18,struct.pack('<II',active[1],active[0]))
    # Exercise the simple Android logging branch, but keep vendor virtual logger off.
    u.mem_write(0xbdaf8,struct.pack('<Q',0x1005000))
    u.mem_write(0x1005000,struct.pack('<I',1))
    entries = {}; result = {}; calls = []; replacements = []
    plt = plt_symbols(a)
    def hook(uc,pc,size,_):
        if pc not in plt:
            return
        name=plt[pc]; x=[uc.reg_read(getattr(reg,'UC_ARM64_REG_X'+str(n))) for n in range(3)]
        lr=uc.reg_read(reg.UC_ARM64_REG_LR); ret=0
        calls.append(name)
        if 'IMetadata8entryFor' in name:
            assert x[1]==0xd000a
            entries[uc.reg_read(reg.UC_ARM64_REG_X8)]=list(values)
        elif 'IEntry5count' in name: ret=len(entries[x[0]])
        elif 'IEntry6itemAt' in name: ret=entries[x[0]][x[1]]
        elif 'IEntry13replaceItemAt' in name:
            v=int.from_bytes(uc.mem_read(x[2],4),'little')
            entries[x[0]][x[1]]=v; replacements.append([x[1],v])
        elif 'IEntry3tag' in name: ret=0xd000a
        elif 'IMetadata6update' in name: result[x[1]]=list(entries[x[2]])
        elif name=='__android_log_print': pass
        else: raise RuntimeError('Unmodelled '+name)
        poison(uc,len(calls))
        uc.reg_write(reg.UC_ARM64_REG_X0,ret)
        uc.reg_write(reg.UC_ARM64_REG_PC,lr)
    u.hook_add(UC_HOOK_CODE,hook)
    u.emu_start(0x7d1dc,0x7d4d4,count=10000)
    assert u.reg_read(reg.UC_ARM64_REG_PC)==0x7d4d4
    return dict(after=result.get(0xd000a,values), updated=bool(result), replacements=replacements,
        log_calls=calls.count('__android_log_print'))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    stock=STOCK.read_bytes(); patch=PATCH.read_bytes()
    assert sha(stock)=='dbd740c5c7ba3081fb9d38b68b2f9975e19d6faad41dd5f87ce75f3c7d7be485'
    assert sha(patch)=='2b3bca8dfa83ea01c3f210b1b187c173a453665f3373afe9e8d17614b0fe95df'
    assert len(stock)==len(patch)==784232
    a,b=parse_elf(stock),parse_elf(patch)
    manifest=json.loads((PATCH.parent/'patch-manifest.json').read_text())
    changed=[i for i in range(len(stock)) if stock[i]!=patch[i]]
    spans=[]
    for i in changed:
        if spans and spans[-1][1]==i: spans[-1][1]+=1
        else: spans.append([i,i+1])
    (OUT/'byte-diff.json').write_text(json.dumps([dict(start=hex(lo),end_exclusive=hex(hi),
        old=stock[lo:hi].hex(),new=patch[lo:hi].hex()) for lo,hi in spans],indent=2))
    covered=set(); replay=bytearray(stock); regions=[]
    for c in manifest['changes']:
        off=int(c['offset'],16); old=bytes.fromhex(c['old']); new=bytes.fromhex(c['new'])
        assert len(old)==len(new) and stock[off:off+len(old)]==old
        extent=set(range(off,off+len(new)))
        assert not covered & extent
        covered |= extent; replay[off:off+len(new)]=new
        regions.append(dict(offset=c['offset'],length=len(new),changed_bytes=sum(x!=y for x,y in zip(old,new)),
            reason=c['reason'],before=disasm(a,off,4) if len(new)==4 else [],after=disasm(b,off,4) if len(new)==4 else []))
    assert bytes(replay)==patch and set(changed)<=covered
    headers=[]
    for x,y in zip(a.phdrs,b.phdrs):
        differences={k:[vars(x)[k],vars(y)[k]] for k in vars(x) if vars(x)[k]!=vars(y)[k]}
        if differences: headers.append(dict(index=x.index,changes=differences))
    assert len(headers)==1 and set(headers[0]['changes'])=={'p_filesz','p_memsz'}
    assert stock[:64]==patch[:64]
    assert a.sections==b.sections
    sections=[]
    for name,s in a.sections.items():
        if s.sh_type==8: continue  # NOBITS has no payload in the file.
        original=stock[s.offset:s.offset+s.size]; modified=patch[s.offset:s.offset+s.size]
        sections.append(dict(name=name,bytes=s.size,identical=original==modified,
            changed_bytes=sum(x!=y for x,y in zip(original,modified))))
    assert [x['name'] for x in sections if not x['identical']]==['.text']
    start,end=0xbc530,0xbc7a8
    assert not any(stock[start:end])
    assert all(s.sh_type==8 or not(s.size and s.offset<end and start<s.offset+s.size) for s in a.sections.values())
    assert b.executable_load.p_vaddr+b.executable_load.p_memsz==end
    assert (end+4095)&~4095 == 0xbd000
    abi=[]; asm=[]
    for t in manifest['targets']:
        for j,h in enumerate(t['hooks']):
            values=[3] if j==0 else t['raw_stream']
            helper=plt_symbols(a)[int(h['helper'],16)]
            assert 'IEntry9push_back' in helper
            for seed in [0,17,65535]: abi.append(abi_case(b,h,values,seed))
            asm += [t['sensor']+' '+helper]+disasm(b,int(h['destination'],16),h['trampoline_size'])
    asm += ['NORMALIZATION GUARD']+disasm(b,0xbc764,68)
    (OUT/'injected-code.asm.txt').write_text('\n'.join(asm)+'\n')
    constructors=[]
    targets={t['symbol']:t for t in manifest['targets']}
    for s in a.symbols:
        if not s.name.startswith('constructCustStaticMetadata_PLATFORM_PROJECT_'): continue
        x,y=emulate(a,s,True),emulate(b,s,True)
        assert x['error'] is None and y['error'] is None
        xm={k:v['values'] for k,v in x['metadata'].items()}; ym={k:v['values'] for k,v in y['metadata'].items()}
        expected={k:list(v) for k,v in xm.items()}
        if s.name in targets:
            expected['0xc000c'] += [3]; expected['0xd0012'] += targets[s.name]['raw_stream']
        assert expected==ym
        constructors.append(dict(symbol=s.name,changed_tags=[k for k in xm if xm[k]!=ym[k]],before=xm,after=ym))
    cases=[]
    raw=[32,2320,1744,0,33333333,33333333]; jpeg=[33,640,480,0,50000000,0]
    inputs=[[],jpeg,raw,jpeg+raw,raw+jpeg,
        raw+[32,4640,3488,0,100000000,33333333],
        [32,4640,3488,0,100000000,33333333]+raw,
        [32,2321,1744,0,33333333,33333333],
        [32,2320,1745,0,33333333,33333333],
        [32,4000,3000,0,50000000,33333333],
        [32,3264,2448,0,33333333,33333333],
        [32,2320,1744,1,33333333,33333333]]
    for active in [(4640,3488),(4640,3487),(4639,3488),(4000,3000),(3264,2448)]:
        for data in inputs:
            for log_level in [0,2]:
                x=normalization(a,active,data,log_level); y=normalization(b,active,data,log_level)
                first=next((i for i in range(0,len(data),6) if data[i]==32),None)
                match=first is not None and data[first+1:first+3]==[2320,1744] and active==(4640,3488)
                expected=data[:] if match else x['after']
                assert y['after']==expected
                if not match: assert x==y
                cases.append(dict(active=active,before=data,log_level=log_level,guard_match=match,stock=x,v07=y))
    packages=[]
    for p in sorted((ROOT/'dist').rglob('*v0.7*.zip')):
        with zipfile.ZipFile(p) as z:
            libs={n:sha(z.read(n)) for n in z.namelist() if n.endswith('.so')}
            assert libs=={'system/vendor/lib64/libmtkcam_metastore.so':sha(patch)}
            packages.append(dict(path=str(p.relative_to(ROOT)),libs=libs))
    module=ROOT/'archive/modules/x6810_raw_v07/system/vendor/lib64/libmtkcam_metastore.so'
    assert module.read_bytes()==patch
    report=dict(input_sha256=sha(stock),output_sha256=sha(patch),size=len(stock),
        changed_bytes=len(changed),contiguous_changed_spans=len(spans),regions=regions,
        program_header_changes=headers,sections=sections,cave_bytes=end-start,
        elf_header_identical=True,section_headers_identical=True,no_unaccounted_changes=True,
        abi_cases=abi,normalization_cases=cases,project_constructors=len(constructors),
        modified_project_constructors=sum(bool(x['changed_tags']) for x in constructors),packages=packages,
        limitations=['External IMetadata calls are simulated; no allocation/OOM/exception test',
            'Normalization starts after active rectangle acquisition, not at provider entry',
            'Two log levels, simple Android logger branch; vendor virtual logger not exercised',
            'No sensor, P1, ISP, gralloc, linker or app executed',
            'Guard keys dimensions, not camera identity or input/output direction'])
    (OUT/'constructors.json').write_text(json.dumps(constructors,indent=2))
    (OUT/'audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:report[k] for k in ['size','changed_bytes','contiguous_changed_spans','program_header_changes','cave_bytes','project_constructors','modified_project_constructors']},indent=2))
    print('PASS:',len(abi),'ABI cases;',len(cases),'normalization comparisons;',len(packages),'ZIPs')


if __name__=='__main__':
    main()
