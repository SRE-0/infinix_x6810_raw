"""Check the binary guard against the actual normalization block in Unicorn."""
from probe_raw_size_update import probe, ROOT, OUT
from package_compatible_modules import registry
from emulate_metadata import parse_elf, emulate
import json

registry()  # independent stock-preimage/manifest replay and output hashes
data=(ROOT/'patches/front-v0.7/libmtkcam_metastore.so').read_bytes()
cases=[]
for active,raw in [((4640,3488),(2320,1744)),((4640,3488),(4640,3488)),
                   ((4000,3000),(4000,3000)),((3264,2448),(3264,2448)),
                   ((4608,3456),(2320,1744)),((4640,3456),(2320,1744)),
                   ((4640,3488),(2321,1744)),((4640,3488),(2320,1745))]:
    original=[33,640,480,0,0,0,32,*raw,0,33333333,33333333]
    keep=active==(4640,3488) and raw==(2320,1744)
    result=probe(*active,original=original,image_data=data,preserve_binned=keep)
    result['guard_taken']=keep;cases.append(result)
a=parse_elf((ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes());b=parse_elf(data)
m=json.loads((ROOT/'patches/front-v0.7/patch-manifest.json').read_text())
targets={t['symbol']:t for t in m['targets']}
constructors=0
for s in a.symbols:
    if not s.name.startswith('constructCustStaticMetadata_PLATFORM_PROJECT_'):continue
    x,y=emulate(a,s,True),emulate(b,s,True)
    assert not x['error'] and not y['error']
    if s.name not in targets:assert x==y
    else:
        assert x['metadata'].keys()==y['metadata'].keys()
        for tag,entry in x['metadata'].items():
            suffix=[3] if tag=='0xc000c' else targets[s.name]['raw_stream'] if tag=='0xd0012' else []
            assert y['metadata'][tag]['values']==entry['values']+suffix
    constructors+=1
baseline=(ROOT/'patches/aux-v0.2/libmtkcam_metastore.so').read_bytes()
for target in m['targets'][:2]:
    for h in target['hooks']:
        for offset,size in [(int(h['offset'],16),4),(int(h['destination'],16),h['trampoline_size'])]:
            assert data[offset:offset+size]==baseline[offset:offset+size]
assert data[0xb9804:0xb9808]==a.data[0xb9804:0xb9808]
report=dict(normalization_cases=cases,constructors=constructors,rear_patch_bytes_preserved=True,
            no_template_request_hook=True,hardware_test=False,
            limitation='Does not emulate the complete provider, sensor policy, P1 or DNG writer')
(ROOT/'dist/verification/front-v0.7.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: 8 normalization cases,',constructors,'constructors, stock manifest replay, rear bytes and request hook')
