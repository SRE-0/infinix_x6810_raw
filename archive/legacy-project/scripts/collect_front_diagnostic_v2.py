"""Collect a labelled reproduction, active dumpsys, kernel and loaded libraries.

No module installation, service restart, setprop, log clearing or app-data writes.
Root shell scripts are sent on stdin, not installed on the phone. A log marker
is emitted. Run manually with the app ready, then reproduce during the window.
"""
import argparse
import datetime
import json
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = r'''id
uname -a
getconf PAGESIZE
for key in ro.product.model ro.product.device ro.build.fingerprint ro.vendor.build.fingerprint ro.build.version.release ro.build.version.sdk ro.vendor.build.security_patch; do
  echo "PROPERTY $key"
  getprop "$key"
done
for lib in libmtkcam_metastore.so libmtkcam_pipelinepolicy.so libmtkcam_3rdparty.customer.so libmtkcam_hwnode.so libmtkcam_featurepolicy.so; do
  sha256sum "/vendor/lib64/$lib"
done
for mod in /data/adb/modules/* /data/adb/modules_update/*; do
  [ -d "$mod" ] || continue
  echo "MODULE $mod"
  cat "$mod/module.prop"
  for flag in disable remove skip_mount; do
    [ ! -e "$mod/$flag" ] || echo "FLAG $flag"
  done
  if [ "${mod##*/}" = x6810_raw12mp ]; then
    cat "$mod/system.prop"
    ls -l "$mod/system/vendor/lib64"
    sha256sum "$mod/system/vendor/lib64/"*.so
  fi
done
echo CAMERA_PROPERTIES
getprop | grep -i -E 'camera|cam3|magisk|apatch'
echo CAMERA_LIBRARY_CANDIDATES
for pattern in /vendor/lib64/*sensor*.so /vendor/lib64/*remosaic*.so /vendor/lib64/*dng*.so /vendor/lib64/*camalgo*.so /vendor/lib64/libmtkcam*.so; do
  [ ! -f "$pattern" ] || ls -l "$pattern"
done
echo CAMERA_PROCESSES
ps -A
echo SHELL_MOUNTINFO
cat /proc/self/mountinfo
'''
PROCESSES = r'''echo CAMERA_PROCESS_VIEWS
for proc in /proc/[0-9]*; do
  [ -r "$proc/cmdline" ] || continue
  name=$(tr '\000' ' ' < "$proc/cmdline" 2>/dev/null)
  case "$name" in
    /system/bin/cameraserver*|*/android.hardware.camera.provider*|*/vendor.mediatek.hardware.camera*)
      echo "PROCESS $proc $name"
      cat "$proc/maps"
      cat "$proc/mountinfo"
      for lib in libmtkcam_metastore.so libmtkcam_pipelinepolicy.so libmtkcam_3rdparty.customer.so; do
        sha256sum "$proc/root/vendor/lib64/$lib"
      done
      ;;
  esac
done
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--label', required=True, help='e.g. mgc-front-v07')
    parser.add_argument('--package', default='org.codeaurora.snapcam')
    parser.add_argument('--serial', help='ADB serial if more than one device is connected')
    args = parser.parse_args()
    if not 15 <= args.seconds <= 60:
        parser.error('--seconds must be 15..60')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', args.label):
        parser.error('--label accepts 1..60 ASCII letters, digits, _ or -')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+', args.package):
        parser.error('Invalid package name')
    prefix = ['adb'] + (['-s',args.serial] if args.serial else [])
    status = subprocess.run(prefix+['get-state'], capture_output=True, timeout=10)
    if status.returncode or status.stdout.strip()!=b'device':
        raise SystemExit('Se necesita un dispositivo ADB autorizado. '+status.stderr.decode(errors='replace'))
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    dest = ROOT/'local-data/device'/f'diagnostic-v2-{stamp}-{args.label}'
    dest.mkdir(parents=True)
    records = []

    def capture(name, command, stdin=None, timeout=15):
        started = datetime.datetime.now().isoformat()
        try:
            p = subprocess.run(prefix+command, input=stdin, capture_output=True, timeout=timeout)
            out,err,code = p.stdout,p.stderr,p.returncode
            state = 'completed'
        except subprocess.TimeoutExpired as e:
            out,err,code = e.stdout or b'',e.stderr or b'',None
            state = 'timeout'
        (dest/(name+'.txt')).write_bytes(out)
        (dest/(name+'.stderr.txt')).write_bytes(err)
        # A zero shell exit code doesn't prove that every nested read succeeded.
        return dict(name=name,started=started,exit_code=code,state=state,bytes=len(out))

    def root_capture(name, script, timeout=15):
        return capture(name,['shell','su -c sh'],script.encode('utf-8'),timeout)

    (dest/'identity-readonly.sh').write_text(IDENTITY,encoding='utf-8',newline='\n')
    (dest/'processes-readonly.sh').write_text(PROCESSES,encoding='utf-8',newline='\n')
    records.append(root_capture('identity-modules-hashes',IDENTITY,30))
    identity = (dest/'identity-modules-hashes.txt').read_bytes()
    root_verified = b'uid=0(' in identity
    if not root_verified:
        print('Root no confirmado: se continuara con los datos accesibles; revisar stderr.',flush=True)
    records.append(capture('app-package',['shell','dumpsys','package',args.package]))
    records.append(root_capture('kernel-before','dmesg\n'))
    print(f'AHORA reproduce {args.label} durante {args.seconds}s. Manten la camara abierta hasta terminar.',flush=True)
    jobs=[]
    with (dest/'logcat-all.txt').open('wb') as out, (dest/'logcat-all.stderr.txt').open('wb') as err:
        proc=subprocess.Popen(prefix+['logcat','-b','all','-v','threadtime','-T','1'],stdout=out,stderr=err)
        try:
            records.append(capture('begin-marker',['shell','log','-t','X6810_RAW_DIAG','BEGIN_'+args.label+'_'+stamp]))
            began=time.monotonic()
            with ThreadPoolExecutor(max_workers=2) as pool:
                for index,part in enumerate([0.25,0.5,0.75],1):
                    delay=began+args.seconds*part-time.monotonic()
                    if delay>0: time.sleep(delay)
                    jobs.append(pool.submit(capture,f'camera-active-{index}', ['shell','dumpsys','media.camera']))
                    if index==2:
                        jobs.append(pool.submit(root_capture,'camera-processes-active',PROCESSES,20))
                delay=began+args.seconds-time.monotonic()
                if delay>0: time.sleep(delay)
                for job in jobs: records.append(job.result())
            records.append(capture('end-marker',['shell','log','-t','X6810_RAW_DIAG','END_'+args.label+'_'+stamp]))
        finally:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait()
    records.append(root_capture('kernel-after','dmesg\n'))
    records.append(capture('crash-buffer',['logcat','-b','crash','-d','-v','threadtime','-t','2000']))
    (dest/'capture.json').write_text(json.dumps(dict(label=args.label,package=args.package,
        requested_seconds=args.seconds,root_verified=root_verified,logcat_exit_code=proc.returncode,
        records=records,changes='Log markers only; root scripts read state via stdin',
        limitations=['No CaptureResult per-frame export','No image files or app configuration collected',
            'Process namespace path hashes describe files visible at capture, not hashes of mapped memory',
            'Inspect stderr and timestamps; failed reads may coexist with exit code zero']),indent=2),encoding='utf-8')
    print('Captura terminada:',dest)
    print('Adjuntar este directorio, configuracion exportada y DNG/JPEG originales de la prueba.')


if __name__=='__main__':
    main()
