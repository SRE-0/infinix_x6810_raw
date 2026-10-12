"""Package capture patch and exact v0.12 rollback using the mandatory template."""
import hashlib,json,zipfile
from pathlib import Path
from module_template import apply_template,normalize_module_prop,style_customize
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/modules/x6810_raw_v012'
NAMES=['libmtkcam_metastore.so','libmtkcam_pipelinepolicy.so','libcam.hal3a.v3.so']
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
 old={n:(SOURCE/'system/vendor/lib64'/n).read_bytes() for n in NAMES}
 new=dict(old);new[NAMES[2]]=(ROOT/'patches/flash-capture'/NAMES[2]).read_bytes()
 manifest=json.loads((ROOT/'patches/flash-capture/manifest.json').read_text())
 assert sha(old[NAMES[2]])==manifest['input_sha256'] and sha(new[NAMES[2]])==manifest['output_sha256']
 triples=[':'.join(sha(d[n]) for n in NAMES) for d in (old,new)]
 for rollback in (False,True):
  version='0.12.0-from-flash-rollback' if rollback else '0.12.1-flash-experimental'
  dest=ROOT/'archive/modules'/('x6810_raw_v012_from_flash_rollback' if rollback else 'x6810_raw_v012_flash')
  apply_template(dest)
  files={p.relative_to(SOURCE).as_posix():p.read_bytes() for p in SOURCE.rglob('*') if p.is_file()}
  payload=old if rollback else new
  for n,b in payload.items():files['system/vendor/lib64/'+n]=b
  description='Restore exact v0.12 RAW/OIS HAL.' if rollback else 'Capture-only main flash duty cap 9..29; OEM timing and v0.12 RAW/OIS preserved; no official strength API support.'
  files['module.prop']=f'id=x6810_raw12mp\nname=X6810 RAW {version}\nversion={version}\nversionCode={12 if rollback else 13}\nauthor=SRE-0\ndescription={description}\n'.encode()
  script='''#!/system/bin/sh
[ "$(getprop ro.product.device)" = Infinix-X6810 ] || abort "X6810 required"
file_sha() { sha256sum "$1" | cut -d ' ' -f 1; }
M=/vendor/lib64/libmtkcam_metastore.so
P=/vendor/lib64/libmtkcam_pipelinepolicy.so
H=/vendor/lib64/libcam.hal3a.v3.so
MS=$(file_sha "$M"); PS=$(file_sha "$P"); HS=$(file_sha "$H")
case "$MS:$PS:$HS" in
  '''+'|'.join(triples)+''') ;;
  *) abort "Unsupported RAW/OIS/flash library triple" ;;
esac
'''
  for n,b in payload.items():script+=f'[ "$(file_sha "$MODPATH/system/vendor/lib64/{n}")" = {sha(b)} ] || abort "Payload mismatch: {n}"\n'
  script+='''for base in /data/adb/modules /data/adb/modules_update; do
 for other in "$base"/*; do
  [ -d "$other" ] || continue
  [ "${other##*/}" = x6810_raw12mp ] && continue
  [ -e "$other/disable" ] && continue
  [ -e "$other/remove" ] && continue
  for lib in libmtkcam_metastore.so libmtkcam_pipelinepolicy.so libcam.hal3a.v3.so; do
   [ ! -f "$other/system/vendor/lib64/$lib" ] && [ ! -f "$other/vendor/lib64/$lib" ] || abort "Conflicting camera module"
  done
 done
done
mkdir -p "$MODPATH/backup"
for lib in libmtkcam_metastore.so libmtkcam_pipelinepolicy.so libcam.hal3a.v3.so; do
 cp -p "/vendor/lib64/$lib" "$MODPATH/backup/$lib" || abort "Backup failed"
done
set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/vendor" 0 0 0755 0644 u:object_r:vendor_file:s0
for script in post-fs-data.sh service.sh boot-completed.sh; do set_perm "$MODPATH/$script" 0 0 0755; done
ui_print "Payload and current libraries verified. Reboot activates overlay."
'''
  files['customize.sh']=script.encode()
  files['payload-sha256.json']=(json.dumps({'system/vendor/lib64/'+n:sha(b) for n,b in payload.items()},indent=2)+'\n').encode()
  files['flash-capture-manifest.json']=json.dumps(manifest,indent=2).encode()
  files['README.md']=(f'# X6810 RAW {version}\n\n{description}\n\nSee docs/FLASH_CAPTURE_API.md for validation and recovery.\n').encode()
  files['service.sh']+=b'\nsetprop vendor.debug.x6810.flashcap 0\n'
  for rel,b in files.items():
   p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  normalize_module_prop(dest);style_customize(dest)
  out=ROOT/'dist'/f'x6810-raw-v{version}.zip'
  with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
   for p in sorted(dest.rglob('*')):
    if p.is_file():z.write(p,p.relative_to(dest).as_posix())
  print(out.name,sha(out.read_bytes()))
if __name__=='__main__':main()
