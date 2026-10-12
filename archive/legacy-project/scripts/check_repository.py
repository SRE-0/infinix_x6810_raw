"""Repository hygiene checks that require only the Python standard library."""
from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "modules"
FORBIDDEN_SUFFIXES = {".dng", ".log", ".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".zip"}
FORBIDDEN_PATH_PARTS = {"__pycache__", ".local-private", ".venv", "venv", "dist", "local-data", "research"}
PERSONAL_PATTERNS = (
    re.compile(r"C:[\\/]Users[\\/]", re.IGNORECASE),
    re.compile(r"[\\/]home[\\/][^/\\]+", re.IGNORECASE),
    re.compile(r"OneDrive[\\/]Documentos", re.IGNORECASE),
)


def public_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(ROOT)
        if any(part in FORBIDDEN_PATH_PARTS for part in relative.parts):
            continue
        files.append(path)
    return files


def check_modules(errors: list[str]) -> None:
    modules = sorted(path for path in MODULES.iterdir() if path.is_dir())
    if not modules:
        errors.append("No modules found")
    name_pattern = re.compile(r"v\d{3}_x6810_GL_[a-z0-9]+(?:_[a-z0-9]+)*_changes")
    required_ui = ("print_banner", "print_modname_frame", "print_env_info", "print_footer")
    module_ids: set[str] = set()
    for module in modules:
        prop = (module / "module.prop").read_text(encoding="utf-8")
        customize = (module / "customize.sh").read_text(encoding="utf-8")
        values = dict(line.split("=", 1) for line in prop.splitlines() if "=" in line)
        if not name_pattern.fullmatch(module.name):
            errors.append(f"{module.name}: release name must use vNNN_x6810_GL_<description>_changes")
        if values.get("name") != module.name:
            errors.append(f"{module.name}: module.prop name does not match release folder")
        if values.get("id") != "x6810_raw12mp":
            errors.append(f"{module.name}: all complete camera releases must share id=x6810_raw12mp")
        module_ids.add(values.get("id", ""))
        if values.get("versionCode") != "1":
            errors.append(f"{module.name}: versionCode must not block manual downgrades")
        if any(path.suffix.lower() in {".apk", ".dex"} for path in module.rglob("*")):
            errors.append(f"{module.name}: apps are not part of the camera module")
        if "author=SRE-0" not in prop.splitlines():
            errors.append(f"{module.name}: module.prop author is not SRE-0")
        if 'MODAUTHOR="SRE-0"' not in customize:
            errors.append(f"{module.name}: installer author is not SRE-0")
        for marker in required_ui:
            if marker not in customize:
                errors.append(f"{module.name}: missing template marker {marker}")
    if len(module_ids) > 1:
        errors.append("Release modules do not share one module ID")


def check_hygiene(errors: list[str]) -> None:
    for path in public_files():
        relative = path.relative_to(ROOT)
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"Private/generated file type in public tree: {relative}")
        if path.suffix.lower() not in {".md", ".txt", ".json", ".xml", ".csv", ".py", ".sh", ".prop", ".yml", ".yaml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in PERSONAL_PATTERNS:
            if pattern.search(text):
                errors.append(f"Personal absolute path in {relative}")
                break


def main() -> None:
    errors: list[str] = []
    check_modules(errors)
    check_hygiene(errors)
    if errors:
        raise SystemExit("Repository validation failed:\n- " + "\n- ".join(errors))
    print(f"PASS: public repository hygiene and {len(list(MODULES.iterdir()))} modules validated")


if __name__ == "__main__":
    main()
