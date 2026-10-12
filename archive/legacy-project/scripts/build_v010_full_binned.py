"""Append full binned JPEG/YUV stream tuples to HI1631Q over verified v0.9."""
from build_raw_patch import *

DEST=ROOT/'patches/front-v0.10-full-binned'
ADDED=[33,2320,1744,0,33333333,33333333,35,2320,1744,0,33333333,0]
def build():
    a=parse_elf((ROOT/'patches/front-v0.9-reprocessing/libmtkcam_metastore.so').read_bytes())
    assert a.sha256=='dc18e2cdd107f4e56c98114a2de16592e275dd37e2bbd3960df7d12806d308d5'
    name='constructCustStaticMetadata_PLATFORM_PROJECT_SENSOR_DRVNAME_HI1631Q_MIPI_RAW'
    sym=next(s for s in a.symbols if s.name==name)
    before=emulate(a,sym,True);assert not before['error']
    assert before['metadata']['0xc000c']['values']==[0,1,2,5,6,3,4,7]
    stream=before['metadata']['0xd0012']
    tuples=[stream['values'][i:i+6] for i in range(0,len(stream['values']),6)]
    assert not any(t[:3] in ([33,2320,1744],[35,2320,1744]) for t in tuples)
    hook=int(stream['sites'][-1],16)
    helper=next(k for k,v in plt_symbols(a).items() if 'IEntry9push_backERKl' in v)
    assert a.data[hook:hook+4]==branch(hook,helper,True)
    rx=a.executable_load;start=(rx.p_offset+rx.p_filesz+15)&~15
    code=trampoline(start,helper,ADDED,False);end=start+len(code)
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
                assert new['metadata'][tag]['values']==old['metadata'][tag]['values']+(ADDED if tag=='0xd0012' else [])
        else:assert old==new,s.name
        checked+=1
    replay=bytearray(a.data)
    for c in changes:
        off=int(c['offset'],16);new=bytes.fromhex(c['new'])
        assert replay[off:off+len(new)]==bytes.fromhex(c['old'])
        replay[off:off+len(new)]=new
    assert replay==b
    DEST.mkdir(exist_ok=True)
    (DEST/'libmtkcam_metastore.so').write_bytes(b)
    (DEST/'libmtkcam_pipelinepolicy.so').write_bytes((ROOT/'patches/front-v0.9-reprocessing/libmtkcam_pipelinepolicy.so').read_bytes())
    manifest=dict(input_sha256=a.sha256,output_sha256=out.sha256,changes=changes,constructors_verified=checked,
        scope='HI1631Q: append JPEG/YUV 2320x1744; original HAL derives PRIVATE and reprocessing inputs',
        added_tuples=[ADDED[:6],ADDED[6:]],hardware_validated=False,hook=hex(hook),cave_start=hex(start),cave_end=hex(end))
    (DEST/'full-binned-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (DEST/'full-binned.asm.txt').write_text('\n'.join(disasm(out,start,len(code))))
    print(json.dumps({k:v for k,v in manifest.items() if k!='changes'},indent=2))
    return manifest
if __name__=='__main__':build()
