from emulate_metadata import *
import lzma

def all_symbols(a):
    if '.gnu_debugdata' not in a.sections: return a.symbols
    sec=a.sections['.gnu_debugdata']; raw=lzma.decompress(a.data[sec.offset:sec.offset+sec.size]); mini=parse_elf(raw)
    if '.symtab' not in mini.sections: return a.symbols
    sy,st=mini.sections['.symtab'],mini.sections['.strtab']
    from mtkcam_raw.elf import Symbol
    results={s.name:s for s in a.symbols}
    for off in range(sy.offset,sy.offset+sy.size,sy.entsize):
        name,info,_,idx,va,size=struct.unpack_from('<IBBHQQ',raw,off)
        if not va or not name or not idx: continue
        pos=st.offset+name; n=raw[pos:raw.index(b'\0',pos)].decode()
        results[n]=Symbol(n,va,size,info)
    return list(results.values())

if __name__=='__main__':
    for p in [ROOT/'stock-binaries/libmtkcam_3rdparty.customer.so',*sorted((ROOT/'local-data/reference-modules').rglob('*customer.so'))]:
        a=parse_elf(p.read_bytes()); symbols=all_symbols(a)
        label=str(p.relative_to(ROOT)).replace('\\','__')
        (OUT/(label+'.all-symbols.json')).write_text(json.dumps([vars(s) for s in symbols],indent=2))
        print('\n',p.relative_to(ROOT),'all symbols',len(symbols))
        lines=[]
        for s in symbols:
            if s.is_function and any(t in s.name.lower() for t in ('negotiate','mfnr','remosaic')):
                lines+=['\n'+s.name]+disasm(a,s.value,s.size)
                if 'negotiate' in s.name: print(s.name,hex(s.value),s.size,'; '.join(disasm(a,s.value,min(s.size,12))))
        (OUT/(label+'.plugins.asm.txt')).write_text('\n'.join(lines))
