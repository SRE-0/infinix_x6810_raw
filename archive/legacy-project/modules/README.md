# RAW modules

These folders are complete APatch module trees, not incremental patches. Both
active packages use `id=x6810_raw12mp`.

| Folder | Description |
|---|---|
| `v001_x6810_GL_raw_hd48_12mp_torch_single_flash_apis_changes/` | Current module: RAW/JPEG/YUV, processed HD48 JPEG, TORCH and SINGLE flash APIs. |
| `v000_x6810_GL_raw_hd48_12mp_torch_changes/` | Previous complete version, without the SINGLE flash API. |

The GitHub release workflow packages a selected folder as a complete install
ZIP. Historical module trees are kept under `archive/modules/`. For tested
compatibility and recovery guidance, see [the Spanish guide](../docs/es/INSTALLATION.md)
or [the English guide](../docs/en/INSTALLATION.md).
