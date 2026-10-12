"""Host-only installer tests; replace device target and mock permissions.
Never executes installer against a device or a real /vendor target.
"""
from pathlib import Path
import subprocess,hashlib,json,shutil
from host_test_utils import SH, shell_quote as quote, test_tempdir
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'archive/modules/x6810_raw12mp/customize.sh').read_text()
results=[]
with test_tempdir(ROOT, 'base-installer-') as tmp:
    out=Path(tmp)
    for case,bad in [('matching-stock',False),('mismatched-stock',True)]:
        folder=out/case;folder.mkdir(exist_ok=True)
        stock=folder/'stock.so';stock.write_bytes(b'wrong build' if bad else (ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes())
        mod=folder/'module';payload=mod/'system/vendor/lib64/libmtkcam_metastore.so';payload.parent.mkdir(parents=True,exist_ok=True)
        payload.write_bytes((ROOT/'patches/libmtkcam_metastore.so').read_bytes())
        harness=folder/'test.sh'
        stubs='abort() { echo "$*"; exit 91; }\nui_print() { echo "$*"; }\nset_perm() { :; }\nset_perm_recursive() { :; }\n'
        harness.write_text('PATH=/usr/bin:$PATH\nMODPATH='+quote(mod)+'\n'+stubs+text.replace('TARGET=/vendor/lib64/libmtkcam_metastore.so','TARGET='+quote(stock)),encoding='utf-8',newline='\n')
        proc=subprocess.run([str(SH),harness.as_posix()],capture_output=True,text=True,cwd=ROOT)
        expected=91 if bad else 0
        assert proc.returncode==expected,(case,proc.returncode,proc.stdout,proc.stderr)
        if not bad:assert (mod/'backup/libmtkcam_metastore.stock.so').read_bytes()==stock.read_bytes()
        if bad:assert not (mod/'backup').exists()
        results.append(dict(case=case,exit_code=proc.returncode,stdout=proc.stdout))
    # Test boot failure counter in a standalone fixture; no Android operations used.
    counter=out/'boot-counter';counter.mkdir(exist_ok=True)
    script=counter/'post-fs-data.sh';script.write_bytes(b'PATH=/usr/bin:$PATH\n'+(ROOT/'archive/modules/x6810_raw12mp/post-fs-data.sh').read_bytes())
    (counter/'.boot_attempts').write_text('0\n')
    for expected in ('1','2','0'):
        subprocess.run([str(SH),script.as_posix()],check=True, cwd=ROOT)
        assert (counter/'.boot_attempts').read_text().strip()==expected
    assert (counter/'disable').exists()
    results.append(dict(case='two-incomplete-boots-disable-on-third-invocation',passed=True))
output=ROOT/'dist/verification/installer-tests.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(results,indent=2))
print('PASS: stock accepted, mismatched build rejected before backup, stock backup exact, boot counter exercised. Permissions are mocked; no Android mount test.')
