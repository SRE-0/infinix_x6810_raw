# Estructura, privacidad y licencias

| Ruta | Contenido |
|---|---|
| `modules/` | Módulos RAW completos activos v000 y v001. |
| `archive/modules/` | Snapshots históricos completos, conservados para auditoría. |
| `stock-binaries/` | Cuatro bibliotecas de firmware originales y sus hashes. |
| `patches/` | Bibliotecas modificadas, manifests, offsets y ASM. |
| `gcam/apatch-startup/` | Instalador systemless y bibliotecas nativas del módulo GCam 0.6.2. |
| `profiles/` | Perfil analítico JSON y overlay XML recomendado. |
| `scripts/` | Análisis, adquisición, construcción, empaquetado y verificación. |
| `docs/` | Guías en español/inglés e informes técnicos de laboratorio. |
| `vendor/mtkcam-raw/` | Dependencia Python de terceros bajo MPL-2.0. |

`.local-private/`, `dist/`, `research/`, entornos virtuales, capturas y logs
locales están excluidos de Git. `dist/` contiene resultados regenerables; los
paquetes completos se reconstruyen con los scripts y módulos versionados. No
subas seriales ADB, imágenes, DNG, preferencias completas de GCam ni dumps del
dispositivo.

Las bibliotecas MediaTek/Transsion son propietarias y su inclusión aquí no
concede derechos de redistribución. El APK GCam incorpora componentes de
terceros. No hay una licencia global declarada para el código original de este
proyecto; MPL-2.0 cubre únicamente `vendor/mtkcam-raw/`. Revisa
[avisos de terceros](../../THIRD_PARTY_NOTICES.md) antes de redistribuir.
