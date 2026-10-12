**English** | [Español](es/FLASH_COMPATIBILITY.md)

# Flash minimum Android review — 2026-10-12

Source, patch manifests and the current ELF were reviewed offline. [Machine-readable ELF audit](flash-framework-audit.json).

| Evidence | Result |
|---|---|
| Current cameraserver SHA-256 | `23cbf1d21c54c923577267a6f974b526c6950b5ecdcae7e3a53fc6b57a640e09` |
| Android ELF note | `24 00 00 00`, build API 36 |
| DT_NEEDED dependencies | 62 libraries |
| Undefined dynamic symbols | 1381 |
| Public TORCH strength API | API 33 |
| Public SINGLE strength API | API 35 |
| SINGLE request metadata | `0x00040006`, read before vendor filtering |
| Internal HAL transport | Private Transsion tag `0xc000008c` |

The combined public feature floor is Android 15/API 35. The ELF build note alone does not prove that every symbol fails on older Android. However, private dependencies, hook offsets and framework layouts prevent establishing compatibility from public API availability alone. The supplied executable and installer therefore remain tied to Android 16/API 36 and a known framework hash. Lowering the SDK check would not create an Android 15 port.

An Android 15 profile requires its original cameraserver and dependencies, symbol/layout analysis, adapted hooks and metadata transport, reproducible binary deltas, preserved pulse/timeouts, and actual TORCH/SINGLE and capture regression checks. These target binaries were not available. Android 13–14 could support a separately implemented TORCH-only profile; SINGLE would require an explicit framework backport. Neither profile is included.

Sources: [CameraManager API 33 changes](https://developer.android.com/sdk/api_diff/33/changes/android.hardware.camera2.CameraManager), [CaptureRequest API 35 changes](https://developer.android.com/sdk/api_diff/35/changes/android.hardware.camera2.CaptureRequest).
