#!/system/bin/sh
##########################################################################################
# service.sh
#
# Runs once the "late_start" service stage is reached (device is mostly
# booted). This is the stage most modules use for background tasks, since
# the system and most apps are already available at this point.
#
# This is a TEMPLATE placeholder. Delete this file if your module does not
# need to run anything after boot.
##########################################################################################

MODDIR=${0%/*}

# TODO: add post-boot logic here.
#
# Example: wait for sys.boot_completed and then hand off to a follow-up
# script (useful because plain Magisk, unlike some managers, does not call
# boot-completed.sh on its own):
#
#   TRIES=0
#   while [ "$(getprop sys.boot_completed)" != 1 ] && [ "$TRIES" -lt 120 ]; do
#     sleep 5
#     TRIES=$((TRIES + 1))
#   done
#   [ "$(getprop sys.boot_completed)" = 1 ] && sh "$MODDIR/boot-completed.sh"