// Temporary, bounded native experiment. Translates only explicit manual SINGLE
// strength to the existing per-request vendor field before VNDK filtering.
const base=Process.mainModule.base;
const update=new NativeFunction(base.add(0x377030),'int',['pointer','uint','pointer','ulong']);
let seen=0;
function entry(metadata,tag){
 const p=metadata.add(8).readPointer();if(p.isNull())return null;
 const count=p.add(12).readU32(),offset=p.add(20).readU32();if(count>4096)return null;
 for(let i=0;i<count;i++){const e=p.add(offset+i*16);if(e.readU32()===tag&&e.add(4).readU32()===1){
  const type=e.add(12).readU8();return type===0?e.add(8).readU8():type===1?e.add(8).readS32():null;
 }}return null;
}
Interceptor.attach(base.add(0x2ac57c),{onEnter(a){
 if(seen++<8)send({event:'filter_call',caller:this.returnAddress.sub(base).toString(),version:a[0].toInt32(),isStatic:a[2].toInt32(),object:hexdump(a[1],{length:32}),buffer:hexdump(a[1].add(8).readPointer(),{length:64})});
 if(a[2].toInt32()!==0||!this.returnAddress.equals(base.add(0x2198c8)))return;
 const strength=entry(a[1],0x40006),mode=entry(a[1],0x40002),ae=entry(a[1],0x10003);
 if(strength===null)return;
 send({event:'request',strength,mode,ae});
 if(mode!==1||![0,1].includes(ae)||strength<1||strength>30)return;
 const value=Memory.alloc(4);value.writeU32(0x68100000+strength);
 const status=update(a[1],0xc000008c,value,1);
 send({event:'transport',strength,status});
}});
send({event:'ready',kind:'experimental framework per-request SINGLE transport'});
