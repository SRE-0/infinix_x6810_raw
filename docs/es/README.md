<div align="center">
<h1>Infinix X6810 RAW</h1>
<p>RAW · OIS del teleobjetivo · JPEG HD48 · Flash opcional</p>
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

<p align="center">[English](../../README.md) · **Español**</p>

## Módulos de cámara

Dos variantes systemless para Infinix Zero X Neo **X6810-GL**. [El proyecto GCam](https://github.com/SRE-0/infinix_x6810_gcam_port) se mantiene por separado.

| Variante | Funciones | Compatibilidad de instalación |
|---|---|---|
| **RAW** | RAW16 en tres sensores, buffers RAW, OIS del teleobjetivo y JPEG HD48 procesado | Android 11/API 30+ con binarios vendor/OIS conocidos |
| **RAW + flash** | Todo lo anterior más intensidad TORCH/SINGLE | Perfil exacto Android 16 GSI/API 36 |

**OIS se probó y funciona correctamente en el teleobjetivo.** Las pruebas corresponden a Android 16 GSI. Android 11 y versiones futuras no se probaron; el mínimo API y los hashes definen la admisión del instalador. HD48 es JPEG procesado, no RAW nativo de 48 MP. Las API públicas combinadas de flash requieren API 35, pero el binario incluido sigue ligado a API 36. [Análisis](FLASH_COMPATIBILITY.md).

## Construcción e instalación

```sh
git lfs install
git lfs pull
python scripts/validate.py
python scripts/build.py
```

Python 3.11+; la validación del instalador necesita `sh` POSIX, disponible con Git Bash. Los ZIP y SHA-256 se generan en `dist/releases/`. Instala una variante desde APatch y reinicia; comparten `id=x6810_raw12mp`. [Instalación y recuperación](INSTALLATION.md). El empaquetado reorganizado no se probó en hardware.

## GCam externa

Puedes instalar cualquier GCam externa compatible. [BSG MGC_9.7.047_V32_MGC.apk](https://1-dontsharethislink.celsoazevedo.com/file/filesc/MGC_9.7.047_V32_MGC.apk), paquete `com.android.MGC_9_7_047`, se probó y funciona perfectamente en Android 16 GSI con [el XML V32 recomendado](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/profiles/x6810-gcam-bsg-9.7-v32-recommended.xml). El módulo GCam de sistema es opcional e independiente.

## Documentación

- [Compatibilidad](COMPATIBILITY.md)
- [Desarrollo y estructura](DEVELOPMENT.md)
- [Auditoría](AUDIT.md) e [investigaciones históricas](RESEARCH.md)
- [Revisión legal](LEGAL.md), [avisos de terceros](THIRD_PARTY_NOTICES.md) y [descargo](DISCLAIMER.md)

`scripts/` contiene los comandos mantenidos, `module/common/` el ciclo de arranque y `payloads/` las entradas verificadas. `archive/legacy-project/` conserva experimentos originales. Datos privados y salidas generadas quedan fuera de Git.

## Descargo de responsabilidad

Software experimental proporcionado tal cual, sin garantías, en la máxima medida permitida por la ley. Asumes los riesgos de instalación y uso. En esa medida, SRE-0 y colaboradores excluyen responsabilidad por daños al dispositivo, pérdida de datos, fallos de arranque y otras pérdidas. Se mantienen los derechos obligatorios y responsabilidades que no pueden excluirse. Los binarios de terceros conservan sus propios derechos; no existe licencia global ni permiso general de redistribución. [Descargo completo](DISCLAIMER.md).

## Contacto

<p align="center">
  <a href="mailto:sergioandresp660@gmail.com"><img src="https://img.shields.io/badge/Email-f7768e?style=for-the-badge&labelColor=1a1b26&logo=gmail&logoColor=white" alt="Email"></a>
  <a href="https://sre-0.github.io/SRE-0_web"><img src="https://img.shields.io/badge/Website-bb9af7?style=for-the-badge&labelColor=1a1b26&logo=googlechrome&logoColor=white" alt="Website"></a>
</p>
