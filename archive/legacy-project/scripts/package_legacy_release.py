"""Repackage a full archived RAW module using the current version naming scheme."""
from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

from module_template import normalize_module_prop, style_customize
from host_test_utils import SH
from package_camera_module import ROOT, sha, zip_module


def live_path(rel: str) -> str:
    return "/" + rel.replace("system/vendor/", "vendor/")


def legacy_installer(payload_hashes: dict[str, str]) -> bytes:
    payload_paths = list(payload_hashes)
    states: set[str] = set()
    candidates = [p for root in (ROOT / "modules", ROOT / "archive/modules")
                  if root.is_dir() for p in sorted(root.iterdir()) if p.is_dir()]
    for candidate in candidates:
        prop = candidate / "module.prop"
        if not prop.is_file():
            continue
        values = dict(line.split("=", 1) for line in prop.read_text(encoding="utf-8").splitlines()
                      if "=" in line)
        if values.get("id") != "x6810_raw12mp" or "rollback" in values.get("name", "").lower():
            continue
        files = []
        for rel in payload_paths:
            path = candidate / rel
            if not path.is_file():
                break
            files.append(sha(path.read_bytes()))
        if len(files) == len(payload_paths):
            states.add(":".join(files))
    if not states:
        raise ValueError("No archived full release matches this payload")
    variables = ":".join(f"$S{i}" for i in range(len(payload_paths)))
    text = '''#!/system/bin/sh
[ "$(getprop ro.product.device)" = Infinix-X6810 ] || abort "X6810 required"
[ "$(getprop ro.build.version.sdk)" = 36 ] || abort "Android 16/API 36 required"
file_sha() { sha256sum "$1" | cut -d ' ' -f 1; }
'''
    for i, rel in enumerate(payload_paths):
        text += f"S{i}=$(file_sha {shlex.quote(live_path(rel))})\n"
    text += "case \"" + variables + "\" in\n " + "|".join(sorted(states))
    text += ") ;;\n *) abort \"Camera files do not match a known full release\" ;;\nesac\n"
    for rel, digest in payload_hashes.items():
        text += f'[ "$(file_sha "$MODPATH/{rel}")" = {digest} ] || abort "Payload mismatch: {rel}"\n'
    text += '''for base in /data/adb/modules /data/adb/modules_update; do
 for other in "$base"/*; do
  [ -d "$other" ] || continue
  [ "${other##*/}" = x6810_raw12mp ] && continue
  [ -e "$other/disable" ] && continue
  [ -e "$other/remove" ] && continue
  for rel in ''' + " ".join(payload_paths) + '''; do
   [ ! -f "$other/$rel" ] && [ ! -f "$other/${rel#system/}" ] || abort "Conflicting camera overlay"
  done
 done
done
mkdir -p "$MODPATH/backup"
'''
    for rel in payload_paths:
        text += f'cp -p {shlex.quote(live_path(rel))} "$MODPATH/backup/{Path(rel).name}" || abort "Backup failed: {rel}"\n'
    text += '''set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/vendor" 0 0 0755 0644 u:object_r:vendor_file:s0
for script in post-fs-data.sh service.sh boot-completed.sh; do set_perm "$MODPATH/$script" 0 0 0755; done
'''
    if "system/bin/cameraserver" in payload_paths:
        text += 'set_perm "$MODPATH/system/bin/cameraserver" 0 2000 0755 u:object_r:cameraserver_exec:s0\n'
    return text.encode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Folder name under archive/modules")
    parser.add_argument("--version", required=True, help="Release label such as v002")
    parser.add_argument("--description", required=True, help="Lowercase underscore-separated feature name")
    args = parser.parse_args()
    if not re.fullmatch(r"v\d{3}", args.version):
        parser.error("--version must match v000, v001, v002, ...")
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", args.description):
        parser.error("--description must contain lowercase letters, digits, and underscores")
    source = ROOT / "archive/modules" / args.source
    if not source.is_dir() or "rollback" in source.name.lower():
        parser.error("source must be a complete archived release, not a rollback")
    source_prop = source / "module.prop"
    if not source_prop.is_file():
        parser.error("source has no module.prop")
    values = dict(line.split("=", 1) for line in source_prop.read_text(encoding="utf-8").splitlines()
                  if "=" in line)
    if values.get("id") != "x6810_raw12mp" or "rollback" in values.get("name", "").lower():
        parser.error("source is not a full X6810 RAW camera release")
    label = f"{args.version}_x6810_GL_{args.description}_changes"
    output_dir = ROOT / "dist/releases" / args.version
    output = output_dir / f"{label}.zip"
    scratch_root = ROOT / ".local-private/legacy-release-build"
    scratch_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="release-", dir=scratch_root) as temporary:
        module = Path(temporary) / label
        shutil.copytree(source, module)
        payload_hashes = {
            path.relative_to(module).as_posix(): sha(path.read_bytes())
            for path in sorted((module / "system").rglob("*")) if path.is_file()
        } if (module / "system").is_dir() else {}
        if not payload_hashes:
            parser.error("source has no system payloads; it cannot be a complete module release")
        prop = dict(values)
        prop["name"] = label
        prop["version"] = args.version
        # Module managers do not need a monotonically increasing versionCode to
        # install a selected archive; keeping it constant permits free downgrades.
        prop["versionCode"] = "1"
        prop["author"] = "SRE-0"
        prop["description"] = args.description.replace("_", " ")
        (module / "module.prop").write_text(
            "".join(f"{key}={prop[key]}\n" for key in
                    ("id", "name", "version", "versionCode", "author", "description")),
            encoding="utf-8", newline="\n")
        (module / "payload-sha256.json").write_text(json.dumps(payload_hashes, indent=2) + "\n",
                                                     encoding="utf-8")
        (module / "customize.sh").write_bytes(legacy_installer(payload_hashes))
        readme = module / "README.md"
        old = readme.read_text(encoding="utf-8") if readme.exists() else ""
        readme.write_text(f"# {label}\n\n{prop['description']}\n\n" + old,
                          encoding="utf-8", newline="\n")
        normalize_module_prop(module)
        style_customize(module)
        for path in module.glob("*.sh"):
            subprocess.run([str(SH), "-n", str(path)], check=True)
        digest = zip_module(module, output)
    index = output_dir / "SHA256SUMS.json"
    rows = json.loads(index.read_text(encoding="utf-8")) if index.exists() else []
    rows = [row for row in rows if row.get("file") != output.name]
    rows.append({"file": output.name, "module": label, "sha256": digest, "source": args.source})
    index.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"file": str(output.relative_to(ROOT)), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
