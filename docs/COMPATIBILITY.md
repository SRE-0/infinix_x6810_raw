**English** | [Español](es/COMPATIBILITY.md)

# Compatibility

| Variant | Contents | Installer requirement | Device evidence |
|---|---|---|---|
| RAW | RAW16, telephoto OIS, processed JPEG HD48 | Android 11/API 30+, ARM64, X6810-GL, known vendor/OIS hashes | Android 16 GSI |
| RAW + flash | All RAW features plus TORCH/SINGLE strength bridges | Exact Android 16/API 36 framework and known binary set | Android 16 GSI |

RAW does not replace `cameraserver` or include the flash bridge. Its HD48 delta changes vendor metadata only; it keeps the RAW/OIS HAL3A and pipeline policy. JPEG 8000×6000 is processed from a 4000×3000 input: it is not native 48 MP RAW. High-resolution stream enumeration was added in API 23, below the Android 11 floor ([Android reference](https://developer.android.com/reference/android/hardware/camera2/params/StreamConfigurationMap#getHighResolutionOutputSizes(int))).

OIS was tested and works correctly on the OV08A10 telephoto sensor on Android 16 GSI. The other sensors do not gain optical stabilization. Apps must request OIS; the recommended BSG V32 profile enables the photo request. This is a functional result, not a quantitative optical calibration.

The API 30 floor is an installation policy, not a claim of Android 11 testing or support for arbitrary future firmware. Known complete vendor tuples and the exact OIS-manager dependency are required. Unknown firmware, mixed libraries, payload corruption and conflicting overlays are rejected. Do not bypass those checks.

Public combined flash APIs require API 35; the supplied private-framework binary profile remains API 36. See [flash analysis](FLASH_COMPATIBILITY.md). Only Android 16 GSI has device evidence; this packaging revision has not been tested on hardware.

Any compatible external GCam can be installed. The separate GCam system module is optional; see [GCam](GCAM.md).
