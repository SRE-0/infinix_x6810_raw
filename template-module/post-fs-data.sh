#!/system/bin/sh
##########################################################################################
# post-fs-data.sh
#
# Runs very early in boot, before most of the system is up (post-fs-data
# stage). Use this stage only for work that must happen before other apps
# or services start (e.g. replacing a file that another process reads
# during boot).
#
# This is a TEMPLATE placeholder. Most modules do NOT need this file —
# delete it if your module has no early-boot requirement.
##########################################################################################

MODDIR=${0%/*}

# TODO: add early-boot logic here.
#
# Example: a boot-attempt counter that auto-disables the module after
# repeated incomplete boots (useful as a safety net for risky patches):
#
#   COUNT=0
#   [ -r "$MODDIR/.boot_attempts" ] && read -r COUNT < "$MODDIR/.boot_attempts"
#   case "$COUNT" in 0|1|2) ;; *) COUNT=0 ;; esac
#   if [ "$COUNT" -ge 2 ]; then
#     touch "$MODDIR/disable"
#     echo 0 > "$MODDIR/.boot_attempts"
#     exit 0
#   fi
#   echo $((COUNT + 1)) > "$MODDIR/.boot_attempts"