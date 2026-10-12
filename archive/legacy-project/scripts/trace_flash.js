// Observational hooks only; no arguments or return values are changed.
const hal = Process.getModuleByName('libcam.hal3a.v3.so');
for (const symbol of hal.enumerateExports()) {
  if (symbol.type !== 'function' || !/StrobeDrvFlashlight.*(setDuty|setOnOff|setTimeOutTime|setDriver)|FlashHal.*(setTorchDuty|setFlashOn)|cust_getFlashHalTorchDuty/.test(symbol.name)) continue;
  Interceptor.attach(symbol.address, {
    onEnter(args) { this.name = symbol.name; send({event:'call', name:this.name, args:[args[0].toString(),args[1].toInt32(),args[2].toInt32()]}); },
    onLeave(ret) { send({event:'return',name:this.name,result:ret.toInt32()}); }
  });
}
send({event:'ready'});
