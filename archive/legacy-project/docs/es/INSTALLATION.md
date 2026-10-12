# Instalación y recuperación

## Requisitos

- Infinix Zero X Neo **X6810-GL**.
- Android 16 / API 36 y los binarios de cámara admitidos por el instalador.
- APatch y espacio suficiente para conservar un respaldo systemless.
- Ningún otro módulo que monte las mismas bibliotecas.

## Módulo RAW v001

1. Descarga el ZIP `x6810-raw-v001.zip` desde la release de GitHub.
2. Verifica el SHA-256 con `SHA256SUMS.txt` de esa release.
3. Instálalo desde APatch y reinicia el teléfono.
4. Comprueba la cámara principal, telefoto y frontal; prueba RAW/DNG y JPEG.

El instalador comprueba modelo, API, hashes admitidos, integridad y conflictos
antes de montar los archivos. No copies bibliotecas a `/vendor` manualmente.

## Módulo GCam como app de sistema

El ZIP `x6810-gcam-system-0.6.2.zip` es independiente del módulo RAW. Instálalo
desde APatch y reinicia el teléfono para que Android detecte el APK original
firmado de BSG 9.7 V32 y sus 21 bibliotecas nativas en `/system/app`. El módulo
preconcede los permisos runtime solicitados por GCam y los deja revocables
desde Ajustes. Desactiva o elimina el módulo y reinicia para retirar la app de
sistema; los datos de GCam se conservan.

## Recuperación del módulo RAW

Desactiva `x6810_raw12mp` desde APatch y reinicia. Para volver de v001 a v000,
instala el ZIP completo `x6810-raw-v000.zip` y reinicia. Mantén una copia de la
release anterior antes de actualizar.

Si compartes un fallo, incluye la versión, modelo, API y hashes de bibliotecas.
Elimina seriales, rutas privadas, fotografías, DNG y logs completos.
