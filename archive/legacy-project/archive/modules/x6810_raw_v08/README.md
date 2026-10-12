# X6810: perfil binned v0.8 / reversion emparejada

Instalar mediante APatch o Magisk sobre x6810_raw12mp y reiniciar.
El instalador exige la pareja exacta stock, v0.7 o v0.8 comprobada.
No acepta otros firmwares ni combinaciones arbitrarias de bibliotecas.

v0.8: RAW frontal 2320x1744. Filtra las salidas procesadas frontales mayores
que 2320x1744 y sus duraciones; conserva comprobaciones de tamano en la
seleccion de PREVIEW. Esto reduce las resoluciones disponibles en TODAS
las apps que usan esa frontal; no habilita RAW nativo de 16 MP ni remosaic.
No modifica las matrices de color, ni iopipe, ni customer.
Mantiene los parches traseros de v0.7. Previews principal y tele probadas.

Validacion 2026-09-23: montaje temporal de ambas bibliotecas, MGC
com.android.MGC_9_7_047, preview frontal y dos capturas JPEG+DNG.
Una captura de hoja blanca mostro colores razonables tanto en JPEG como
en revelado independiente LibRaw. No equivale a calibracion colorimetrica.
No se ha validado instalacion persistente/reinicio, video, todas las apps,
todas las combinaciones Camera2 ni estabilidad prolongada.

Para volver a v0.7 desde v0.8, instalar
dist/x6810-raw-v0.7.0-paired-rollback.zip y reiniciar. Incluye el metastore
v0.7 Y pipelinepolicy original, para retirar ambas mitades del cambio.
No usar los antiguos ZIP compat1 para revertir esta pareja.
Desactivar el modulo y reiniciar elimina sus montajes systemless.
El contador de arranque heredado es una ayuda, no garantiza recuperacion.

Informe: docs/VERSION_HISTORY.md.
