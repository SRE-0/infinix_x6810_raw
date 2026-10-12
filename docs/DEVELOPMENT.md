**English** | [Español](es/DEVELOPMENT.md)

# Architecture and builds

Python 3.11+ is required. Building uses only the standard library; installer validation also needs POSIX `sh` (Git Bash on Windows). Historical analyzers retain their own dependencies.

```sh
git lfs install
git lfs pull
python scripts/validate.py
python scripts/build.py --variant all
```

Use `--variant raw` or `--variant raw-flash` for a single variant and `--output` for a separate destination. Each output manifest describes only that invocation; use separate directories for partial builds. ZIP timestamps and Unix modes are fixed.

| Path | Responsibility |
|---|---|
| `scripts/build.py` | Single builder: profiles, hash admission, metadata, services, ZIP |
| `scripts/validate.py` | ELF/hash checks, manifest reconstruction/reversal, isolated installer cases, ZIP checks |
| `module/common/` | Boot lifecycle and installer entry point |
| `payloads/raw/` | Three pinned vendor ELF files: RAW/OIS plus HD48 metadata |
| `payloads/raw-flash/` | Five pinned integrated vendor/framework ELF files |
| `archive/legacy-project/` | Original patches, versions, reports and research |
| `dist/` | Ignored build output |

Validation reconstructs `old/new` manifest deltas, reversing preserved outputs when needed to verify input hashes. Installer fixtures simulate firmware properties, real payload hashes and module paths; they check backups, mixed states, conflicts, SDK gates, corruption and archive permissions. They do not exercise a camera or connect to ADB.

RAW provenance: `archive/legacy-project/archive/modules/x6810_raw_v012` plus `archive/legacy-project/patches/v0122_x6810_raw_hd48_12mp/manifest.json`. HAL3A and policy retain the flash-free RAW/OIS bytes. Flash provenance: `archive/legacy-project/modules/v001_x6810_GL_raw_hd48_12mp_torch_single_flash_apis_changes`.

A new firmware profile needs original ELF files, verified deltas and capture/preview/OIS/flash evidence. An SDK number alone does not authorize an older cameraserver. [Licensing and redistribution review](LEGAL.md).
