#!/system/bin/sh
# Best-effort incomplete-boot counter, not a guarantee of recovery.
# A manager may already have snapshotted its mount list for this boot.
MODDIR=${0%/*}
COUNT=0
[ -r "$MODDIR/.boot_attempts" ] && read -r COUNT < "$MODDIR/.boot_attempts"
case "$COUNT" in 0|1|2) ;; *) COUNT=0 ;; esac
if [ "$COUNT" -ge 2 ]; then
  touch "$MODDIR/disable"
  echo 0 > "$MODDIR/.boot_attempts"
  echo "Disabled after two incomplete boots; effective no later than next boot." > "$MODDIR/boot-status.txt"
  exit 0
fi
echo $((COUNT + 1)) > "$MODDIR/.boot_attempts"
