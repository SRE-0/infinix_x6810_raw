"""Package the tested paired binned profile and an explicit paired v0.7 rollback."""
from pathlib import Path
import hashlib
import json
from package_compatible_modules import write_zip, LIB

ROOT = Path(__file__).resolve().parents[1]
POL = 'system/vendor/lib64/libmtkcam_pipelinepolicy.so'
META7 = '2b3bca8dfa83ea01c3f210b1b187c173a453665f3373afe9e8d17614b0fe95df'
META8 = '00066e79cbeb0020d09e8e1fb43670cde08ef30133bd0d86a138609fb561e4a6'
POL0 = '47924889f98b5e01c3220eb69235df8580d597172faa439cd71beb0f8f41d7bd'
POL8 = '40360af0dc17d589cdf36b5388b642200093511815e00d702f5d02e612333c47'
STOCK = 'dbd740c5c7ba3081fb9d38b68b2f9975e19d6faad41dd5f87ce75f3c7d7be485'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def installer(meta, policy):
    return f'''#!/system/bin/sh
# Exact supported library pairs only. Never writes the vendor partition.
command -v sha256sum >/dev/null 2>&1 || abort "sha256sum required"
file_sha() {{ sha256sum "$1" | cut -d ' ' -f 1; }}
M=/vendor/lib64/libmtkcam_metastore.so
P=/vendor/lib64/libmtkcam_pipelinepolicy.so
MS=$(file_sha "$M")
PS=$(file_sha "$P")
case "$MS:$PS" in
  {STOCK}:{POL0}|{META7}:{POL0}|{META8}:{POL8}) ;;
  *) abort "Unsupported camera library pair: $MS / $PS" ;;
esac
[ "$(file_sha "$MODPATH/{LIB}")" = {meta} ] || abort "Metastore payload checksum mismatch"
[ "$(file_sha "$MODPATH/{POL}")" = {policy} ] || abort "Policy payload checksum mismatch"
for base in /data/adb/modules /data/adb/modules_update; do
  for other in "$base"/*; do
    [ -d "$other" ] || continue
    [ "${{other##*/}}" = x6810_raw12mp ] && continue
    [ -e "$other/disable" ] && continue
    [ -e "$other/remove" ] && continue
    [ -e "$other/skip_mount" ] && continue
    for lib in libmtkcam_metastore.so libmtkcam_pipelinepolicy.so; do
      if [ -f "$other/system/vendor/lib64/$lib" ] || [ -f "$other/vendor/lib64/$lib" ]; then
        abort "Conflicting camera module: ${{other##*/}}"
      fi
    done
  done
done
mkdir -p "$MODPATH/backup"
cp -p "$M" "$MODPATH/backup/libmtkcam_metastore.previous.so" || abort "Cannot back up metastore"
cp -p "$P" "$MODPATH/backup/libmtkcam_pipelinepolicy.previous.so" || abort "Cannot back up policy"
printf '%s\\n%s\\n' "$MS" "$PS" > "$MODPATH/backup/previous.sha256"
set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/vendor" 0 0 0755 0644 u:object_r:vendor_file:s0
for script in post-fs-data.sh service.sh boot-completed.sh; do
  set_perm "$MODPATH/$script" 0 0 0755
done
ui_print "X6810: both camera libraries verified; reboot required."
ui_print "Read README.md for front resolution limits and paired rollback."
'''

