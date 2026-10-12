"""Diagnostic pair: reduce only HI1631Q square YUV and retain policy size checks.

Not a universal RAW fix: other large processed+small RAW combinations remain
unsupported. Does not modify originals or the v0.7 release.
"""
from build_raw_patch import *
from build_v07_sensor_policy import build as build_policy

DEST = ROOT/'patches/front-v0.8-trial'

def main():
    DEST.mkdir(exist_ok=True)
    source = ROOT/'patches/front-v0.7/libmtkcam_metastore.so'
    a = parse_elf(source.read_bytes())
    assert a.sha256 == '2b3bca8dfa83ea01c3f210b1b187c173a453665f3373afe9e8d17614b0fe95df'
    b = bytearray(a.data)
    start = (a.executable_load.p_offset+a.executable_load.p_filesz+15)&~15
    code = mov32(8,1728)+word(0xf9000028)+branch(start+8,0xbbcb0)
    end = start+len(code)
    assert not any(a.data[start:end])
    assert end <= min(p.p_offset for p in a.load_segments if p.p_offset>a.executable_load.p_offset)
    for sec in a.sections.values():
        assert not (sec.size and sec.offset<end and start<sec.offset+sec.size)
    changes=[]
    def change(off,new):
        changes.append(dict(offset=hex(off),old=a.data[off:off+len(new)].hex(),new=new.hex()))
        b[off:off+len(new)]=new
    for hook in (0x4e648,0x4e658):
        assert a.data[hook:hook+4]==branch(hook,0xbbcb0,True)
        change(hook,branch(hook,start,True))
    change(start,code)
    ph=struct.unpack_from('<Q',b,32)[0]+a.executable_load.index*struct.unpack_from('<H',b,54)[0]
    for field in (32,40):change(ph+field,struct.pack('<Q',end-a.executable_load.p_offset))
    patched=parse_elf(bytes(b)); checked=0
    for s in a.symbols:
        if not s.name.startswith('constructCustStaticMetadata_PLATFORM_PROJECT_'):continue
        x,y=emulate(a,s,True),emulate(patched,s,True)
        assert not x['error'] and not y['error']
        expected={k:v['values'][:] for k,v in x['metadata'].items()}
        if s.name.endswith('SENSOR_DRVNAME_HI1631Q_MIPI_RAW'):
            assert expected['0xd0012'][42:48]==[35,3456,3456,0,33333333,0]
            expected['0xd0012'][43:45]=[1728,1728]
        assert expected=={k:v['values'] for k,v in y['metadata'].items()},s.name
        checked+=1
    (DEST/'libmtkcam_metastore.so').write_bytes(b)
    (DEST/'metastore-manifest.json').write_text(json.dumps(dict(input_sha256=a.sha256,
        output_sha256=patched.sha256,changes=changes,constructors_verified=checked,
        scope='HI1631Q YUV square 3456 -> 1728 only',hardware_test=False),indent=2))
    build_policy(preserve_size_checks=True,destination=DEST)
    print('PASS',checked,'constructors;',patched.sha256)

if __name__=='__main__':main()
