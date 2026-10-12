# Infinix Zero X Neo X6810-GL camera project

This repository contains complete APatch modules, MediaTek camera-library
patches, analysis tools, and a separate GCam system-app module.

## Guides

- [Installation and recovery](INSTALLATION.md)
- [GCam and recommended XML](GCAM.md)
- [Building and publishing](BUILDING.md)
- [Project structure and licensing](PROJECT.md)
- [Camera architecture](ARCHITECTURE.md)
- [Compatibility and limitations](LIMITATIONS.md)

## Current versions

| Component | Version / target | Summary |
|---|---|---|
| RAW module | v001 | Camera2 RAW, processed JPEG up to 8000×6000, and TORCH/SINGLE APIs. HD48 is not 48 MP RAW. |
| GCam system-app module | 0.6.2, BSG 9.7 V32 | Installs the original signed APK and all 21 ARM64 libraries; pre-grants revocable runtime permissions and applies the native cache fix. |
| Recommended XML | BSG 9.7 V18 | Partial overlay with neutral values; not a complete preferences backup. |

The XML and GCam module target different BSG revisions. The GCam module does
not apply the XML. Read the [GCam guide](GCAM.md) before using either one.

Detailed experiment reports are grouped in the
[documentation index](../README.md). The experiments have not established a
repeatable visual improvement from the experimental RAW/denoise factors.
