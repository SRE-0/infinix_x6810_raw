# X6810 RAW v0.9: reprocesado frontal

Instalar en APatch/Magisk sobre x6810_raw12mp y reiniciar. Verifica parejas
exactas de metastore/pipelinepolicy stock, v0.7, v0.8 y v0.9.

Conserva el RAW frontal binned de v0.8 (2320x1744) y su filtro de salidas
procesadas. Agrega PRIVATE_REPROCESSING y YUV_REPROCESSING SOLO al constructor
HI1631Q. La rutina original updateReprocessCapabilities genera el mapa de
entrada/salida, una entrada maxima y modos ZSL. No cambia iopipe, customer,
matrices de color ni configuracion trasera. Principal y tele ya tenian ambas
capacidades. No implementa remosaic ni RAW frontal de 16 MP.

Validacion 2026-09-24: PRIVATE->JPEG, PRIVATE->YUV, YUV->JPEG y YUV->YUV
ejecutados mediante createReprocessableCaptureSession, ImageWriter y
createReprocessCaptureRequest. Cuatro salidas 1968x864 con timestamp igual
al frame de origen. BSG conserva preview frontal y guarda JPEG+DNG.
52 constructores emulados: solo HI1631Q cambia sus dos capabilities.

Limites: el HAL publica actualmente entradas 1968x864; no afirmar
reprocesado de 16 MP ni cumplimiento CTS completo. No se han probado todas
las combinaciones de streams, video, calidad bajo toda iluminacion o
estabilidad prolongada. El RAW DNG exportado por GCam puede incluir recorte
y fusion. La hoja neutra de v0.8 demuestra un caso de color razonable,
no una calibracion colorimetrica universal.

Reversion directa: dist/x6810-raw-v0.8.0-from-v09-rollback.zip, reiniciar.
Para bajar luego a v0.7, usar el rollback emparejado v0.7 desde v0.8.
No usar los antiguos ZIP compat1 directamente sobre v0.9.
Desactivar el modulo y reiniciar elimina sus montajes systemless.

Fuentes, cambios y evidencias: docs/VERSION_HISTORY.md.
