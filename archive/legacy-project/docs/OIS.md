# OIS on the OV08A10 telephoto

## Finding

The X6810's third rear camera (Camera2 ID `2`, MTK sensor device `4`, focal length about 11.8 mm) is the OV08A10 telephoto. Its vendor metadata already identifies it as an OIS master: `com.transsion.tranOisSupport=1`, `tranOisIsMaster=1`, `tranOisNumber=1`. The vendor OIS library and device endpoint are present as `libtran_oismgr.so` and `/dev/bu63169_ois`.

Stock Camera2 characteristics nevertheless reported `android.lens.info.availableOpticalStabilization=[OFF]` for every camera. The OV08A10's existing private request/result keys include `com.transsion.tranOisMode`; `com.transsion.availtranoismode` lists `[0,1,2]`. A standard Camera2 client asking for OIS ON did not by itself keep the Transsion controller running. During the stock-path trace, the HAL sent `EOisCmd_SuspendOis` after initializing the telephoto controller.

The HAL also contains an explicit package allowlist for its normal private OIS request handling. The factory Transsion camera is allowed, while `com.android.MGC_9_7_047` is not. This explains how the factory app can know about the actuator while a third-party camera sees OIS as unavailable and may have its request overridden.

## Experimental correction

The v0.12 experimental module overlays three libraries systemlessly:

- `libmtkcam_metastore.so` adds the standard byte array `[OFF, ON]` only to OV08A10 `LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION` (`0x90003`). The other 103 metadata constructors were compared under AArch64 ABI-clobber emulation and were unchanged.
- `libcam.hal3a.v3.so` reads the standard `LENS_OPTICAL_STABILIZATION_MODE` request (`0x80004`) in the existing non-allowlisted Transsion request path. For sensor device 4, it maps OFF to Transsion suspend command 2 and ON to resume command 1. It checks that the OIS object has an open file descriptor and reports one supported OIS unit. Other sensor devices continue through the original code path.
- `libmtkcam_pipelinepolicy.so` is the unmodified v0.11 payload, retained so the RAW-buffer fix remains active.

The original stock Transsion camera remains on the vendor's allowlisted path. Android's OIS position reporting is not advertised: `STATISTICS_INFO_AVAILABLE_OIS_DATA_MODES` remains null.

GCam 9.7 has its own developer flag, `camera.ois_forced_photo_mode`, which defaults to false in this profile. Enabling this flag caused GCam to put `ON` in the Camera2 request. The separate `pref_video_stabilization_ois_key` is a video preference and does not enable photo OIS. The v0.12 installer does not edit either GCam preference. On the test phone the photo flag was enabled for the GCam verification; its other preference values were preserved.

## Device evidence

Tested on 2 October 2026 with the connected Infinix X6810-GL, Android fingerprint `Infinix/X6810-GL/Infinix-X6810:11/RP1A.200720.011/230824V630:user/release-keys`, APatch root, and package `com.android.MGC_9_7_047`. The user had requested no ARTEMIS, so all device exploration used ADB, Camera2, and a bounded Frida trace of the loaded HAL.

With the installed module after reboot:

- the telephoto advertised `[0, 1]`; each other Camera2 device continued to advertise `[0]`;
- a Camera2 probe completed OFF → ON → OFF with 45 preview results per state; the request and capture result agreed for each state;
- the concurrent native trace saw successful BU63169 suspend, resume, and suspend ioctls (`0x7002`, `0x7001`, `0x7002`), each returning `0`;
- GCam with `camera.ois_forced_photo_mode=true` reported the capture-result mode as `ON`, and the last controller command during that session was resume (`0x7001`), rather than the post-initialization suspend seen on stock;
- six regression capture paths passed: RAW16 and JPEG on the main, front, and telephoto cameras. The temporary overlay was also compared with Camera2 characteristics: the only static-characteristic difference was the telephoto OIS array.

The controller's mode-read ioctl (`0x80047005`) returns `ENOTTY` on this kernel, and OIS position data is not published. Therefore these checks prove the request reaches the vendor suspend/resume path and that the HAL reports the requested mode. They do not measure lens displacement or show a before/after stabilization improvement in a moving scene. Treat v0.12 as experimental until that optical comparison is made.

