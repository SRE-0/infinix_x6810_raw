#!/system/bin/sh
# Magisk does not invoke boot-completed.sh; provide a bounded fallback.
MODDIR=${0%/*}
[ "$APATCH" = true ] && exit 0
TRIES=0
while [ "$(getprop sys.boot_completed)" != 1 ] && [ "$TRIES" -lt 120 ]; do
  sleep 5
  TRIES=$((TRIES + 1))
done
[ "$(getprop sys.boot_completed)" = 1 ] && sh "$MODDIR/boot-completed.sh"
exit 0

setprop vendor.debug.x6810.flashcap 0

# The individual executable bind must allow init -> cameraserver transition.
# Never remount /data or relax SELinux.
if [ "$(sha256sum /system/bin/cameraserver | cut -d ' ' -f 1)" = 2f361a730064a2e8ccab8a3cd7fce8854f30dfffa141e7888f0f3b91b8aa867c ]; then
 mount -o remount,bind,suid /system/bin/cameraserver
 [ "$(getprop init.svc.cameraserver)" = running ] || start cameraserver
fi
