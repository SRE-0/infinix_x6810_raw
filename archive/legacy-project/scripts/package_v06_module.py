"""Package v0.6 with HI1631Q full-size RAW and front-only remosaic defaults."""
from build_v06_raw_patch import build_front, ROOT, DEST
from module_template import apply_template, normalize_module_prop, style_customize
import hashlib, zipfile


def package():
    manifest = build_front()
    source = ROOT/'archive/modules/x6810_raw12mp'
    module = ROOT/'archive/modules/x6810_raw_v06'
    module.mkdir(parents=True, exist_ok=True)
    apply_template(module)
    for rel in ('post-fs-data.sh','service.sh','boot-completed.sh',
                'META-INF/com/google/android/update-binary','META-INF/com/google/android/updater-script'):
        target = module/rel; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source/rel).read_bytes().replace(b'\r\n', b'\n'))
    payload = module/'system/vendor/lib64/libmtkcam_metastore.so'
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_bytes((DEST/'libmtkcam_metastore.so').read_bytes())
    (module/'patch-manifest.json').write_bytes((DEST/'patch-manifest.json').read_bytes())
    (module/'system.prop').write_bytes((ROOT/'archive/modules/x6810_raw_v05/system.prop').read_bytes().replace(b'\r\n',b'\n'))
    (module/'module.prop').write_text('''id=x6810_raw12mp
name=X6810 RAW16 main + telephoto + HI1631Q remosaic
version=0.6.0-hi1631q-remosaic
versionCode=6
author=SRE-0
description=Preserves tested rear RAW; removes invalid binned front RAW and enables MTK 4Cell remosaic/processed RAW defaults for camera 1. Includes auxiliary camera properties.
''', encoding='utf-8', newline='\n')
    previous = {
        'STOCK_SHA': 'dbd740c5c7ba3081fb9d38b68b2f9975e19d6faad41dd5f87ce75f3c7d7be485',
        'MAIN_SHA': 'daecf7263eafbf1075432979e2854617ef0e830e301059a22977551e5469caa8',
        'AUX_SHA': '7a41b870658b2eeea8eb0a612219ca6e73de90b78b6b27a74d778d2804e43f5b',
        'FRONT_SHA': 'a1bb426f73f1e363f3e0a7fbcf2e7e95d24b52c45efc25633b58ed057622575a',
        'TIMING_SHA': 'd3cc530a971f187bde4873dd63c8c257496e446a31996f3f3df0c866716c41c6',
        'BINNED_SHA': '99b9762ec7d6fd0b341c7d82b41dca50fa2ddd141225d9294e45638021d599f0',
        'PATCH_SHA': manifest['output_sha256'],
    }
    assignments = '\n'.join(f'{key}={value}' for key,value in previous.items())
    installer = '''#!/system/bin/sh
__ASSIGNMENTS__
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
  "$STOCK_SHA"|"$MAIN_SHA"|"$AUX_SHA"|"$FRONT_SHA"|"$TIMING_SHA"|"$BINNED_SHA"|"$PATCH_SHA") ;;
  *) abort "! Unsupported vendor library hash: $LIVE_SHA. Restore a supported stock/v0.1-v0.5 base first." ;;
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
printf '%s\n' "$LIVE_SHA" > "$MODPATH/backup/previous.sha256"
set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/vendor" 0 0 0755 0644 u:object_r:vendor_file:s0
for script in post-fs-data.sh service.sh boot-completed.sh; do
  set_perm "$MODPATH/$script" 0 0 0755
done
ui_print "- Exact library and payload hashes verified"
ui_print "- Rear RAW patches preserved"
ui_print "- HI1631Q publishes only valid 4640x3488 RAW16"
ui_print "- Front request defaults enable MTK 4Cell remosaic and processed RAW"
ui_print "- Auxiliary camera properties included; reboot required"
'''.replace('__ASSIGNMENTS__', assignments)
    (module/'customize.sh').write_text(installer, encoding='utf-8', newline='\n')
    (module/'README.md').write_text('''# X6810 RAW v0.6 — HI1631Q remosaic

Esta versión conserva el RAW funcional de la principal y el teleobjetivo.
Para la frontal elimina el stream RAW16 2320×1744: el log real demostró que
MediaTek abre el modo de sensor 4640×3488 y rechaza ese buffer por stride.

Sólo se publica RAW16 4640×3488. Para camera ID 1, la plantilla de petición
activa `com.mediatek.control.capture.remosaicenable=1` y
`processRaw.enable=1`. El X6810 ya identifica HI1631Q como 4Cell y su tabla de
features contiene `MTK_FEATURE_REMOSAIC`; este parche intenta hacer que el HAL
entregue Bayer regular en lugar del mosaico Quad Bayer que produce el tinte rosa.

El ZIP incluye `system.prop` para exponer las tres cámaras a aplicaciones
Camera2. Instálalo como actualización en APatch y reinicia. Esta ruta nueva
requiere validación física; si camerahalserver no inicia, vuelve a v0.2.
Consulta `docs/VERSION_HISTORY.md` en el proyecto.
''', encoding='utf-8', newline='\n')
    normalize_module_prop(module)
    style_customize(module)
    out = ROOT/'dist'; out.mkdir(exist_ok=True)
    archive = out/'x6810-raw16-v0.6.0-hi1631q-remosaic.zip'
    paths = ['system.prop','customize.sh','module.prop','README.md','patch-manifest.json',
             'post-fs-data.sh','service.sh','boot-completed.sh',
             'META-INF/com/google/android/update-binary','META-INF/com/google/android/updater-script',
             'system/vendor/lib64/libmtkcam_metastore.so']
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel in sorted(paths):
            data=(module/rel).read_bytes()
            if not rel.endswith('.so'): data=data.replace(b'\r\n',b'\n')
            info=zipfile.ZipInfo(rel,date_time=(2026,9,13,0,0,0));info.create_system=3
            info.external_attr=(0o100755 if rel.endswith('.sh') or rel.endswith('update-binary') else 0o100644)<<16
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None: raise ValueError('ZIP CRC failed')
        if z.read('system/vendor/lib64/libmtkcam_metastore.so') != payload.read_bytes(): raise ValueError('Wrong payload')
    (out/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(out.glob('*.zip'))))
    print('Packaged', archive.name, hashlib.sha256(archive.read_bytes()).hexdigest())
    return archive


if __name__ == '__main__': package()
