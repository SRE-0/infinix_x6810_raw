from emulate_metadata import *
for p in sorted((ROOT/'local-data/reference-modules').rglob('*metastore.so')):
    if 'Hot10s' not in str(p) and 'Camon' not in str(p): continue
    a=parse_elf(p.read_bytes()); print('\n',p)
    s=next(s for s in a.symbols if s.name=='constructCustStaticMetadata_PLATFORM_PROJECT_SENSOR_DRVNAME_S5KGM1ST_MIPI_RAW')
    print('\n'.join(disasm(a,s.value+0x80,0x130)))
for p in [ROOT/'stock-binaries/libmtkcam_3rdparty.customer.so',*sorted((ROOT/'local-data/reference-modules').rglob('*customer.so'))]:
    a=parse_elf(p.read_bytes()); print('\n',p)
    for s in a.symbols:
        if s.is_function and any(t in s.name for t in ('negotiate','property')):
            print(s.name,hex(s.value),s.size)
            print('\n'.join(disasm(a,s.value,min(20,s.size))))
og=parse_elf((ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes())
for s in og.symbols:
    if 'PLATFORM_CUSTOM_' in s.name and s.name.endswith(('S5KGM1ST_MIPI_RAW','OV08A10_MIPI_RAW','OV16B10FF_MIPI_RAW')):
        print(s.name,hex(s.value)); print(emulate(og,s))
