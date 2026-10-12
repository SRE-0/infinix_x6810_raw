"""Capture evidence while the user manually tests camera modes. No app/device changes."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--label', required=True, help='Release or capture label for the evidence folder')
    parser.add_argument('--seconds', type=int, default=90)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.label) or not 5 <= args.seconds <= 600:
        parser.error('Simple label required; duration must be 5..600 seconds')
    adb = ['adb', '-s', args.serial]
    if subprocess.check_output(adb + ['get-state'], timeout=10).strip() != b'device':
        raise SystemExit('Device is not connected/authorized')
    root = Path(__file__).resolve().parents[1]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = root / 'dist/main-resolution-device' / (args.label + '-' + stamp)
    output.mkdir(parents=True, exist_ok=False)
    commands = []

    def save(name, arguments):
        try:
            result = subprocess.run(adb + arguments, capture_output=True, timeout=25)
            (output / name).write_bytes(result.stdout)
            (output / (name + '.stderr')).write_bytes(result.stderr)
            commands.append(dict(file=name, returncode=result.returncode))
        except subprocess.TimeoutExpired:
            commands.append(dict(file=name, error='timeout'))

    save('camera-before.txt', ['shell', 'dumpsys', 'media.camera'])
    save('firmware.txt', ['shell', 'getprop', 'ro.build.fingerprint'])
    save('gcam.txt', ['shell', 'dumpsys', 'package', 'com.android.MGC_9_7_047'])
    save('hashes.txt', ['shell', 'sha256sum', '/vendor/lib64/libmtkcam_metastore.so', '/vendor/lib64/libmtkcam_pipelinepolicy.so'])
    print(f'Capturing {args.seconds}s: manually open GCam and take the target photos. Output: {output}', flush=True)
    with (output / 'logcat.txt').open('wb') as log, (output / 'logcat.stderr').open('wb') as error:
        process = subprocess.Popen(adb + ['logcat', '-b', 'all', '-v', 'threadtime', '-T', '1'], stdout=log, stderr=error)
        start = time.monotonic()
        try:
            while time.monotonic() - start < args.seconds:
                if process.poll() is not None:
                    raise RuntimeError(f'logcat exited early: {process.returncode}')
                time.sleep(min(0.25, max(0, args.seconds - (time.monotonic() - start))))
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            commands.append(dict(file='logcat.txt', elapsed_seconds=time.monotonic() - start))
            (output / 'collection.json').write_text(json.dumps(commands, indent=2), encoding='utf-8')
    save('camera-after.txt', ['shell', 'dumpsys', 'media.camera'])
    save('kernel.txt', ['exec-out', 'su', '--no-pty', '-c', 'dmesg'])
    (output / 'collection.json').write_text(json.dumps(commands, indent=2) + '\n', encoding='utf-8')
    print(output)


if __name__ == '__main__':
    main()
