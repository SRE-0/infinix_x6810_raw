**English** | [Español](es/GCAM.md)

# External GCam

You can install any compatible external GCam as a normal app. RAW/OIS/HD48 and flash operate at the Camera2/vendor layer and do not require a specific APK or the optional GCam system module. Compatibility still depends on the port and Android version.

[BSG MGC_9.7.047_V32_MGC.apk](https://1-dontsharethislink.celsoazevedo.com/file/filesc/MGC_9.7.047_V32_MGC.apk), package `com.android.MGC_9_7_047`, was tested and works perfectly with [the recommended X6810 V32 profile](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/profiles/x6810-gcam-bsg-9.7-v32-recommended.xml) on Android 16 GSI. Telephoto OIS was tested and works correctly.

Export your current BSG config, then import the recommended XML using `Load config`. See the [profile guide](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/profiles/README.md). DNG saving is disabled in the supplied snapshot (`pref_camera_raw_output_key=0`); enable it in the app if needed. The profile enables photo OIS but does not force every port to request HD48 JPEG or provide 48 MP RAW.

The optional system module uses the exact original signed V32 APK with a separate native cache-library replacement. It is maintained in [infinix_x6810_gcam_port](https://github.com/SRE-0/infinix_x6810_gcam_port), not bundled into either RAW ZIP.
