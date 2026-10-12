"""Build the unified X6810 RAW + Camera2 flash API releases."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from host_test_utils import SH
from module_template import apply_template, normalize_module_prop, style_customize

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "modules"
BASE = MODULES / "v000_x6810_GL_raw_hd48_12mp_torch_changes"
CURRENT = MODULES / "v001_x6810_GL_raw_hd48_12mp_torch_single_flash_apis_changes"
PATCH = ROOT / "patches/single-flash-api"
OUT = ROOT / "dist/releases"

TORCH_TUPLE = {
    "system/vendor/lib64/libmtkcam_metastore.so": "bafeda846d6d6b81361487a6fa265ee4c70d6b085ce5520d0bd727b077d55d68",
    "system/vendor/lib64/libmtkcam_pipelinepolicy.so": "d3bfa9aab5d43af352a3bf717ff4b399cad6744ccc2c548ef8ae4650f3635ad2",
    "system/vendor/lib64/libcam.hal3a.v3.so": "0669ac8e0f329e941ead3098a3ea0828597f8ce68c40a6ec7bef4607d6bbbecd",
    "system/bin/cameraserver": "2f361a730064a2e8ccab8a3cd7fce8854f30dfffa141e7888f0f3b91b8aa867c",
    "system/vendor/lib64/libmtkcam_device3_hal.so": "5044cc95b014182d1639539db49e0a2418a2d4ff1e9e25c093cadd8d456911c8",
}
SINGLE_PATCHED = {
    "system/vendor/lib64/libcam.hal3a.v3.so": "8fdc35e83cf5f08dcc5c3e841256514f4fa9933e24aa6841a003eb79006b86b2",
    "system/bin/cameraserver": "23cbf1d21c54c923577267a6f974b526c6950b5ecdcae7e3a53fc6b57a640e09",
}
BASE_LABEL = "v000_x6810_GL_raw_hd48_12mp_torch_changes"
CURRENT_LABEL = "v001_x6810_GL_raw_hd48_12mp_torch_single_flash_apis_changes"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def live_path(rel: str) -> str:
    return "/" + rel.replace("system/vendor/", "vendor/")


def zip_module(module: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(module.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(module).as_posix()
            info = zipfile.ZipInfo(rel, (2026, 10, 8, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o100755 if rel.endswith(".sh") or rel == "system/bin/cameraserver" else 0o100644
            info.external_attr = mode << 16
            archive.writestr(info, path.read_bytes())
    return sha(destination.read_bytes())


def module_files(module: Path) -> dict[str, bytes]:
    return {p.relative_to(module).as_posix(): p.read_bytes()
            for p in module.rglob("*") if p.is_file()}


def set_metadata(files: dict[str, bytes], label: str, version: str,
                 version_code: int, description: str) -> None:
    files["module.prop"] = (
        f"id=x6810_raw12mp\nname={label}\nversion={version}\n"
        f"versionCode={version_code}\nauthor=SRE-0\ndescription={description}\n"
    ).encode()


def installer(payload_hashes: dict[str, str], description: str) -> bytes:
    # Accept only the known v0.12.2 RAW/TORCH baseline or this integrated release.
    # The same allow-list makes moving between full releases a normal APatch update.
    pairs = [TORCH_TUPLE, {**TORCH_TUPLE, **SINGLE_PATCHED}]
    tuple_rows = [": ".join(state[p] for p in TORCH_TUPLE) for state in pairs]
    # Shell case patterns cannot contain whitespace around their separators.
    tuple_rows = [row.replace(": ", ":") for row in tuple_rows]
    variables = [f"$S{i}" for i in range(len(TORCH_TUPLE))]
    text = '''#!/system/bin/sh
[ "$(getprop ro.product.device)" = Infinix-X6810 ] || abort "X6810 required"
[ "$(getprop ro.build.version.sdk)" = 36 ] || abort "Android 16/API 36 required"
file_sha() { sha256sum "$1" | cut -d ' ' -f 1; }
'''
    for i, rel in enumerate(TORCH_TUPLE):
        text += f"S{i}=$(file_sha {live_path(rel)})\n"
    text += "case \"" + ":".join(variables) + "\" in\n " + "|".join(tuple_rows)
    text += ") ;;\n *) abort \"Unsupported X6810 camera binary set\" ;;\nesac\n"

    # Protect the other RAW/OIS payloads and verify the complete package.
    for rel, digest in payload_hashes.items():
        text += f'[ "$(file_sha "$MODPATH/{rel}")" = {digest} ] || abort "Payload mismatch: {rel}"\n'
    text += '''for base in /data/adb/modules /data/adb/modules_update; do
 for other in "$base"/*; do
  [ -d "$other" ] || continue
  [ "${other##*/}" = x6810_raw12mp ] && continue
  [ -e "$other/disable" ] && continue
  [ -e "$other/remove" ] && continue
  for rel in system/bin/cameraserver system/vendor/lib64/libcam.hal3a.v3.so system/vendor/lib64/libmtkcam_device3_hal.so system/vendor/lib64/libmtkcam_metastore.so system/vendor/lib64/libmtkcam_pipelinepolicy.so; do
   [ ! -f "$other/$rel" ] && [ ! -f "$other/${rel#system/}" ] || abort "Conflicting camera overlay"
  done
 done
done
mkdir -p "$MODPATH/backup"
for file in /system/bin/cameraserver /vendor/lib64/libcam.hal3a.v3.so /vendor/lib64/libmtkcam_device3_hal.so /vendor/lib64/libmtkcam_metastore.so /vendor/lib64/libmtkcam_pipelinepolicy.so; do
 cp -p "$file" "$MODPATH/backup/${file##*/}" || abort "Backup failed"
done
set_perm_recursive "$MODPATH" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/vendor" 0 0 0755 0644 u:object_r:vendor_file:s0
for script in post-fs-data.sh service.sh boot-completed.sh; do set_perm "$MODPATH/$script" 0 0 0755; done
set_perm "$MODPATH/system/bin/cameraserver" 0 2000 0755 u:object_r:cameraserver_exec:s0
'''
    return text.encode()


def service(camera_server_hash: str) -> bytes:
    return f'''#!/system/bin/sh
MODDIR=${{0%/*}}
setprop vendor.debug.x6810.flashcap 0
if [ "$(sha256sum /system/bin/cameraserver | cut -d ' ' -f 1)" = {camera_server_hash} ]; then
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
'''.encode()


def build_base(records: list[dict]) -> dict[str, str]:
    files = module_files(BASE)
    observed = {rel: sha(files[rel]) for rel in TORCH_TUPLE}
    if observed != TORCH_TUPLE:
        raise ValueError(f"Base RAW/TORCH payload does not match manifest: {observed}")
    for rel, expected in TORCH_TUPLE.items():
        if expected != observed[rel]:
            raise ValueError(f"Wrong baseline {rel}")
    description = "RAW/HD48 Level 3+ with Camera2 TORCH strength 1-9; complete prior release."
    set_metadata(files, BASE_LABEL, "v000", 1, description)
    files["README.md"] = (
        f"# {BASE_LABEL}\n\n{description}\n\n"
        "Instalable completo anterior a SINGLE, con el mismo ID APatch `x6810_raw12mp`. "
        "Instala este ZIP para volver a esta revisión y reinicia. Consulte docs/FLASH_CAMERA2_API.md.\n"
    ).encode()
    files["service.sh"] = service(TORCH_TUPLE["system/bin/cameraserver"])
    files["customize.sh"] = installer(observed, description)
    files["payload-sha256.json"] = (json.dumps(observed, indent=2) + "\n").encode()
    for rel, data in files.items():
        target = BASE / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    normalize_module_prop(BASE)
    style_customize(BASE)
    for path in BASE.glob("*.sh"):
        subprocess.run([str(SH), "-n", str(path)], check=True)
    digest = zip_module(BASE, OUT / "v000" / f"{BASE_LABEL}.zip")
    records.append({"version": "v000", "file": f"dist/releases/v000/{BASE_LABEL}.zip",
                    "sha256": digest, "module": BASE_LABEL, "payloads": observed})
    return observed


def build_current(records: list[dict], base_hashes: dict[str, str]) -> None:
    files = module_files(BASE)
    manifests: dict[str, dict] = {}
    for name, rel in (("libcam.hal3a.v3.so", "system/vendor/lib64/libcam.hal3a.v3.so"),
                      ("cameraserver", "system/bin/cameraserver")):
        manifest = json.loads((PATCH / f"{name}.json").read_text(encoding="utf-8"))
        patch_data = (PATCH / name).read_bytes()
        if manifest["input_sha256"] != base_hashes[rel] or sha(patch_data) != manifest["output_sha256"]:
            raise ValueError(f"SINGLE patch does not match the Torch base: {name}")
        files[rel] = patch_data
        manifests[name] = manifest

    candidate = {rel: sha(files[rel]) for rel in base_hashes}
    expected_candidate = {**base_hashes, **SINGLE_PATCHED}
    if candidate != expected_candidate:
        raise ValueError(f"Unexpected merged payload: {candidate}")
    description = (
        "RAW/HD48 Level 3+; Camera2 TORCH levels 1-9 (duties 0-8) and "
        "SINGLE photographic levels 1-30 (duties 0-29)."
    )
    set_metadata(files, CURRENT_LABEL, "v001", 1, description)
    files["customize.sh"] = installer(candidate, description)
    files["service.sh"] = service(candidate["system/bin/cameraserver"])
    files["README.md"] = (
        f"# {CURRENT_LABEL}\n\n{description}\n\n"
        "Este es el módulo unificado. SINGLE 1-30 asigna duty 0-29; el default 7 conserva duty 6. "
        "El pulso fotográfico mantiene un timeout de software de 300 ms. "
        "Consulta docs/FLASH_CAMERA2_API.md y docs/INSTALLATION.md.\n"
    ).encode()
    files["payload-sha256.json"] = (json.dumps(candidate, indent=2) + "\n").encode()
    files["flash-api-manifests.json"] = (json.dumps(manifests, indent=2) + "\n").encode()
    apply_template(CURRENT)
    for rel, data in files.items():
        target = CURRENT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    normalize_module_prop(CURRENT)
    style_customize(CURRENT)
    for path in CURRENT.glob("*.sh"):
        subprocess.run([str(SH), "-n", str(path)], check=True)
    digest = zip_module(CURRENT, OUT / "v001" / f"{CURRENT_LABEL}.zip")
    records.append({"version": "v001", "file": f"dist/releases/v001/{CURRENT_LABEL}.zip",
                    "sha256": digest, "module": CURRENT_LABEL, "payloads": candidate})


def main() -> None:
    if not BASE.is_dir():
        raise FileNotFoundError(f"Missing complete prior release source: {BASE}")
    records: list[dict] = []
    base_hashes = build_base(records)
    build_current(records, base_hashes)
    for version in ("v000", "v001"):
        (OUT / version / "SHA256SUMS.json").write_text(
            json.dumps([row for row in records if row["version"] == version], indent=2) + "\n",
            encoding="utf-8")
    (OUT / "RELEASES.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
