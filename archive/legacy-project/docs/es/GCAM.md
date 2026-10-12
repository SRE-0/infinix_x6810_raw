# GCam y configuración XML

## Componentes y compatibilidad

| Archivo | Destino | Uso |
|---|---|---|
| `x6810-gcam-system-0.7.0.zip` | APK original firmado de BSG 9.7 V32, hash exacto comprobado | Instala el APK original y sus 21 bibliotecas ARM64 como app privilegiada de sistema, concede permisos runtime y privilegiados y accesos especiales y aplica el arreglo de caché nativa; independiente del módulo RAW. |
| `x6810-gcam-bsg-v18-recommended.xml` | BSG 9.7 V18 (`com.android.MGC_9_7_047`) | Overlay de preferencias con valores conservadores. |

El XML no se ha validado contra V32 y el módulo no lo aplica.

## Qué contiene el XML

Los factores de luma y chroma se mantienen en `1.0` para los tres sensores.
El enfoque trasero queda en autofocus, AWB de Google desactivado y HDR+ en
`auto`. Son valores neutros/conservadores; las pruebas no demostraron una
mejora de calidad repetible al usar los factores experimentales.

El archivo contiene sólo 16 preferencias en formato Android SharedPreferences.
**No es una exportación completa de GCam. No reemplaces con él todo el archivo
de preferencias ni lo cargues como una copia integral.** El script del proyecto
lo combina con las preferencias actuales, crea un respaldo y verifica la
lectura después de escribir:

```powershell
python scripts/configure_mgc_photo.py apply --serial SERIAL --backup-dir .local-private/gcam-backup --profile-xml profiles/x6810-gcam-bsg-v18-recommended.xml
```

El comando requiere ADB autorizado, root y el APK BSG V18 auditado. Guarda el
respaldo fuera de Git. Para revisar los valores aplicados, usa `status`; para
restaurar los valores previos, usa `restore` con el mismo `--backup-dir`.

## Uso fotográfico

Mantén el enfoque automático como opción general. HDR+ mejorado puede servir
para sujetos estáticos; usa HDR+ normal/automático cuando haya movimiento.
AWB de Google es una comparación opcional, no una calibración universal. No
importes matrices de color, niveles negros ni perfiles de ruido de otro sensor
o teléfono.

Más medidas y límites: [perfiles fotográficos](../GCAM_PHOTO_PROFILES.md),
[controles manuales y preview](../GCAM_MANUAL_PREVIEW.md) y
[estado del módulo de arranque](../GCAM_STARTUP_CURRENT.md).
