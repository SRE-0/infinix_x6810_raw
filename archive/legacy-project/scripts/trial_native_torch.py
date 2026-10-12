"""Stage and execute a bounded, hash-checked three-binary bind-mount trial."""
import hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'patches/native-torch'
REMOTE='/data/local/tmp/x6810-native-torch'
TARGETS={'libcam.hal3a.v3.so':'/vendor/lib64/libcam.hal3a.v3.so',
         'libmtkcam_device3_hal.so':'/vendor/lib64/libmtkcam_device3_hal.so',
         'cameraserver':'/system/bin/cameraserver'}
def adb(*args):return subprocess.run(['adb',*args],check=True)
def main():
    adb('shell','mkdir','-p',REMOTE)
    adb('shell','su','-c','rm -f '+REMOTE+'/stop')
    checks=[];mounts=[];undo=[]
    for name,target in TARGETS.items():
        m=json.loads((OUT/(name+'.json')).read_text())
        if hashlib.sha256((OUT/name).read_bytes()).hexdigest()!=m['output_sha256']:raise ValueError(name)
        adb('push',str(OUT/name),REMOTE+'/'+name+'.incoming')
        adb('shell','su','-c',f'mv {REMOTE}/{name}.incoming {REMOTE}/{name}')
        for path,digest in [(target,m['input_sha256']),(REMOTE+'/'+name,m['output_sha256'])]:
            checks.append(f'[ "$(sha256sum {path} | cut -d " " -f 1)" = "{digest}" ]')
        flag='m'+str(len(mounts))
        context='u:object_r:cameraserver_exec:s0' if name=='cameraserver' else 'u:object_r:vendor_file:s0'
        mount=f'chmod 0755 {REMOTE}/{name}\nchcon {context} {REMOTE}/{name}\nmount -o bind {REMOTE}/{name} {target}\n{flag}=1'
        # /data is nosuid; this isolated executable bind needs domain transition.
        # Do not change /data mount flags or weaken SELinux policy.
        if name=='cameraserver':mount+=f'\nmount -o remount,bind,suid {target}'
        mounts.append(mount)
        undo.insert(0,f'[ "${flag}" = 0 ] || umount {target}')
    script='''#!/system/bin/sh
set -eu
'''+ '\n'.join(checks)+'''
m0=0; m1=0; m2=0
cleanup() {
 trap - EXIT HUP INT TERM
 set +e
 am force-stop org.x6810.flashcontrol
 stop cameraserver
 stop camerahalserver
'''+ '\n'.join(undo)+'''
 start camerahalserver
 start cameraserver
 echo NATIVE_TRIAL_RESTORED
}
trap cleanup EXIT HUP INT TERM
am force-stop com.transsion.camera
am force-stop com.android.MGC_9_7_047
am force-stop org.x6810.flashcontrol
stop cameraserver
stop camerahalserver
'''+ '\n'.join(mounts)+'''
start camerahalserver
start cameraserver
echo NATIVE_TRIAL_READY
i=0
while [ "$i" -lt 600 ] && [ ! -e __TRIAL_STOP__ ]; do
 sleep 1
 i=$((i+1))
done
'''.replace('__TRIAL_STOP__', REMOTE+'/stop')
    path=OUT/'trial.sh';path.write_text(script,newline='\n')
    adb('push',str(path),REMOTE+'/trial.sh')
    adb('shell','su','-c','sh '+REMOTE+'/trial.sh')
if __name__=='__main__':main()
