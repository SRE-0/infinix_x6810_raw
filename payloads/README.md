# Entradas verificadas

`raw/` contiene los tres ELF de v0.12 RAW + OIS, antes de las modificaciones de
flash: metastore `a7f9…`, policy `d3bf…`, HAL3A `7aee…`.
`raw-flash/` contiene los cinco ELF del release integrado v001, incluyendo
HD48, OIS y puentes TORCH/SINGLE. `SHA256SUMS.json` fija cada ruta de instalación.
El constructor comprueba estos hashes y ELF64 AArch64 antes de crear un ZIP.

Procedencia y deltas completos:

- [RAW + OIS original](../archive/legacy-project/archive/modules/x6810_raw_v012/README.md)
- [OIS](../archive/legacy-project/patches/v0.12-ois-trial/metadata-manifest.json)
- [Control OIS](../archive/legacy-project/patches/v0.12-ois-trial/control-manifest.json)
- [Flash integrado](../archive/legacy-project/modules/v001_x6810_GL_raw_hd48_12mp_torch_single_flash_apis_changes/README.md)

RAW + OIS conserva las resoluciones RAW de la revisión v0.12. HD48 es una
capacidad JPEG de la variante integrada y no se anuncia en esta variante RAW.
No sustituyas ELF de otra ROM manteniendo el mismo manifest.
