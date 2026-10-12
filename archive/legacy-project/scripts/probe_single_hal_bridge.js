// Temporary experiment: exact duty only inside the existing main SINGLE ON call.
// No new ON commands; fixed hardware watchdog 300 ms; OEM OFF path unchanged.
const hal=Process.getModuleByName('libcam.hal3a.v3.so');
const active=new Map();
function emit(v){send(Object.assign({time:Date.now(),tid:Process.getCurrentThreadId()},v));}
Interceptor.attach(hal.base.add(0x100ee8),{onEnter(a){
 const mode=a[1].add(0x3c).readU32(),value=a[1].add(0x30c).readU32();
 if(mode===1)emit({event:'params',sensor:a[0].add(0xc4).readU32(),mode,ae:a[1].add(0x20).readU32(),value});
}});
Interceptor.attach(hal.base.add(0x103688),{onEnter(a){
 this.tid=Process.getCurrentThreadId();this.previous=active.get(this.tid);
 const value=a[0].add(0x484).readU32(),sensor=a[0].add(0xc4).readU32();
 emit({event:'single_gate',sensor,on:a[1].toInt32(),single:a[2].toInt32(),value});
 const level=value-0x68100000;
 if(sensor===1&&a[1].toInt32()===1&&a[2].toInt32()===1&&level>=1&&level<=30)active.set(this.tid,level);
 },onLeave(){if(this.previous===undefined)active.delete(this.tid);else active.set(this.tid,this.previous);}});
Interceptor.attach(hal.base.add(0x229140),{onEnter(a){
 const level=active.get(Process.getCurrentThreadId());
 if(level===undefined||a[0].add(0x30).readU32()!==1)return;
 const oldDuty=a[1].toInt32(),oldTimeout=a[2].toInt32();
 a[1]=ptr(a[1].and(ptr('0xffffffff00000000')).or(ptr(level-1)));
 a[2]=ptr(a[2].and(ptr('0xffffffff00000000')).or(ptr(300)));
 emit({event:'fixed_single',level,duty:level-1,oldDuty,oldTimeout,timeout:300});
}});
send({event:'ready',kind:'experimental SINGLE pulse-bound duty'});
