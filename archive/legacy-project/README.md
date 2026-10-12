# Infinix Zero X Neo X6810-GL: camera RAW and GCam

[Guía en español](docs/es/README.md) · [English guide](docs/en/README.md) · [Document index](docs/README.md)

This repository contains complete APatch modules, binary patch sources and
manifests, device-specific camera research, and a GCam system-app module for the
Infinix Zero X Neo X6810-GL.

- **RAW module:** current package is `v001`, with Camera2 RAW support, processed
  8000×6000 JPEG output, and TORCH/SINGLE flash APIs. `HD48` is processed JPEG,
  not 48 MP RAW.
- **GCam module:** `x6810_gcam_startup` 0.7.0 installs the hash-verified BSG
  9.7 V32 original signed APK as a privileged system app, grants declared runtime
  permissions and special accesses, and keeps the native cache fix. It is independent from the RAW module.
- **GCam settings:** the recommended XML is a small, neutral BSG V18
  SharedPreferences overlay. It is not a full app backup. The profile keeps
  experimental noise factors neutral because the project has not established
  a repeatable image-quality gain.
- **Releases:** `.github/workflows/create-release.yml` can publish the selected
  complete RAW module, the GCam module, the XML overlay, and SHA-256 checksums.
  The workflow is restricted to `sre-0` and the `main` branch.

Start with the [Spanish documentation](docs/es/README.md) or the
[English documentation](docs/en/README.md). Detailed experiment notes remain
available in [docs/](docs/README.md).

The four stock MediaTek/Transsion camera libraries and the patched module
payloads are included for reproducibility. Their redistribution terms are not
granted by this project; see [third-party notices](THIRD_PARTY_NOTICES.md).
The project itself has no general-purpose license declaration. The vendored
`mtkcam-raw` library remains under MPL-2.0.

## Español

Este repositorio contiene módulos APatch completos, parches binarios con sus
manifests, herramientas y un módulo independiente para el arranque de GCam en
el Infinix Zero X Neo X6810-GL.

- **Módulo RAW:** la versión actual es `v001`; habilita RAW Camera2, JPEG
  procesado de hasta 8000×6000 y APIs de flash TORCH/SINGLE. HD48 no significa
  RAW de 48 MP.
- **Módulo GCam:** `x6810_gcam_startup` 0.7.0 instala el APK BSG 9.7 V32
  original como app privilegiada de sistema, concede permisos runtime y accesos
  especiales, y conserva el arreglo de caché nativa. Es independiente del módulo RAW.
- **Configuración GCam:** el XML recomendado es un overlay parcial y neutro
  para BSG V18, no un respaldo completo. No se ha demostrado una mejora visual
  repetible con los factores experimentales.
- **Releases:** el flujo manual genera el módulo RAW elegido, módulo GCam,
  overlay XML y checksums; sólo permite ejecutar o reintentar a `sre-0` desde
  `main`.

Los binarios MediaTek/Transsion y el APK GCam son de terceros. El proyecto no
otorga derechos de redistribución ni declara una licencia global; consulta
[avisos de terceros](THIRD_PARTY_NOTICES.md) antes de publicar.
