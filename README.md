<div align="center">
<h1>Infinix X6810 RAW</h1>
<p>RAW · Telephoto OIS · JPEG HD48 · Optional flash</p>
<p>By <a href="https://github.com/SRE-0">SRE-0</a></p>
</div>

<p align="center">
  <img src="https://raw.githubusercontent.com/SRE-0/SRE-0/90a97a564019ec898fbf6a22afc2c59fd2004cf2/githubBanner.png" alt="SRE-0 project banner" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Android-X6810--GL-9ece6a?style=for-the-badge&labelColor=1a1b26&logo=android&logoColor=white" alt="Android X6810-GL">
  <img src="https://img.shields.io/badge/Python-3.11+-7aa2f7?style=for-the-badge&labelColor=1a1b26&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Git-LFS-f7768e?style=for-the-badge&labelColor=1a1b26&logo=git&logoColor=white" alt="Git LFS">
  <img src="https://img.shields.io/badge/APatch-systemless-73daca?style=for-the-badge&labelColor=1a1b26" alt="APatch systemless">
</p>

<p align="center">**English** · [Español](docs/es/README.md)</p>

## Camera modules

Two systemless camera variants for the Infinix Zero X Neo **X6810-GL**, maintained separately from the [GCam port project](https://github.com/SRE-0/infinix_x6810_gcam_port).

| Variant | Features | Installation compatibility |
|---|---|---|
| **RAW** | Three-sensor RAW16, RAW buffers, telephoto OIS, processed JPEG HD48 | Android 11/API 30+ with known vendor/OIS binaries |
| **RAW + flash** | All RAW features plus TORCH/SINGLE strength bridges | Exact Android 16 GSI/API 36 vendor/framework profile |

**OIS was tested and works correctly on the telephoto sensor.** Device evidence is from Android 16 GSI. Android 11 and future releases have not been tested: the RAW SDK floor and firmware hash checks express the installation policy. HD48 is processed JPEG, not native 48 MP RAW.

The combined public flash APIs require Android 15/API 35, but the included framework binary and hooks remain tied to Android 16/API 36. [Compatibility review](docs/FLASH_COMPATIBILITY.md).

## Build and install

```sh
git lfs install
git lfs pull
python scripts/validate.py
python scripts/build.py
```

Python 3.11+ is required; installer validation needs POSIX `sh` (Git Bash on Windows). ZIPs and SHA-256 manifests are generated in `dist/releases/`. Install **one** variant through APatch and reboot. Both share `id=x6810_raw12mp`. [Installation, switching and recovery](docs/INSTALLATION.md). The standard Magisk entry point is retained; the reorganized packaging has not been tested on hardware.

## External GCam

You can install any compatible external GCam; the optional GCam system module is separate. [BSG MGC_9.7.047_V32_MGC.apk](https://1-dontsharethislink.celsoazevedo.com/file/filesc/MGC_9.7.047_V32_MGC.apk), package `com.android.MGC_9_7_047`, was tested and works perfectly on Android 16 GSI with [the recommended V32 XML](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/profiles/x6810-gcam-bsg-9.7-v32-recommended.xml). [Profile instructions and GCam project](https://github.com/SRE-0/infinix_x6810_gcam_port).

## Documentation and organization

- [Compatibility and sensor limitations](docs/COMPATIBILITY.md)
- [Architecture and reproducible builds](docs/DEVELOPMENT.md)
- [Organization audit](docs/AUDIT.md)
- [Historical research](docs/RESEARCH.md)
- [Legal review](docs/LEGAL.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [disclaimer](DISCLAIMER.md)

`scripts/` provides the maintained commands, `module/common/` the boot lifecycle, and `payloads/` the pinned inputs. `archive/legacy-project/` preserves original camera experiments; it is not an automatic release selection. Generated output and private device data stay outside Git. GCam has its own repository and local-only decompilation workflow.

## Disclaimer

Experimental software, supplied as-is without warranties to the fullest extent permitted by law. You assume the risks of installation and use. To that extent, SRE-0 and contributors disclaim liability for device damage, data loss, boot failures and other losses. Mandatory rights and non-excludable liability remain unaffected. Third-party binaries retain their own rights; this repository has no blanket license or blanket redistribution permission. Read [the full disclaimer](DISCLAIMER.md) and [legal review](docs/LEGAL.md).

## Contact

<p align="center">
  <a href="mailto:sergioandresp660@gmail.com"><img src="https://img.shields.io/badge/Email-f7768e?style=for-the-badge&labelColor=1a1b26&logo=gmail&logoColor=white" alt="Email"></a>
  <a href="https://sre-0.github.io/SRE-0_web"><img src="https://img.shields.io/badge/Website-bb9af7?style=for-the-badge&labelColor=1a1b26&logo=googlechrome&logoColor=white" alt="Website"></a>
</p>