## Main rear camera: S5KGM1ST

The main camera is not configured as an OIS camera in this X6810 software stack. The kernel log identifies sensor index 0 as `s5kgm1st_mipi_raw`; Camera2 ID 0 is the rear camera with a 4.71 mm focal length. Its stock `LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION` is `[OFF]`, and its static metadata does not contain the Transsion `tranOisSupport`, `tranOisIsMaster`, or `tranOisNumber` characteristics. By comparison, the 11.8 mm tele camera has all three private values set to `1` and advertises Transsion OIS modes `[0,1,2]`.

On 2 October 2026, the existing Camera2 probe opened ID 0 and submitted standard OIS requests OFF → ON → OFF. It received 45 preview results in each state. The HAL echoed the requested ON value in capture results even though ID 0 advertises only OFF; that echo alone does not indicate actuator movement. A bounded Frida trace overlapped the ON request and recorded no OIS-manager method calls or BU63169 ioctls for ID 0. This contrasts with the telephoto trace, where `setOisNumber(1)`, `setisMaster(1)`, and successful suspend/resume ioctls were observed.

The sensor itself is an image-sensing chip, not the moving optical actuator. Samsung's announcement for the GM1 family describes gyro-based electronic image stabilization (EIS); Samsung Electro-Mechanics describes OIS as lens movement driven by an actuator in the camera module. The public Samsung GM1 article does not specify the exact `S5KGM1ST` suffix, so it is family-level evidence rather than a suffix-specific datasheet. The useful distinction is that EIS capability in a sensor does not establish that the phone's main lens module contains an OIS actuator.

The vendor image also contains general EIS/gyro libraries and `libvidhance_active_ois.so`. The latter has Vidhance/stabilizer/stabilization processing strings but no literal reference to S5KGM1ST, OV08A10, `/dev/bu63169_ois`, or an `ioctl` interface. It is evidence of a software stabilization component, not evidence that the main camera has a mechanical OIS actuator.

**Conclusion:** the available software evidence says the X6810 main S5KGM1ST path has no configured or reachable OIS control path, while it supports the standard electronic/video stabilization path. It does not prove the physical main-camera module lacks an unconfigured actuator. Confirming that physical fact requires the main module's exact part number/BOM or inspection of the module/EEPROM and actuator hardware. Do not extend the telephoto-only v0.12 bridge to sensor device 0 without that evidence.

References: [Samsung Semiconductor, GM1/GD1 announcement](https://semiconductor.samsung.com/us/news-events/news/introducing-two-new-0-point-8-micrometer-isocell-image-sensors/); [Samsung Electro-Mechanics, camera-module actuators and OIS](https://sem.samsung.com/global/product/module/camera-module/main-core-technology.do).

## Reproduction and recovery

The device probe can be rebuilt with `python scripts/build_ois_probe.py`. Install `dist/ois-probe/ois-probe.apk`, stop GCam, and run:

```sh
adb shell am start -n org.x6810.oisprobe/.ProbeActivity --es camera 2 --ez standardOnly true
adb pull /sdcard/Android/data/org.x6810.oisprobe/files/result.txt
```

The HAL trace helper `scripts/collect_ois_trace.py` requires a local Frida server matching the pinned Frida version and ADB forwarding. It records OIS methods and controller ioctls; `--readback` optionally also records the unsupported mode-read attempt. A trace can stall preview while hooks are attached, so stop and close the trace before judging frame delivery.

The installed overlay is APatch module `x6810_raw12mp`, version `0.12.0-ois-experimental`. Before installing an earlier full release, turn `camera.ois_forced_photo_mode` off in GCam; the v0.11 characteristics do not advertise OIS and may reject a request that asks for it. Repackage the complete v0.11 snapshot from `archive/modules/x6810_raw_v011` with `scripts/package_legacy_release.py`, install its ZIP, and reboot. The active catalog no longer uses paired rollback modules. To remove the camera module altogether, turn that GCam flag off, disable `x6810_raw12mp` in APatch, and reboot.

The stock HAL, Transsion OIS manager, traces, captures, GCam preferences, and device identifiers used during this investigation stay under ignored local paths. Do not add those private artifacts to a public report.
