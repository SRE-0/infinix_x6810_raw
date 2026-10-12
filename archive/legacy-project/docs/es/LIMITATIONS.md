# Compatibilidad y límites

- Los offsets pertenecen a builds exactos de ELF. Una OTA puede invalidarlos;
  el instalador sólo admite los hashes enumerados.
- La validación corresponde al X6810-GL con Android 16/API 36 y APatch. No se
  ha acreditado compatibilidad general con otras ROM o gestores.
- `LEVEL_3` no equivale a certificación CTS ni garantiza todos los modos
  Camera2.
- JPEG 8000×6000 es salida procesada desde entrada 4000×3000; no ofrece RAW48.
  La frontal RAW convencional es 2320×1744 binned.
- Las rutas de control OIS y flash se comprobaron; no se ha demostrado una
  mejora óptica cuantificada en movimiento ni una calibración universal de
  intensidad.
- Los factores de denoise/luma/chroma de GCam son experimentales. No se ha
  reproducido una mejora de calidad visual aislada.
- El módulo APatch de arranque GCam y el XML son para revisiones BSG distintas
  (V32 y V18). El primer arranque después de reiniciar puede tardar mientras
  ART optimiza la aplicación.
- Los binarios MediaTek/Transsion y el APK de GCam son de terceros. Este
  repositorio no otorga derechos de redistribución ni declara licencia global
  para el código del proyecto.

Los resultados concretos están enlazados desde el
[índice técnico](../README.md).
