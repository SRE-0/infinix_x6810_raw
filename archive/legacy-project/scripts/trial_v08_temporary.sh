#!/system/bin/sh
set -eu
M=/vendor/lib64/libmtkcam_metastore.so
P=/vendor/lib64/libmtkcam_pipelinepolicy.so
MC=/data/local/tmp/x6810-v08-metastore.so
PC=/data/local/tmp/x6810-v08-policy.so
file_sha() { sha256sum "$1" | cut -d ' ' -f 1; }
[ "$(file_sha "$M")" = 2b3bca8dfa83ea01c3f210b1b187c173a453665f3373afe9e8d17614b0fe95df ]
[ "$(file_sha "$P")" = 47924889f98b5e01c3220eb69235df8580d597172faa439cd71beb0f8f41d7bd ]
[ "$(file_sha "$MC")" = bdcf1bb3e5abe4bc14612e365730e7e15c4dd427b601060b7b30791944fdfddb ]
[ "$(file_sha "$PC")" = 40360af0dc17d589cdf36b5388b642200093511815e00d702f5d02e612333c47 ]
MM=0
PM=0
cleanup() {
  trap - EXIT HUP INT TERM
  set +e
  am force-stop com.android.MGC_9_7_047
  stop cameraserver
  stop camerahalserver
  [ "$PM" = 0 ] || umount "$P"
  [ "$MM" = 0 ] || umount "$M"
  start camerahalserver
  start cameraserver
  sha256sum "$M" "$P"
  echo RESTORED
}
trap cleanup EXIT HUP INT TERM
am force-stop com.android.MGC_9_7_047
chmod 0644 "$MC" "$PC"
chcon u:object_r:vendor_file:s0 "$MC" "$PC"
stop cameraserver
stop camerahalserver
mount -o bind "$MC" "$M"
MM=1
mount -o bind "$PC" "$P"
PM=1
start camerahalserver
start cameraserver
sha256sum "$M" "$P"
echo TEST_READY
sleep 150
