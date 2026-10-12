#!/system/bin/sh
# Run as root on Android. Reads diagnostics; writes only the selected output folder.
# No setprop/resetprop, mounts, service restarts, flashing, or module installation.
OUT=${1:-/sdcard/Download/x6810-camera-diagnostics}
mkdir -p "$OUT" || exit 1
getprop > "$OUT/getprop.txt"
dumpsys media.camera > "$OUT/media-camera.txt" 2>&1
pm list features > "$OUT/features.txt" 2>&1
ps -A > "$OUT/processes.txt" 2>&1
cat /proc/mounts > "$OUT/mounts.txt"
logcat -b all -d -t 8000 > "$OUT/logcat.txt" 2>&1
dmesg > "$OUT/dmesg.txt" 2>&1
find /vendor /odm -type f \( -name '*mtkcam*' -o -name '*camera*' -o -name '*imgsensor*' -o -name '*remosaic*' -o -name '*_tuning.so' -o -name '*_IdxMgr.so' -o -name '*cam_cal*' \) > "$OUT/vendor-camera-files.txt" 2>&1
for p in /vendor/lib64/libmtkcam_metastore.so /vendor/lib64/libmtkcam_3rdparty.customer.so /vendor/lib/libmtkcam_metastore.so; do
  [ -f "$p" ] || continue
  sha256sum "$p"
  ls -lZ "$p"
done > "$OUT/library-identities.txt" 2>&1
ls -ldZ /vendor /vendor/lib64 /vendor/etc /vendor/etc/permissions > "$OUT/vendor-contexts.txt" 2>&1
ls -la /data/adb/modules > "$OUT/modules.txt" 2>&1
for p in /proc/driver/camera_info /proc/driver/camera_info2 /proc/driver/camera_info3; do
  if [ -r "$p" ]; then echo "$p"; cat "$p"; fi
done > "$OUT/sensor-info.txt" 2>&1
echo "Diagnostics saved in $OUT"
