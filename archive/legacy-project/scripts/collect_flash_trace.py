"""Bounded read-only native flash trace; requires running Frida and ADB forwarding."""
import argparse
import json
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dist/python-deps'))
import frida

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--seconds', type=float, default=45)
args = p.parse_args()
if not 0 < args.seconds <= 120: p.error('seconds must be in (0,120]')
args.output.parent.mkdir(parents=True, exist_ok=True)
device = frida.get_device_manager().add_remote_device('127.0.0.1:27042')
session = device.attach('camerahalserver')
with args.output.open('w', encoding='utf-8') as output:
    script = session.create_script((ROOT / 'scripts/trace_flash.js').read_text())
    def message(m, data):
        output.write(json.dumps(m) + '\n')
        output.flush()
    script.on('message', message)
    try:
        script.load()
        print('TRACE_READY', flush=True)
        time.sleep(args.seconds)
    finally:
        session.detach()
print('Trace saved')
