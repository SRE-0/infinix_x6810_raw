# RAW16 principal, teleobjetivo y frontal candidata del X6810

Esta versión conserva exactamente los hooks y trampolines del parche S5KGM1ST
con el que se comunicó captura RAW funcional. Añade capacidad RAW y entradas
RAW16 a OV08A10 (3264×2448) y OV16B10FF (4608×3456 iniciales). La identidad de
OV16B10FF como frontal y la captura de ambas auxiliares están pendientes de prueba.
El proveedor puede ajustar las dimensiones al área activa del sensor.

## Instalación con APatch

1. Conserva el ZIP v0.1 que ya funciona.
2. Instala `dist/x6810-raw16-v0.2.0-aux-experimental.zip` desde Módulos de APatch.
   Comparte el id `x6810_raw12mp`: actualiza v0.1 en su lugar, sin activar dos
   módulos que monten la misma biblioteca. El instalador admite el original
   exacto, el binario v0.1 conocido y este v0.2; rechaza otras bases.
3. Reinicia. Si el módulo queda desactivado en el gestor, actívalo y reinicia.
4. Comprueba cada cámara por separado en una aplicación Camera2 con RAW.
   Usa los tamaños RAW que publique Camera2, no los tamaños de JPEG ni el zoom
   digital de la cámara principal. Verifica cuál lente captura cubriéndolo.

El instalador guarda la biblioteca visible anterior en
`backup/libmtkcam_metastore.previous.so` junto a su hash; puede ser v0.1,
v0.2 u original. No se etiqueta ese respaldo como stock.

## Verificación y diagnóstico

El hash montado tras reiniciar debe coincidir con `patch-manifest.json`:

```sh
su -c 'sha256sum /vendor/lib64/libmtkcam_metastore.so'
```

Comprueba capacidad RAW, tamaños RAW_SENSOR, captura de varios DNG, JPEG/preview,
orientación y funcionamiento de la principal. Que aparezca RAW en una lista
no demuestra que la captura funcione. Si no aparece el teleobjetivo, primero
hay que resolver su enumeración o acceso por la aplicación.

Desde el PC, para guardar diagnóstico después de reproducir un fallo:

```powershell
adb push scripts/collect-device.sh /data/local/tmp/x6810-collect.sh
adb shell su -c 'sh /data/local/tmp/x6810-collect.sh'
adb pull /sdcard/Download/x6810-camera-diagnostics local-data/device-aux
```

## Volver a la versión funcional

Desactiva el módulo en APatch y reinicia para recuperar la biblioteca original
de vendor. Instala el ZIP v0.1 guardado, comprueba que quede habilitado y reinicia.
El contador de intentos de arranque es una ayuda de recuperación, no garantiza
la recuperación de todos los fallos. El procedimiento de rescate de APatch
está en https://apatch.dev/rescue-bootloop.html.

El procedimiento binario completo está en `docs/BINARY_PATCHES.md`.
No se modifican los originales, `libmtkcam_3rdparty.customer.so`, calibraciones,
matrices de color, kernel ni propiedades de enumeración de cámaras.
