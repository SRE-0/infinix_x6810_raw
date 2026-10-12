# Auditoría del mínimo Android del módulo flash — 12 de octubre de 2026

Se revisaron las fuentes de ambos puentes, sus manifests y el ELF actual sin
ejecutarlo en un teléfono. [Resultado ELF](flash-framework-audit.json).

| Evidencia | Resultado |
|---|---|
| SHA-256 `cameraserver` actual | `23cbf1d21c54c923577267a6f974b526c6950b5ecdcae7e3a53fc6b57a640e09` |
| Nota Android del ELF | bytes `24 00 00 00`: API 36 |
| Dependencias DT_NEEDED | 62 bibliotecas |
| Símbolos dinámicos externos | 1381 |
| TORCH público | `turnOnTorchWithStrengthLevel`, API 33 |
| SINGLE público | `FLASH_STRENGTH_LEVEL`, API 35 |
| Request actual SINGLE | lectura de `0x00040006` antes del filtro vendor |
| Transporte interno HAL | `0xc000008c`, privado Transsion |

El API 35 es el mínimo de las funciones combinadas; el ejecutable entregado es
de API 36. La nota ELF indica el nivel de compilación, no prueba por sí sola
que cada símbolo sea incompatible hacia atrás. Sin embargo, junto con los
offsets de hooks y dependencias privadas demuestra que no es un binario portátil
cuya compatibilidad pueda establecerse sólo por API pública. No se dispuso de
`cameraserver` y bibliotecas del framework Android 15 para comprobar/resolver
símbolos o construir su perfil.

Para portar: obtener los ELF originales de la ROM de destino; localizar métodos
equivalentes; adaptar offsets, layouts y transporte de metadata; reconstruir
deltas verificables; conservar los controles de pulso/timeouts; verificar
TORCH/SINGLE y regresiones de captura. Android 13–14 necesita un perfil sólo
TORCH, o un backport explícito del framework si se desea la API SINGLE nueva.

Fuentes de API:
[CameraManager API 33](https://developer.android.com/sdk/api_diff/33/changes/android.hardware.camera2.CameraManager),
[CaptureRequest API 35](https://developer.android.com/sdk/api_diff/35/changes/android.hardware.camera2.CaptureRequest).
