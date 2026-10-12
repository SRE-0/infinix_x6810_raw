# X6810: RAW16 de 12 megapíxeles, experimental

Derivado exclusivamente de `stock-binaries/libmtkcam_metastore.so`, SHA-256
`dbd740c5c7ba3081fb9d38b68b2f9975e19d6faad41dd5f87ce75f3c7d7be485`.

Añade capacidad RAW y una entrada RAW16 4000×3000 a S5KGM1ST. Conserva las
capacidades, resoluciones y metadatos privados originales. No certifica capturas
reales, RAW de 48 MP ni funcionamiento de las cámaras auxiliares.

Entorno previsto: Infinix Zero X Neo X6810, Evolution X 11.10 / Android 16 GSI,
APatch. La compatibilidad depende del vendor exacto, no de que el sistema diga
Android 16. La instalación exige el hash original visible en `/vendor/lib64`.

## Instalación y comparación

1. Guarda diagnósticos y muestras del módulo actual antes de cambiarlo.
2. Desactiva el módulo anterior `GSIfixes` y otros que sustituyan esta biblioteca.
3. Reinicia y verifica que el hash visible coincide con el original indicado.
4. Instala el ZIP de esta variante desde APatch Manager y reinicia.
5. Comprueba `/data/adb/modules/x6810_raw12mp/boot-status.txt` y prueba RAW_SENSOR
   4000×3000 con una aplicación Camera2. Guarda el DNG y los metadatos de captura.

No actives simultáneamente esta variante y `48mp+raw_KSU`: montan la misma ruta.
Esta variante no incluye las propiedades ni el XML del módulo anterior. Por ello,
el número de cámaras visibles o el acceso público a 48 MP pueden cambiar durante
la comparación. Los tamaños privados originales de 48 MP siguen en la biblioteca.

## Reversión

Desactiva `x6810_raw12mp` desde APatch y reinicia. Si ADB y root funcionan:

```sh
su -c 'touch /data/adb/modules/x6810_raw12mp/disable'
```

Reinicia después. Para volver a la configuración previa, reactiva `GSIfixes`
una vez desactivada esta variante. No hace falta escribir la partición vendor.
El contador incluido desactiva el módulo tras dos arranques incompletos; es una
ayuda adicional y puede surtir efecto en el siguiente arranque. El modo seguro de
APatch se documenta en https://apatch.dev/rescue-bootloop.html.

El informe `docs/BINARY_PATCHES.md` explica los offsets, las pruebas y las
limitaciones. `patch-manifest.json` identifica cada byte alterado.
