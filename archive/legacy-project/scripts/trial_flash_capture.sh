#!/system/bin/sh
# Reversible bind-mount trial. Never writes the vendor partition or RAW module.
set -eu
H=/vendor/lib64/libcam.hal3a.v3.so
C=/data/local/tmp/x6810-flash-capture.so
BASE=7aeeb34cb3ec38bddb695effb1a4f1c0ab8aa39b447e12781579025cdffc3d6e
NEW=4d5a62e26aa736cc9b7632ba6b9ee6f63904f5d248ec3bfeece87fe80dcd15d2
[ "$(sha256sum "$H" | cut -d ' ' -f 1)" = "$BASE" ]
[ "$(sha256sum "$C" | cut -d ' ' -f 1)" = "$NEW" ]
mounted=0
cleanup() {
 trap - EXIT HUP INT TERM
 set +e
 setprop vendor.debug.x6810.flashcap 0
 am force-stop org.x6810.flashcontrol
 stop cameraserver
 stop camerahalserver
 [ "$mounted" = 0 ] || umount "$H"
 start camerahalserver
 start cameraserver
 sha256sum "$H"
 echo RESTORED_V012
}
trap cleanup EXIT HUP INT TERM
am force-stop com.transsion.camera
am force-stop com.android.MGC_9_7_047
am force-stop org.x6810.flashcontrol
chmod 0644 "$C"
chcon u:object_r:vendor_file:s0 "$C"
setprop vendor.debug.x6810.flashcap 0
stop cameraserver
stop camerahalserver
mount -o bind "$C" "$H"
mounted=1
start camerahalserver
start cameraserver
echo TRIAL_READY
# Caller may end the trial early through this dedicated marker.
i=0
while [ "$i" -lt 600 ] && [ ! -e /data/local/tmp/x6810-flash-trial-stop ]; do
 sleep 1
 i=$((i+1))
done
