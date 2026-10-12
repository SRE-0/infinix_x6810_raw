# GCam externa

El módulo RAW/OIS/HD48, y su variante flash, no instalan ni exigen una GCam
concreta. Puedes instalar cualquier GCam externa como APK de usuario, siempre
que ese port admita tu Android y HAL. El instalador GCam de sistema del otro
repo es opcional y está fijado a una APK; esa restricción no pertenece al módulo
de cámara. No uses ese instalador fijo para empaquetar otra GCam.

El propietario confirma que
[MGC_9.7.047_V32_MGC.apk](https://1-dontsharethislink.celsoazevedo.com/file/filesc/MGC_9.7.047_V32_MGC.apk)
(`com.android.MGC_9_7_047`) funciona perfectamente en su X6810-GL Android 16 GSI
con [x6810-gcam-bsg-9.7-v32-recommended.xml](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/profiles/x6810-gcam-bsg-9.7-v32-recommended.xml).
La guía de carga y descripción de las 755 preferencias está en
[el proyecto GCam](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/profiles/README.md).
OIS del teleobjetivo también está probado y funciona correctamente; el perfil
incluye `camera.ois_forced_photo_mode=true`.

El perfil habilita la disponibilidad de RAW, pero guarda
`pref_camera_raw_output_key=0`: no activa automáticamente guardar DNG. Activa
la salida RAW en la app si deseas archivos DNG. JPEG HD48 tampoco se impone a
GCam: el port debe elegir ese stream Camera2.
