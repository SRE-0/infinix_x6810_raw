from emulate_metadata import *
data=json.loads((OUT/'constructor-metadata.json').read_text())
for file in data:
    print('\n'+file['path'])
    for r in file['constructors']:
        if r['name'].endswith(('S5KGM1ST_MIPI_RAW','OV08A10_MIPI_RAW','OV16B10FF_MIPI_RAW')):
            print(r['name'],r['va'])
            for k,e in r['metadata'].items():
                print(k, e['values'])
                if k=='0xc000c': print('sites',e['sites'])
a=parse_elf((ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes())
plt=plt_symbols(a)
(OUT/'original-plt.json').write_text(json.dumps({hex(k):v for k,v in plt.items()},indent=2))
for s in a.symbols:
    if s.name.startswith('constructCustStaticMetadata_PLATFORM_PRO_OVERWRITE_') and s.name.endswith(('S5KGM1ST_MIPI_RAW','OV08A10_MIPI_RAW','OV16B10FF_MIPI_RAW')):
        print(s.name,hex(s.value),emulate(a,s))
for s in a.symbols:
    if s.name.endswith('updateDataERN5NSCam9IMetadataE') and 'MetadataProvider' in s.name:
        lines=disasm(a,s.value,s.size)
        for j,line in enumerate(lines):
            if '#3' in line and ('cmp ' in line or 'mov ' in line):
                print('\n'.join(lines[max(0,j-5):j+9]))
