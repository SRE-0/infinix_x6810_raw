# X6810 RAW16: principal, teleobjetivo y frontal HI1631Q

v0.3 conserva los hooks y trampolines de S5KGM1ST y OV08A10 que ya funcionan
según las pruebas comunicadas. La frontal ha sido identificada como HI1631Q.
Se añade RAW a su constructor y se restaura OV16B10FF al original.

La entrada inicial de HI1631Q es RAW16 4608×3456. La captura frontal con este
parche sigue pendiente de prueba física; las comprobaciones de metadatos,
bytes, ELF y empaquetado se realizan en el PC.

## Instalar

Instala `x6810-raw16-v0.3.0-hi1631q-experimental.zip` desde Módulos de APatch
y reinicia. Mantiene el id `x6810_raw12mp`: actualiza v0.1/v0.2 en su lugar.
El instalador acepta los hashes conocidos de stock, v0.1, v0.2 y v0.3.
Rechaza otras bibliotecas y módulos activos que monten la misma ruta.

Después del reinicio, el hash de `/vendor/lib64/libmtkcam_metastore.so` debe ser:

```text
a1bb426f73f1e363f3e0a7fbcf2e7e95d24b52c45efc25633b58ed057622575a
```

Abre la frontal en una aplicación Camera2 con RAW, elige un tamaño de la lista
RAW_SENSOR publicada y captura varios DNG. Comprueba también preview/JPEG y
las cámaras traseras. El proveedor puede ajustar el tamaño al área activa.

## Diagnóstico y reversión

Si falla, guarda `dumpsys media.camera`, logcat y un DNG si llega a generarse.
El proyecto incluye `scripts/collect-device.sh` e `inspect_dng.py`.

Para volver a v0.2: desactiva el módulo, reinicia para recuperar stock,
instala el ZIP v0.2 conservado, habilítalo si hace falta y reinicia.
El respaldo `backup/libmtkcam_metastore.previous.so` contiene la biblioteca
visible al instalar; no necesariamente stock. Conserva el ZIP funcional.

Procedimiento exacto: `docs/BINARY_PATCHES.md`, junto con la guía general
`docs/BINARY_PATCHES.md` y el manifiesto incluido.
