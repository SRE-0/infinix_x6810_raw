"""Collect one camera reproduction without clearing logs or changing app data.

Run, open the app manually, reproduce within --seconds. Requires authorized ADB.
Root is used only to read module metadata and hashes via a pushed shell script.
"""
from pathlib import Path
import argparse
import datetime
import json
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]


def adb(*args):
    p=subprocess.run(['adb',*args],capture_output=True,timeout=60)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
    return p.stdout


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=int,default=30)
    args=parser.parse_args()
    if not 5<=args.seconds<=60:parser.error('--seconds must be 5..60')
    if adb('get-state').strip()!=b'device':raise RuntimeError('ADB device not authorized')
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    dest=ROOT/'local-data/device'/('diagnostic-'+stamp);dest.mkdir()
    remote='/data/local/tmp/x6810-raw-readonly-diagnostic.sh'
    script=dest/'read-only.sh'
    script.write_text('''#!/system/bin/sh
id
sha256sum /vendor/lib64/libmtkcam_metastore.so /vendor/lib64/libmtkcam_3rdparty.customer.so /vendor/lib64/libmtkcam_pipelinepolicy.so
cat /data/adb/modules/x6810_raw12mp/module.prop
cat /data/adb/modules/x6810_raw12mp/system.prop
ls -l /data/adb/modules/x6810_raw12mp/disable /data/adb/modules/x6810_raw12mp/remove
exit 0
''',newline='\n')
    adb('push',str(script),remote)
    # One command string remains quoted through the remote shell. Never use a
    # semicolon-separated adb su argument that silently drops root mid-command.
    root=adb('shell',"su -c 'sh /data/local/tmp/x6810-raw-readonly-diagnostic.sh'")
    (dest/'module-and-hashes.txt').write_bytes(root)
    if b'uid=0(' not in root:raise RuntimeError('Root verification failed; no capture started')
    (dest/'properties.txt').write_bytes(adb('shell','getprop'))
    print('Abre la app y reproduce el fallo ahora; captura durante',args.seconds,'segundos.',flush=True)
    with (dest/'logcat.txt').open('wb') as out,(dest/'logcat-stderr.txt').open('wb') as err:
        proc=subprocess.Popen(['adb','logcat','-b','all','-v','threadtime','-T','1'],stdout=out,stderr=err)
        try:
            adb('shell','log','-t','X6810_RAW_DIAG','BEGIN_'+stamp)
            time.sleep(args.seconds)
        finally:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
    (dest/'dumpsys-media-camera.txt').write_bytes(adb('shell','dumpsys','media.camera'))
    (dest/'crash-buffer.txt').write_bytes(adb('logcat','-b','crash','-d','-v','threadtime','-t','2000'))
    (dest/'capture.json').write_text(json.dumps(dict(start=stamp,seconds=args.seconds,
        changes='Pushed read-only diagnostic script and emitted a log marker; app data and properties untouched'),indent=2))
    print(dest)


if __name__=='__main__':main()
