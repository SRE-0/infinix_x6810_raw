"""Build standalone diagnostic APK from the official SDK; no Gradle/dependencies."""
from pathlib import Path
import subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'dist/reprocess-probe'
SDK=ROOT/'local-data/android-sdk'
BT=SDK/'build-tools_r35_windows/android-15'
JAR=SDK/'platform-35_r02/android-35/android.jar'
OUT=P/'build';OUT.mkdir(exist_ok=True)
CL=OUT/'classes';CL.mkdir(exist_ok=True)
def run(*args):subprocess.run([str(a) for a in args],check=True)
run('javac','-source','8','-target','8','-cp',JAR,'-d',CL,*P.glob('src/**/*.java'))
run('java','-cp',BT/'lib/d8.jar','com.android.tools.r8.D8','--lib',JAR,'--min-api','26','--output',OUT,*CL.rglob('*.class'))
unsigned=OUT/'probe-unsigned.apk';signed=OUT/'probe.apk'
run(BT/'aapt.exe','package','-f','-M',P/'AndroidManifest.xml','-I',JAR,'-F',unsigned)
with zipfile.ZipFile(unsigned,'a') as z:z.write(OUT/'classes.dex','classes.dex')
key=OUT/'debug.keystore'
if not key.exists():run('C:/Program Files/Java/jdk-21.0.12/bin/keytool.exe','-genkeypair','-keystore',key,'-storepass','android','-keypass','android','-alias','probe','-keyalg','RSA','-validity','3650','-dname','CN=X6810 Local Probe')
run('java','-jar',BT/'lib/apksigner.jar','sign','--ks',key,'--ks-pass','pass:android','--out',signed,unsigned)
run('java','-jar',BT/'lib/apksigner.jar','verify',signed)
print(signed)
