# Modificaciones binarias

## Método

Los parches parten de ELF AArch64 *little-endian* con hashes conocidos. Los scripts localizan los constructores `constructCustStaticMetadata_PLATFORM_PROJECT_SENSOR_DRVNAME_*`, reemplazan llamadas puntuales por saltos `BL`/`B` hacia trampolines y colocan esos trampolines en padding cero del segmento ejecutable. Después amplían `p_filesz` y `p_memsz` del segmento RX sin cambiar el tamaño total del archivo ni crear segmentos RWX.

Cada trampoline respeta AAPCS64: mantiene alineación de stack de 16 bytes, conserva los registros no volátiles, reproduce la operación original y retorna a la instrucción siguiente. Los manifests de `patches/` registran hash de entrada/salida, bytes anteriores/nuevos, offsets y alcance.

## Base conocida

`libmtkcam_metastore.so` stock:

```text
SHA-256: dbd740c5c7ba3081fb9d38b68b2f9975e19d6faad41dd5f87ce75f3c7d7be485
Tamaño: 784232 bytes
```

El instalador no debe aceptar silenciosamente otra compilación. Los offsets siguientes sólo son válidos para esa familia exacta de binarios.

## Hooks de metadatos RAW

| Sensor | Constructor | Hook capacidad RAW | Hook stream RAW16 | Tupla final |
|---|---:|---:|---:|---|
| S5KGM1ST | `0x54760` | `0x5482c` | `0x54c4c` | `[32,4000,3000,0,50000000,33333333]` |
| OV08A10 | `0x30338` | `0x303fc` | `0x305b8` | `[32,3264,2448,0,33333333,33333333]` |
| HI1631Q | `0x4e1c8` | `0x4e26c` | `0x4e688` | `[32,2320,1744,0,33333333,33333333]` |

`32` es `HAL_PIXEL_FORMAT_RAW16` y `0` indica stream de salida. A la lista de `ANDROID_REQUEST_AVAILABLE_CAPABILITIES` se añade el valor `3` (`RAW`). Los dos últimos valores de cada tupla son duración mínima y *stall* en nanosegundos según la convención encontrada en los constructores del vendor.

## Evolución del metastore

- **v0.1–v0.3:** hooks por sensor y trampolines en la code cave desde `0xbc530`; v0.3 corrige el constructor frontal a HI1631Q.
- **v0.4:** hace coincidir 4640×3488 con sus tablas de duración para evitar tiempos cero.
- **v0.5:** prueba además 2320×1744, pero el HAL combina ese buffer con el modo físico 4640×3488 y falla el stride.
- **v0.6:** retira el stream inválido e inyecta `remosaicenable=1` y `processRaw.enable=1` sólo para `openId=1`; la aplicación podía sobrescribir esos defaults.
- **v0.7:** adopta la salida binned y fuerza la normalización frontal; su binario termina en SHA-256 `2b3bca8dfa83ea01c3f210b1b187c173a453665f3373afe9e8d17614b0fe95df`.
- **v0.8:** en `0x7eacc` deriva a una rutina en `0xbc7b0` para omitir candidatos frontales mayores de 2320×1744. Salida SHA-256 `00066e79cbeb0020d09e8e1fb43670cde08ef30133bd0d86a138609fb561e4a6`.
- **v0.9:** cambia la llamada en `0xbc6c4` y usa `0xbc800–0xbc83c` para añadir `PRIVATE_REPROCESSING=4` y `YUV_REPROCESSING=7` sólo a HI1631Q. Salida SHA-256 `dc18e2cdd107f4e56c98114a2de16592e275dd37e2bbd3960df7d12806d308d5`.
- **v0.10/v0.11:** en `0xbc758` deriva a `0xbc840–0xbc950` y añade JPEG `[33,2320,1744,0,33333333,33333333]` y YUV `[35,2320,1744,0,33333333,0]`. El HAL deriva de ellas los inputs de reprocesado. Salida SHA-256 `a05f038d7e638f597f751750cafc0e0c9d788be85588e52afbfeff9e583759d5`.

## Política de sensor y buffers

La policy v0.8 parte de SHA-256 `47924889f98b5e01c3220eb69235df8580d597172faa439cd71beb0f8f41d7bd`, modifica el hook `0x488a4` y usa la code cave `0x9fb90–0x9fbd8`. El resultado es `40360af0dc17d589cdf36b5388b642200093511815e00d702f5d02e612333c47`.

La policy v0.11 parte de ese resultado y modifica:

| Offset | Antes | Después | Función |
|---:|---|---|---|
| `0x5a0b8` | `e10313aa` | `ca160114` | salto al helper |
| `0x9fbe0` | 16 bytes cero | `c10080527f1a00f16122819a34e9fe17` | eleva el mínimo RAW16 a 6 |
| `0xd0`, `0xd8` | `d8eb060000000000` | `f0eb060000000000` | amplía el segmento RX |

El helper conserva cualquier mínimo original mayor que 6. El binario final tiene SHA-256 `d3bfa9aab5d43af352a3bf717ff4b399cad6744ccc2c548ef8ae4650f3635ad2` y 680192 bytes.

## Controles y propiedades

El experimento v0.6 inyectó los tags MediaTek:

```text
0x800b0006  com.mediatek.control.capture.remosaicenable = 1
0x800b0019  com.mediatek.control.capture.processRaw.enable = 1
```

La solución final no depende de tratar el Quad Bayer completo como Bayer normal; usa el stream binned. `system.prop` expone las tres cámaras y HAL3, pero esas propiedades no sustituyen los cambios de metadata/policy.

## Verificación

Los verificadores reconstruyen y revierten manifests, comparan bytes, validan límites ELF y saltos AArch64, emulan los 52 constructores con registros volátiles contaminados y exigen que los 49 constructores no objetivo permanezcan idénticos. Las pruebas del instalador cubren stock válido, actualización, reinstalación, payload corrupto, firmware incorrecto y conflicto con otro módulo.

## APIs de flash Camera2

Los puentes TORCH y SINGLE se integran ahora en un solo release de cámara.
TORCH mantiene su transporte nativo en los tres payloads del puente original;
SINGLE añade hooks sólo en HAL3A y CameraService. La tabla de tags, el mapeo
1–30 → duties 0–29, timeout y hashes están en
[FLASH_CAMERA2_API.md](FLASH_CAMERA2_API.md) y en los manifests de
`patches/native-torch/` y `patches/single-flash-api/`.
