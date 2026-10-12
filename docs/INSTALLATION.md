**English** | [Español](es/INSTALLATION.md)

# Installation and recovery

1. Build with `python scripts/build.py`, or obtain a project release and verify `SHA256SUMS.txt`.
2. Keep a working root/recovery route before changing camera libraries. Stop if the installer rejects the firmware.
3. Install one variant through APatch: `x6810-raw-1.1.0.zip` for RAW/OIS/HD48, or `x6810-raw-flash-1.1.0.zip` for the exact Android 16 flash profile.
4. Reboot. Check the OEM camera, preview and capture on all three sensors, and DNG in an app that requests RAW. Boot success alone does not establish camera functionality.
5. Request `LENS_OPTICAL_STABILIZATION_MODE=ON` on the telephoto sensor. OIS was tested and works correctly on Android 16 GSI. The module does not change app settings; the separate recommended BSG V32 XML enables photo OIS.

Both variants share `id=x6810_raw12mp`. Switch by installing the other ZIP and rebooting. The manager must replace the complete module tree, so RAW does not retain the flash cameraserver. Offline fixtures cover accepted binary tuples; the repackaged variant switch has not been exercised on a phone.

To undo, disable/remove `x6810_raw12mp` and reboot. From recovery/root, create `/data/adb/modules/x6810_raw12mp/disable` if Android cannot boot. Do not copy backups onto vendor: they contain the previous visible library, which may itself be an overlay. The two-incomplete-boot counter is a recovery aid, may take an additional boot to act, and does not guarantee bootloop prevention.

Before returning to stock, turn off GCam settings that force OIS. [External GCam and recommended V32 settings](GCAM.md). The GCam system module is installed separately.
