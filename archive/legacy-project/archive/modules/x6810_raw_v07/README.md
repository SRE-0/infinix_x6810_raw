# v0.7: candidato experimental, no correccion confirmada

HI1631Q publica unicamente RAW16 2320x1744. Un guard en updateRawCapability
conserva ese tamano solo si el area activa es 4640x3488; evita que el HAL
lo reescriba al tamano completo. No inyecta los tags remosaic/processRaw de v0.6.
El objetivo es usar la salida del sensor con binning, no convertir Quad Bayer por software.

Las dimensiones RAW deben conservarse tambien al final de la construccion
del proveedor, y P1 debe seleccionar 2320x1744. Esto aun requiere probar el telefono.
No hay confirmacion de color, DNG valido, GCam estable ni mejora de FPS.
Principal y teleobjetivo conservan sus bytes de parche anteriores.

Incluye system.prop con vendor.camera.tran.nums=3. Retira los otros overrides
de procesado de v0.6 para reducir interferencias. No modifica customer.so.
Se instala encima del modulo actual en APatch y requiere un reinicio.
Para volver, usa dist/compatible/*v0.2*-compat1.zip (sin desinstalar previamente).
No uses los ZIP historicos sin compat1 para bajar de version.

Documentacion: docs/VERSION_HISTORY.md.