def main():
    source = ROOT/'archive/modules/x6810_raw_v07'
    outputs = []
    for rollback in (False, True):
        name = 'x6810_raw_v07_paired_rollback' if rollback else 'x6810_raw_v08'
        module = ROOT/'archive/modules'/name
        meta = (ROOT/('patches/front-v0.7/libmtkcam_metastore.so' if rollback else 'patches/front-v0.8-binned/libmtkcam_metastore.so')).read_bytes()
        policy = (ROOT/('stock-binaries/libmtkcam_pipelinepolicy.so' if rollback else 'patches/front-v0.8-binned/libmtkcam_pipelinepolicy.so')).read_bytes()
        assert sha(meta) == (META7 if rollback else META8)
        assert sha(policy) == (POL0 if rollback else POL8)
        version = '0.7.0-paired-rollback' if rollback else '0.8.0-binned-preview-experimental'
        description = ('Restore v0.7 metastore and stock pipeline policy together.' if rollback else
            'HI1631Q binned RAW 2320x1744 and guarded preview policy. MGC preview and JPEG+DNG tested. Limits front processed sizes. Extended validation pending.')
        files = {LIB:meta, POL:policy,
            'customize.sh':installer(sha(meta), sha(policy)).encode(),
            'module.prop':f'id=x6810_raw12mp\nname=X6810 RAW {version}\nversion={version}\nversionCode={7 if rollback else 8}\nauthor=SRE-0\ndescription={description}\n'.encode(),
            'system.prop':b'vendor.camera.tran.nums=3\n'}
        for rel in ('post-fs-data.sh','service.sh','boot-completed.sh','META-INF/com/google/android/update-binary','META-INF/com/google/android/updater-script'):
            files[rel]=(source/rel).read_bytes().replace(b'\r\n',b'\n')
        files['boot-completed.sh'] += b'\nsha256sum /vendor/lib64/libmtkcam_pipelinepolicy.so >> "$MODDIR/boot-status.txt" 2>&1\n'
        readme = '''# X6810: perfil binned v0.8 / reversion emparejada

Instalar mediante APatch o Magisk sobre x6810_raw12mp y reiniciar.
El instalador exige la pareja exacta stock, v0.7 o v0.8 comprobada.
No acepta otros firmwares ni combinaciones arbitrarias de bibliotecas.

v0.8: RAW frontal 2320x1744. Filtra las salidas procesadas frontales mayores
que 2320x1744 y sus duraciones; conserva comprobaciones de tamano en la
seleccion de PREVIEW. Esto reduce las resoluciones disponibles en TODAS
las apps que usan esa frontal; no habilita RAW nativo de 16 MP ni remosaic.
No modifica las matrices de color, ni iopipe, ni customer.
Mantiene los parches traseros de v0.7. Previews principal y tele probadas.

Validacion 2026-09-23: montaje temporal de ambas bibliotecas, MGC
com.android.MGC_9_7_047, preview frontal y dos capturas JPEG+DNG.
Una captura de hoja blanca mostro colores razonables tanto en JPEG como
en revelado independiente LibRaw. No equivale a calibracion colorimetrica.
No se ha validado instalacion persistente/reinicio, video, todas las apps,
todas las combinaciones Camera2 ni estabilidad prolongada.

Para volver a v0.7 desde v0.8, instalar
dist/x6810-raw-v0.7.0-paired-rollback.zip y reiniciar. Incluye el metastore
v0.7 Y pipelinepolicy original, para retirar ambas mitades del cambio.
No usar los antiguos ZIP compat1 para revertir esta pareja.
Desactivar el modulo y reiniciar elimina sus montajes systemless.
El contador de arranque heredado es una ayuda, no garantiza recuperacion.

Informe: docs/VERSION_HISTORY.md.
'''
        if rollback:
            readme = '# Este paquete RESTAURA v0.7 y pipelinepolicy original.\n\n'+readme
        files['README.md']=readme.encode('utf-8')
        if not rollback:
            for filename in ('metastore-manifest.json','policy-manifest.json'):
                files[filename]=(ROOT/'patches/front-v0.8-binned'/filename).read_bytes()
        files['payload-sha256.json']=json.dumps({LIB:sha(meta),POL:sha(policy)},indent=2).encode()
        module.mkdir(parents=True,exist_ok=True)
        for rel,data in files.items():
            target=module/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
        archive=ROOT/'dist'/f'x6810-raw-v{version}.zip'
        write_zip(archive,files)
        outputs.append({'file':str(archive.relative_to(ROOT)),'sha256':sha(archive.read_bytes()),'payloads':{LIB:sha(meta),POL:sha(policy)}})
    (ROOT/'dist/v08-package-checksums.json').write_text(json.dumps(outputs,indent=2)+'\n')
    print(json.dumps(outputs,indent=2))

if __name__ == '__main__':
    main()
