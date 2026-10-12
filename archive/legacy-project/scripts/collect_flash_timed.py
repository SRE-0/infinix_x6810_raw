"""Bounded observational capture; stop early by creating OUTPUT/STOP."""
import argparse, json, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dist/python-deps'))
import frida
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--output', required=True, type=Path)
p.add_argument('--seconds', type=int, default=900)
a = p.parse_args()
if not 1 <= a.seconds <= 1800: p.error('seconds must be 1..1800')
a.output.mkdir(parents=True, exist_ok=True)
adb = ['adb', '-s', a.serial]
subprocess.run(adb + ['get-state'], check=True, timeout=10)
streams = []
children = []
session = None
try:
    for name, cmd in [('logcat', ['logcat','-b','all','-v','epoch','-T','1']),
                      ('kernel', ['shell','su','-c','dmesg -w'])]:
        f = (a.output / (name+'.txt')).open('wb'); streams.append(f)
        children.append(subprocess.Popen(adb+cmd, stdout=f, stderr=subprocess.STDOUT))
    session = frida.get_device_manager().add_remote_device('127.0.0.1:27042').attach('camerahalserver')
    with (a.output/'native.jsonl').open('w', encoding='utf-8') as f:
        script = session.create_script((ROOT/'scripts/trace_flash_timed.js').read_text())
        def message(m, data):
            f.write(json.dumps(m)+'\n'); f.flush()
        script.on('message', message)
        script.load()
        print('TRACE_READY', flush=True)
        deadline = time.monotonic()+a.seconds
        while time.monotonic()<deadline and not (a.output/'STOP').exists(): time.sleep(.25)
        session.detach(); session=None
finally:
    if session is not None: session.detach()
    for child in children:
        child.terminate()
        try: child.wait(timeout=5)
        except subprocess.TimeoutExpired: child.kill(); child.wait()
    for stream in streams: stream.close()
print('TRACE_SAVED', flush=True)
