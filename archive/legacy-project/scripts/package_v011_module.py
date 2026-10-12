"""Package the RAW16 buffer fix and a checksum-aware v0.10 rollback."""
from package_v08_module import ROOT, LIB, POL, POL8, sha, write_zip
from package_v010_module import META10
import json

POL11 = 'd3bfa9aab5d43af352a3bf717ff4b399cad6744ccc2c548ef8ae4650f3635ad2'


def main():
    source = ROOT/'archive/modules/x6810_raw_v010'
    index = []
    for rollback in (False, True):
        name = 'x6810_raw_v010_from_v011_rollback' if rollback else 'x6810_raw_v011'
        version = '0.10.0-from-v011-rollback' if rollback else '0.11.0-raw-buffer-fix'
        files = {str(p.relative_to(source)).replace('\\','/'):p.read_bytes()
                 for p in source.rglob('*') if p.is_file()}
        policy = POL8 if rollback else POL11
        if not rollback:
            files[POL] = (ROOT/'patches/v0.11-raw-buffers/libmtkcam_pipelinepolicy.so').read_bytes()
            files['raw-buffers-manifest.json'] = (ROOT/'patches/v0.11-raw-buffers/raw-buffers-manifest.json').read_bytes()
        assert sha(files[LIB]) == META10 and sha(files[POL]) == policy
        script = files['customize.sh'].decode()
        needle = META10+':'+POL8+')'
        assert script.count(needle) == 1
        script = script.replace(needle, META10+':'+POL8+'|'+META10+':'+POL11+')')
        needle = '= '+POL8+' ] || abort "Policy payload checksum mismatch"'
        assert script.count(needle) == 1
        script = script.replace(needle, '= '+policy+' ] || abort "Policy payload checksum mismatch"')
        script = script.replace('MODNAME="X6810 RAW 0.10.0"', f'MODNAME="X6810 RAW {version}"')
        script = script.replace('MODVERSION="0.10.0"', f'MODVERSION="{version}"')
        files['customize.sh'] = script.encode()
        description = ('Restore v0.10 camera libraries, removing RAW16 buffer floor.' if rollback else
                       'RAW16 HAL buffer floor 6: fixes BSG preview lag at native RAW resolutions. Preserves v0.10 front streams and reprocessing.')
        files['module.prop'] = f'id=x6810_raw12mp\nname=X6810 RAW {version}\nversion={version}\nversionCode={10 if rollback else 11}\nauthor=SRE-0\ndescription={description}\n'.encode()
        files['README.md'] = (('# RESTAURACION v0.10 desde v0.11\n\nRetira el arreglo de buffers.\n\n' if rollback else '# X6810 RAW v0.11: arreglo de buffers RAW16\n\n') +
            'Deriva de v0.10. Conserva metastore y resoluciones RAW nativas.\n'
            'En pipelinepolicy, la coleccion RAW16 usa max(limite original, 6).\n'
            'No cambia algoritmos de imagen, exposicion ni codecs.\n'
            'Pruebas temporales BSG: ~29 FPS en principal, frontal y tele; ver informe\n'
            'para mediciones exactas y limites. No garantiza 30 FPS con exposiciones largas.\n'
            'Puede requerir mas memoria para buffers simultaneos.\n\n'
            'Instalar sobre x6810_raw12mp en APatch/Magisk y reiniciar.\n'
            'La pareja de bibliotecas y payloads se verifica por SHA-256.\n'
            'Para revertir: x6810-raw-v0.10.0-from-v011-rollback.zip y reiniciar.\n'
            'El ZIP v0.10 antiguo no reconoce el hash de v0.11.\n\n'
            'Informe: docs/VERSION_HISTORY.md\n'
            'Manifest base policy-manifest.json: cambio frontal heredado.\n'
            'Manifest raw-buffers-manifest.json (solo v0.11): delta adicional sobre v0.10.\n').encode()
        files['payload-sha256.json'] = json.dumps({LIB:META10,POL:policy}, indent=2).encode()
        dest = ROOT/'archive/modules'/name
        for rel, data in files.items():
            p=dest/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
        archive=ROOT/'dist'/f'x6810-raw-v{version}.zip'; write_zip(archive, files)
        index.append(dict(file=str(archive.relative_to(ROOT)), sha256=sha(archive.read_bytes()), metastore=META10, policy=policy))
    (ROOT/'dist/v011-package-checksums.json').write_text(json.dumps(index, indent=2)+'\n')
    print(json.dumps(index, indent=2))


if __name__ == '__main__':
    main()
