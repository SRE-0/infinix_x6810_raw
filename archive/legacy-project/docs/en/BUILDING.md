# Building and publishing

## Prepare the clone

The modified GCam APK and native library exceed GitHub's regular 100 MB file
limit, so Git LFS stores them.

```powershell
git lfs install
git clone <repository-URL>
cd raw-camera-infinix-x6810
git lfs pull
```

Without LFS, the GCam module will be missing the payloads required to build.

## Build packages locally

From the repository root with Python 3.11 or newer:

```powershell
python scripts/package_github_release.py --raw-version v001 --output-dir dist/github-release
```

This creates a complete ZIP of the selected RAW module, builds the GCam module
with hash checks, copies the XML, and writes `SHA256SUMS.txt`. It does not
install anything on a phone. The output directory must not already exist.

To rebuild the RAW modules from source and manifests, install the build
dependencies and run:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r scripts\requirements.txt
.venv\Scripts\python.exe scripts\build_single_flash_api.py
.venv\Scripts\python.exe scripts\verify_single_flash_api.py
.venv\Scripts\python.exe scripts\package_camera_module.py
```

The builders require known input hashes. Keep the originals in
`stock-binaries/`; do not substitute libraries from another ROM.

Binary patch builders require the stock libraries in `stock-binaries/`. See
[scripts/README.md](../../scripts/README.md) and the manifests under `patches/`
before changing offsets or hashes.

## Create a release with GitHub Actions

After these files are pushed and merged into `main`, open **Actions → Create
X6810 release → Run workflow**. Enter a unique tag and select `v000` or `v001`.
The workflow attaches the complete RAW module, GCam module, XML, and checksums.
It only accepts runs started or re-run by `sre-0` from `main`; the account
needs write access and Actions must be enabled for the repository.

The GCam APK is stored in Git LFS. Check the GitHub plan's LFS storage and
bandwidth quotas before publishing large clones. This workspace has not run
the release workflow.
