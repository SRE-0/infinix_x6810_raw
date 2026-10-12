# Contributing / Contribuir

## English

- Keep `.local-private/`, `dist/`, `research/`, photos, DNGs, logs, complete
  device preferences, and ADB serials out of commits.
- Keep original and modified camera libraries together with their SHA-256
  manifests. Record offsets, before/after bytes, and the reason for every
  binary change.
- Do not widen the device/API/hash checks without documenting the exact
  firmware and repeating the device validation.
- Preserve full APatch module trees and the shared RAW module ID. Use Git LFS
  for the version-locked GCam APK and native payload.
- Keep user guides in `docs/es/` and `docs/en/`; add dated measurements to the
  technical records linked from `docs/README.md`.
- Do not add a repository-wide license without the copyright holder's choice.

## Español

- Mantén `.local-private/`, `dist/`, `research/`, fotos, DNG, logs,
  preferencias completas del dispositivo y seriales ADB fuera de los commits.
- Conserva las bibliotecas originales y modificadas junto con sus manifests
  SHA-256. Registra offset, bytes anteriores/nuevos y motivo de cada cambio.
- No amplíes las comprobaciones de dispositivo/API/hash sin documentar el
  firmware exacto y repetir la validación en el teléfono.
- Conserva los árboles completos de módulos APatch y el ID común del módulo
  RAW. Usa Git LFS para el APK GCam versionado y su payload nativo.
- Mantén las guías de uso en `docs/es/` y `docs/en/`; añade las mediciones
  fechadas a los informes enlazados desde `docs/README.md`.
- No declares una licencia global sin que la elija el titular del copyright.

Package construction and release workflow instructions are in
[English](docs/en/BUILDING.md) and [Spanish](docs/es/BUILDING.md).
