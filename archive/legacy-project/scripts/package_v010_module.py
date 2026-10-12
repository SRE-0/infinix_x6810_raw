"""Package maximum full-binned frontal streams and explicit v0.9 rollback."""
from package_v08_module import ROOT, LIB, POL, META8, POL8, installer, sha, write_zip
from package_v09_module import META9
import json

META10='a05f038d7e638f597f751750cafc0e0c9d788be85588e52afbfeff9e583759d5'
README='''# X6810 RAW v0.10: salidas frontales 2320x1744

Version derivada de v0.9. Anade tuplas JPEG/YUV 2320x1744 al constructor
HI1631Q. El HAL deriva PRIVATE, YV12 y entradas PRIVATE/YUV 2320x1744.
Mantiene tamanos menores y el filtro que impide seleccionar salidas mayores
que el modo binned. RAW sigue siendo 2320x1744. No cambia las otras camaras,
pipelinepolicy, iopipe, calibracion ni modos del sensor.

Validacion 2026-09-24: cuatro rutas PRIVATE/YUV -> JPEG/YUV a 2320x1744,
capturas directas RAW/JPEG/YUV/PRIVATE y peticion YV12 a 2320x1744.
ImageReader presenta la peticion YV12 como YUV_420_888 planar (format=35).
BSG conserva preview y guarda JPEG+DNG. No es certificacion CTS ni prueba
de video o estabilidad prolongada. GCam puede exportar dimensiones distintas
por recorte, zoom o escalado; el maximo del stream no fuerza cada foto a 4 MP.

Instalar sobre x6810_raw12mp en APatch/Magisk y reiniciar. Se verifican ambas
bibliotecas como pareja exacta. Rollback directo desde v0.10:
dist/x6810-raw-v0.9.0-from-v010-rollback.zip, instalar y reiniciar.
No usar directamente sobre v0.10 los ZIP antiguos sin este reconocimiento.
Desactivar el modulo y reiniciar elimina sus montajes systemless.

Informe: docs/BINARY_PATCHES.md.
'''
def main():
    source=ROOT/'archive/modules/x6810_raw_v09';index=[]
    for rollback in (False,True):
        name='x6810_raw_v09_from_v010_rollback' if rollback else 'x6810_raw_v010'
        version='0.9.0-from-v010-rollback' if rollback else '0.10.0-full-binned-streams'
        names=(LIB,POL,'customize.sh','module.prop','system.prop','post-fs-data.sh','service.sh','boot-completed.sh',
            'META-INF/com/google/android/update-binary','META-INF/com/google/android/updater-script',
            'metastore-manifest.json','policy-manifest.json','reprocessing-manifest.json')
        files={rel:(source/rel).read_bytes() for rel in names}
        meta=META9 if rollback else META10
        if not rollback:
            files[LIB]=(ROOT/'patches/front-v0.10-full-binned/libmtkcam_metastore.so').read_bytes()
            files['full-binned-manifest.json']=(ROOT/'patches/front-v0.10-full-binned/full-binned-manifest.json').read_bytes()
        assert sha(files[LIB])==meta and sha(files[POL])==POL8
        script=installer(meta,POL8);needle=META8+':'+POL8+')';assert script.count(needle)==1
        files['customize.sh']=script.replace(needle,META8+':'+POL8+'|'+META9+':'+POL8+'|'+META10+':'+POL8+')').encode()
        desc='Restore v0.9 front RAW and 1968x864 reprocessing.' if rollback else 'HI1631Q maximum RAW/JPEG/YUV/PRIVATE/YV12 outputs and PRIVATE/YUV inputs at 2320x1744. Nine capture paths tested. Rear metadata preserved.'
        files['module.prop']=f'id=x6810_raw12mp\nname=X6810 RAW {version}\nversion={version}\nversionCode={9 if rollback else 10}\nauthor=SRE-0\ndescription={desc}\n'.encode()
        files['README.md']=(('ESTE PAQUETE RESTAURA v0.9, no habilita los tamanos de v0.10.\n\n' if rollback else '')+README).encode()
        files['payload-sha256.json']=json.dumps({LIB:meta,POL:POL8},indent=2).encode()
        dest=ROOT/'archive/modules'/name
        for rel,data in files.items():
            p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        archive=ROOT/'dist'/f'x6810-raw-v{version}.zip';write_zip(archive,files)
        index.append(dict(file=str(archive.relative_to(ROOT)),sha256=sha(archive.read_bytes()),metastore=meta,policy=POL8))
    (ROOT/'dist/v010-package-checksums.json').write_text(json.dumps(index,indent=2)+'\n')
    print(json.dumps(index,indent=2))
if __name__=='__main__':main()
