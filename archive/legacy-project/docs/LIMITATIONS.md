# Limitaciones y seguridad

## Compatibilidad estricta

Los parches contienen offsets absolutos dentro de ELF concretos. Una OTA puede recompilar las bibliotecas, mover funciones o cambiar code caves aunque el modelo comercial sea el mismo. Nunca amplíes la lista de hashes aceptados sin repetir el análisis y las pruebas.

## `LEVEL_3` no es certificación

Anunciar `LEVEL_3` permite que las aplicaciones intenten combinaciones avanzadas, pero no prueba el cumplimiento completo del CDD/CTS. El alcance validado es RAW/JPEG en los tres sensores, reprocesado frontal descrito y el comportamiento de preview medido.

## OIS telefoto OV08A10 (experimental)

v0.12 advertises Camera2 OIS ON/OFF and bridges requests to the Transsion BU63169 suspend/resume commands. The control path and all six RAW/JPEG regressions were verified after installation. GCam requires `camera.ois_forced_photo_mode=true` to request OIS in photo mode. This kernel returns `ENOTTY` for the OIS mode-read ioctl and does not publish OIS position samples. Lens motion reduction in a moving scene has not yet been measured; see [the OIS evidence](OIS.md).

The current v0.12.2 resolution candidate is [HD48 + 12 MP](MAIN_RESOLUTION_TRIALS.md). It publishes JPEG 8000×6000, while the measured sensor/IMGO input remains 4000×3000. BSG GCam 9.7 was observed using 4000×3000 RAW/YUV and did not request the HD JPEG. This is processed high-resolution output, not verified native 48 MP or RAW48.

## Frontal Quad Bayer

El stream completo 4640×3488 no debe tratarse como Bayer GRBG 2×2. La revisión actual usa 2320×1744 binned. No ofrece un RAW remosaic de 16 MP y no intenta reconstruirlo por software.

## Rendimiento

Seis buffers eliminan el cuello de cola observado, pero no pueden superar el tiempo de exposición ni las restricciones térmicas/ISP. En poca luz es normal que los FPS bajen.

## Datos de diagnóstico

El repositorio excluye fotografías, DNG, pantallazos, logcats completos, configuraciones de GCam, seriales ADB, dumpsys y rutas de usuario. Para reportar un fallo publica sólo extractos relevantes y redactados junto con hashes de las bibliotecas y versión de firmware.

## Binarios propietarios

Las bibliotecas MediaTek/Transsion no se consideran código fuente del proyecto. Comprueba las condiciones aplicables antes de redistribuir payloads o firmware. Los scripts y manifests permiten auditar exactamente qué bytes se alteraron.
