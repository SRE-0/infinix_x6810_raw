# X6810 RAW v0.10: salidas frontales 2320x1744

Version derivada de v0.9. Anade tuplas JPEG/YUV 2320x1744 al constructor
HI1631Q. El HAL deriva PRIVATE, YV12 y entradas PRIVATE/YUV 2320x1744.
Mantiene tamanos menores y el filtro que impide seleccionar salidas mayores
que el modo binned. RAW sigue siendo 2320x1744. No cambia las otras camaras,
pipelinepolicy, iopipe, calibracion ni modos del sensor.

Validacion 2026-09-24: cuatro rutas PRIVATE/YUV -> JPEG/YUV a 2320x1744,
capturas directas RAW/JPEG/YUV/PRIVATE y peticion YV12 a 2320x1744.
ImageReader presenta la peticion YV12 como YUV_420_888 planar (format=35).
BSG conserva preview y guarda JPEG+DNG. No es certificacion CTS ni prueba
de video o estabilidad prolongada. GCam puede exportar dimensiones distintas
por recorte, zoom o escalado; el maximo del stream no fuerza cada foto a 4 MP.

Instalar sobre x6810_raw12mp en APatch/Magisk y reiniciar. Se verifican ambas
bibliotecas como pareja exacta. Rollback directo desde v0.10:
dist/x6810-raw-v0.9.0-from-v010-rollback.zip, instalar y reiniciar.
No usar directamente sobre v0.10 los ZIP antiguos sin este reconocimiento.
Desactivar el modulo y reiniciar elimina sus montajes systemless.

Informe: docs/BINARY_PATCHES.md.
