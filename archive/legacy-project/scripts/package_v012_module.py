"""Package experimental OIS upgrade and exact v0.11 rollback from mandatory template."""
from pathlib import Path
import hashlib,json,zipfile
from module_template import apply_template,normalize_module_prop,style_customize
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 source=ROOT/'archive/modules/x6810_raw_v011';patch=ROOT/'patches/v0.12-ois-trial'
 names=['libmtkcam_metastore.so','libmtkcam_pipelinepolicy.so','libcam.hal3a.v3.so']
 old={n:(source/'system/vendor/lib64'/n).read_bytes() if n!='libcam.hal3a.v3.so' else (ROOT/'stock-binaries'/n).read_bytes() for n in names}
 new={n:(patch/n).read_bytes() if n!='libmtkcam_pipelinepolicy.so' else old[n] for n in names}
 triples=[':'.join(sha(v[n]) for n in names) for v in [old,new]]
 packages=[]
 for rollback in [False,True]:
  version='0.11.0-from-v012-rollback' if rollback else '0.12.0-ois-experimental'
  dest=ROOT/'archive/modules'/('x6810_raw_v011_from_v012_rollback' if rollback else 'x6810_raw_v012');apply_template(dest)
  files={str(p.relative_to(source)).replace('\\','/'):p.read_bytes() for p in source.rglob('*') if p.is_file()}
  payload=old if rollback else new
  for n,b in payload.items():files['system/vendor/lib64/'+n]=b
  desc='Restore v0.11 and original 3A; remove OIS bridge.' if rollback else 'OV08A10 Camera2 OIS OFF/ON bridge; v0.11 RAW preserved. Experimental: optical effectiveness not yet measured.'
  files['module.prop']=f'id=x6810_raw12mp\nname=X6810 RAW {version}\nversion={version}\nversionCode={11 if rollback else 12}\nauthor=SRE-0\ndescription={desc}\n'.encode()
  script='''#!/system/bin/sh
command -v sha256sum >/dev/null 2>&1 || abort "sha256sum required"
file_sha() { sha256sum "$1" | cut -d ' ' -f 1; }
M=/vendor/lib64/libmtkcam_metastore.so
P=/vendor/lib64/libmtkcam_pipelinepolicy.so
H=/vendor/lib64/libcam.hal3a.v3.so
MS=$(file_sha "$M"); PS=$(file_sha "$P"); HS=$(file_sha "$H")
case "$MS:$PS:$HS" in
  '''+'|'.join(triples)+''') ;;
  *) abort "Unsupported camera library triple: $MS / $PS / $HS" ;;
esac
[ "$(file_sha /vendor/lib64/libtran_oismgr.so)" = b061c7e672e285e7933053874c6892360b7bb9585a4982a4ff64624c4cd650b7 ] || abort "Unsupported OIS manager"
'''
  for n,b in payload.items():script+=f'[ "$(file_sha "$MODPATH/system/vendor/lib64/{n}")" = {sha(b)} ] || abort "Payload checksum mismatch: {n}"\n'
  script+='''for base in /data/adb/modules /data/adb/modules_update; do
 for other in "$base"/*; do
  [ -d "$other" ] || continue
  [ "${other##*/}" = x6810_raw12mp ] && continue
  [ -e "$other/disable" ] && continue
  [ -e "$other/remove" ] && continue
  for lib in libmtkcam_metastore.so libmtkcam_pipelinepolicy.so libcam.hal3a.v3.so; do
   if [ -f "$other/system/vendor/lib64/$lib" ] || [ -f "$other/vendor/lib64/$lib" ]; then
    abort "Conflicting camera module: ${other##*/}"
   fi
  done
 done
done
mkdir -p "$MODPATH/backup"
for lib in libmtkcam_metastore.so libmtkcam_pipelinepolicy.so libcam.hal3a.v3.so; do
 cp -p "/vendor/lib64/$lib" "$MODPATH/backup/$lib" || abort "Backup failed: $lib"
done
printf '%s\\n%s\\n%s\\n' "$MS" "$PS" "$HS" > "$MODPATH/backup/previous.sha256"
set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/vendor" 0 0 0755 0644 u:object_r:vendor_file:s0
for script in post-fs-data.sh service.sh boot-completed.sh; do set_perm "$MODPATH/$script" 0 0 0755; done
ui_print "Three camera libraries verified. Reboot required."
ui_print "OIS telemetry remains unsupported; read docs/OIS.md."
'''
  files['customize.sh']=script.encode()
  files['payload-sha256.json']=json.dumps({'system/vendor/lib64/'+n:sha(b) for n,b in payload.items()},indent=2).encode()
  files['README.md']=(f'# X6810 RAW {version}\n\n'+desc+'\n\nOnly upgrades verified v0.11/v0.12 triples. Uses template-module.\nRequires exact stock libcam.hal3a.v3.so and libtran_oismgr.so.\nStandard OFF/ON controls BU63169 suspend/resume only for OV08A10 and non-stock camera packages.\nStock Transsion package path stays unchanged. OIS_DATA_MODE is not advertised.\nRollback: dist/x6810-raw-v0.11.0-from-v012-rollback.zip\nSee docs/OIS.md for evidence, limits and recovery.\n').encode()
  if not rollback:
   for n in ['metadata-manifest.json','control-manifest.json']:files['ois-'+n]=(patch/n).read_bytes()
  files['boot-completed.sh']+=b'\nsha256sum /vendor/lib64/libcam.hal3a.v3.so >> "$MODDIR/boot-status.txt" 2>&1\n'
  for rel,b in files.items():p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  normalize_module_prop(dest);style_customize(dest)
  archive=ROOT/'dist'/f'x6810-raw-v{version}.zip'
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
   for p in sorted(dest.rglob('*')):
    if p.is_file():z.write(p,str(p.relative_to(dest)).replace('\\','/'))
  packages.append(dict(file=str(archive.relative_to(ROOT)),sha256=sha(archive.read_bytes())))
 (ROOT/'dist/v012-package-checksums.json').write_text(json.dumps(packages,indent=2)+'\n');print(json.dumps(packages,indent=2))
if __name__=='__main__':main()
