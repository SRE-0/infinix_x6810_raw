#!/system/bin/sh
MODDIR=${0%/*}
echo 0 > "$MODDIR/.boot_attempts"
{
  echo "Android boot completed; this does not establish RAW capture success."
  sha256sum /vendor/lib64/libmtkcam_metastore.so
  ls -lZ /vendor/lib64/libmtkcam_metastore.so
} > "$MODDIR/boot-status.txt" 2>&1

sha256sum /vendor/lib64/libmtkcam_pipelinepolicy.so >> "$MODDIR/boot-status.txt" 2>&1

sha256sum /vendor/lib64/libcam.hal3a.v3.so >> "$MODDIR/boot-status.txt" 2>&1
