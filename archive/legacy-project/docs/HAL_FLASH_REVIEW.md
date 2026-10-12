# Análisis de HAL y controlador de flash

Este análisis reúne los hallazgos del teléfono X6810 y enlaza la solución
Camera2 actual. La implementación de uso está en
[FLASH_CAMERA2_API.md](FLASH_CAMERA2_API.md); aquí quedan la ruta del driver,
las observaciones de bajo nivel y los límites de calibración.

## Hardware y camino nativo

El flash de cámara observado usa el controlador **AW36515** registrado como
`9-0063` (`strobe_main`). El kernel expone
`/sys/class/flashlight_core/flashlight/flashlight_capability` y el HAL envía
las órdenes mediante `/dev/flashlight` y `flashlight_core`.

Los nodos `/sys/class/flashlight/mt-flash-led1` y `mt-flash-led2` pertenecen al
MT6360: su presencia y su máximo no identifican los emisores AW36515. La tabla
publicada por el driver da duty 0–29 para el flash principal y duty 0–8 para el
rango normal de linterna. Duty 0 es el mínimo, no una orden OFF. El valor del
driver es un índice; no se calibró como corriente o porcentaje de luz.

Antes del puente Camera2, la traza Torch OEM observó `setDuty(6)`, timeout 0,
ON y OFF con retorno 0. El HAL consultaba una ruta personalizada para el duty;
el símbolo `FlashCustomAdapter::getTorchDuty` devolvía cero sin rellenar sus
punteros. Esa ruta no permitía que una app third-party controlara claramente
la intensidad. v001 usa el transporte nativo documentado en
[`patches/native-torch/`](../patches/native-torch/) y conserva el comportamiento
OEM de encendido y apagado.

## SINGLE y tags Transsion

El HAL original publicaba `com.transsion.availableflashLuminanceValue` con una
lista escasa y recibía `com.transsion.flashLuminanceValue` como tag privado
`0xc000008c`. Una lectura inmediata del builder no siempre devolvía la clave;
reconstruirla por nombre y tipo entero sí preservaba el request. El primer
valor 10 produjo JPEG y `FLASH_STATE_FIRED`, pero no permitió inferir escala
óptica. Una captura con valor 0 también informó FIRED, de modo que 0 no es OFF.

v001 publica el rango 1–30 y default 7 para la cámara principal. Los niveles
1–9 asignan duties 0–8; los niveles fotográficos 10–30 asignan duties 9–29.
El ajuste se aplica dentro del escenario SINGLE, con la programación de flash
OEM y timeout de 300 ms. El tag, el resultado por frame y la propagación al HAL
se explican en [FLASH_CAMERA2_API.md](FLASH_CAMERA2_API.md).

## Límites de interpretación

- No se midió iluminancia, corriente ni relación monotónica de luz para cada
  duty; no se afirma calibración de lúmenes.
- El AW36515 conserva sus límites y protecciones del driver. No se cambiaron
  NVRAM, tablas de calibración ni registros I²C.
- La familia de controladores puede cambiar entre firmware. El instalador
  acepta sólo los hashes X6810/API 36 incluidos en el release.
- Un `FLASH_STATE_FIRED` demuestra el resultado reportado por Camera2, no la
  potencia óptica emitida.
- El inventario de ELF y los nombres de funciones permiten orientar el análisis,
  pero no equivalen a desensamblar exhaustivamente toda la cadena 3A.

La evidencia detallada de dispositivo (logs, dumps, capturas y binarios) se
mantiene en `.local-private/` y no se redistribuye.
