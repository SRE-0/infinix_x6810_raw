# Proyecto de cámara para Infinix Zero X Neo X6810-GL

Este repositorio reúne módulos APatch completos, parches de bibliotecas de
cámara MediaTek, herramientas de análisis y un módulo independiente para el
arranque de GCam.

## Guías

- [Instalación y recuperación](INSTALLATION.md)
- [GCam y XML recomendado](GCAM.md)
- [Construcción y publicación](BUILDING.md)
- [Estructura y licencias](PROJECT.md)
- [Arquitectura de cámara](ARCHITECTURE.md)
- [Compatibilidad y límites](LIMITATIONS.md)

## Versiones vigentes

| Componente | Versión / destino | Resumen |
|---|---|---|
| Módulo RAW | v001 | RAW Camera2, JPEG procesado hasta 8000×6000 y APIs TORCH/SINGLE. HD48 no es RAW de 48 MP. |
| Módulo GCam como app de sistema | 0.6.2, BSG 9.7 V32 | Instala el APK original firmado y las 21 bibliotecas ARM64; preconcede permisos runtime revocables y aplica el arreglo de caché nativa. |
| XML recomendado | BSG 9.7 V18 | Overlay parcial de valores neutros; no es una copia completa de preferencias. |

El archivo XML y el módulo de GCam se dirigen a revisiones BSG distintas. El
módulo de GCam no aplica el XML. Lee [la guía de GCam](GCAM.md) antes de usar
cualquiera de los dos.

Los informes detallados de experimentos están organizados en el
[índice de documentación](../README.md). Los ensayos no demuestran una mejora
visual repetible de los factores RAW/denoise experimentales.
