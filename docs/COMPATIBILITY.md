# Compatibilidad

La versión de Android y la familia de binarios son requisitos separados.
El mismo X6810-GL puede tener un vendor diferente tras una actualización OEM.
Una GSI puede conservar el vendor original y cambiar `cameraserver`.

| Aspecto | RAW + OIS (`raw`) | RAW + OIS + flash (`raw-flash`) |
|---|---|---|
| SDK mínimo | 30 (Android 11); sin techo artificial | Perfil actual: exactamente 36 |
| Framework reemplazado | Ninguno | `system/bin/cameraserver` |
| Bibliotecas | metastore, pipelinepolicy, HAL3A | Las anteriores y device3 HAL |
| Dependencia OIS | SHA-256 del `libtran_oismgr.so` original | La misma |
| Pruebas reales disponibles | Revisiones históricas en Android 16 GSI | Revisiones históricas en Android 16 GSI |
| Empaquetado 1.0.0 | Verificación local; pendiente de prueba real | Verificación local; pendiente de prueba real |
| Android 11–15 o 17+ | Admitido por SDK si coincide el vendor; no validado | Sin perfil de framework; rechazado |

El instalador verifica conjuntos coherentes de hashes, integridad de payloads,
ARM64 y conflictos activos/pendientes antes del respaldo. No utiliza una lista
independiente de hashes que pueda admitir una mezcla incompatible.

RAW usa la base v0.12: RAW16, reprocesado/frontal binned, mínimo de seis buffers
RAW y puente OIS. No incluye las modificaciones de flash ni el framework de una
GSI. Las APIs Camera2 usadas por el puente OIS ya existen antes de Android 11.
Eso reduce dependencias; no constituye una garantía de ABI o funcionamiento en
todas las ROM futuras. No se han obtenido los binarios de un teléfono con Android
11 en esta sesión. Un hash desconocido exige analizar/reconstruir su perfil y
validarlo; quitar la comprobación de SDK o SHA-256 no es un port.

El control de intensidad TORCH estándar apareció en API 33:
[CameraManager](https://developer.android.com/reference/android/hardware/camera2/CameraManager#turnOnTorchWithStrengthLevel(java.lang.String,int)).
`FLASH_STRENGTH_LEVEL` apareció en API 35:
[CaptureRequest](https://developer.android.com/reference/android/hardware/camera2/CaptureRequest#FLASH_STRENGTH_LEVEL).
Estos mínimos del SDK no prueban compatibilidad del parche binario actual.
SINGLE conserva el transporte privado Transsion descrito en el informe histórico;
no se afirma que toda app Camera2 use automáticamente el puente.

OIS sólo se anuncia/controla en el teleobjetivo OV08A10 (Camera2 ID histórico 2,
sensor vendor 4). No se añade OIS a la principal ni a la frontal. No se publica
telemetría de posición OIS, ni se asegura mejora óptica o calibración CTS.
TORCH 1–9 y SINGLE 1–30 son índices de duty, no lúmenes ni porcentajes.
