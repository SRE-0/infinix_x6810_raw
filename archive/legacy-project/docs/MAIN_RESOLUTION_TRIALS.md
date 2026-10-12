# S5KGM1ST: resolución 12 MP y salida JPEG HD48

**Base del ensayo:** v0.12.2 native-torch, X6810 / Android 16 GSI / API 36.  
**Release conservado:** v000_x6810_GL_raw_hd48_12mp_torch_changes.  
**Fecha de prueba física:** 2026-10-07.  
**Resultado principal:** JPEG/YUV/RAW de 4000×3000 funciona; Camera2 puede entregar JPEG 8000×6000; la entrada observada sigue siendo 4000×3000.

## Qué se entrega

Se conserva un solo candidato de resolución. Combina los 12 MP completos que funcionaron para el usuario con el anuncio de JPEG de alta resolución de 8000×6000. Se retiró el ZIP y la fuente del candidato separado Full12 de v0.12.2.

| Artefacto | Función |
|---|---|
| `v000_x6810_GL_raw_hd48_12mp_torch_changes.zip` | Release completo con RAW, Torch y JPEG 8000×6000. |
| `v001_x6810_GL_raw_hd48_12mp_torch_single_flash_apis_changes.zip` | Release actual que agrega la API SINGLE sin retirar HD48. |
| `SHA256SUMS.json` dentro de cada carpeta | Hash del ZIP publicado y payloads. |

El nombre HD48 describe el tamaño JPEG que anuncia Camera2 y la función 48M de la cámara Transsion. No significa que el paquete habilite RAW48 o lectura física del sensor a 8000×6000.

## Hechos medidos en el dispositivo

### Capacidades que Camera2 publica

| Formato | Tamaño máximo normal | getHighResolutionOutputSizes |
|---|---:|---:|
| JPEG | 4000×3000 | 8000×6000 |
| YUV_420_888 | 4000×3000 | vacío |
| RAW_SENSOR | 4000×3000 | vacío |
| PRIVATE | 4000×3000 | vacío |

El área activa continúa en Rect(0,0–4000,3000). PRIVATE/YUV de reprocesado también llegan a 4000×3000.

El JPEG HD declara una duración mínima de 100 ms. Android puede separarlo en la lista de alta resolución cuando la cámara anuncia BURST_CAPTURE y la app implementa esa consulta. Una app de especificaciones que sólo consulte getOutputSizes() puede omitirlo. La lista de tamaños no obliga a una aplicación a usar el JPEG HD.

### Captura JPEG 8000×6000 directa

El probe Camera2 creó un ImageReader JPEG 8000×6000, configuró la sesión y recibió la imagen con TotalCaptureResult y timestamp coincidente. En esa toma, la entrega tardó aproximadamente 764 ms; no es una medición de FPS sostenidos ni una calibración de duración. El JPEG guardado ocupó 6 522 372 bytes. La captura de control 4000×3000 también terminó correctamente.

La traza registró:

    select size(4000x3000)@30 sensorMode:1
    .imgoAlloc={ format:0x2201 4000x3000 }
    Hal:Image:JpegYuv ... 8000x6000 ... NV21

Esto confirma una salida JPEG de 8000×6000 generada después de leer 4000×3000. No confirma captura de 48 millones de fotosensores.

### Modo 48M de la cámara Transsion

Se verificó el control 48M, se eligió 8000×6000 y se completó la captura. El log registró cap_superresolution con ocho buffers de entrada YUV de 4000×3000 y un buffer de salida de 8000×6000. El bloque de procesamiento registró 1603 ms y el JPEG guardado ocupó 8 724 572 bytes.

La superresolución multiframe puede reconstruir detalle a partir de varios cuadros; no equivale a escalar una sola imagen. Tampoco equivale a una lectura RAW nativa de 8000×6000.

### BSG GCam 9.7

La aplicación com.android.MGC_9_7_047 abrió una sesión con:

- preview de 1440×1080;
- YUV_420_888 de 4000×3000;
- RAW16 de 4000×3000;
- YUV auxiliar de 640×480.

La sesión observada no pidió JPEG de 8000×6000 ni la ruta privada cap_superresolution de Transsion. Aunque el JPEG HD exista en el mapa Camera2, BSG puede no mostrarlo en sus especificaciones porque prioriza su ruta RAW/YUV y crea el JPEG con su propio pipeline. Para distinguir esas dos cosas hay que revisar el mapa Camera2 y la sesión que abre la app, no sólo su pantalla de información.

