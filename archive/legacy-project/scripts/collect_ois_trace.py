"""Collect a bounded native OIS trace. Requires an already running local Frida server.
Hooks observe only. --readback uses the vendor's mode-read ioctl; ENOTTY is expected
on the tested kernel. No calibration, firmware-write or actuator-write RPC exists.
"""
import argparse,json,os,subprocess,sys,time,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dist/python-deps'))
import frida
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial',required=True);p.add_argument('--adb',default='adb');p.add_argument('--seconds',type=float,default=20)
p.add_argument('--output',type=Path,required=True);p.add_argument('--address',default='127.0.0.1:27042');p.add_argument('--readback',action='store_true')
args=p.parse_args()
if not 0<args.seconds<=300:p.error('seconds must be in (0,300]')
args.output.parent.mkdir(parents=True,exist_ok=True)
# The caller owns server startup and adb forwarding. Check the chosen serial explicitly.
subprocess.run([args.adb,'-s',args.serial,'get-state'],check=True,timeout=10)
d=frida.get_device_manager().add_remote_device(args.address);session=d.attach('camerahalserver')
f=args.output.open('w',encoding='utf-8');failed=threading.Event()
def message(m,data):
 f.write(json.dumps(m)+'\n');f.flush()
 if m.get('type')=='error':failed.set();print(m,flush=True)
script=session.create_script('globalThis.OIS_READBACK='+str(args.readback).lower()+';\n'+(ROOT/'scripts/trace_ois.js').read_text(encoding='utf-8-sig'))
script.on('message',message)
try:
 script.load();print('TRACE_READY',flush=True)
 deadline=time.monotonic()+args.seconds
 while time.monotonic()<deadline and not failed.is_set():time.sleep(min(.2,max(0,deadline-time.monotonic())))
finally:
 # Frida detach can block on an in-flight vendor callback; bound host shutdown.
 done=threading.Event()
 def detach():
  try:session.detach()
  finally:done.set()
 threading.Thread(target=detach,daemon=True).start()
 if not done.wait(5):
  f.flush();print('Trace saved; detach timed out. Restart camera services before another trace.',flush=True);os._exit(2)
 f.close()
print('Trace saved:',args.output)
if failed.is_set():raise SystemExit(1)
