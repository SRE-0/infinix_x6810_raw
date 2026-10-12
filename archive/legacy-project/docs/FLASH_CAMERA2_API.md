# APIs de intensidad Camera2: TORCH y SINGLE

v001 integra los dos controles de intensidad en el módulo RAW Level 3+ con ID
`x6810_raw12mp`. No instala una aplicación, servicio de UI, daemon root ni un
segundo módulo de flash.

## TORCH

CameraService y MediaTek exponen la API estándar `CameraManager` de Android:

- `turnOnTorchWithStrengthLevel(cameraId, level)`;
- `getTorchStrengthLevel(cameraId)`;
- `FLASH_INFO_STRENGTH_MAXIMUM_LEVEL = 9`.

La ruta nativa traduce nivel Camera2 `1..9` a duty AW36515 `0..8` (`duty =
level - 1`). El nivel normal predeterminado es 7, que conserva el duty 6
observado en la linterna OEM. Las peticiones inválidas y la indisponibilidad de
la cámara conservan los errores de API esperados. El módulo retiene los tres
payloads del puente TORCH existente: `cameraserver`,
`libmtkcam_device3_hal.so` y `libcam.hal3a.v3.so`.

## SINGLE fotográfico

El firmware usa los tags privados Transsion:

| Nombre / campo | Tag / tipo | Uso |
|---|---|---|
| `com.transsion.availableflashLuminanceValue` | Array vendor observado originalmente `[0,10,100]` | Descriptor del firmware; no es una escala óptica calibrada |
| `com.transsion.flashLuminanceValue` | `0xc000008c`, int32 | Nivel pedido y valor correlacionado al resultado |
| máximo de luminancia | `0x00040007`, int32 | Valor máximo publicado: 30 |
| luminancia predeterminada | `0x00040008`, int32 | Valor predeterminado: 7 |

El CameraService original filtraba el tag privado antes de que llegara al HAL.
El hook de `cameraserver` lo reconoce para la cámara principal, asigna el
default 7 cuando no hay request explícita, valida `1..30` y conserva el valor
en la metadata que recibe el HAL. En el HAL, un registro acotado correlaciona
owner, número de frame y nivel para aislar solicitudes simultáneas. El nivel
solo se consume en el escenario SINGLE del flash; el flujo OEM conserva la
decisión de encender y apagar.

| Nivel Camera2 | Duty AW36515 | Interpretación del driver |
|---:|---:|---|
| 1–9 | 0–8 | Rango de la linterna/TORCH |
| 10–30 | 9–29 | Rango de potencia para SINGLE fotográfico |

La conversión es `duty = level - 1`. Los 21 niveles 10–30 corresponden a los
duties fotográficos 9–29 solicitados. El HAL envía el duty a la ruta de flash
OEM con timeout software de 300 ms y restaura el timeout original después de
la solicitud. No se escriben nodos sysfs directamente, no se fuerzan pulsos
fuera de una captura y no se desactiva la protección del controlador.

## Cambios binarios

El release v001 conserva los cinco payloads RAW/TORCH de v000. Sobre estos se
parchan únicamente:

1. `vendor/lib64/libcam.hal3a.v3.so`: extracción SINGLE desde metadata,
   propagación bajo mutex, selección de duty por escenario y resultado por frame.
2. `system/bin/cameraserver`: publicación de características SINGLE, retención
   del tag Transsion antes del filtro VNDK y echo de resultado.

Las entradas, salidas, offsets, bytes reemplazados y bloques ASM están en
[`patches/single-flash-api/`](../patches/single-flash-api/). El puente TORCH se
documenta en [`patches/native-torch/`](../patches/native-torch/). El manifest
`flash-api-manifests.json` dentro del módulo fija las salidas incluidas en v001.

## Evidencia y reproducción

La matriz ADB/Cámara2 ya ejecutada cubrió valores omitidos/default, límites,
Torch regresivo, AE_ON, flash OFF y todos los niveles 10–30. Las capturas
principales devolvieron `FLASH_STATE_FIRED`, nivel de resultado coincidente y
JPEG con timestamp del sensor; no se observó crash de cámara. Una repetición
de los 29 niveles fotográficos registró duties 9–29, timeout de 300 ms y
resultado 0 del driver. Los detalles privados del teléfono no se redistribuyen.

El verificador host reproducible es `scripts/verify_single_flash_api.py`; cubre
aislamiento de frames, rutas de request/pulso, límites y reversibilidad del
parche. Para volver a generar los binarios y el ZIP, ejecuta los tres comandos
de [Construcción](BUILDING.md). Una captura real requiere una app Camera2 que
escriba el tag privado Transsion; ninguna app de control se instala ni se
incluye en el release.

## Límites de la medición

El número de duty es el índice discreto del AW36515, no lúmenes ni porcentaje
óptico. No se midieron iluminancia, corriente ni uniformidad por nivel. No se
afirma certificación CTS para las API privadas Transsion. La compatibilidad se
limita al X6810 Android 16/API 36 y al conjunto de hashes aceptado por el
instalador. Un firmware distinto requiere reconstruir offsets y volver a
validar la secuencia de captura.
