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
