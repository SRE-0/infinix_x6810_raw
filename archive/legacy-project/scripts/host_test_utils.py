"""Portable shell helpers shared by host-side installer tests."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile


def find_shell() -> Path:
    candidate = shutil.which("sh")
    if candidate:
        return Path(candidate)
    git_bash = Path("C:/Program Files/Git/usr/bin/sh.exe")
    if git_bash.is_file():
        return git_bash
    raise SystemExit("Host installer tests require a POSIX sh (Git Bash on Windows)")


SH = find_shell()


def shell_path(path: object) -> str:
    """Convert a host path to the syntax understood by the selected shell."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        pass
    value = resolved.as_posix()
    if os.name == "nt" and len(value) >= 3 and value[1:3] == ":/":
        value = f"/{value[0].lower()}/{value[3:]}"
    return value


def shell_quote(path: object) -> str:
    value = shell_path(path).replace("'", "'\\''")
    return f"'{value}'"


def test_tempdir(root: Path, prefix: str) -> tempfile.TemporaryDirectory[str]:
    """Create disposable installer fixtures inside the writable repository."""
    parent = root / "dist" / "verification" / "tmp"
    parent.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix=prefix, dir=parent)
