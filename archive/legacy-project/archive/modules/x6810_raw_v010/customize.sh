#!/system/bin/sh
# X6810 RAW installer style — SRE-0
MODNAME="X6810 RAW 0.10.0"
MODVERSION="0.10.0"
MODAUTHOR="SRE-0"
MODLINK="https://github.com/SRE-0"

print_separator() { printf '%*s' "$1" '' | tr ' ' "$2"; }
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
print_modname_frame() {
  local name_len frame_len line
  name_len=$(printf '%s' "$MODNAME" | wc -c)
  frame_len=$((name_len + 4))
  line=$(print_separator "$frame_len" '#')
  ui_print "$line"
  ui_print "  $MODNAME  "
  ui_print "$line"
}
print_env_info() {
  if [ "$APATCH" = true ]; then ui_print "Manager: APatch"
  elif [ "$KSU" = true ]; then ui_print "Manager: KernelSU"
  else ui_print "Manager: Magisk (versionCode $MAGISK_VER_CODE)"; fi
  ui_print "Android API level: $API"
  ui_print "Device ABI: $ARCH"
}
print_module_info() {
  ui_print "Version: $MODVERSION"
  ui_print "Author : $MODAUTHOR"
  ui_print "GitHub : $MODLINK"
  ui_print ' '
}
print_step() { ui_print "[$1/$2] $3"; }
print_footer() {
  ui_print ' '
  ui_print "$(print_separator 40 '-')"
  ui_print "$MODAUTHOR  |  $MODLINK"
  ui_print "$(print_separator 40 '-')"
}

print_banner
print_modname_frame
print_module_info
print_env_info
ui_print ' '
print_step 1 4 "Checking supported camera libraries"
# Exact supported library pairs only. Never writes the vendor partition.
command -v sha256sum >/dev/null 2>&1 || abort "sha256sum required"
file_sha() { sha256sum "$1" | cut -d ' ' -f 1; }
M=/vendor/lib64/libmtkcam_metastore.so
P=/vendor/lib64/libmtkcam_pipelinepolicy.so
MS=$(file_sha "$M")
PS=$(file_sha "$P")
case "$MS:$PS" in
  dbd740c5c7ba3081fb9d38b68b2f9975e19d6faad41dd5f87ce75f3c7d7be485:47924889f98b5e01c3220eb69235df8580d597172faa439cd71beb0f8f41d7bd|2b3bca8dfa83ea01c3f210b1b187c173a453665f3373afe9e8d17614b0fe95df:47924889f98b5e01c3220eb69235df8580d597172faa439cd71beb0f8f41d7bd|00066e79cbeb0020d09e8e1fb43670cde08ef30133bd0d86a138609fb561e4a6:40360af0dc17d589cdf36b5388b642200093511815e00d702f5d02e612333c47|dc18e2cdd107f4e56c98114a2de16592e275dd37e2bbd3960df7d12806d308d5:40360af0dc17d589cdf36b5388b642200093511815e00d702f5d02e612333c47|a05f038d7e638f597f751750cafc0e0c9d788be85588e52afbfeff9e583759d5:40360af0dc17d589cdf36b5388b642200093511815e00d702f5d02e612333c47) ;;
  *) abort "Unsupported camera library pair: $MS / $PS" ;;
esac
[ "$(file_sha "$MODPATH/system/vendor/lib64/libmtkcam_metastore.so")" = a05f038d7e638f597f751750cafc0e0c9d788be85588e52afbfeff9e583759d5 ] || abort "Metastore payload checksum mismatch"
[ "$(file_sha "$MODPATH/system/vendor/lib64/libmtkcam_pipelinepolicy.so")" = 40360af0dc17d589cdf36b5388b642200093511815e00d702f5d02e612333c47 ] || abort "Policy payload checksum mismatch"
for base in /data/adb/modules /data/adb/modules_update; do
  for other in "$base"/*; do
    [ -d "$other" ] || continue
    [ "${other##*/}" = x6810_raw12mp ] && continue
    [ -e "$other/disable" ] && continue
    [ -e "$other/remove" ] && continue
    [ -e "$other/skip_mount" ] && continue
    for lib in libmtkcam_metastore.so libmtkcam_pipelinepolicy.so; do
      if [ -f "$other/system/vendor/lib64/$lib" ] || [ -f "$other/vendor/lib64/$lib" ]; then
        abort "Conflicting camera module: ${other##*/}"
      fi
    done
  done
done
mkdir -p "$MODPATH/backup"
cp -p "$M" "$MODPATH/backup/libmtkcam_metastore.previous.so" || abort "Cannot back up metastore"
cp -p "$P" "$MODPATH/backup/libmtkcam_pipelinepolicy.previous.so" || abort "Cannot back up policy"
printf '%s\n%s\n' "$MS" "$PS" > "$MODPATH/backup/previous.sha256"
set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/vendor" 0 0 0755 0644 u:object_r:vendor_file:s0
for script in post-fs-data.sh service.sh boot-completed.sh; do
  set_perm "$MODPATH/$script" 0 0 0755
done
print_step 4 4 "Finishing installation"
ui_print "X6810: both camera libraries verified; reboot required."
ui_print "Read README.md for front resolution limits and paired rollback."
print_footer
