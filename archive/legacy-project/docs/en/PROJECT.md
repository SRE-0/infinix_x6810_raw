# Structure, privacy, and licensing

| Path | Contents |
|---|---|
| `modules/` | Complete active RAW modules v000 and v001. |
| `archive/modules/` | Complete historical snapshots retained for auditing. |
| `stock-binaries/` | Four original firmware libraries and their hashes. |
| `patches/` | Modified libraries, manifests, offsets, and assembly. |
| `gcam/apatch-startup/` | Systemless installer and native payloads for GCam module 0.6.2. |
| `profiles/` | Analytical JSON profile and recommended XML overlay. |
| `scripts/` | Analysis, collection, building, packaging, and verification. |
| `docs/` | Spanish/English guides and technical lab reports. |
| `vendor/mtkcam-raw/` | Third-party Python dependency under MPL-2.0. |

`.local-private/`, `dist/`, `research/`, virtual environments, local captures,
and logs are excluded from Git. `dist/` holds regenerable outputs; complete
packages can be rebuilt from the versioned scripts and modules. Do not upload
ADB serials, photos, DNGs, full GCam preferences, or device dumps.

MediaTek/Transsion libraries are proprietary; their inclusion here grants no
redistribution rights. The GCam APK contains third-party components. The
project's original code has no repository-wide license declaration; MPL-2.0
covers only `vendor/mtkcam-raw/`. Review
[third-party notices](../../THIRD_PARTY_NOTICES.md) before redistribution.
