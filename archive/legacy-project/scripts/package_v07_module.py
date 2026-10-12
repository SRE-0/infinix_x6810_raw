"""Build the experimental binned-normalization profile and refresh rollback ZIPs."""
from build_v07_raw_patch import build, ROOT, DEST
from package_compatible_modules import registry, installer, write_zip, main as refresh_compatible, LIB
from module_template import apply_template, normalize_module_prop, style_customize
import re


def main():
    m=build()
    source=ROOT/'archive/modules/x6810_raw_v06'
    module=ROOT/'archive/modules/x6810_raw_v07'
    apply_template(module)
    files={}
    for rel in ('post-fs-data.sh','service.sh','boot-completed.sh',
                'META-INF/com/google/android/update-binary','META-INF/com/google/android/updater-script'):
        files[rel]=(source/rel).read_bytes().replace(b'\r\n',b'\n')
    files[LIB]=(DEST/'libmtkcam_metastore.so').read_bytes()
    files['patch-manifest.json']=(DEST/'patch-manifest.json').read_bytes()
    script=installer((source/'customize.sh').read_text(),registry())
    script=re.sub(r'(?m)^PATCH_SHA=.*$', 'PATCH_SHA='+m['output_sha256'],script)
    script=re.sub(r'(?m)^ui_print .*\n?', '',script)
    script+='''ui_print "- Verified X6810 library; upgrade/downgrade supported"
ui_print "- EXPERIMENTAL: HI1631Q binned RAW 2320x1744 + normalization guard"
ui_print "- No remosaic request injection; rear patches preserved"
ui_print "- Color, front preview and GCam require device validation"
ui_print "- Auxiliary property included; reboot required"
'''
    files['customize.sh']=script.encode()
    files['system.prop']=b'# Transsion Camera2 camera count; no unrelated imaging overrides.\nvendor.camera.tran.nums=3\n'
    files['module.prop']=b'''id=x6810_raw12mp
name=X6810 RAW - experimental HI1631Q binned normalization
version=0.7.0-binned-normalization-experimental
versionCode=7
author=SRE-0
description=Experimental front 2320x1744 RAW with guarded size normalization. Removes v0.6 request hook. Rear patches preserved. Hardware validation pending.
'''
    files['README.md']='''# v0.7: candidato experimental, no correccion confirmada

HI1631Q publica unicamente RAW16 2320x1744. Un guard en updateRawCapability
conserva ese tamano solo si el area activa es 4640x3488; evita que el HAL
lo reescriba al tamano completo. No inyecta los tags remosaic/processRaw de v0.6.
El objetivo es usar la salida del sensor con binning, no convertir Quad Bayer por software.

Las dimensiones RAW deben conservarse tambien al final de la construccion
del proveedor, y P1 debe seleccionar 2320x1744. Esto aun requiere probar el telefono.
No hay confirmacion de color, DNG valido, GCam estable ni mejora de FPS.
Principal y teleobjetivo conservan sus bytes de parche anteriores.

Incluye system.prop con vendor.camera.tran.nums=3. Retira los otros overrides
de procesado de v0.6 para reducir interferencias. No modifica customer.so.
Se instala encima del modulo actual en APatch y requiere un reinicio.
Para volver, usa dist/compatible/*v0.2*-compat1.zip (sin desinstalar previamente).
No uses los ZIP historicos sin compat1 para bajar de version.

Documentacion: docs/VERSION_HISTORY.md.
'''.encode('utf-8')
    for rel,data in files.items():
        p=module/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    normalize_module_prop(module)
    style_customize(module)
    archive=ROOT/'dist/x6810-raw16-v0.7.0-binned-normalization-experimental.zip'
    write_zip(archive,files)
    refresh_compatible()
    print(archive)


if __name__=='__main__': main()
