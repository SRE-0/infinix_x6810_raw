from build_raw_patch import build, ROOT
from module_template import apply_template, normalize_module_prop, style_customize
import hashlib, json, zipfile

manifest=build()
module=ROOT/'archive/modules/x6810_raw12mp'
apply_template(module)
payload=module/'system/vendor/lib64/libmtkcam_metastore.so'
payload.parent.mkdir(parents=True,exist_ok=True)
payload.write_bytes((ROOT/'patches/libmtkcam_metastore.so').read_bytes())
(module/'patch-manifest.json').write_bytes((ROOT/'patches/patch-manifest.json').read_bytes())
if 'PATCH_SHA='+manifest['output_sha256'] not in (module/'customize.sh').read_text():
    raise ValueError('Installer hash is stale')
normalize_module_prop(module)
style_customize(module)
out=ROOT/'dist'; out.mkdir(exist_ok=True)
archive=out/'x6810-raw16-12mp-v0.1.0-experimental.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(module.rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(module).as_posix()
        b=p.read_bytes()
        if p.suffix in ('.sh','.prop','.md','.json') or p.name in ('update-binary','updater-script'):
            b=b.replace(b'\r\n',b'\n')
            p.write_bytes(b)
        info=zipfile.ZipInfo(rel,date_time=(2026,9,12,0,0,0))
        info.create_system=3
        mode=0o100755 if p.suffix=='.sh' or p.name=='update-binary' else 0o100644
        info.external_attr=mode<<16
        z.writestr(info,b,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
with zipfile.ZipFile(archive) as z:
    if z.testzip() is not None: raise ValueError('ZIP CRC failure')
    if hashlib.sha256(z.read('system/vendor/lib64/libmtkcam_metastore.so')).hexdigest()!=manifest['output_sha256']:
        raise ValueError('ZIP payload mismatch')
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
(out/'SHA256SUMS.txt').write_text(sha+'  '+archive.name+'\n')
print('Packaged:',archive,'SHA256:',sha)
