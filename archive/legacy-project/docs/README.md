# Documentation index

## Maintained guides

- [Español](es/README.md): overview, installation, GCam, building, architecture, limitations, and project layout.
- [English](en/README.md): the same guides in English.

## Detailed technical records

These reports preserve measurements and implementation history. Most were
written in Spanish and describe the experiment or software version named in
their title; they are not all statements about the current release.

| Topic | Records |
|---|---|
| Camera HAL, RAW and image sizes | [Architecture](ARCHITECTURE.md), [HD48 measurements](HD48_DEVICE_RESULTS.md), [resolution trials](MAIN_RESOLUTION_TRIALS.md), [limitations](LIMITATIONS.md) |
| Binary patches and flash APIs | [Binary patches](BINARY_PATCHES.md), [Camera2 flash API](FLASH_CAMERA2_API.md), [HAL flash review](HAL_FLASH_REVIEW.md) |
| Module versions and OIS | [Version history](VERSION_HISTORY.md), [OIS findings](OIS.md) |
| GCam settings and capture behavior | [Photo profiles](GCAM_PHOTO_PROFILES.md), [manual controls and preview](GCAM_MANUAL_PREVIEW.md), [Top Shot](GCAM_TOP_SHOT.md) |
| GCam startup investigations | [Initial report](GCAM_STARTUP.md), [October 11 report](GCAM_STARTUP_20261011.md), [remaining review](GCAM_REMAINING_REVIEW_20261011.md), [current status](GCAM_STARTUP_CURRENT.md), [APK audit](GCAM_APK_FULL_AUDIT_20261011.md), [CRC fix](GCAM_CRC_FIX_20261011.md), [segmenter cache](GCAM_SEGMENTER_CACHE_FIX_20261011.md), [panel optimization](GCAM_PANEL_OPTIMIZATION_20261011.md), [lab notebook](GCAM_STARTUP_LAB_NOTEBOOK_20261012.md) |

Use the localized guides for current installation and release instructions.
Use a technical report when you need the underlying measurements or patch
history. Local device captures and `dist/` outputs are intentionally excluded.
Paths to `dist/analysis/` files in older reports are historical: the local
research datasets were removed during the October 2026 disk cleanup. The reports
retain their summarized findings; reproducing a raw analysis may require fresh
device captures or a privately obtained APK.

## Índice en español

### Guías mantenidas

- [Inicio](es/README.md)
- [Instalación y recuperación](es/INSTALLATION.md)
- [GCam y XML recomendado](es/GCAM.md)
- [Construcción y publicación](es/BUILDING.md)
- [Arquitectura](es/ARCHITECTURE.md)
- [Compatibilidad y límites](es/LIMITATIONS.md)
- [Estructura y licencias](es/PROJECT.md)

### Informes técnicos detallados

Los informes de laboratorio conservan sus mediciones y el idioma en que se
redactaron; describen la prueba o versión indicada en cada título y no siempre
el estado actual. Las rutas `dist/analysis/` de informes antiguos son históricas:
los datos locales de investigación se eliminaron en la limpieza de espacio de
octubre de 2026. Se mantienen los resultados resumidos; reproducir el análisis
crudo puede requerir nuevas capturas o un APK obtenido de forma privada.

| Tema | Informes |
|---|---|
| HAL, RAW y tamaños de imagen | [Arquitectura histórica](ARCHITECTURE.md), [resultados HD48](HD48_DEVICE_RESULTS.md), [ensayos de resolución](MAIN_RESOLUTION_TRIALS.md), [límites técnicos](LIMITATIONS.md) |
| Parches binarios y flash | [Parches binarios](BINARY_PATCHES.md), [API Camera2 de flash](FLASH_CAMERA2_API.md), [revisión HAL de flash](HAL_FLASH_REVIEW.md) |
| Versiones y OIS | [Historial de versiones](VERSION_HISTORY.md), [OIS](OIS.md) |
| Perfiles y uso de GCam | [Perfiles fotográficos](GCAM_PHOTO_PROFILES.md), [controles manuales y preview](GCAM_MANUAL_PREVIEW.md), [Top Shot](GCAM_TOP_SHOT.md) |
| Estudios de arranque GCam | [informe inicial](GCAM_STARTUP.md), [informe del 11 de octubre](GCAM_STARTUP_20261011.md), [revisión de pendientes](GCAM_REMAINING_REVIEW_20261011.md), [estado actual](GCAM_STARTUP_CURRENT.md), [auditoría APK](GCAM_APK_FULL_AUDIT_20261011.md), [CRC](GCAM_CRC_FIX_20261011.md), [caché del segmentador](GCAM_SEGMENTER_CACHE_FIX_20261011.md), [optimización del panel](GCAM_PANEL_OPTIMIZATION_20261011.md), [cuaderno de laboratorio](GCAM_STARTUP_LAB_NOTEBOOK_20261012.md) |
