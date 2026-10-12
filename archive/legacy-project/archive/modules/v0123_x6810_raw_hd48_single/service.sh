#!/system/bin/sh
MODDIR=${0%/*}
setprop vendor.debug.x6810.flashcap 0
if [ "$(sha256sum /system/bin/cameraserver | cut -d ' ' -f 1)" = 23cbf1d21c54c923577267a6f974b526c6950b5ecdcae7e3a53fc6b57a640e09 ]; then
 mount -o remount,bind,suid /system/bin/cameraserver
 [ "$(getprop init.svc.cameraserver)" = running ] || start cameraserver
fi
TRIES=0
while [ "$(getprop sys.boot_completed)" != 1 ] && [ "$TRIES" -lt 120 ]; do
 sleep 5
 TRIES=$((TRIES + 1))
done
[ "$(getprop sys.boot_completed)" = 1 ] && sh "$MODDIR/boot-completed.sh"
exit 0
