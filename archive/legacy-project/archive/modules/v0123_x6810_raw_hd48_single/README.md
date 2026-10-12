# v0123_x6810_raw_hd48_single

Main Camera2 SINGLE strength 1..30 to AW36515 duty 0..29; bounded 300ms timeout; preserves HD48, RAW/OIS and torch 0..8.

Only the exact X6810 Android 16 GSI and five-file baseline are accepted. Install with APatch and reboot. CameraService is firmware-specific.

SINGLE levels 10..30 select photographic duties 9..29; default 7 preserves duty 6. CameraManager torch remains levels 1..9 / duties 0..8. No claim of optical power calibration or CTS compliance. See docs/SINGLE_FLASH.md.

Paired rollback: v0123_x6810_raw_rollback_single.zip (keeps HD48).
