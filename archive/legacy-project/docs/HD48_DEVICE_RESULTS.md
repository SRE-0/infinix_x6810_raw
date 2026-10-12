# Resultado de las pruebas físicas HD, 2026-10-07

## Resultado

Con `v0122_x6810_raw_hd48_12mp` instalado, **JPEG 8000×6000 está
publicado y se puede capturar desde Camera2**. Sin embargo, las trazas de esta
sesión no muestran lectura nativa de 48 MP:

- La captura JPEG HD directa usa sensor e IMGO de 4000×3000 y una salida
  procesada de 8000×6000.
- El modo 48M de Transsion activa `cap_superresolution`: combina ocho entradas
  YUV de 4000×3000 para producir una salida de 8000×6000.
- La sesión BSG observada solicita RAW16 y YUV de 4000×3000. No solicita el
  JPEG HD ni la ruta privada de superresolución observada en Transsion.

Los 12 MP fueron confirmados por el propietario y por una captura JPEG directa
de 4000×3000. No se cambiaron el módulo instalado, propiedades del HAL ni
preferencias de BSG durante este diagnóstico. No se utilizó ARTEMIS.

## Qué publica Camera2

Una aplicación de diagnóstico consulta ambas listas del StreamConfigurationMap:

| Formato público | Máximo normal observado | Lista highResolution |
|---|---|---|
| JPEG (256; BLOB 33 internamente) | 4000×3000 | 8000×6000 |
| YUV_420_888 (35) | 4000×3000 | Vacía |
| RAW_SENSOR (32) | 4000×3000 | Vacía |
| PRIVATE (34) | 4000×3000 | Vacía |

El área activa sigue siendo `Rect(0,0–4000,3000)`. El dumpsys confirma también
entradas de reprocesado PRIVATE/YUV 4000×3000.

