// Read-only: correlate MTK frame magic numbers with result callbacks.
const h=Process.getModuleByName('libcam.hal3a.v3.so');
Interceptor.attach(h.base.add(0x24fa68),{onEnter(a){
 const m=a[1].readPointer().readPointer();
 this.self=a[0]; this.magic=m.add(0x28).readU32();
 },onLeave(){send({event:'parse',self:this.self.toString(),magic:this.magic,mode:this.self.add(0x12c).readU32(),level:this.self.add(0x3fc).readU32()});}});
for(const off of [0x25e040,0x25f3a0])Interceptor.attach(h.base.add(off),{onEnter(a){send({event:'get',offset:off,self:a[0].toString(),magic:a[1].toUInt32(),out:a[2].toString()});}});
send({event:'ready'});
