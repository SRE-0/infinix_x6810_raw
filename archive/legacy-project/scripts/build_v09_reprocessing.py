"""Enable existing MTK reprocessing metadata path only for HI1631Q over v0.8."""
from build_raw_patch import *

DEST=ROOT/'patches/front-v0.9-reprocessing'
def build():
    a=parse_elf((ROOT/'patches/front-v0.8-binned/libmtkcam_metastore.so').read_bytes())
    assert a.sha256=='00066e79cbeb0020d09e8e1fb43670cde08ef30133bd0d86a138609fb561e4a6'
    name='constructCustStaticMetadata_PLATFORM_PROJECT_SENSOR_DRVNAME_HI1631Q_MIPI_RAW'
    sym=next(s for s in a.symbols if s.name==name)
    before=emulate(a,sym,True);assert not before['error']
    caps=before['metadata']['0xc000c'];assert caps['values']==[0,1,2,5,6,3]
    hook=int(caps['sites'][-1],16)
    helper=next(k for k,v in plt_symbols(a).items() if 'IEntry9push_backERKh' in v)
    assert a.data[hook:hook+4]==branch(hook,helper,True)
    rx=a.executable_load;start=(rx.p_offset+rx.p_filesz+15)&~15
    code=trampoline(start,helper,[4,7],True);end=start+len(code)
    assert not any(a.data[start:end])
    assert end<=min(p.p_offset for p in a.load_segments if p.p_offset>rx.p_offset)
    for s in a.sections.values():assert not(s.size and s.offset<end and start<s.offset+s.size)
    b=bytearray(a.data);changes=[]
    def change(off,new):
        changes.append(dict(offset=hex(off),old=a.data[off:off+len(new)].hex(),new=new.hex()))
        b[off:off+len(new)]=new
    change(hook,branch(hook,start,True));change(start,code)
    ph=struct.unpack_from('<Q',b,32)[0]+rx.index*struct.unpack_from('<H',b,54)[0]
    for field in (32,40):change(ph+field,struct.pack('<Q',end-rx.p_offset))
    out=parse_elf(bytes(b));checked=0
    for s in a.symbols:
        if not s.name.startswith('constructCustStaticMetadata_PLATFORM_PROJECT_'):continue
        old,new=emulate(a,s,True),emulate(out,s,True)
        assert not old['error'] and not new['error']
        if s.name==name:
            assert old['metadata'].keys()==new['metadata'].keys()
            for tag in old['metadata']:
                assert new['metadata'][tag]['values']==old['metadata'][tag]['values']+([4,7] if tag=='0xc000c' else [])
        else:assert old==new,s.name
        checked+=1
    DEST.mkdir(exist_ok=True)
    (DEST/'libmtkcam_metastore.so').write_bytes(b)
    (DEST/'libmtkcam_pipelinepolicy.so').write_bytes((ROOT/'patches/front-v0.8-binned/libmtkcam_pipelinepolicy.so').read_bytes())
    manifest=dict(input_sha256=a.sha256,output_sha256=out.sha256,changes=changes,constructors_verified=checked,
        scope='HI1631Q only: append PRIVATE_REPROCESSING=4, YUV_REPROCESSING=7; existing updateReprocessCapabilities generates dependent metadata',
        hardware_validated=False,hook=hex(hook),cave_start=hex(start),cave_end=hex(end))
    (DEST/'reprocessing-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (DEST/'reprocessing.asm.txt').write_text('\n'.join(disasm(out,start,len(code))))
    print(json.dumps(manifest,indent=2))
    return manifest
if __name__=='__main__':build()
