"""Run actual repackaged installers against every known visible library."""
from package_compatible_modules import ROOT, LIB, registry
import subprocess
import tempfile
import zipfile
import json

SH = 'C:/Program Files/Git/usr/bin/sh.exe'


def quote(p):
    return "'"+str(p).replace('\\', '/').replace("'", "'\\''")+"'"


def main():
    registry()  # Verify binary provenance before exercising acceptance.
    versions = [ROOT/'stock-binaries/libmtkcam_metastore.so',
                *sorted((ROOT/'patches').rglob('libmtkcam_metastore.so'))]
    rows = []
    with tempfile.TemporaryDirectory(prefix='x6810-compat-') as tmp:
        for archive in sorted((ROOT/'dist/compatible').glob('*.zip')):
            with zipfile.ZipFile(archive) as z:
                script = z.read('customize.sh').decode()
                data = z.read(LIB)
            for case in [*versions, 'wrong-base', 'bad-payload', 'active-conflict', 'disabled-conflict']:
                d = __import__('pathlib').Path(tmp)/str(len(rows)); d.mkdir()
                mod = d/'new'; p = mod/LIB; p.parent.mkdir(parents=True)
                p.write_bytes(b'corrupt' if case == 'bad-payload' else data)
                live = d/'live.so'
                live.write_bytes(case.read_bytes() if hasattr(case, 'read_bytes') else
                    b'unsupported' if case == 'wrong-base' else versions[0].read_bytes())
                modules = d/'modules'; modules.mkdir()
                if case in ('active-conflict', 'disabled-conflict'):
                    c = modules/'another_camera'/LIB; c.parent.mkdir(parents=True); c.write_bytes(b'x')
                    if case == 'disabled-conflict': (modules/'another_camera/disable').touch()
                harness = d/'run.sh'
                changed = script.replace('TARGET=/vendor/lib64/libmtkcam_metastore.so', 'TARGET='+quote(live))
                changed = changed.replace('MODULES=/data/adb/modules', 'MODULES='+quote(modules))
                changed = changed.replace('for other in /data/adb/modules/*;', 'for other in '+quote(modules)+'/*;')
                harness.write_text('PATH=/usr/bin:$PATH\nMODPATH='+quote(mod)+'\n'+
                    'abort() { echo "$*"; exit 91; }\nui_print() { :; }\n'+
                    'set_perm() { :; }\nset_perm_recursive() { :; }\n'+changed, newline='\n')
                result = subprocess.run([SH, harness.as_posix()], capture_output=True, text=True)
                reject = case in ('wrong-base', 'bad-payload', 'active-conflict')
                assert result.returncode == (91 if reject else 0), (archive.name, case, result.stdout, result.stderr)
                if not reject:
                    assert (mod/'backup/libmtkcam_metastore.previous.so').read_bytes() == live.read_bytes()
                else:
                    assert not (mod/'backup').exists()
                rows.append(dict(archive=archive.name, case=str(case), rejected=reject, exit=result.returncode))
    (ROOT/'dist/verification/compatible-installers.json').write_text(json.dumps(rows, indent=2)+'\n')
    print(f'PASS {len(rows)} installer executions; upgrades, downgrades, payload and base rejection, conflicts, backups')


if __name__ == '__main__': main()
