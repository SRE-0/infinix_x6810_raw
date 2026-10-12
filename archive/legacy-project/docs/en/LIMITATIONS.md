# Compatibility and limitations

- Offsets belong to exact ELF builds. An OTA can invalidate them; the
  installer accepts only the listed hashes.
- Validation covers the X6810-GL with Android 16/API 36 and APatch. General
  compatibility with other ROMs or managers has not been established.
- `LEVEL_3` does not mean CTS certification or guarantee every Camera2 mode.
- The 8000×6000 JPEG is processed from a 4000×3000 input; RAW48 is not
  provided. Conventional front RAW is 2320×1744 binned.
- OIS and flash control paths were checked; quantified optical improvement in
  motion and universal intensity calibration have not been demonstrated.
- GCam denoise/luma/chroma factors remain experimental. An isolated visual
  quality improvement has not been reproduced.
- The GCam startup APatch module and XML target different BSG revisions (V32
  and V18). First launch after reboot can be slow while ART optimizes the app.
- MediaTek/Transsion binaries and the GCam APK belong to third parties. This
  repository grants no redistribution rights and has no project-wide license.

Specific results are linked from the [technical index](../README.md).
