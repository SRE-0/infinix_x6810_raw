from analyze_binaries import *
for p in [ROOT/'stock-binaries/libmtkcam_metastore.so', *sorted((ROOT/'local-data/reference-modules').rglob('*metastore.so'))]:
    a=parse_elf(p.read_bytes())
    print('\nFILE',p.relative_to(ROOT))
    for s in a.symbols:
        if 'updateRawCapability' in s.name:
            print(s.name,hex(s.value),s.size)
            print('\n'.join(disasm(a,s.value+0x50, min(0x64,s.size-0x50))))
    for s in a.symbols:
        if s.name=='constructCustStaticMetadata_COMMON_SCALER_COMMON':
            lines=disasm(a,s.value,s.size)
            for i,line in enumerate(lines):
                if 'cbz ' in line or 'nop ' in line:
                    if i<160: print('\n'.join(lines[max(0,i-6):i+8]))
