// Read-only inspection of the hash-locked GSI framework object layout.
const exe=Process.mainModule;
for (const offset of [0x14f2ec,0x14f31c,0x13f130]) {
 Interceptor.attach(exe.base.add(offset),{onEnter(a){
  send({event:'framework',offset:'0x'+offset.toString(16),self:a[0].toString(),arg:a[1].toString(),
    memory:hexdump(a[0],{length:0x150,header:false,ansi:false})});
 }});
}
send({event:'ready',base:exe.base.toString()});
