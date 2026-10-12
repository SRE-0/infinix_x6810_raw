// Read-only request-to-flash correlation; records no image buffers.
const meta=Process.getModuleByName('libmtkcam_metadata.so');
const hal=Process.getModuleByName('libcam.hal3a.v3.so');
function emit(v){send(Object.assign({time:Date.now(),tid:Process.getCurrentThreadId()},v));}
Interceptor.attach(meta.base.add(0x29f88),{onEnter(a){
 if(a[1].isNull())return;
 const count=a[1].add(12).readU32(),offset=a[1].add(20).readU32();
 if(count>4096)return;
 for(let i=0;i<count;i++){
  const e=a[1].add(offset+16*i),tag=e.readU32();
  if(tag===0x40006)emit({event:'raw_strength_entry',count:e.add(4).readU32(),type:e.add(12).readU8(),value:e.add(8).readS32()});
 }
}});
Interceptor.attach(meta.base.add(0x2a1f8),{onEnter(){
 const sp=this.context.sp,tag=sp.add(0x58).readU32();
 if(![0x40002,0x40006,0x10003,0x1000d,0xc0000].includes(tag))return;
 const type=sp.add(0x5c).readU8(),count=sp.add(0x60).readU64().toNumber(),data=sp.add(0x68).readPointer();
 emit({event:'android_metadata',tag:'0x'+tag.toString(16),type,count,value:count?(type===0?data.readU8():data.readS32()):null});
}});
for(const s of hal.enumerateExports()){
 if(s.type!=='function'||!/FlashHal.*(setInfoDuty|setFlashOn|setOnOff)|FlashMgrM.*(setFlashMode|setAeFlashMode|setCapPara|hw_setCapExp)|Hal3AAdapter3.*startCapture/.test(s.name))continue;
 Interceptor.attach(s.address,{onEnter(a){emit({event:'call',name:s.name,self:a[0].toString(),args:[a[1].toString(),a[2].toString(),a[3].toString()],backtrace:s.name.includes('setFlashOn')?Thread.backtrace(this.context,Backtracer.ACCURATE).slice(0,8).map(p=>p.sub(hal.base).toString()):undefined});}});
}
emit({event:'ready'});
