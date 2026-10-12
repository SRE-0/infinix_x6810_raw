# Compatibilidad: SDK público, vendor y framework

| Requisito | RAW + OIS + HD48 (`raw`) | RAW + OIS + HD48 + flash (`raw-flash`) |
|---|---|---|
| SDK mínimo del paquete actual | 30 / Android 11 | 36 / Android 16 GSI del perfil exacto |
| SDK mínimo de las funciones de flash | No añade intensidad flash | TORCH: 33; SINGLE estándar: 35 |
| Framework reemplazado | Ninguno | `system/bin/cameraserver` |
| Bibliotecas vendor | metastore, pipelinepolicy, HAL3A | Las anteriores y device3 HAL |
| Gestor OIS | Hash original de `libtran_oismgr.so` | El mismo |
| OIS | Probado y funcionando, confirmado por el propietario | El mismo puente OIS probado |
| Android 11–15 o 17+ | Admitido por SDK con vendor conocido; sin prueba real de esas versiones | Sin perfil compatible: rechazado |

La evidencia real corresponde a Android 16 GSI. El funcionamiento de OIS y de
GCam V32 con el XML recomendado está confirmado por el propietario el 12 de
octubre de 2026. No se ejecutaron nuevas pruebas móviles durante este cambio;
el empaquetado 1.1.0 se valida localmente. Una GSI puede conservar el vendor OEM
y sustituir el framework; el fingerprint del vendor Android 11 citado en un
informe antiguo no prueba que el sistema activo fuera Android 11.

## HD48 en RAW desde Android 11

RAW conserva la base v0.12 (RAW16, frontal binned, buffers y OIS) y aplica sólo el
delta HD48 verificado: JPEG/YUV 4000×3000 y JPEG 8000×6000 en el metastore.
Es metadata del vendor; no añade hooks de flash, un framework nuevo ni una API
posterior a Android 11. La enumeración Camera2 de tamaños de alta resolución
existe desde API 23:
[StreamConfigurationMap](https://developer.android.com/reference/android/hardware/camera2/params/StreamConfigurationMap#getHighResolutionOutputSizes(int)).
Por eso se mantiene mínimo API 30. La dependencia real sigue siendo el mismo
vendor compatible, y Android 11 aún necesita una prueba real.

HD48 significa JPEG procesado de 8000×6000. La evidencia histórica muestra
entrada física 4000×3000; no significa RAW nativo de 48 MP. Una app debe solicitar
ese tamaño JPEG y consultar también `getHighResolutionOutputSizes()`. Instalar
el módulo no hace que todas las GCam capturen JPEG HD48 automáticamente.

## ¿Puede flash funcionar antes de Android 16?

Sí, las funciones permiten desarrollar un port anterior: intensidad TORCH desde
Android 13/API 33 y el conjunto TORCH + SINGLE estándar desde Android 15/API 35.
[CameraManager, API 33](https://developer.android.com/sdk/api_diff/33/changes/android.hardware.camera2.CameraManager) ·
[CaptureRequest, API 35](https://developer.android.com/sdk/api_diff/35/changes/android.hardware.camera2.CaptureRequest).
El parche SINGLE actual lee `android.flash.strengthLevel` (`0x00040006`) y publica
sus metadatos de máximo/default (`0x00040007`/`0x00040008`); luego los traduce al
tag privado Transsion `0xc000008c`. No es exclusivamente un control privado que
permita ignorar la API pública 35.

**El ZIP actual no se puede declarar compatible con Android 15.** Se inspeccionó
su ELF: `.note.android.ident` contiene `0x24`, es decir API 36; tiene 62 dependencias
compartidas y 1381 símbolos dinámicos externos. Incluye bibliotecas privadas de
CameraService/Binder y flags del framework. Sus hooks también usan offsets y
estructuras de esa compilación concreta. Bajar el SDK del instalador no adapta
esas dependencias ni transportes. Véase [auditoría binaria](FLASH_COMPATIBILITY.md).

Por tanto: **35 es el mínimo público para portar todas las funciones de flash;
36 sigue siendo el mínimo del paquete binario disponible.** Para Android 15 hace
falta su `cameraserver` original, reubicar/reconstruir los hooks, comprobar ABI y
realizar pruebas de request/result y pulso. Para Android 13–14 se podría crear
un port TORCH sin el SINGLE estándar. Este cambio no genera esos ports sin sus
binarios originales ni instala un ejecutable API 36 sobre sistemas anteriores.

## OIS y apps

OIS está probado y funciona correctamente según confirma el propietario en el
teleobjetivo OV08A10 (ID Camera2 histórico 2, sensor vendor 4). Se conservan las
pruebas de OFF→ON→OFF, ioctls suspend/resume correctos y resultados ON en GCam.
La confirmación funcional actualiza la conclusión provisional del informe
histórico. No hay OIS añadido a principal/frontal ni telemetría de posición.
No se afirma calibración óptica cuantitativa o certificación CTS.

Puedes usar cualquier GCam externa compatible, sin instalar el módulo GCam de
sistema. V32 y su perfil recomendado están comprobados por el propietario;
otros ports no quedan automáticamente certificados. TORCH 1–9 y SINGLE 1–30
son índices de duty, no lúmenes ni porcentajes.
