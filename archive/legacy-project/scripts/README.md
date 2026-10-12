# Scripts catalog

Scripts are kept at the project root level to preserve their existing import
paths and command lines. The main groups are:

- `build_*.py`, `verify_*.py`, `package_*.py`: patch creation, review, and
  complete module packaging.
- `analyze_*.py`, `audit_*.py`, `inspect_*.py`, `compare_*.py`: offline
  binary, metadata, image, and trace analysis.
- `collect_*.py`, `probe_*.py`, `trial_*.py`, `trace_*.py`: device-backed
  diagnostics and experiments. These may call ADB and can change device state;
  read each script before running it.
- `configure_mgc_photo.py`: backed-up, hash-checked GCam preference overlay.
- `package_github_release.py`: creates the release packages and their SHA-256
  manifest without connecting to a device.

Python dependencies are declared in `requirements*.txt`. Binary patch scripts
depend on the exact stock hashes in `stock-binaries/`; do not substitute a
library from a different firmware build.
