# Arquitectura y construcción

Requisitos: Python 3.11+; POSIX `sh` para validar instaladores (Git Bash en Windows).
La construcción usa sólo la biblioteca estándar. Los analizadores históricos
tienen sus propios requisitos, conservados dentro del archivo.

```sh
git lfs install
git lfs pull
python scripts/validate.py
python scripts/build.py --variant all
```

También puedes construir una sola variante con `--variant raw` o `--variant
raw-flash`, y elegir el directorio con `--output`. Los manifests y checksums de
ese directorio describen las variantes de la invocación actual; usa directorios
distintos para construcciones parciales. Los ZIP tienen fechas/modos Unix fijos.

| Ruta | Responsabilidad |
|---|---|
| `scripts/build.py` | Constructor único: perfiles, admisión por SHA, metadata, servicios y ZIP |
| `scripts/validate.py` | ELF/hashes, reconstrucción/reversión de manifests, fixtures del instalador y ZIP |
| `module/common/` | Ciclo de boot, registro y entrada de instalación |
| `payloads/raw/` | Tres ELF: v0.12 RAW + OIS y delta HD48; hashes inmutables |
| `payloads/raw-flash/` | Cinco ELF v001: RAW + OIS + flash/HD48 |
| `archive/legacy-project/` | Fuentes de parches, originales, versiones e informes históricos |
| `dist/` | Paquetes y resultados generados, ignorados por Git |

La validación reconstruye los deltas `old/new` de los manifiestos. Cuando falta
la entrada original pero se conserva la salida, primero revierte y comprueba el
hash de entrada. Los fixtures simulan propiedades/hashes del firmware y rutas
de módulos; usan hashes reales para el payload y verifican respaldo, rechazo de
mezclas/conflictos, API, corrupción y permisos ZIP. No acceden a ADB ni prueban
la funcionalidad física de la cámara.

Procedencia RAW: `archive/legacy-project/archive/modules/x6810_raw_v012` más
el delta `archive/legacy-project/patches/v0122_x6810_raw_hd48_12mp/manifest.json`.
HAL3A y policy siguen siendo los de RAW + OIS sin modificaciones de flash.
Procedencia flash: `archive/legacy-project/modules/v001_x6810_GL_raw_hd48_12mp_torch_single_flash_apis_changes`.
Los bytes se preservan; el refactor cambia empaquetado y política de instalación.
Las fuentes AArch64 y verificadores avanzados permanecen en el archivo para
reproducir offsets y emulación. No se reescribieron sus algoritmos de imagen.

Para un nuevo firmware añade un perfil derivado de sus ELF originales, deltas
verificados y evidencia de capture/preview/OIS/flash. Un número SDK nuevo por sí
solo no autoriza un `cameraserver` antiguo.
