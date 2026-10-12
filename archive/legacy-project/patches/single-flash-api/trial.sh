#!/system/bin/sh
set -eu
[ "$(sha256sum /vendor/lib64/libcam.hal3a.v3.so | cut -d " " -f 1)" = "0669ac8e0f329e941ead3098a3ea0828597f8ce68c40a6ec7bef4607d6bbbecd" ]
[ "$(sha256sum /data/local/tmp/x6810-single-trial/libcam.hal3a.v3.so | cut -d " " -f 1)" = "8fdc35e83cf5f08dcc5c3e841256514f4fa9933e24aa6841a003eb79006b86b2" ]
[ "$(sha256sum /system/bin/cameraserver | cut -d " " -f 1)" = "2f361a730064a2e8ccab8a3cd7fce8854f30dfffa141e7888f0f3b91b8aa867c" ]
[ "$(sha256sum /data/local/tmp/x6810-single-trial/cameraserver | cut -d " " -f 1)" = "23cbf1d21c54c923577267a6f974b526c6950b5ecdcae7e3a53fc6b57a640e09" ]
m0=0; m1=0; m2=0
cleanup() {
 trap - EXIT HUP INT TERM
 set +e
 am force-stop org.x6810.flashcontrol
 stop cameraserver
 stop camerahalserver
[ "$m1" = 0 ] || umount /system/bin/cameraserver
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
chmod 0755 /data/local/tmp/x6810-single-trial/libcam.hal3a.v3.so
chcon u:object_r:vendor_file:s0 /data/local/tmp/x6810-single-trial/libcam.hal3a.v3.so
mount -o bind /data/local/tmp/x6810-single-trial/libcam.hal3a.v3.so /vendor/lib64/libcam.hal3a.v3.so
m0=1
chmod 0755 /data/local/tmp/x6810-single-trial/cameraserver
chcon u:object_r:cameraserver_exec:s0 /data/local/tmp/x6810-single-trial/cameraserver
mount -o bind /data/local/tmp/x6810-single-trial/cameraserver /system/bin/cameraserver
m1=1
mount -o remount,bind,suid /system/bin/cameraserver
start camerahalserver
start cameraserver
echo NATIVE_TRIAL_READY
i=0
while [ "$i" -lt 600 ] && [ ! -e /data/local/tmp/x6810-single-trial/stop ]; do
 sleep 1
 i=$((i+1))
done
