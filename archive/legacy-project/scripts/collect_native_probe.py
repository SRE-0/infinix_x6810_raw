"""Run a bounded, explicitly supplied Frida probe; preserve its messages locally."""
import argparse,json,sys,time,threading,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dist/python-deps'))
import frida
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--process',required=True);p.add_argument('--script',type=Path,required=True)
p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=int,default=90)
a=p.parse_args()
if not 1<=a.seconds<=600:p.error('seconds must be 1..600')
a.output.parent.mkdir(parents=True,exist_ok=True)
session=frida.get_device_manager().add_remote_device('127.0.0.1:27042').attach(a.process)
with a.output.open('w',encoding='utf-8') as f:
 script=session.create_script(a.script.read_text(encoding='utf-8'))
 failed=threading.Event()
 def message(m,data):
  f.write(json.dumps(m)+'\n');f.flush()
  if m.get('type')=='error':failed.set();print(m,flush=True)
 script.on('message',message)
 try:
  script.load();print('PROBE_READY',flush=True)
  end=time.monotonic()+a.seconds
  while time.monotonic()<end and not failed.is_set() and not a.output.with_suffix('.stop').exists():time.sleep(.25)
 finally:
  done=threading.Event()
  def detach():
   try:session.detach()
   finally:done.set()
  threading.Thread(target=detach,daemon=True).start()
  if not done.wait(5):f.flush();print('Detach timed out',flush=True);os._exit(2)
print('PROBE_SAVED',flush=True)
if failed.is_set():raise SystemExit(1)
