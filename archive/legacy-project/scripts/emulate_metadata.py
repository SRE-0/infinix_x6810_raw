"""Execute AArch64 constructors with simulated IMetadata calls, never camera hardware.
This verifies encoded constants and control flow, not actual RAW capture support.
"""
from analyze_binaries import *
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

def plt_symbols(a):
    ds,st,rp,plt=[a.sections[n] for n in ('.dynsym','.dynstr','.rela.plt','.plt')]
    out={}
    for j in range(rp.size//24):
        _,info,_=struct.unpack_from('<QQq',a.data,rp.offset+j*24)
        k=struct.unpack_from('<I',a.data,ds.offset+(info>>32)*24)[0]+st.offset
        out[plt.addr+32+j*16]=a.data[k:a.data.index(b'\0',k)].decode()
    return out

def emulate(a,s, clobber=False, initial=None):
    u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
    u.mem_map(0,0x200000)
    for ph in a.load_segments: u.mem_write(ph.p_vaddr,a.data[ph.p_offset:ph.p_offset+ph.p_filesz])
    u.mem_map(0x1000000,0x200000)
    u.reg_write(UC_ARM64_REG_SP,0x1100000)
    u.reg_write(UC_ARM64_REG_TPIDR_EL0,0x1000000)
    u.reg_write(UC_ARM64_REG_X0,0x1001000)
    u.reg_write(UC_ARM64_REG_X1,0x1002000)
    u.reg_write(UC_ARM64_REG_LR,0x1ff000)
    plt=plt_symbols(a); entries={}; result=dict(initial or {}); calls=[]
    def hook(uc,pc,size,unused):
        if pc not in plt: return
        name=plt[pc]
        x=[uc.reg_read(r) for r in (UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2)]
        ret=0
        calls.append((hex(pc),name))
        if 'IMetadata8entryFor' in name:
            dest=uc.reg_read(UC_ARM64_REG_X8)
            src=result.get(hex(x[1]),dict(tag=x[1],values=[],sites=[]))
            entries[dest]=dict(tag=src['tag'],values=list(src['values']),sites=list(src.get('sites',[])))
        elif 'IMetadata6IEntryC' in name and name.endswith('Ej'):
            entries[x[0]]={'tag':x[1], 'values':[], 'sites':[]}
        elif 'IMetadata6IEntry9push_back' in name:
            n=1 if 'Type2TypeIh' in name else 8 if 'Type2TypeIx' in name or 'Type2TypeIl' in name else 4
            value=int.from_bytes(uc.mem_read(x[1],n),'little')
            entries[x[0]]['values'].append(value)
            entries[x[0]]['sites'].append(hex(uc.reg_read(UC_ARM64_REG_LR)-4))
        elif 'IMetadata6IEntry3tag' in name:
            ret=entries[x[0]]['tag']
        elif 'IMetadata6IEntry5count' in name:
            ret=len(entries[x[0]]['values'])
        elif 'IMetadata6IEntry7isEmpty' in name:
            ret=int(not entries[x[0]]['values'])
        elif 'IMetadata6IEntry6itemAt' in name:
            ret=entries[x[0]]['values'][x[1]]
        elif 'IMetadata6update' in name:
            result[hex(x[1])]=dict(entries[x[2]])
        elif 'IMetadata6IEntryD' in name: pass
        elif '__stack_chk_fail' in name: raise RuntimeError('Stack canary failed')
        else: raise RuntimeError('Unmodelled external call: '+name)
        if clobber:
            for reg in range(1,18):
                uc.reg_write(globals()['UC_ARM64_REG_X'+str(reg)],0xDEAD0000+reg*0x100)
        uc.reg_write(UC_ARM64_REG_X0,ret)
        uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_LR))
    u.hook_add(UC_HOOK_CODE,hook)
    error=None
    try:
        u.emu_start(s.value,0x1ff000,count=100000)
        if u.reg_read(UC_ARM64_REG_PC)!=0x1ff000: error='Instruction budget exceeded'
    except Exception as e: error=str(e)+' at '+hex(u.reg_read(UC_ARM64_REG_PC))
    return dict(name=s.name,va=hex(s.value),metadata=result,error=error)

def run():
    allresults=[]
    for folder in ('stock-binaries','local-data/reference-modules'):
        for p in sorted((ROOT/folder).rglob('*metastore.so')):
            a=parse_elf(p.read_bytes())
            results=[emulate(a,s) for s in a.symbols if s.name.startswith('constructCustStaticMetadata_PLATFORM_PROJECT_')]
            allresults.append(dict(path=str(p.relative_to(ROOT)),constructors=results))
            print('\n',p.relative_to(ROOT))
            for r in results:
                caps=r['metadata'].get('0xc000c',{}).get('values')
                if r['error'] or any(t in r['name'] for t in ('S5KGM1ST','OV08A10','OV16B10','S5KJN1')):
                    print(r['name'],caps,r['error'])
            print('constructors',len(results),'RAW constructors',sum(3 in r['metadata'].get('0xc000c',{}).get('values',[]) for r in results))
            (OUT/(p.parent.parent.parent.parent.name+'-'+p.name+'.plt.json')).write_text(json.dumps({hex(k):v for k,v in plt_symbols(a).items()},indent=2))
    (OUT/'constructor-metadata.json').write_text(json.dumps(allresults,indent=2))
if __name__=='__main__': run()
