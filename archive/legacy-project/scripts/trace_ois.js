// Read-only tracing. No calibration, firmware update or direct actuator commands.
const o = Process.getModuleByName('libtran_oismgr.so');
const a = Process.getModuleByName('libcam.hal3a.v3.so');
const seen = new Map();
function emit(k,v){const s=JSON.stringify(v);if(seen.get(k)!==s){seen.set(k,s);send({time:Date.now(),event:k,...v});}}
for (const e of o.enumerateExports()) {
 if(e.type!=='function'|| !/OISPltDrv/.test(e.name)|| !/(sendCommand|setOisMode|resumeOis|suspendOis|powerOn|setOisNumber|setisMaster|setOEMode)/.test(e.name))continue;
 Interceptor.attach(e.address,{onEnter(args){emit(e.name,{object:args[0].toString(),arg1:args[1].toInt32(),arg2:args[2].toInt32(),fd:args[0].add(8).readS32()});}});
}
for (const e of a.enumerateExports()) {
 if(e.type!=='function'|| !/AfMgr(27setOpticalStabilizationMode|16setOiSModeEnable)/.test(e.name))continue;
 Interceptor.attach(e.address,{onEnter(args){emit(e.name,{object:args[0].toString(),arg1:args[1].toInt32(),arg2:args[2].toInt32()});}});
}
Interceptor.attach(Process.getModuleByName('libc.so').getExportByName('ioctl'),{
 onEnter(args){this.cmd=args[1].toUInt32();this.log=((this.cmd>>>8)&255)===0x70; if(this.log)this.val={fd:args[0].toInt32(),cmd:'0x'+this.cmd.toString(16),arg:args[2].toString()};},
 onLeave(ret){if(this.log)send({time:Date.now(),event:'ois_ioctl',...this.val,result:ret.toInt32()});}
});
send({event:'ready',oisBase:o.base.toString()});

if (globalThis.OIS_READBACK === true) {
const libc=Process.getModuleByName('libc.so');
const readlink=new NativeFunction(libc.getExportByName('readlink'),'int',['pointer','pointer','ulong']);
const ioctlRead=new SystemFunction(libc.getExportByName('ioctl'),'int',['int','ulong','pointer']);
function sample(fd){
 const path=Memory.allocUtf8String('/proc/self/fd/'+fd),target=Memory.alloc(256);
 const n=readlink(path,target,255);if(n<0||target.readUtf8String(n)!=='/dev/bu63169_ois')return;
 const buf=Memory.alloc(4);buf.writeU32(0xffffffff);const r=ioctlRead(fd,0x80047005,buf);
 send({event:'ois_mode_readback',time:Date.now(),fd,result:r.value,errno:r.errno,mode:buf.readU32()});
}
Interceptor.attach(libc.getExportByName('ioctl'),{
 onEnter(args){this.cmd=args[1].toUInt32();this.fd=args[0].toInt32();},
 onLeave(ret){if(ret.toInt32()===0&&[0x7000,0x7001,0x7002].includes(this.cmd)){const fd=this.fd;setTimeout(()=>sample(fd),250);}}
});

}
