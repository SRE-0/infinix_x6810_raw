from pathlib import Path
import subprocess,zipfile,argparse,shutil
args=argparse.ArgumentParser(description=__doc__)
args.add_argument("--sdk",type=Path,default=Path(".local-private/research/tools/android-sdk"))
options=args.parse_args()
r=Path.cwd();sdk=options.sdk.resolve();bt=sdk/'build-tools_r35_windows/android-15';jar=sdk/'platform-35_r02/android-35/android.jar';src=r/'scripts/ois-probe';out=r/'dist/ois-probe';cl=out/'classes';cl.mkdir(parents=True,exist_ok=True)
def run(*a):subprocess.run(list(map(str,a)),check=True)
# javac rejects UTF-8 BOMs; normalize editable source files.
for f in src.rglob('*'):
 if f.is_file(): f.write_text(f.read_text(encoding='utf-8-sig'),encoding='utf-8')
run('javac','-encoding','UTF-8','-source','8','-target','8','-cp',jar,'-d',cl,*src.glob('src/**/*.java'))
run('java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--lib',jar,'--min-api','26','--output',out,*cl.rglob('*.class'))
unsigned=out/'unsigned.apk';signed=out/'ois-probe.apk'
run(bt/'aapt.exe','package','-f','-M',src/'AndroidManifest.xml','-I',jar,'-F',unsigned)
with zipfile.ZipFile(unsigned,'a') as z:z.write(out/'classes.dex','classes.dex')
key=out/'debug.keystore'
if not key.exists():
 run(str(Path(shutil.which('javac')).with_name('keytool.exe')),'-genkeypair','-keystore',key,'-storepass','android','-keypass','android','-alias','probe','-keyalg','RSA','-validity','3650','-dname','CN=X6810 OIS Probe')
run('java','-jar',bt/'lib/apksigner.jar','sign','--ks',key,'--ks-pass','pass:android','--out',signed,unsigned)
run('java','-jar',bt/'lib/apksigner.jar','verify',signed)
print(signed)
