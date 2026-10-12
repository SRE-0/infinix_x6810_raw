# Arquitectura de cámara

## Sensores y streams

| Cámara | Sensor | RAW16 validado |
|---|---|---:|
| Principal | S5KGM1ST | 4000×3000 |
| Telefoto | OV08A10 | 3264×2448 |
| Frontal | HI1631Q | 2320×1744 binned |

El módulo cambia metadatos y decisiones de política del HAL MediaTek. Las
bibliotecas se montan como overlay systemless bajo `system/vendor`; el
firmware y la partición física no se sustituyen. El instalador valida el
dispositivo, la API y los hashes admitidos, y guarda los originales para poder
desactivar el módulo desde APatch.

`libmtkcam_metastore.so` anuncia streams y capacidades; `libmtkcam_pipelinepolicy.so`
limita la selección binned frontal y el mínimo de buffers RAW; los bridges de
flash y OIS viven en las bibliotecas HAL correspondientes. Los cambios de
cada versión se describen en `patches/` mediante manifests y ASM.

## Alcance

La salida JPEG 8000×6000 es procesada desde entrada medida 4000×3000. No es
RAW48 ni lectura nativa demostrada del sensor a 48 MP. La frontal usa la
salida 2320×1744 binned; no se anuncia la matriz Quad Bayer 4640×3488 como un
CFA Bayer 2×2 convencional.

`LEVEL_3` es el nivel declarado por el HAL; no certifica cumplimiento CTS ni
todas las combinaciones de streams. Para medidas y resultados de versiones
anteriores, consulta [el informe HD48](../HD48_DEVICE_RESULTS.md) y
[el historial](../VERSION_HISTORY.md).
