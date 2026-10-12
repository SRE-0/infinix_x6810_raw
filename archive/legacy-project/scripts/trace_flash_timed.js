// Read-only observation of the vendor flash path. No driver commands are issued.
const start = Date.now();
let seq = 0;
function emit(data) { send(Object.assign({seq: ++seq, epochMs: Date.now(), elapsedMs: Date.now()-start, tid: Process.getCurrentThreadId()}, data)); }
const hal = Process.getModuleByName('libcam.hal3a.v3.so');
let hooks = 0;
for (const s of hal.enumerateExports()) {
  if (s.type !== 'function' || !/StrobeDrvFlashlight.*(setDuty|setOnOff|setTimeOutTime|setDriver)|FlashHal.*(setTorchDuty|setFlashOn|setInfoDuty|sendCustom3ACtrl)/.test(s.name)) continue;
  Interceptor.attach(s.address, {
    onEnter(a) { this.name=s.name; emit({event:'call',name:s.name,self:a[0].toString(),args:[a[1].toInt32(),a[2].toInt32(),a[3].toInt32()],raw:[a[1].toString(),a[2].toString(),a[3].toString()],sensorDev:a[0].add(0x30).readS32(),luminance:a[0].add(0x2d8).readS32()}); },
    onLeave(r) { emit({event:'return',name:this.name,result:r.toInt32()}); }
  });
  hooks++;
}
const libc = Process.getModuleByName('libc.so');
Interceptor.attach(libc.getExportByName('ioctl'), {
  onEnter(a) {
    const cmd=a[1].toUInt32();
    if (![0xc004531e,0x80045364,0x8004536e,0x80045373].includes(cmd)) return;
    this.traced=true; this.cmd=cmd;
    try { emit({event:'ioctl',fd:a[0].toInt32(),cmd:'0x'+cmd.toString(16),type:a[2].readS32(),ct:a[2].add(4).readS32(),arg:a[2].add(8).readS32()}); }
    catch(e) { emit({event:'decode-error',error:String(e)}); }
  },
  onLeave(r) { if(this.traced) emit({event:'ioctl-return',cmd:'0x'+this.cmd.toString(16),result:r.toInt32()}); }
});
emit({event:'ready',hooks});
