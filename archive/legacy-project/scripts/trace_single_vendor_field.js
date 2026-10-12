const m=Process.getModuleByName('libmtkcam_metadata.so');
Interceptor.attach(m.base.add(0x2a200),{onEnter(){
 const sp=this.context.sp,tag=sp.add(0x58).readU32();
 if(tag!==0xc000008c)return;
 send({event:'vendor_map',mapped:this.context.x0.toString(),type:sp.add(0x5c).readU8(),value:sp.add(0x68).readPointer().readS32()});
}});
send({event:'ready'});
