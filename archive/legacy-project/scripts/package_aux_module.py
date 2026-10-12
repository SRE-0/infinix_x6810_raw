"""Package v0.2 separately; same module id allows an in-place APatch upgrade."""
from build_aux_raw_patch import build_aux, ROOT, DEST
from module_template import apply_template, normalize_module_prop, style_customize
import hashlib, json, zipfile


def package():
    m = build_aux()
    source = ROOT/'archive/modules/x6810_raw12mp'
    module = ROOT/'archive/modules/x6810_raw_aux'
    module.mkdir(parents=True, exist_ok=True)
    apply_template(module)
    # Explicit allowlist: never package local backup files or boot counters.
    for rel in ('post-fs-data.sh','service.sh','boot-completed.sh',
                'META-INF/com/google/android/update-binary','META-INF/com/google/android/updater-script'):
        target = module/rel; target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((source/rel).read_bytes().replace(b'\r\n',b'\n'))
    payload = module/'system/vendor/lib64/libmtkcam_metastore.so'
    payload.parent.mkdir(parents=True,exist_ok=True)
    payload.write_bytes((DEST/'libmtkcam_metastore.so').read_bytes())
    (module/'patch-manifest.json').write_bytes((DEST/'patch-manifest.json').read_bytes())
    (module/'module.prop').write_text('''id=x6810_raw12mp
name=X6810 RAW16 main + telephoto + front candidate
version=0.2.0-aux-experimental
versionCode=2
author=SRE-0
description=Preserves confirmed S5KGM1ST RAW patch; adds OV08A10 and candidate OV16B10FF RAW streams. Auxiliary capture validation pending.
''',encoding='utf-8',newline='\n')
    installer = '''#!/system/bin/sh
STOCK_SHA=dbd740c5c7ba3081fb9d38b68b2f9975e19d6faad41dd5f87ce75f3c7d7be485
MAIN_SHA=daecf7263eafbf1075432979e2854617ef0e830e301059a22977551e5469caa8
PATCH_SHA=__PATCH_SHA__
TARGET=/vendor/lib64/libmtkcam_metastore.so
MODULES=/data/adb/modules
PAYLOAD="$MODPATH/system/vendor/lib64/libmtkcam_metastore.so"
[ -f "$TARGET" ] || abort "! Missing $TARGET"
command -v sha256sum >/dev/null 2>&1 || abort "! sha256sum is required"
ACTUAL_SHA=$(sha256sum "$PAYLOAD")
ACTUAL_SHA=${ACTUAL_SHA%% *}
[ "$ACTUAL_SHA" = "$PATCH_SHA" ] || abort "! Payload checksum mismatch"
LIVE_SHA=$(sha256sum "$TARGET")
LIVE_SHA=${LIVE_SHA%% *}
case "$LIVE_SHA" in
  "$STOCK_SHA"|"$MAIN_SHA"|"$PATCH_SHA") ;;
  *) abort "! Unsupported vendor library hash: $LIVE_SHA. Restore the supplied stock or confirmed v0.1 first." ;;
esac
for other in "$MODULES"/*; do
  [ -d "$other" ] || continue
  [ "${other##*/}" = x6810_raw12mp ] && continue
  [ -e "$other/disable" ] && continue
  [ -e "$other/remove" ] && continue
  [ -e "$other/skip_mount" ] && continue
  if [ -f "$other/system/vendor/lib64/libmtkcam_metastore.so" ] || [ -f "$other/vendor/lib64/libmtkcam_metastore.so" ]; then
    abort "! Conflicting camera library module: ${other##*/}. Disable it and reboot first."
  fi
done
mkdir -p "$MODPATH/backup"
cp -p "$TARGET" "$MODPATH/backup/libmtkcam_metastore.previous.so" || abort "! Cannot back up visible library"
printf '%s\\n' "$LIVE_SHA" > "$MODPATH/backup/previous.sha256"
set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/vendor" 0 0 0755 0644 u:object_r:vendor_file:s0
for script in post-fs-data.sh service.sh boot-completed.sh; do
  set_perm "$MODPATH/$script" 0 0 0755
done
ui_print "- Library base and payload hashes verified"
ui_print "- Confirmed main patch preserved; OV08A10 and OV16B10FF RAW metadata added"
ui_print "- Telephoto/front capture and front sensor identity require device validation"
ui_print "- Updates x6810_raw12mp in place. Reboot to load the new library."
'''.replace('__PATCH_SHA__',m['output_sha256'])
    (module/'customize.sh').write_text(installer,encoding='utf-8',newline='\n')
    if not (module/'README.md').is_file(): raise ValueError('Module README missing')
    normalize_module_prop(module)
    style_customize(module)
    out = ROOT/'dist'; out.mkdir(exist_ok=True)
    archive = out/'x6810-raw16-v0.2.0-aux-experimental.zip'
    paths = ['customize.sh','module.prop','README.md','patch-manifest.json',
             'post-fs-data.sh','service.sh','boot-completed.sh',
             'META-INF/com/google/android/update-binary','META-INF/com/google/android/updater-script',
             'system/vendor/lib64/libmtkcam_metastore.so']
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel in sorted(paths):
            data = (module/rel).read_bytes()
            if not rel.endswith('.so'): data=data.replace(b'\r\n',b'\n')
            info=zipfile.ZipInfo(rel,date_time=(2026,9,12,0,0,0));info.create_system=3
            info.external_attr=(0o100755 if rel.endswith('.sh') or rel.endswith('update-binary') else 0o100644)<<16
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None: raise ValueError('ZIP CRC failed')
        if z.read('system/vendor/lib64/libmtkcam_metastore.so') != payload.read_bytes(): raise ValueError('Wrong payload')
    sha=hashlib.sha256(archive.read_bytes()).hexdigest()
    # Preserve the old ZIP and include both distributable archives in the checksum index.
    (out/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(out.glob('*.zip'))))
    print('Packaged',archive.name,sha)
    return archive

if __name__ == '__main__': package()
