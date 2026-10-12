# Infinix X6810-GL — RAW, OIS y flash

Dos variantes systemless del módulo de cámara para Infinix Zero X Neo X6810-GL.
El proyecto de GCam está separado: [infinix_x6810_gcam_port](https://github.com/SRE-0/infinix_x6810_gcam_port).

| Variante | Incluye | Compatibilidad de instalación |
|---|---|---|
| `raw` | RAW16 de tres sensores, buffers RAW, JPEG HD48 y OIS del teleobjetivo | Android 11/API 30 o posterior y vendor con hashes conocidos |
| `raw-flash` | RAW, OIS, JPEG HD48, intensidad TORCH/SINGLE | Perfil exacto Android 16 GSI/API 36 y hashes de vendor/framework conocidos |

**Sólo existe evidencia histórica de pruebas en Android 16 GSI.** El mínimo API 30
de RAW expresa la política del instalador; Android 11 y versiones futuras no se
han probado. **El propietario confirma que OIS se probó y funciona correctamente**
en Android 16 GSI, en el teleobjetivo OV08A10. HD48 está en ambas variantes y es
JPEG procesado, no RAW de 48 MP.

```sh
python scripts/validate.py
python scripts/build.py
```

Los ZIP y sus SHA-256 quedan en `dist/releases/`. Instala **una variante** desde
APatch y reinicia. Ambas comparten `id=x6810_raw12mp` para sustituirse entre sí.
El soporte de Magisk conserva el punto de entrada estándar, pero este empaquetado
no se ha validado en el dispositivo con ningún gestor.

Puedes instalar cualquier GCam externa: el módulo de cámara no exige una APK
concreta ni el módulo GCam de sistema. La compatibilidad depende de cada port.
La [BSG MGC_9.7.047_V32_MGC.apk](https://1-dontsharethislink.celsoazevedo.com/file/filesc/MGC_9.7.047_V32_MGC.apk),
paquete `com.android.MGC_9_7_047`, funciona perfectamente según las pruebas
confirmadas por el propietario, con el
[perfil recomendado V32](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/profiles/x6810-gcam-bsg-9.7-v32-recommended.xml).
[Instalación de GCam externa](docs/GCAM.md).

- [Compatibilidad y límites](docs/COMPATIBILITY.md)
- [Instalación, cambio de variante y recuperación](docs/INSTALLATION.md)
- [Arquitectura y construcción](docs/DEVELOPMENT.md)
- [Auditoría y reorganización](docs/AUDIT.md)
- [Índice de investigaciones históricas](docs/RESEARCH.md)
- [English overview](docs/en/README.md)

El árbol activo usa `scripts/` para dos comandos, `module/common/` para el ciclo
de boot y `payloads/` para entradas verificadas. `archive/legacy-project/` conserva
experimentos y scripts originales; no forma parte de la selección automática de
releases. `projects/infinix_x6810_gcam_port/` es un repositorio Git independiente,
excluido del repositorio RAW. Fotos, trazas y datos privados siguen excluidos.

Consulta [avisos de terceros](THIRD_PARTY_NOTICES.md). Los binarios del firmware
conservan sus derechos originales; no se declara una licencia global.
