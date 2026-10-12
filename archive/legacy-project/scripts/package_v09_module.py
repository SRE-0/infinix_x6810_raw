"""Package front reprocessing plus a v0.8 rollback accepting the new hash pair."""
from package_v08_module import ROOT, LIB, POL, META8, POL8, installer, sha, write_zip
import json

META9='dc18e2cdd107f4e56c98114a2de16592e275dd37e2bbd3960df7d12806d308d5'
def main():
    source=ROOT/'archive/modules/x6810_raw_v08'
    index=[]
    for rollback in (False,True):
        name='x6810_raw_v08_from_v09_rollback' if rollback else 'x6810_raw_v09'
        version='0.8.0-from-v09-rollback' if rollback else '0.9.0-front-reprocessing'
        names=(LIB,POL,'customize.sh','module.prop','system.prop','post-fs-data.sh','service.sh','boot-completed.sh',
            'META-INF/com/google/android/update-binary','META-INF/com/google/android/updater-script',
            'metastore-manifest.json','policy-manifest.json','payload-sha256.json','README.md')
        files={rel:(source/rel).read_bytes() for rel in names}
        files[LIB]=(ROOT/('patches/front-v0.8-binned/libmtkcam_metastore.so' if rollback else 'patches/front-v0.9-reprocessing/libmtkcam_metastore.so')).read_bytes()
        assert sha(files[LIB])==(META8 if rollback else META9)
        assert sha(files[POL])==POL8
        script=installer(sha(files[LIB]),POL8)
        needle=META8+':'+POL8+')'
        assert script.count(needle)==1
        files['customize.sh']=script.replace(needle,META8+':'+POL8+'|'+META9+':'+POL8+')').encode()
        desc=('Restore v0.8 front binned RAW and its sensor policy.' if rollback else 'HI1631Q binned RAW plus PRIVATE/YUV reprocessing. Four real reprocess paths validated at 1968x864. Rear configuration preserved.')
        files['module.prop']=f'id=x6810_raw12mp\nname=X6810 RAW {version}\nversion={version}\nversionCode={8 if rollback else 9}\nauthor=SRE-0\ndescription={desc}\n'.encode()
        files['payload-sha256.json']=json.dumps({LIB:sha(files[LIB]),POL:sha(files[POL])},indent=2).encode()
        if not rollback:
            files['reprocessing-manifest.json']=(ROOT/'patches/front-v0.9-reprocessing/reprocessing-manifest.json').read_bytes()
        files['README.md']=('''# X6810 RAW v0.9: reprocesado frontal

Instalar en APatch/Magisk sobre x6810_raw12mp y reiniciar. Verifica parejas
exactas de metastore/pipelinepolicy stock, v0.7, v0.8 y v0.9.

Conserva el RAW frontal binned de v0.8 (2320x1744) y su filtro de salidas
procesadas. Agrega PRIVATE_REPROCESSING y YUV_REPROCESSING SOLO al constructor
HI1631Q. La rutina original updateReprocessCapabilities genera el mapa de
entrada/salida, una entrada maxima y modos ZSL. No cambia iopipe, customer,
matrices de color ni configuracion trasera. Principal y tele ya tenian ambas
capacidades. No implementa remosaic ni RAW frontal de 16 MP.

Validacion 2026-09-24: PRIVATE->JPEG, PRIVATE->YUV, YUV->JPEG y YUV->YUV
ejecutados mediante createReprocessableCaptureSession, ImageWriter y
createReprocessCaptureRequest. Cuatro salidas 1968x864 con timestamp igual
al frame de origen. BSG conserva preview frontal y guarda JPEG+DNG.
52 constructores emulados: solo HI1631Q cambia sus dos capabilities.

Limites: el HAL publica actualmente entradas 1968x864; no afirmar
reprocesado de 16 MP ni cumplimiento CTS completo. No se han probado todas
las combinaciones de streams, video, calidad bajo toda iluminacion o
estabilidad prolongada. El RAW DNG exportado por GCam puede incluir recorte
y fusion. La hoja neutra de v0.8 demuestra un caso de color razonable,
no una calibracion colorimetrica universal.

Reversion directa: dist/x6810-raw-v0.8.0-from-v09-rollback.zip, reiniciar.
Para bajar luego a v0.7, usar el rollback emparejado v0.7 desde v0.8.
No usar los antiguos ZIP compat1 directamente sobre v0.9.
Desactivar el modulo y reiniciar elimina sus montajes systemless.

Fuentes, cambios y evidencias: docs/VERSION_HISTORY.md.
'''+('\nESTE ZIP ES LA REVERSION A v0.8; NO HABILITA REPROCESADO FRONTAL.\n' if rollback else '')).encode('utf-8')
        dest=ROOT/'archive/modules'/name
        # Remove only the mistakenly copied nested archive from the first build.
        (dest/'x6810_raw_v08.zip').unlink(missing_ok=True)
        for rel,data in files.items():
            p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        archive=ROOT/'dist'/f'x6810-raw-v{version}.zip';write_zip(archive,files)
        index.append(dict(file=str(archive.relative_to(ROOT)),sha256=sha(archive.read_bytes()),metastore=sha(files[LIB]),policy=sha(files[POL])))
    (ROOT/'dist/v09-package-checksums.json').write_text(json.dumps(index,indent=2)+'\n')
    print(json.dumps(index,indent=2))
if __name__=='__main__':main()
