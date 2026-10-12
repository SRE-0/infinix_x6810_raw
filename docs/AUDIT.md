**English** | [Español](es/AUDIT.md)

# Organization audit — 2026-10-12

The original public tree contained 752 files, approximately 1251.7 MiB including local GCam packages. SHA-256 was checked during migration; [inventory](inventory.json) excludes private data and personal paths.

The mixed tree contained 131 top-level tool/script files, 20 historical module directories, two complete release trees, repeated bilingual documentation and builders coupled to a personal Downloads path. GCam 0.5.0 modified-DEX experiments were easily confused with the original signed 0.7.0 system release.

The maintained structure now has two independent repositories with cross-links, one RAW builder and two hash-pinned variants. RAW contains OIS and vendor-only HD48 without a framework replacement; flash keeps its exact API 36 profile. Original camera experiments remain grouped in `archive/legacy-project/` for reproducibility. Fifty-seven identical-content groups are recorded; their historical copies are retained intentionally, while new releases use canonical inputs and one implementation.

English is the default documentation language with linked Spanish editions. GCam decompilation is local-only; its standalone instrumentation files were removed from tracked history, with project-authored generators retained as tools. The signed APK actually packaged by its current module is retained through Git LFS.

OIS and BSG V32 with the recommended XML were tested and work correctly on Android 16 GSI. Outstanding validation includes the reorganized packaging on hardware, Android 11, other frameworks and quantitative optical/flash calibration. Offline verification does not replace those measurements. No new mobile testing was performed during this documentation revision.
