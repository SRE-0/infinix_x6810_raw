# Historial técnico y resultados

## Versiones

| Versión / etiqueta | Cambio | Resultado |
|---|---|---|
| v0.1–v0.2 | RAW16 principal y telefoto; primer candidato frontal | La frontal inicial estaba mal identificada. |
| v0.3 | Identificación frontal corregida a HI1631Q | RAW frontal disponible; surgieron diferencias de formato Quad Bayer. |
| v0.4–v0.6 | Corrección de dimensiones, duraciones y ensayos binned/remosaic | Se descartó anunciar la matriz Quad Bayer como Bayer 2×2 convencional. |
| v0.7–v0.8 | Normalización frontal y política de selección del sensor | JPEG+DNG frontal estable; se corrigió una incompatibilidad de stride. |
| v0.9–v0.10 | Reprocesado frontal y streams JPEG/YUV binned | PRIVATE/YUV de reprocesado frontal y salidas 2320×1744. |
| v0.11.0 (v0110) | Mínimo de seis buffers en la cola RAW16 | En la prueba, la principal subió de ~14,8 a ~29,6 FPS; se conservan streams de foto. |
| v0.12.0 (v0120) | Puente Camera2 OIS OFF/ON para OV08A10 | Las solicitudes alcanzan el camino suspend/resume BU63169; falta medir estabilización óptica en movimiento. |
| v0.12.1 (v0121) | Revisión intermedia de flash nativo | Base histórica previa al puente Torch. |
| v0.12.2 (v0122) | Torch nativo, OIS y límite de captura | Base de cámara para Android 16 GSI/API 36. |
| v0.12.2 HD48 (v0122_x6810_raw_hd48_12mp) | JPEG/YUV/RAW principal de 4000×3000 y JPEG 8000×6000 | Los 12 MP funcionan. El JPEG HD se genera desde entrada de 12 MP; no es RAW48 ni lectura nativa demostrada. |
| v000 | RAW HD48 + API Camera2 TORCH | Snapshot completo anterior, con niveles Torch 1–9 y el mismo ID instalable. |
| v001 | RAW HD48 + API Camera2 TORCH/SINGLE | Integra SINGLE 1–30; niveles fotográficos 10–30 corresponden a duties 9–29. Timeout software 300 ms y default 7. |

## Fallos que guiaron las correcciones

### Sensor frontal mal identificado

La primera extensión auxiliar apuntó a OV16B10FF. La inspección del dispositivo identificó CAM[1]:hi1631q_mipi_raw; desde v0.3, ambos hooks frontales apuntan al constructor HI1631Q.

### Metadatos de duración incoherentes

GCam registró frame_readout_time_ms (0.000) is <= 0. El HAL había normalizado el stream frontal a 4640×3488, pero las tablas de duración conservaban las dimensiones anteriores. Las consultas no encontraban coincidencia y devolvían cero. v0.4/v0.5 hicieron coherentes los tamaños y duraciones.

### CFA incorrecto en la frontal

El DNG 4640×3488 mostraba bloques de color 4×4 compatibles con Quad Bayer. Camera2 lo anunciaba como GRBG 2×2, por lo que el revelador interpretaba mal los canales y producía tinte rosa/morado. Cambiar matrices de color no corrige esa geometría. El proyecto usa 2320×1744 binned para RAW convencional.

### Pantalla negra por stride

En v0.5 la app pidió RAW16 2320×1744, pero el pipeline seleccionó el modo 4640×3488. El buffer tenía stride de 4640 bytes cuando P1 necesitaba 9280 (4640 píxeles × 2 bytes). Aparecieron enqueue_img_stride(4640) < query_img_stride(9280), onCaptureFailed y onBufferLost. v0.8 añadió una restricción para que la frontal binned no seleccionara un modo mayor.

### Preview lento con RAW

Reducir resoluciones YUV aceleraba el preview, pero degradaba las salidas anunciadas sin corregir la cola. v0.11 elevó el mínimo de buffers RAW16 a max(original, 6), preservando cualquier valor mayor. La prueba pasó de ~14,8 a ~29,6 FPS a 4000×3000; exposición y luz siguen determinando el límite real.

### 12 MP y el nombre «48 MP»

El ensayo v0.12.2 añade tuplas Camera2 al constructor S5KGM1ST. El probe físico recibió JPEG 8000×6000, pero los logs registraron sensor/IMGO a 4000×3000. La cámara Transsion generó el modo 48M a partir de ocho cuadros YUV de 12 MP. Por tanto, se documenta como JPEG HD/superresolución procesada y no como sensor RAW de 48 MP.

## Estado de validación

RAW16/DNG y JPEG en los tres sensores se validaron históricamente con v0.11. El candidato HD48 se instaló y se probó en el dispositivo: 12 MP JPEG quedaron funcionales y se recibió una salida JPEG directa de 8000×6000. BSG GCam 9.7 observada abrió RAW/YUV 4000×3000, pero no pidió JPEG HD en esa sesión. Los resultados no certifican CTS ni todas las combinaciones de streams. Consulta [el informe HD48](HD48_DEVICE_RESULTS.md).

Para la evolución y reproducción actual de las APIs de flash, consulta
[FLASH_CAMERA2_API.md](FLASH_CAMERA2_API.md),
[HAL_FLASH_REVIEW.md](HAL_FLASH_REVIEW.md) y [BUILDING.md](BUILDING.md).
