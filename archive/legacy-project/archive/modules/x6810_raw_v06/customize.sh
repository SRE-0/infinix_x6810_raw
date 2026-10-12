#!/system/bin/sh
##########################################################################################
# customize.sh
#
# This script runs during module installation (Magisk / APatch installer).
# It is responsible for:
#   1. Printing a personalized installer banner (ASCII art + GitHub info).
#   2. Printing environment info (which root manager is installing the module).
#   3. Printing numbered installation steps for a clear, organized log.
#   4. Setting file/folder permissions for the module payload.
#   5. Printing a closing footer block.
#
# This is a TEMPLATE. Replace the TODO sections below with the actual
# installation logic for your specific module (file checks, hash
# verification, backups, conflict detection, etc).
#
# COMPATIBILITY NOTE: this script targets minimal Android shells (some root
# managers run customize.sh with toybox sh instead of BusyBox ash), so it
# intentionally avoids constructs that are not universally supported, such
# as single-line "{ cmd; }" brace groups.
##########################################################################################

# -----------------------------------------------------------------------------
# Module identity constants
#
# Edit these values to personalize the banner text without touching the
# print functions below. Keeping them separate makes it easy to reuse this
# customize.sh across different modules.
# -----------------------------------------------------------------------------
MODNAME="X6810 RAW16 main + telephoto + HI1631Q remosaic"
MODVERSION="0.6.0-hi1631q-remosaic"
MODAUTHOR="SRE-0"
MODLINK="https://github.com/SRE-0"

# -----------------------------------------------------------------------------
# print_separator
#
# What it does:
#   Prints a horizontal line made of a repeated character, sized to a given
#   width. Used to frame the module name without hardcoding a fixed-width
#   string that breaks if MODNAME changes length.
#
# How it works:
#   Uses printf to generate $1 spaces and tr to convert them into the
#   requested character ($2). This mirrors the approach used in Magisk's
#   own official module installer script (print_modname).
#
# Parameters:
#   $1 - width of the line, in characters
#   $2 - single character to repeat (e.g. '#', '-', '=')
#
# Usage:
#   print_separator 40 '='
# -----------------------------------------------------------------------------
print_separator() {
  printf '%*s' "$1" '' | tr ' ' "$2"
}

# -----------------------------------------------------------------------------
# print_banner
#
# What it does:
#   Prints an ASCII art banner (the author's GitHub handle) one line at a
#   time through ui_print, the installer's output function.
#
# How it works:
#   Each line is passed individually to ui_print because some installer
#   implementations do not reliably render embedded newlines inside a single
#   ui_print call. Single quotes are REQUIRED here (not double quotes),
#   because the ASCII art contains backslashes. Inside double quotes, a
#   trailing backslash right before the closing " escapes that quote
#   instead of closing the string, which silently swallows the rest of the
#   script into one giant unterminated string and produces a confusing
#   syntax error far below this function. Single quotes make every
#   character literal, so this cannot happen.
#
# Parameters:
#   None.
#
# Usage:
#   print_banner
# -----------------------------------------------------------------------------
print_banner() {
  ui_print '==========================================='
  ui_print '   _____ ____  ______      ____ '
  ui_print '  / ___// __ \/ ____/     / __ \'
  ui_print '  \__ \/ /_/ / __/ ______/ / / /'
  ui_print ' ___/ / _, _/ /__ /_____/ /_/ / '
  ui_print '/____/_/ |_/_____/      \____/  '
  ui_print ' '
  ui_print '==========================================='
  ui_print ' '
}

# -----------------------------------------------------------------------------
# print_modname_frame
#
# What it does:
#   Prints the module name inside a dynamically sized frame, so the border
#   always matches the name length instead of using a fixed-width string.
#
# How it works:
#   Calculates the frame width from the length of MODNAME plus padding,
#   then calls print_separator twice (top and bottom) around the name line.
#
# Parameters:
#   None (reads MODNAME defined above).
#
# Usage:
#   print_modname_frame
# -----------------------------------------------------------------------------
print_modname_frame() {
  local name_len frame_len line
  name_len=$(printf '%s' "$MODNAME" | wc -c)
  frame_len=$((name_len + 4))
  line=$(print_separator "$frame_len" '#')
  ui_print "$line"
  ui_print "  $MODNAME  "
  ui_print "$line"
}

# -----------------------------------------------------------------------------
# print_env_info
#
# What it does:
#   Prints which root manager is installing the module (APatch, KernelSU or
#   Magisk) plus the Magisk version code when available. Helps the user
#   confirm the module is running on a supported environment at a glance.
#
# How it works:
#   Reads the environment variables the installer exports: $APATCH and $KSU
#   are set to true by their respective managers, $MAGISK_VER_CODE is set by
#   Magisk. Falls back to "Magisk" when neither APATCH nor KSU is set.
#
# Parameters:
#   None.
#
# Usage:
#   print_env_info
# -----------------------------------------------------------------------------
print_env_info() {
  if [ "$APATCH" = true ]; then
    ui_print "Manager: APatch"
  elif [ "$KSU" = true ]; then
    ui_print "Manager: KernelSU"
  else
    ui_print "Manager: Magisk (versionCode $MAGISK_VER_CODE)"
  fi
  ui_print "Android API level: $API"
  ui_print "Device ABI: $ARCH"
}

