# X6810 v0.5: HI1631Q RAW binning y compatibilidad con GCam

La frontal ofrece dos streams RAW16: 4640×3488 de resolución completa y
2320×1744 binning. Usa 2320×1744 para color Bayer convencional. La salida
completa conserva el mosaico Quad Bayer y puede verse morada en reveladores
que la interpretan como GRBG 2×2.

La entrada completa y sus duraciones usan el mismo tamaño, corrigiendo el
`frame_readout_time_ms=0` con el que GCam rechazaba sensor ID 1. El módulo
incluye `system.prop`, `vendor.camera.tran.nums=3` y `ro.odm.camera=1`.

Instala el ZIP v0.5 como actualización en APatch y reinicia. Conserva los ZIP
v0.2 y v0.3 para reversión. Consulta `docs/VERSION_HISTORY.md`.
