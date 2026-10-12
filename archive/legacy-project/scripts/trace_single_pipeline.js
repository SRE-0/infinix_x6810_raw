// Read-only mapping of the exact X6810 request parser and flash parameters.
const h=Process.getModuleByName('libcam.hal3a.v3.so');
function emit(v){send(Object.assign({ms:Date.now(),tid:Process.getCurrentThreadId()},v));}
Interceptor.attach(h.base.add(0x24fa68),{onEnter(a){this.obj=a[0];emit({event:'parse',self:a[0].toString(),meta:a[1].readPointer().readPointer().toString()});}});
Interceptor.attach(h.base.add(0x100ee8),{onEnter(a){emit({event:'params',self:a[0].toString(),params:a[1].toString(),mode:a[1].add(0x3c).readU32(),ae:a[1].add(0x20).readU32(),value:a[1].add(0x30c).readU32(),caller:this.returnAddress.sub(h.base).toString()});}});
Interceptor.attach(h.base.add(0x103688),{onEnter(a){emit({event:'gate',on:a[1].toInt32(),single:a[2].toInt32(),value:a[0].add(0x484).readU32()});}});
emit({event:'ready'});
