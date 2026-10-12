"""Exercise actual v0.3 installer with host paths and mocked Android permissions."""
from pathlib import Path
import subprocess, tempfile, json
from host_test_utils import SH, shell_quote as q, test_tempdir

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'archive/modules/x6810_raw_v04'
script=(MODULE/'customize.sh').read_text()
results=[]
with test_tempdir(ROOT, 'x6810-v04-installer-') as tmp:
    for case in ('stock','main-upgrade','aux-upgrade','front-upgrade','aux-reinstall','wrong-base','bad-payload','active-conflict','disabled-conflict'):
        d=Path(tmp)/case;d.mkdir()
        mod=d/'new';payload=mod/'system/vendor/lib64/libmtkcam_metastore.so';payload.parent.mkdir(parents=True)
        data=(ROOT/('patches/front-v0.3/libmtkcam_metastore.so' if case=='front-upgrade' else 'patches/aux-v0.2/libmtkcam_metastore.so' if case=='aux-upgrade' else 'patches/libmtkcam_metastore.so' if case=='main-upgrade' else
                   'patches/front-v0.4/libmtkcam_metastore.so' if case=='aux-reinstall' else
                   'stock-binaries/libmtkcam_metastore.so')).read_bytes()
        target=d/'live.so';target.write_bytes(b'unknown firmware' if case=='wrong-base' else data)
        payload.write_bytes(b'corrupt' if case=='bad-payload' else (MODULE/'system/vendor/lib64/libmtkcam_metastore.so').read_bytes())
        modules=d/'modules';modules.mkdir()
        if 'conflict' in case:
            other=modules/'other_camera';f=other/'system/vendor/lib64/libmtkcam_metastore.so';f.parent.mkdir(parents=True);f.write_bytes(b'conflict')
            if case=='disabled-conflict':(other/'disable').touch()
        stubs='abort() { echo "$*"; exit 91; }\nui_print() { echo "$*"; }\nset_perm() { :; }\nset_perm_recursive() { :; }\n'
        harness=d/'run.sh'
        harness.write_text('PATH=/usr/bin:$PATH\nMODPATH='+q(mod)+'\n'+stubs+
                           script.replace('TARGET=/vendor/lib64/libmtkcam_metastore.so','TARGET='+q(target)).replace('MODULES=/data/adb/modules','MODULES='+q(modules)),newline='\n')
        p=subprocess.run([str(SH),harness.as_posix()],capture_output=True,text=True)
        reject=case in ('wrong-base','bad-payload','active-conflict')
        assert p.returncode==(91 if reject else 0),(case,p.stdout,p.stderr)
        if reject:assert not (mod/'backup').exists()
        else:assert (mod/'backup/libmtkcam_metastore.previous.so').read_bytes()==target.read_bytes()
        results.append(dict(case=case,exit_code=p.returncode,stdout=p.stdout))
    for p in [*MODULE.glob('*.sh'),MODULE/'META-INF/com/google/android/update-binary']:
        subprocess.run([str(SH),'-n',p.as_posix()],check=True)
(ROOT/'dist/verification/front-v0.4-installer.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: 9 installer cases and shell syntax. Android permissions/mounts not tested.')
