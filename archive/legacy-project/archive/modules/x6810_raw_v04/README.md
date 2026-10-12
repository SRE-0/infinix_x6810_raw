# X6810 v0.4: tiempos RAW de HI1631Q y system.prop

Corrige la entrada inicial RAW frontal a 4640×3488, tamaño real del driver y
del DNG. En v0.3 el HAL anunciaba ese tamaño pero conservaba los tiempos bajo
4608×3456; GCam rechazaba sensor ID 1 con frame_readout_time_ms=0.

Incluye el system.prop local solicitado, con vendor.camera.tran.nums=3 y
ro.odm.camera=1, sin lista de paquetes ni comodines inventados. Se mantienen
las demás propiedades del archivo local. Las propiedades exponen cámaras;
no conceden el permiso Android CAMERA ni fuerzan a cada aplicación a usarlas.

Instala como actualización en APatch y reinicia. El id sigue siendo
x6810_raw12mp. Se aceptan stock y versiones v0.1/v0.2/v0.3/v0.4 conocidas.
Los parches de principal y teleobjetivo se conservan.

El tono rosa es un problema distinto: la muestra RAW frontal contiene un
mosaico por bloques 2×2 compatible con Quad Bayer, declarado como GRBG 2×2.
Esta versión NO implementa remosaic ni corrige los píxeles del HAL. No se
alteran CFA o matrices arbitrariamente. El informe COLOR-Y-CRASH-v0.4.md
documenta la evidencia y la conversión fuera del teléfono.

Para volver a v0.3: desactiva el módulo y reinicia; instala el ZIP v0.3
guardado, habilítalo si hace falta y reinicia. Conserva los ZIP anteriores.
