# Installation and recovery

## Requirements

- Infinix Zero X Neo **X6810-GL**.
- Android 16 / API 36 and camera binaries accepted by the installer.
- APatch and enough space for a systemless backup.
- No other module mounting the same camera libraries.

## RAW module v001

1. Download `x6810-raw-v001.zip` from the GitHub release.
2. Verify its SHA-256 against that release's `SHA256SUMS.txt`.
3. Install it in APatch and reboot the phone.
4. Check the main, telephoto, and front cameras; try RAW/DNG and JPEG.

The installer checks the model, API, accepted hashes, payload integrity, and
overlay conflicts before mounting files. Do not copy libraries to `/vendor`
manually.

## GCam system-app module

`x6810-gcam-system-0.6.2.zip` is separate from the RAW module. Install it in
APatch and reboot so Android scans the original signed BSG 9.7 V32 APK and its
21 native libraries in `/system/app`. The module pre-grants the runtime
permissions requested by GCam and leaves them revocable in Settings. Disable or
remove the module and reboot to remove the system app; GCam data is preserved.

## RAW module recovery

Disable `x6810_raw12mp` in APatch and reboot. To move from v001 back to v000,
install the complete `x6810-raw-v000.zip` package and reboot. Keep a copy of
the previous release before updating.

When reporting an issue, include the version, model, API, and library hashes.
Remove serials, private paths, photos, DNGs, and full logs.
