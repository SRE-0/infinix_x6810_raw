# Entradas verificadas

`raw/` conserva HAL3A `7aee…` y policy `d3bf…` de v0.12 RAW + OIS. El metastore
`bafe…` resulta de aplicar únicamente el delta HD48 a su base OIS `a7f9…`.
`raw-flash/` contiene los cinco ELF del release integrado v001, incluyendo
HD48, OIS y los puentes TORCH/SINGLE. SHA256SUMS.json fija sus rutas/hashes.

- [RAW + OIS original](../archive/legacy-project/archive/modules/x6810_raw_v012/README.md)
- [Delta HD48 aplicado a RAW](../archive/legacy-project/patches/v0122_x6810_raw_hd48_12mp/manifest.json)
- [Metadata OIS](../archive/legacy-project/patches/v0.12-ois-trial/metadata-manifest.json)
- [Control OIS](../archive/legacy-project/patches/v0.12-ois-trial/control-manifest.json)
- [Flash integrado](../archive/legacy-project/modules/v001_x6810_GL_raw_hd48_12mp_torch_single_flash_apis_changes/README.md)

RAW 1.1.0 anuncia JPEG 8000×6000 y JPEG/YUV 4000×3000 sin modificar flash ni
reemplazar `cameraserver`. El delta opera en metadata existente: HD48 no requiere
una API posterior a Android 11. Es JPEG procesado, no RAW nativo de 48 MP.
No sustituyas ELF de otra ROM manteniendo el mismo manifest.
