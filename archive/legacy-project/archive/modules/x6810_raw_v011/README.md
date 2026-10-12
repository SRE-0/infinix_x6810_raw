# X6810 RAW v0.11: arreglo de buffers RAW16

Deriva de v0.10. Conserva metastore y resoluciones RAW nativas.
En pipelinepolicy, la coleccion RAW16 usa max(limite original, 6).
No cambia algoritmos de imagen, exposicion ni codecs.
Pruebas temporales BSG: ~29 FPS en principal, frontal y tele; ver informe
para mediciones exactas y limites. No garantiza 30 FPS con exposiciones largas.
Puede requerir mas memoria para buffers simultaneos.

Instalar sobre x6810_raw12mp en APatch/Magisk y reiniciar.
La pareja de bibliotecas y payloads se verifica por SHA-256.
Para revertir: x6810-raw-v0.10.0-from-v011-rollback.zip y reiniciar.
El ZIP v0.10 antiguo no reconoce el hash de v0.11.

Informe: docs/VERSION_HISTORY.md
Manifest base policy-manifest.json: cambio frontal heredado.
Manifest raw-buffers-manifest.json (solo v0.11): delta adicional sobre v0.10.
