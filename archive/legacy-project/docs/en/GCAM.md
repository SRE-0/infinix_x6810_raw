# GCam and the XML settings overlay

## Components and compatibility

| File | Target | Use |
|---|---|---|
| `x6810-gcam-system-0.7.0.zip` | Original signed BSG 9.7 V32, exact hash checked | Installs the original APK and all 21 ARM64 libraries as a privileged system app, grants runtime/privileged permissions and special accesses, and applies the native cache fix; separate from the RAW module. |
| `x6810-gcam-bsg-v18-recommended.xml` | BSG 9.7 V18 (`com.android.MGC_9_7_047`) | Preferences overlay with conservative values. |

The XML has not been validated against V32, and the module does not apply it.

## XML contents

Luma and chroma factors remain at `1.0` for all three sensors. Rear focus is
autofocus, Google AWB is disabled, and HDR+ is `auto`. These are neutral and
conservative values; testing did not establish a repeatable image-quality gain
from the experimental factors.

The file contains only 16 Android SharedPreferences entries. **It is not a
full GCam export. Do not replace the entire preferences file with it or load
it as a complete backup.** The project script merges it with current
preferences, saves a backup, and verifies the readback:

```powershell
python scripts/configure_mgc_photo.py apply --serial SERIAL --backup-dir .local-private/gcam-backup --profile-xml profiles/x6810-gcam-bsg-v18-recommended.xml
```

The command requires authorized ADB, root, and the audited BSG V18 APK. Keep
the backup outside Git. Use `status` to inspect applied values and `restore`
with the same `--backup-dir` to restore the saved values.

## Photo use

Keep autofocus as the general setting. Enhanced HDR+ can suit static subjects;
use normal/automatic HDR+ when subjects move. Google AWB is an optional
comparison, not a universal calibration. Do not import color matrices, black
levels, or noise profiles from another sensor or phone.

Further measurements and limits: [photo profiles](../GCAM_PHOTO_PROFILES.md),
[manual controls and preview](../GCAM_MANUAL_PREVIEW.md), and
[startup module status](../GCAM_STARTUP_CURRENT.md).
