"""Reproducible read-only input audit; writes only dist/analysis/audit-v07.

No ADB, module build, property changes or device access. Log event cadence is
not sensor FPS. Donor ELF differences are not stock-to-mod patch attribution.
"""
from pathlib import Path
import collections
import hashlib
import json
import re
import statistics
import zipfile
import array
import struct
import sys
from analyze_binaries import parse_elf, disasm
from emulate_metadata import emulate
from inspect_debugdata import all_symbols

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist/analysis/audit-v07'


def digest(b):
    return hashlib.sha256(b).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p = ROOT / 'local-data/logs/test-mgc-gcam-sensor-frontal-negro.log'
    lines = p.read_text(encoding='utf-8').splitlines()
    records = []
    for n, line in enumerate(lines, 1):
        m = re.match(r'^(\d+\.\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([VDIWEF])\s+([^:]+):\s?(.*)$', line)
        if m:
            t, uid, pid, tid, severity, tag, message = m.groups()
            records.append(dict(line=n, time=float(t), uid=uid, pid=pid, tid=tid,
                                severity=severity, tag=tag.strip(), message=message))
    terms = ['onCaptureFailed', 'onBufferLost', 'unlock(', 'unlocked buffer',
             'FATAL EXCEPTION', 'Fatal signal', 'enqueue_img_stride',
             'determineScenRaw16', 'ERROR_CAMERA', '[CMDQ][ERR]clt', 'CameraDevice was already closed',
             'Session has been closed', 'execmod', 'FIX_SENSOR_INFO', 'RAW_SENSORw2320']
    selected = [r for r in records if any(t in r['message'] or t in r['tag'] for t in terms)]
    cadence = [r['time'] for r in records if r['tag'] == 'Gralloc4' and 'unlock(' in r['message']
               and 1789409827.8 <= r['time'] <= 1789409830.15]
    gaps = [1000*(b-a) for a,b in zip(cadence,cadence[1:])]
    log = dict(path=str(p.relative_to(ROOT)), sha256=digest(p.read_bytes()), lines=len(lines),
               parsed=len(records), pids=dict(collections.Counter(r['pid'] for r in records)),
               uids=dict(collections.Counter(r['uid'] for r in records)),
               seconds=max(r['time'] for r in records)-min(r['time'] for r in records),
               counts={t:sum(t in line for line in lines) for t in terms},
               gralloc_event_cadence=dict(events=len(cadence), median_ms=statistics.median(gaps),
                  mean_ms=statistics.mean(gaps), warning='App unlock error cadence, not measured camera FPS'),
               events=selected)
    (OUT/'log.json').write_text(json.dumps(log, indent=2), encoding='utf-8')
    inventory=[]; constructors=[]; customer_functions=[]
    for folder in ['stock-binaries', 'local-data/reference-modules', 'patches/front-v0.7']:
        for p in sorted((ROOT/folder).rglob('*.so')):
            b=p.read_bytes(); a=parse_elf(b)
            row=dict(path=str(p.relative_to(ROOT)), bytes=len(b), sha256=digest(b))
            inventory.append(row)
            if p.name.endswith('customer.so'):
                for s in all_symbols(a):
                    if s.is_function and ('9negotiateE' in s.name or 'customer_get_' in s.name):
                        customer_functions.append(dict(path=row['path'], symbol=s.name,
                            va=hex(s.value), size=s.size, entry=disasm(a,s.value,min(s.size,16))))
            if p.name != 'libmtkcam_metastore.so':
                continue
            for s in a.symbols:
                if (s.name.startswith('constructCustStaticMetadata_PLATFORM_PROJECT_')
                    and s.name.endswith('_MIPI_RAW')
                    and (any(x in s.name for x in ['HI1631Q','S5KGM1ST','OV08A10']) or 'a32_' in str(p))):
                    e=emulate(a,s,True)
                    constructors.append(dict(path=row['path'], symbol=s.name, va=hex(s.value),
                       error=e['error'], capabilities=e['metadata'].get('0xc000c'),
                       streams=e['metadata'].get('0xd0012')))
    payload='system/vendor/lib64/libmtkcam_metastore.so'
    archives=[]
    for p in sorted((ROOT/'dist').rglob('*v0.7*.zip')):
        with zipfile.ZipFile(p) as z:
            archives.append(dict(path=str(p.relative_to(ROOT)), sha256=digest(p.read_bytes()),
                 libs={n:digest(z.read(n)) for n in z.namelist() if n.endswith('.so')},
                 system_prop=z.read('system.prop').decode() if 'system.prop' in z.namelist() else None))
    policies=[]
    for p in [ROOT/'stock-binaries/libmtkcam_pipelinepolicy.so',
              ROOT/'patches/front-v0.7/libmtkcam_pipelinepolicy.so']:
        a=parse_elf(p.read_bytes())
        policies += [str(p.relative_to(ROOT)),*disasm(a,0x48850,0x1c0)]
    (OUT/'policy-context.asm.txt').write_text('\n'.join(policies),encoding='utf-8')
    stock=(ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes()
    patched=(ROOT/'patches/front-v0.7/libmtkcam_metastore.so').read_bytes()
    m=json.loads((ROOT/'patches/front-v0.7/patch-manifest.json').read_text())
    replay=bytearray(stock)
    for c in m['changes']:
        off=int(c['offset'],16); old=bytes.fromhex(c['old']); new=bytes.fromhex(c['new'])
        assert stock[off:off+len(old)]==old
        replay[off:off+len(new)]=new
    assert replay==patched and digest(patched)==m['output_sha256']
    result=dict(inventory=inventory, constructors=constructors, archives=archives,
       customer_functions=customer_functions,
       module_libs=[str(p.relative_to(ROOT)) for p in (ROOT/'archive/modules/x6810_raw_v07').rglob('*.so')],
       exact_v07_manifest_replay=True,changed_bytes=sum(x!=y for x,y in zip(stock,patched)))
    (OUT/'binaries.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    # Independently recompute phase means from the actual historical DNG.
    p=ROOT/'local-data/device/front-sample.dng'
    b=p.read_bytes(); assert b[:4]==b'II*\x00'
    off=struct.unpack_from('<I',b,4)[0]; tags={}
    for j in range(struct.unpack_from('<H',b,off)[0]):
        pos=off+2+12*j; tag,kind,n=struct.unpack_from('<HHI',b,pos)
        if tag not in (256,257,258,259,273,279,33421,33422,50714,50717): continue
        unit={1:1,3:2,4:4,5:8}[kind]
        loc=pos+8 if unit*n<=4 else struct.unpack_from('<I',b,pos+8)[0]
        if kind in (1,3,4): tags[tag]=struct.unpack_from('<'+{1:'B',3:'H',4:'I'}[kind]*n,b,loc)
    assert tags[258]==(16,) and tags[259]==(1,)
    w,h=tags[256][0],tags[257][0]
    pixels=array.array('H')
    for off,n in zip(tags[273],tags[279]): pixels.frombytes(b[off:off+n])
    if sys.byteorder!='little': pixels.byteswap()
    assert len(pixels)==w*h
    sums=[[0]*4 for _ in range(4)]; counts=[[0]*4 for _ in range(4)]
    for y in range(h):
        for x in range(4):
            vals=pixels[y*w+x:(y+1)*w:4]
            sums[y%4][x]+=sum(vals); counts[y%4][x]+=len(vals)
    phases=[[round(sums[y][x]/counts[y][x],3) for x in range(4)] for y in range(4)]
    dng=dict(path=str(p.relative_to(ROOT)),sha256=digest(b),width=w,height=h,
        cfa_repeat=tags.get(33421),cfa=tags.get(33422),white=tags.get(50717),
        phases_4x4=phases,warning='Historical full-resolution DNG, not a v0.7 binned sample')
    (OUT/'dng-phases.json').write_text(json.dumps(dng,indent=2),encoding='utf-8')
    properties=['persist.vendor.camera.max.previewfps','camera.disable_zsl_mode',
        'ro.vendor.camera3.zsl.default','vendor.camera.mdp.dre.enable',
        'vendor.camera.mdp.cz.enable','persist.vendor.camera.awb.sync',
        'vendor.debug.camera.hal3.level','persist.vendor.camera2.level',
        'vendor.debug.camera.raw.enable','persist.vendor.camera.raw',
        'vendor.debug.camera.3rdalgo.plugin.enable',
        'vendor.debug.camera.transsion.3rd.plugin.enable']
    corpus=list((ROOT/'stock-binaries').glob('*.so'))+list((ROOT/'local-data/device/libs').glob('*.so'))
    blobs={str(p.relative_to(ROOT)):p.read_bytes() for p in corpus}
    presence={s:[p for p,b in blobs.items() if s.encode()+b'\0' in b] for s in properties}
    (OUT/'property-presence.json').write_text(json.dumps(presence,indent=2),encoding='utf-8')
    print(json.dumps(dict(log={k:v for k,v in log.items() if k!='events'},
                         archives=archives, module_libs=result['module_libs'],
                         constructors=len(constructors),changed_bytes=result['changed_bytes']),indent=2))


if __name__=='__main__':
    main()
