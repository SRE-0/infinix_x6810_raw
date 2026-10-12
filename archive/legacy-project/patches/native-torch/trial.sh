#!/system/bin/sh
set -eu
[ "$(sha256sum /vendor/lib64/libcam.hal3a.v3.so | cut -d " " -f 1)" = "4d5a62e26aa736cc9b7632ba6b9ee6f63904f5d248ec3bfeece87fe80dcd15d2" ]
[ "$(sha256sum /data/local/tmp/x6810-native-torch/libcam.hal3a.v3.so | cut -d " " -f 1)" = "0669ac8e0f329e941ead3098a3ea0828597f8ce68c40a6ec7bef4607d6bbbecd" ]
[ "$(sha256sum /vendor/lib64/libmtkcam_device3_hal.so | cut -d " " -f 1)" = "0333ea749a9b15eb9ecf21215a2ebea11c5d3fbff247acd7ec93022256d544b1" ]
[ "$(sha256sum /data/local/tmp/x6810-native-torch/libmtkcam_device3_hal.so | cut -d " " -f 1)" = "5044cc95b014182d1639539db49e0a2418a2d4ff1e9e25c093cadd8d456911c8" ]
[ "$(sha256sum /system/bin/cameraserver | cut -d " " -f 1)" = "0e61fed272068a7855e236f9fb23d3e07e46bc1ba5588f92398c1a789e457f0c" ]
[ "$(sha256sum /data/local/tmp/x6810-native-torch/cameraserver | cut -d " " -f 1)" = "2f361a730064a2e8ccab8a3cd7fce8854f30dfffa141e7888f0f3b91b8aa867c" ]
m0=0; m1=0; m2=0
cleanup() {
 trap - EXIT HUP INT TERM
 set +e
 am force-stop org.x6810.flashcontrol
 stop cameraserver
 stop camerahalserver
[ "$m2" = 0 ] || umount /system/bin/cameraserver
[ "$m1" = 0 ] || umount /vendor/lib64/libmtkcam_device3_hal.so
[ "$m0" = 0 ] || umount /vendor/lib64/libcam.hal3a.v3.so
 start camerahalserver
 start cameraserver
 echo NATIVE_TRIAL_RESTORED
}
trap cleanup EXIT HUP INT TERM
am force-stop com.transsion.camera
am force-stop com.android.MGC_9_7_047
am force-stop org.x6810.flashcontrol
stop cameraserver
stop camerahalserver
chmod 0755 /data/local/tmp/x6810-native-torch/libcam.hal3a.v3.so
chcon u:object_r:vendor_file:s0 /data/local/tmp/x6810-native-torch/libcam.hal3a.v3.so
mount -o bind /data/local/tmp/x6810-native-torch/libcam.hal3a.v3.so /vendor/lib64/libcam.hal3a.v3.so
m0=1
chmod 0755 /data/local/tmp/x6810-native-torch/libmtkcam_device3_hal.so
chcon u:object_r:vendor_file:s0 /data/local/tmp/x6810-native-torch/libmtkcam_device3_hal.so
mount -o bind /data/local/tmp/x6810-native-torch/libmtkcam_device3_hal.so /vendor/lib64/libmtkcam_device3_hal.so
m1=1
chmod 0755 /data/local/tmp/x6810-native-torch/cameraserver
chcon u:object_r:cameraserver_exec:s0 /data/local/tmp/x6810-native-torch/cameraserver
mount -o bind /data/local/tmp/x6810-native-torch/cameraserver /system/bin/cameraserver
m2=1
mount -o remount,bind,suid /system/bin/cameraserver
start camerahalserver
start cameraserver
echo NATIVE_TRIAL_READY
i=0
while [ "$i" -lt 600 ] && [ ! -e /data/local/tmp/x6810-native-torch/stop ]; do
 sleep 1
 i=$((i+1))
done
