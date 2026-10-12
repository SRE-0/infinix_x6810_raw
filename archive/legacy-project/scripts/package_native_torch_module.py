"""Package paired native torch bridge and exact preceding RAW capture rollback."""
import hashlib,json,zipfile
from pathlib import Path
from module_template import apply_template,normalize_module_prop,style_customize
ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/'patches/native-torch'
BASE=ROOT/'archive/modules/x6810_raw_v012_flash'
sha=lambda b:hashlib.sha256(b).hexdigest()

def write_release_index(release):
    folder=ROOT/'dist/releases'/release
    folder.mkdir(parents=True,exist_ok=True)
    records=[]
    for archive in sorted(folder.glob('v*.zip')):
        with zipfile.ZipFile(archive) as package:
            fields=dict(line.split('=',1) for line in package.read('module.prop').decode().splitlines() if '=' in line)
            payloads=json.loads(package.read('payload-sha256.json'))
        records.append(dict(file=archive.relative_to(ROOT).as_posix(),sha256=sha(archive.read_bytes()),
                            module=fields.get('name',archive.stem),versionCode=int(fields.get('versionCode','0')),
                            payloads=payloads))
    (folder/'SHA256SUMS.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')

def main():
    manifests={n:json.loads((PATCH/(n+'.json')).read_text()) for n in ('cameraserver','libmtkcam_device3_hal.so','libcam.hal3a.v3.so')}
    targets={n:('system/bin/' if n=='cameraserver' else 'system/vendor/lib64/')+n for n in manifests}
    basefiles={p.relative_to(BASE).as_posix():p.read_bytes() for p in BASE.rglob('*') if p.is_file()}
    for rollback in (False,True):
        version='v0121_x6810_raw_rollback_native_torch' if rollback else 'v0122_x6810_raw_native_torch'
        dest=ROOT/'archive/modules'/('x6810_raw_v012_from_native_rollback' if rollback else 'x6810_raw_v012_native_torch')
        apply_template(dest)
        files=dict(basefiles)
        if not rollback:
            for n,rel in targets.items():
                data=(PATCH/n).read_bytes();assert sha(data)==manifests[n]['output_sha256'];files[rel]=data
        desc='Restore RAW 0.12.1 capture cap and remove native framework torch overlay.' if rollback else 'Native CameraManager torch strength 1..9 (physical duties 0..8), RAW/OIS and bounded capture cap; exact Android 16 GSI only; SINGLE intensity not implemented.'
        files['module.prop']=f'id=x6810_raw12mp\nname={version}\nversion={version}\nversionCode={13 if rollback else 14}\nauthor=SRE-0\ndescription={desc}\n'.encode()
        script='''#!/system/bin/sh
[ "$(getprop ro.product.device)" = Infinix-X6810 ] || abort "X6810 required"
[ "$(getprop ro.build.version.sdk)" = 36 ] || abort "Exact Android 16 GSI required"
file_sha() { sha256sum "$1" | cut -d ' ' -f 1; }
'''
        # Require a coherent original or native tuple, never a mixed installation.
        combinations=[]
        for state in ('input_sha256','output_sha256'):
            combinations.append(':'.join(manifests[n][state] for n in manifests))
        variables=[]
        for i,n in enumerate(manifests):
            path='/'+targets[n];path=path.replace('/system/vendor/','/vendor/')
            script+=f'S{i}=$(file_sha {path})\n';variables.append('$S'+str(i))
        script+='case "'+':'.join(variables)+'" in\n '+ '|'.join(combinations)+') ;;\n *) abort "Native torch requires an exact matched GSI/HAL tuple" ;;\nesac\n'
        for name in ('libmtkcam_metastore.so','libmtkcam_pipelinepolicy.so'):
            digest=sha(files['system/vendor/lib64/'+name])
            script+=f'[ "$(file_sha /vendor/lib64/{name})" = {digest} ] || abort "RAW/OIS baseline mismatch"\n'
        payload={rel:sha(b) for rel,b in files.items() if rel.startswith('system/')}
        for rel,digest in payload.items():script+=f'[ "$(file_sha "$MODPATH/{rel}")" = {digest} ] || abort "Payload mismatch: {rel}"\n'
        script+='''for base in /data/adb/modules /data/adb/modules_update; do
 for other in "$base"/*; do
  [ -d "$other" ] || continue
  [ "${other##*/}" = x6810_raw12mp ] && continue
  [ -e "$other/disable" ] && continue
  [ -e "$other/remove" ] && continue
  for rel in system/bin/cameraserver system/vendor/lib64/libcam.hal3a.v3.so system/vendor/lib64/libmtkcam_device3_hal.so system/vendor/lib64/libmtkcam_metastore.so system/vendor/lib64/libmtkcam_pipelinepolicy.so; do
   [ ! -f "$other/$rel" ] && [ ! -f "$other/${rel#system/}" ] || abort "Conflicting native camera overlay"
  done
 done
done
mkdir -p "$MODPATH/backup"
for file in /system/bin/cameraserver /vendor/lib64/libcam.hal3a.v3.so /vendor/lib64/libmtkcam_device3_hal.so; do
 cp -p "$file" "$MODPATH/backup/${file##*/}" || abort "Backup failed"
done
set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/vendor" 0 0 0755 0644 u:object_r:vendor_file:s0
for script in post-fs-data.sh service.sh boot-completed.sh; do set_perm "$MODPATH/$script" 0 0 0755; done
'''
        if not rollback:
            script+='set_perm "$MODPATH/system/bin/cameraserver" 0 2000 0755 u:object_r:cameraserver_exec:s0\n'
            files['service.sh']+=f'''
# The individual executable bind must allow init -> cameraserver transition.
# Never remount /data or relax SELinux.
if [ "$(sha256sum /system/bin/cameraserver | cut -d ' ' -f 1)" = {manifests['cameraserver']['output_sha256']} ]; then
 mount -o remount,bind,suid /system/bin/cameraserver
 [ "$(getprop init.svc.cameraserver)" = running ] || start cameraserver
fi
'''.encode()
        files['customize.sh']=script.encode()
        files['payload-sha256.json']=(json.dumps(payload,indent=2)+'\n').encode()
        files['native-torch-manifests.json']=(json.dumps(manifests,indent=2)+'\n').encode()
        files['README.md']=f'# {version}\n\n{desc}\n\nRead docs/NATIVE_FLASH_API.md. Remove before changing the GSI. Rollback requires reboot.\n'.encode()
        for rel,b in files.items():
            path=dest/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
        normalize_module_prop(dest);style_customize(dest)
        release='v0121' if rollback else 'v0122'
        out=ROOT/'dist/releases'/release/(version+'.zip')
        out.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            for path in sorted(dest.rglob('*')):
                if path.is_file():z.write(path,path.relative_to(dest).as_posix())
        print(out.name,sha(out.read_bytes()))
    for release in ('v0121','v0122'):
        write_release_index(release)
if __name__=='__main__':main()