El JPEG HD declara un mínimo de 100 ms. Android separa las salidas que no
alcanzan 20 FPS de la lista habitual cuando existe BURST_CAPTURE. Por eso un
enumerador que solo use `getOutputSizes()` no muestra este tamaño; debe consultar
también `getHighResolutionOutputSizes()`. Esto es una explicación compatible
con lo observado en la aplicación de especificaciones del usuario, **no una
auditoría de su código**. Fuente:
[StreamConfigurationMap](https://developer.android.com/reference/android/hardware/camera2/params/StreamConfigurationMap#getHighResolutionOutputSizes(int)).

Reducir ficticiamente los 100 ms a 50 ms podría cambiar de lista el anuncio,
pero no añade lectura nativa ni RAW/YUV 48 MP. No se aplicó ese cambio.

## Captura Camera2 directa

El probe creó ImageReader JPEG 8000×6000, configuró una sesión y recibió imagen
y TotalCaptureResult con el mismo timestamp. Demoró aproximadamente 764 ms
desde la petición hasta recibirlos en esta ejecución; no es una medición de
FPS sostenidos ni una calibración de minFrameDuration.

La traza contiene:

```text
select size(4000x3000)@30 sensorMode:1
.imgoAlloc={ format:0x2201 4000x3000 }
Hal:Image:JpegYuv ... 8000x6000 ... NV21
```

Por tanto, esa entrega JPEG tiene dimensiones de 48 MP, pero se genera después
de una lectura de 12 MP. El archivo guardado tiene 6 522 372 bytes. La prueba
de control JPEG 4000×3000 también terminó correctamente (407 ms en esa toma).

La policy enumeró estos escenarios para el sensor principal:

| Escenario | Dimensiones y FPS publicados por la consulta del HAL |
|---|---|
| PREVIEW, CAPTURE, VIDEO | 4000×3000 @30 |
| SLIM_VIDEO1 | 2000×1500 @120 |
| SLIM_VIDEO2 | 1280×720 @240 |
| CUSTOM1 | 4000×3000 @30 |
| CUSTOM2 | 2000×1500 @60 |
| CUSTOM3, CUSTOM4, CUSTOM5 | 4000×3000 @30 |

No apareció un escenario 8000×6000 en esa enumeración. Esto limita lo que
puede conseguirse cambiando únicamente los anuncios del metastore; no prueba
que el hardware carezca de cualquier modo adicional fuera de esa consulta.

## Captura Transsion 48M

Se verificó el control UI `key_super_definition-on-back`, el tamaño seleccionado
8000×6000 y se efectuó un disparo. El log identifica:

```text
IMAGE_PRO: addAlgo:cap_superresolution E
sr_android: [In 0] ... size(4000,3000,4000)
...
sr_android: [In 7] ... size(4000,3000,4000)
sr_android: [Out] ... size(8000,6000,8000)
```

El bloque de procesado registró 1603 ms. El JPEG guardado tiene 8 724 572 bytes;
su cabecera SOF mide 6000×8000 por la orientación vertical, equivalente a
los 8000×6000 del buffer previo a rotación.
La metadata de la sesión contiene `remosaicenable=1`,
`com.transsion.megSuperresolutionMode=1` y `com.transsion.3rdpluginenable=1`.
El nombre remosaic del tag no demuestra por sí mismo lectura de 48 MP; los
buffers realmente observados aquí son ocho imágenes de 12 MP.

La superresolución multiframe puede reconstruir detalle de forma diferente a
un escalado de una única imagen. No se la equipara al simple escalado, pero
tampoco a un RAW físico de 8000×6000.

## BSG

`com.android.MGC_9_7_047` abrió una sesión con:

- Preview 1440×1080.
- YUV_420_888 4000×3000.
- RAW16 4000×3000, con el mínimo de seis buffers del módulo.
- Stream auxiliar YUV 640×480.

No existe un stream JPEG 8000×6000 en esa sesión. El parámetro guardado de
resolución está en `full`, pero el máximo RAW disponible sigue siendo 12 MP.
Una corrección de enumeración JPEG por sí sola no convierte el pipeline RAW
de BSG en el algoritmo privado multiframe de Transsion.

## Estado y siguiente límite técnico

Se conserva la instalación del usuario: 12 MP completos y JPEG HD experimental.
No se ha creado otro parche que anuncie RAW/YUV 48 MP sin soporte demostrado.
Para perseguir lectura nativa 48 MP hace falta analizar el driver imgsensor
exacto y sus tablas de escenarios/registros, además de la ruta ISP/remosaic.
Para reproducir la superresolución de Transsion en otra app, el objetivo sería
integrar o activar esa ruta procesada; es distinto de conseguir RAW48 en BSG.

## Artefactos y reproducción

El paquete privado de evidencia de esta sesión (dumpsys de BSG/Transsion,
enumeración, logs, JPEG y `resolution-evidence.json`) se eliminó durante la
limpieza local de `dist/`. Este informe conserva el resumen; no publiques
capturas ni datos identificables del dispositivo.

Probe reproducible: `scripts/resolution-probe/`, constructor
`scripts/build_resolution_probe.py`. Usa esperas explícitas de apertura,
configuración, resultado y entrega; valida dimensiones y timestamp. La acción
sin `--ez capture true` enumera solamente.

```powershell
python scripts/build_resolution_probe.py
adb -s SERIAL install -r -g dist/resolution-probe/resolution-probe.apk
adb -s SERIAL shell am start -W -n org.x6810.resolutionprobe/.ProbeActivity --es label hd --ez capture true --ei width 8000 --ei height 6000
```

El reporte se guarda en
`/sdcard/Android/data/org.x6810.resolutionprobe/files/hd.txt`.
La aplicación de diagnóstico quedó instalada para posteriores pruebas.

Los reportes verifican esta sesión concreta; no certifican estabilidad prolongada,
OIS, flash o todas las combinaciones de streams.