# -----------------------------------------------------------------------------
# print_module_info
#
# What it does:
#   Prints module metadata (version, author, GitHub link) right below the
#   name frame, giving the installer output a consistent, personalized look.
#
# How it works:
#   Reads the MODVERSION / MODAUTHOR / MODLINK constants defined above and
#   writes each one through ui_print.
#
# Parameters:
#   None (reads the module constants defined above this function).
#
# Usage:
#   print_module_info
# -----------------------------------------------------------------------------
print_module_info() {
  ui_print "Version: $MODVERSION"
  ui_print "Author : $MODAUTHOR"
  ui_print "GitHub : $MODLINK"
  ui_print ' '
}

# -----------------------------------------------------------------------------
# print_step
#
# What it does:
#   Prints a numbered installation step (e.g. "[2/4] Setting permissions"),
#   so a multi-stage TODO section reads as an organized sequence instead of
#   a wall of unrelated ui_print lines.
#
# How it works:
#   Formats the current step and total step count, then the description.
#
# Parameters:
#   $1 - current step number
#   $2 - total number of steps
#   $3 - short description of the step
#
# Usage:
#   print_step 1 4 "Checking target file"
# -----------------------------------------------------------------------------
print_step() {
  ui_print "[$1/$2] $3"
}

# -----------------------------------------------------------------------------
# fail
#
# What it does:
#   Prints a clearly tagged error line before aborting the installation.
#   Keeps error output visually distinct from normal informational lines
#   without overriding the installer's built-in abort() function.
#
# How it works:
#   Prefixes the message with "[ERROR]" and delegates to abort(), which the
#   Magisk/APatch installer environment provides (it stops the install and
#   shows the message).
#
# Parameters:
#   $1 - error message to display
#
# Usage:
#   fail "Missing required file"
# -----------------------------------------------------------------------------
fail() {
  abort "[ERROR] $1"
}

# -----------------------------------------------------------------------------
# print_footer
#
# What it does:
#   Prints a closing block that mirrors the opening banner, so the log ends
#   on a personalized note instead of stopping abruptly after the last step.
#
# Parameters:
#   None.
#
# Usage:
#   print_footer
# -----------------------------------------------------------------------------
print_footer() {
  ui_print ' '
  ui_print "$(print_separator 40 '-')"
  ui_print "$MODAUTHOR  |  $MODLINK"
  ui_print "$(print_separator 40 '-')"
}

# ==========================================================================
# Module-specific installation logic
# ==========================================================================

print_banner
print_modname_frame
print_module_info
print_env_info
ui_print ' '

STOCK_SHA=dbd740c5c7ba3081fb9d38b68b2f9975e19d6faad41dd5f87ce75f3c7d7be485
MAIN_SHA=daecf7263eafbf1075432979e2854617ef0e830e301059a22977551e5469caa8
AUX_SHA=7a41b870658b2eeea8eb0a612219ca6e73de90b78b6b27a74d778d2804e43f5b
FRONT_SHA=a1bb426f73f1e363f3e0a7fbcf2e7e95d24b52c45efc25633b58ed057622575a
TIMING_SHA=d3cc530a971f187bde4873dd63c8c257496e446a31996f3f3df0c866716c41c6
BINNED_SHA=99b9762ec7d6fd0b341c7d82b41dca50fa2ddd141225d9294e45638021d599f0
PATCH_SHA=663c326b319a8e70f99089677cf43c02fbd8f1942b3b2fa9b4b5682af3f04c55
TARGET=/vendor/lib64/libmtkcam_metastore.so
MODULES=/data/adb/modules
PAYLOAD="$MODPATH/system/vendor/lib64/libmtkcam_metastore.so"
[ -f "$TARGET" ] || abort "! Missing $TARGET"
command -v sha256sum >/dev/null 2>&1 || abort "! sha256sum is required"
ACTUAL_SHA=$(sha256sum "$PAYLOAD")
ACTUAL_SHA=${ACTUAL_SHA%% *}
[ "$ACTUAL_SHA" = "$PATCH_SHA" ] || abort "! Payload checksum mismatch"
LIVE_SHA=$(sha256sum "$TARGET")
LIVE_SHA=${LIVE_SHA%% *}
case "$LIVE_SHA" in
  "$STOCK_SHA"|"$MAIN_SHA"|"$AUX_SHA"|"$FRONT_SHA"|"$TIMING_SHA"|"$BINNED_SHA"|"$PATCH_SHA") ;;
  *) abort "! Unsupported vendor library hash: $LIVE_SHA. Restore a supported stock/v0.1-v0.5 base first." ;;
esac
for other in "$MODULES"/*; do
  [ -d "$other" ] || continue
  [ "${other##*/}" = x6810_raw12mp ] && continue
  [ -e "$other/disable" ] && continue
  [ -e "$other/remove" ] && continue
  [ -e "$other/skip_mount" ] && continue
  if [ -f "$other/system/vendor/lib64/libmtkcam_metastore.so" ] || [ -f "$other/vendor/lib64/libmtkcam_metastore.so" ]; then
    abort "! Conflicting camera library module: ${other##*/}. Disable it and reboot first."
  fi
done
mkdir -p "$MODPATH/backup"
cp -p "$TARGET" "$MODPATH/backup/libmtkcam_metastore.previous.so" || abort "! Cannot back up visible library"
printf '%s
' "$LIVE_SHA" > "$MODPATH/backup/previous.sha256"
set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/vendor" 0 0 0755 0644 u:object_r:vendor_file:s0
for script in post-fs-data.sh service.sh boot-completed.sh; do
  set_perm "$MODPATH/$script" 0 0 0755
done
ui_print "- Exact library and payload hashes verified"
ui_print "- Rear RAW patches preserved"
ui_print "- HI1631Q publishes only valid 4640x3488 RAW16"
ui_print "- Front request defaults enable MTK 4Cell remosaic and processed RAW"
ui_print "- Auxiliary camera properties included; reboot required"

print_footer
