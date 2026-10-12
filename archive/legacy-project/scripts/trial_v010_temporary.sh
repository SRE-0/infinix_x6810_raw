#!/system/bin/sh
set -eu
M=/vendor/lib64/libmtkcam_metastore.so
P=/vendor/lib64/libmtkcam_pipelinepolicy.so
MC=/data/local/tmp/x6810-v010-metastore.so
file_sha() { sha256sum "$1" | cut -d ' ' -f 1; }
[ "$(file_sha "$M")" = dc18e2cdd107f4e56c98114a2de16592e275dd37e2bbd3960df7d12806d308d5 ]
[ "$(file_sha "$P")" = 40360af0dc17d589cdf36b5388b642200093511815e00d702f5d02e612333c47 ]
[ "$(file_sha "$MC")" = a05f038d7e638f597f751750cafc0e0c9d788be85588e52afbfeff9e583759d5 ]
MM=0
cleanup() {
  trap - EXIT HUP INT TERM
  set +e
  am force-stop org.x6810.reprocessprobe
  am force-stop com.android.MGC_9_7_047
  stop cameraserver
  stop camerahalserver
  [ "$MM" = 0 ] || umount "$M"
  start camerahalserver
  start cameraserver
  sha256sum "$M" "$P"
  echo RESTORED_V09
}
trap cleanup EXIT HUP INT TERM
am force-stop com.android.MGC_9_7_047
chmod 0644 "$MC"
chcon u:object_r:vendor_file:s0 "$MC"
stop cameraserver
stop camerahalserver
mount -o bind "$MC" "$M"
MM=1
start camerahalserver
start cameraserver
echo TEST_READY
sleep 240
