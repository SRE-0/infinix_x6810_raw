# Arquitectura del módulo

## Objetivo

El firmware del X6810-GL contiene soporte interno para sensores RAW y rutas de procesado MediaTek, pero los metadatos estáticos publicados a Camera2 no exponían una combinación completa y estable para aplicaciones de terceros. El proyecto modifica esos metadatos y una decisión de política del pipeline; no sustituye el driver del sensor ni implementa un ISP nuevo.

## Hardware identificado

| Posición | Sensor | Stream RAW usado |
|---|---|---:|
| Principal | `S5KGM1ST_MIPI_RAW` | RAW16 4000×3000 |
| Telefoto | `OV08A10_MIPI_RAW` | RAW16 3264×2448 |
| Frontal | `HI1631Q_MIPI_RAW` | RAW16 2320×1744 binned |

La HI1631Q tiene una matriz Quad Bayer/4Cell de 4640×3488. Anunciar esa matriz directamente como un CFA Bayer 2×2 convencional produjo color rosa/morado. La solución final conserva únicamente la salida binned 2320×1744 para aplicaciones Camera2 generales.

## Bibliotecas modificadas

### `libmtkcam_metastore.so`

Construye los metadatos estáticos y plantillas de petición de cada sensor. Aquí se añadieron:

- capacidad Camera2 `RAW` (valor 3);
- entradas RAW16 en `ANDROID_SCALER_AVAILABLE_STREAM_CONFIGURATIONS`;
- duraciones mínima y de *stall* coherentes;
- normalización del stream frontal binned;
- capacidades de reprocesado frontal;
- salidas JPEG/YUV 2320×1744 que permiten derivar las rutas PRIVATE/YUV correspondientes.

La variante v0.12.2 HD48 añade además las tuplas JPEG/YUV 4000×3000 de la principal y JPEG 8000×6000 de alta resolución. En el dispositivo, el JPEG 8000×6000 se obtuvo desde sensor/IMGO 4000×3000; no se parchea el driver ni se habilita RAW48. Consulta [el informe de captura](HD48_DEVICE_RESULTS.md) y [el análisis del ensayo](MAIN_RESOLUTION_TRIALS.md).

### `libcam.hal3a.v3.so` (v0.12 experimental OIS)

The v0.12 trial adds a standard Camera2 OFF/ON request bridge for the OV08A10 telephoto. It maps the standard request to the existing Transsion OIS suspend/resume path and leaves other sensor devices on the original code path. The factory camera remains on Transsion's original private-tag path. The bridge does not expose OIS position samples.

### `libmtkcam_pipelinepolicy.so`

Decide qué modo de sensor y cuántos buffers necesita el pipeline. Se modificó para:

- impedir que la HI1631Q seleccione un modo mayor que 2320×1744 para el stream binned;
- elevar a 6 el mínimo de buffers RAW16 cuando el valor original es menor, sin reducir valores mayores.

## Flujo de instalación

El módulo usa el mecanismo de overlay de Magisk/APatch:

```text
Aplicación Camera2
       ↓
Camera service / HAL MediaTek
       ↓
overlay system/vendor/lib64/*.so del módulo
       ↓
drivers y firmware originales del sensor
```

El instalador valida el par exacto de hashes stock/parcheado, detecta módulos en conflicto, guarda copias de respaldo dentro del módulo y asigna permisos/contexto SELinux. La partición física `vendor` permanece intacta.

## `LEVEL_3`

Las propiedades del módulo habilitan HAL3 y la integración expone el nivel `LEVEL_3`. Este nivel sólo describe lo que el HAL declara. No demuestra por sí solo que todas las combinaciones de streams, controles manuales o requisitos CTS estén implementados. La validación real se hizo con los flujos concretos descritos en este repositorio.
