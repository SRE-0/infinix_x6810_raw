# X6810 RAW 0.12.2-full12-hd48-trial

Experimental resolution metadata on v0.12.2; preserves RAW, OIS, capture cap and native torch.

Instalar sobre 0.12.2-native-torch-experimental o estos ensayos y reiniciar.
Requiere el mismo X6810 / Android 16 GSI exacto; verifica cinco payloads.
Conserva HAL 3A, device3 HAL, cameraserver, policy y servicio de 0.12.2.
Solo cambia el metastore: JPEG/YUV 4000x3000, y en HD48 JPEG 8000x6000.
HD48 solo anuncia metadata; 48MP nativos no verificados, no agrega RAW48.
Timing HD provisional 100ms. Hardware pendiente de prueba.
Probar Full12 primero, luego HD48. Instalar un solo ZIP y reiniciar.
Rollback: x6810-v0122-from-main-resolution-rollback.zip y reiniciar.
Verificar principal, frontal, telefoto, OIS y linterna nativa.
Ver docs/MAIN_RESOLUTION_TRIALS.md. No usar rollback v0.11/v0.12.0 para este ensayo.
