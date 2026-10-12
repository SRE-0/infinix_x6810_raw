"""Check full v000/v001 installers and downgrade acceptance on host fixtures."""
import json
import shutil
import subprocess
from pathlib import Path

from host_test_utils import SH, shell_quote as q, test_tempdir
from package_camera_module import BASE, CURRENT, ROOT, live_path

rows = []
with test_tempdir(ROOT, "camera-releases-") as temp:
    root = Path(temp).resolve()
    assert root.is_relative_to((ROOT / "dist/verification/tmp").resolve())
    for source in (BASE, CURRENT):
        payload = json.loads((source / "payload-sha256.json").read_text())
        for case in ("base", "current", "wrong-device", "wrong-sdk", "mixed", "corrupt",
                     "unknown", "conflict", "pending", "disabled"):
            folder = root / source.name / case
            active, pending = folder / "active", folder / "pending"
            target, current = folder / "new", folder / "live"
            for path in (active, pending, target, current):
                path.mkdir(parents=True)
            baseline = CURRENT if case in ("current", "mixed") else BASE
            for rel in payload:
                for directory, origin in ((current, baseline), (target, source)):
                    destination = directory / rel
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(origin / rel, destination)
            if case == "mixed":
                shutil.copyfile(BASE / "system/bin/cameraserver", current / "system/bin/cameraserver")
            if case == "corrupt":
                (target / "system/bin/cameraserver").write_bytes(b"corrupt")
            if case == "unknown":
                (current / "system/vendor/lib64/libmtkcam_pipelinepolicy.so").write_bytes(b"unknown")
            if case in ("conflict", "pending", "disabled"):
                other = (pending if case == "pending" else active) / "other"
                conflict = other / "system/vendor/lib64/libcam.hal3a.v3.so"
                conflict.parent.mkdir(parents=True)
                conflict.write_bytes(b"conflict")
                if case == "disabled":
                    (other / "disable").touch()
            script = (source / "customize.sh").read_text()
            script = script.replace("/data/adb/modules /data/adb/modules_update", q(active) + " " + q(pending))
            for rel in payload:
                script = script.replace("file_sha " + live_path(rel), "file_sha " + q(current / rel))
            backups = ("system/bin/cameraserver", "system/vendor/lib64/libcam.hal3a.v3.so",
                       "system/vendor/lib64/libmtkcam_device3_hal.so",
                       "system/vendor/lib64/libmtkcam_metastore.so",
                       "system/vendor/lib64/libmtkcam_pipelinepolicy.so")
            script = script.replace(
                "for file in " + " ".join(live_path(rel) for rel in backups) + "; do",
                "for file in " + " ".join(q(current / rel) for rel in backups) + "; do")
            stubs = (
                "abort() { echo \"$*\"; exit 91; }\nui_print() { :; }\n"
                "set_perm() { :; }\nset_perm_recursive() { :; }\n"
            )
            stubs += "getprop() { case \"$1\" in ro.product.device) echo "
            stubs += ("wrong" if case == "wrong-device" else "Infinix-X6810")
            stubs += ";; ro.build.version.sdk) echo " + ("35" if case == "wrong-sdk" else "36")
            stubs += ";; esac; }\n"
            harness = folder / "run.sh"
            harness.write_text("PATH=/usr/bin:$PATH\nMODPATH=" + q(target) + "\n" + stubs + script,
                               newline="\n")
            result = subprocess.run([str(SH), harness.as_posix()], capture_output=True, text=True)
            accepted = case in ("base", "current", "disabled")
            assert result.returncode == (0 if accepted else 91), (source.name, case, result.stdout, result.stderr)
            if accepted:
                for rel in payload:
                    assert (target / "backup" / Path(rel).name).read_bytes() == (current / rel).read_bytes()
            else:
                assert not (target / "backup").exists()
            rows.append({"module": source.name, "case": case, "accepted": accepted})

output = ROOT / "dist/verification/camera-installers.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(rows, indent=2) + "\n")
print("PASS", len(rows), "release installer cases; downgrade and backup paths checked")
