# Instalación y recuperación

1. Genera los paquetes con `python scripts/build.py` o descarga un release del
   repositorio RAW y comprueba su `SHA256SUMS.txt`.
2. Guarda un método de acceso a recovery/root antes de cambiar bibliotecas de
   cámara. No instales si el instalador rechaza el firmware.
3. Elige `x6810-raw-1.0.0.zip` (RAW + OIS) o
   `x6810-raw-flash-1.0.0.zip` (RAW + OIS + flash) e instálalo desde APatch.
4. Reinicia. Comprueba apertura de la cámara OEM, preview/captura de los tres
   sensores y DNG en una app que solicite RAW. El boot exitoso no prueba captura.
5. Para OIS usa una app que solicite `LENS_OPTICAL_STABILIZATION_MODE=ON` en el
   teleobjetivo. El módulo no modifica preferencias de GCam. Para comparar
   eficacia óptica hacen falta capturas repetibles, no sólo resultados metadata.

Para cambiar de variante instala el otro ZIP sobre el mismo ID y reinicia.
El gestor debe reemplazar el árbol del módulo: RAW no puede conservar el
`system/bin/cameraserver` de la variante flash. Los fixtures locales verifican
la admisión de ambos conjuntos de binarios; el cambio real sigue pendiente.

Para deshacer, desactiva/elimina `x6810_raw12mp` en el gestor y reinicia. Si no
puedes iniciar Android, desde recovery/root crea
`/data/adb/modules/x6810_raw12mp/disable` y reinicia. No copies el respaldo a
la partición vendor: contiene la biblioteca visible anterior, que puede ser
otro overlay. El contador de dos boots incompletos es una ayuda de recuperación;
puede tardar otro arranque en surtir efecto y no garantiza evitar un bootloop.

Antes de volver a stock, desactiva cualquier flag de GCam que fuerce OIS para
evitar solicitudes incompatibles con la metadata original.
GCam se instala por separado: [repositorio y guía](https://github.com/SRE-0/infinix_x6810_gcam_port).
