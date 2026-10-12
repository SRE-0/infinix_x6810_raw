# Plantilla de módulo — SRE-0

Base obligatoria para los módulos Magisk/APatch de este repositorio.

## Reglas

1. Conserva en `customize.sh` el banner, el marco dinámico, la detección del gestor, los datos de versión/autor/enlace y el footer.
2. Define `MODAUTHOR="SRE-0"` y `author=SRE-0` en `module.prop`.
3. Mantén la identidad en `MODNAME`, `MODVERSION` y `MODLINK`.
4. Añade la lógica específica sin retirar verificaciones de hashes, conflictos, backups, permisos ni mensajes de error.
5. Conserva `post-fs-data.sh`, `service.sh` y `boot-completed.sh` sólo cuando sean necesarios y márcalos como ejecutables.

## Archivos

| Archivo | Función |
|---|---|
| `module.prop` | Metadatos leídos por el gestor |
| `customize.sh` | Interfaz y validación durante la instalación |
| `post-fs-data.sh` | Lógica temprana de arranque, si se necesita |
| `service.sh` | Lógica de `late_start`, si se necesita |

Antes de distribuir ejecuta:

```text
python scripts/test_module_template.py
python scripts/check_repository.py
```

Autor: [SRE-0](https://github.com/SRE-0)