La aplicación de especificaciones del usuario no fue auditada. La explicación compatible con las mediciones es que consulta sólo los tamaños normales o muestra la salida usada por su sesión.

## Modificación binaria

El paquete añade tuplas al constructor estático PROJECT del sensor S5KGM1ST en libmtkcam_metastore.so. No cambia la policy del sensor, no fuerza un escenario físico y no parchea el driver.

| Formato Camera2 | Tamaño | Duración mínima | Stall |
|---|---:|---:|---:|
| JPEG | 4000×3000 | 50 ms | 33,333333 ms |
| YUV_420_888 | 4000×3000 | 50 ms | 0 |
| JPEG | 8000×6000 | 100 ms, provisional | 100 ms, provisional |

La modificación afecta la tabla interna 0x000d0012, formada por tuplas de seis int64: formato, ancho, alto, dirección, duración mínima y stall. No debe confundirse con 0x000d000a, la lista pública de cuatro int32 que el HAL construye desde las capacidades internas.

Base metastore v0.12.2 SHA-256: a7f9b751cb73f4bc567f8db89b53b8e3a143d64ed605764e34a3abd719007b35.  
Metastore HD48 SHA-256: bafeda846d6d6b81361487a6fa265ee4c70d6b085ce5520d0bd727b077d55d68.

El hook ocupa 0xbc5e0 y dirige al trampoline en 0xbc9c0–0xbcb50. El trampoline ejecuta primero el comportamiento original y añade las tres tuplas sólo para S5KGM1ST. El constructor se emuló para 52 sensores PROJECT: las otras 51 salidas no cambian. El manifest incluye el delta exacto y revierte byte por byte a la base.

El paquete conserva sin cambios los otros cuatro payloads de v0.12.2: pipelinepolicy, HAL 3A, device HAL y cameraserver. Mantiene OIS, flash, linterna nativa, límites de captura y service de esa base. El instalador rechaza combinaciones no admitidas.

## Por qué no se anuncia RAW48

La policy enumeró para el sensor principal PREVIEW, CAPTURE, VIDEO y CUSTOM a 4000×3000; otros escenarios observados fueron 2000×1500 y 1280×720. No apareció un modo 8000×6000 en esa consulta. Eso no demuestra que el hardware carezca de toda ruta adicional, pero cambiar metadatos por sí solo no la crea.

El ensayo antiguo 48mp+raw_KSU tampoco demuestra un modo RAW48 correcto: el análisis binario detectó cambios de capacidades incompatibles y una preparación de registros rota en una ruta. El paquete actual conserva las capacidades RAW que ya funcionan y sólo anuncia la salida procesada medida.

Para perseguir lectura nativa de 48 MP hacen falta las tablas del driver imgsensor exacto del firmware y análisis de la ruta ISP/remosaic. La siguiente pieza útil sería el módulo de sensor .ko exacto del teléfono o el kernel/boot de esa misma compilación. No se propone flashear boot ni escribir registros del sensor a ciegas.

## Instalación y reproducción

Instala un release completo desde el [catálogo](MODULES.md) en la base compatible. Para volver de v001 a la revisión anterior, instala v000 desde APatch y reinicia. Las duraciones HD son provisionales; no se redujeron artificialmente a 50 ms porque eso sólo podría alterar dónde se lista el tamaño, no la resolución física.

El parche de metadata se puede regenerar con `scripts/build_hd48_metadata_trial.py`.
Para volver a empaquetar los releases activos, ejecuta:

    .venv\Scripts\python.exe scripts\build_single_flash_api.py
    .venv\Scripts\python.exe scripts\package_camera_module.py

El empaquetador verifica hashes del conjunto base y del parche, scripts shell y
payloads. La evidencia completa del dispositivo era local y privada; se retiró
de `dist/` durante la limpieza de espacio. Este informe y el resumen en
[HD48_DEVICE_RESULTS.md](HD48_DEVICE_RESULTS.md) conservan los resultados, no
las imágenes ni los logs originales.

No se utilizó ARTEMIS. Las capturas citadas corresponden a la sesión documentada y no certifican estabilidad prolongada, todas las combinaciones de streams, OIS o flash.
