# X6810 RAW/OIS/HD48 and RAW + flash — v1.1.0

[English](README.md) · [Español](docs/es/README.md) · [GCam project](https://github.com/SRE-0/infinix_x6810_gcam_port)

This release provides two systemless camera modules for the Infinix Zero X Neo X6810-GL.

## Downloads

- `x6810-raw-1.1.0.zip` — RAW16, telephoto OIS and processed JPEG HD48.
- `x6810-raw-flash-1.1.0.zip` — those camera features plus TORCH/SINGLE flash strength support for the pinned framework profile.
- `SHA256SUMS.txt` and `releases.json` — verify package integrity and identify each variant.

Install only one variant through APatch, then reboot. Both share module ID `x6810_raw12mp`; install the other variant over it to switch. Read [installation and recovery](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/INSTALLATION.md) first, keep a working recovery route, and stop if the installer rejects your firmware.

## Compatibility and evidence

**RAW** admits Android 11/API 30 and later only when the device, architecture, vendor camera binaries and OIS manager match a known supported set. The API floor is an installer policy; Android 11 and future versions have not been tested.

**RAW + flash** requires the exact Android 16/API 36 vendor/framework profile and binary hashes. Public APIs used by the combined features have a floor of API 35 (Android 15), but the supplied framework ELF and private hooks remain tied to API 36. Android 15 would require a separate framework port. See the [flash API and binary audit](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/FLASH_COMPATIBILITY.md).

Telephoto OIS on the OV08A10 and the BSG V32 camera app with the recommended profile were tested and work correctly on Android 16 GSI. This packaging was validated offline; the new release ZIPs were not retested on a phone. HD48 produces processed 8000×6000 JPEG from 4000×3000 input. It does not produce native 48 MP RAW.

You can install any compatible external GCam as a normal app. The optional system GCam module and its tested profile are in the [separate GCam project](https://github.com/SRE-0/infinix_x6810_gcam_port).

## Verify or build

Check a downloaded ZIP against `SHA256SUMS.txt`. To build from source, install Git LFS and Python 3.11+, retrieve LFS objects, then run:

```sh
python scripts/validate.py
python scripts/build.py
```

See [architecture and reproducible builds](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/DEVELOPMENT.md), [compatibility](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/COMPATIBILITY.md), and the [legal review and disclaimer](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/LEGAL.md).

## Legal and risk notice

Experimental software, provided as-is without warranties to the fullest extent permitted by law. Installing root/system camera changes carries risks including boot failure, data loss, camera malfunction and device damage. Responsibility is excluded only to the extent the applicable law permits; mandatory rights and non-excludable liability remain. No blanket project license or general redistribution right for proprietary firmware binaries is claimed. Read the [full disclaimer](https://github.com/SRE-0/infinix_x6810_raw/blob/main/DISCLAIMER.md) and [third-party notices](https://github.com/SRE-0/infinix_x6810_raw/blob/main/THIRD_PARTY_NOTICES.md).

---

# Español

Esta versión ofrece dos módulos systemless de cámara para Infinix Zero X Neo X6810-GL.

## Descargas

- `x6810-raw-1.1.0.zip`: RAW16, OIS del teleobjetivo y JPEG HD48 procesado.
- `x6810-raw-flash-1.1.0.zip`: esas funciones más intensidad TORCH/SINGLE para el perfil fijado de framework.
- `SHA256SUMS.txt` y `releases.json`: comprueba integridad e identifica cada variante.

Instala solo una variante desde APatch y reinicia. Ambas usan el ID `x6810_raw12mp`; instala la otra encima para cambiar. Antes, lee la [guía de instalación y recuperación](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/es/INSTALLATION.md), conserva una vía funcional de recuperación y detente si el instalador rechaza tu firmware.

## Compatibilidad y pruebas

**RAW** admite Android 11/API 30 o posterior solo cuando dispositivo, arquitectura, bibliotecas de cámara vendor y gestor OIS coinciden con un conjunto conocido. El mínimo API es una política del instalador; Android 11 y versiones futuras no se probaron.

**RAW + flash** exige el perfil exacto Android 16/API 36 y sus hashes. Las API públicas combinadas comienzan en API 35 (Android 15), pero el ELF del framework y los hooks privados incluidos siguen ligados a API 36. Android 15 requiere otro port del framework. Consulta la [auditoría del flash](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/es/FLASH_COMPATIBILITY.md).

OIS del teleobjetivo OV08A10 y la app BSG V32 con el perfil recomendado se probaron y funcionan correctamente en Android 16 GSI. El nuevo empaquetado se validó sin conexión; los ZIP de esta versión no se volvieron a probar en el teléfono. HD48 produce JPEG procesado de 8000×6000 desde una entrada 4000×3000; no produce RAW nativo de 48 MP.

Puedes instalar cualquier GCam externa compatible como app normal. El módulo de sistema GCam y su perfil probado están en [el proyecto GCam independiente](https://github.com/SRE-0/infinix_x6810_gcam_port).

## Verificación y construcción

Comprueba los ZIP con `SHA256SUMS.txt`. Para construir desde el código fuente, instala Git LFS y Python 3.11+, descarga los objetos LFS y ejecuta:

```sh
python scripts/validate.py
python scripts/build.py
```

Consulta [arquitectura](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/es/DEVELOPMENT.md), [compatibilidad](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/es/COMPATIBILITY.md) y la [revisión legal](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/es/LEGAL.md).

## Aviso legal y riesgos

Software experimental, proporcionado tal cual y sin garantías en la máxima medida permitida por la ley. Los cambios root/system pueden provocar fallos de arranque, pérdida de datos, problemas de cámara y daños al equipo. La responsabilidad se excluye solo en la medida legal; siguen vigentes los derechos obligatorios y responsabilidades no excluibles. No se reclama licencia global ni permiso general para redistribuir firmware propietario. Lee el [descargo completo](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/es/DISCLAIMER.md) y los [avisos de terceros](https://github.com/SRE-0/infinix_x6810_raw/blob/main/docs/es/THIRD_PARTY_NOTICES.md).
