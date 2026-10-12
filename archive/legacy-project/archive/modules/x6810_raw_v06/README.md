# X6810 RAW v0.6 — HI1631Q remosaic

Esta versión conserva el RAW funcional de la principal y el teleobjetivo.
Para la frontal elimina el stream RAW16 2320×1744: el log real demostró que
MediaTek abre el modo de sensor 4640×3488 y rechaza ese buffer por stride.

Sólo se publica RAW16 4640×3488. Para camera ID 1, la plantilla de petición
activa `com.mediatek.control.capture.remosaicenable=1` y
`processRaw.enable=1`. El X6810 ya identifica HI1631Q como 4Cell y su tabla de
features contiene `MTK_FEATURE_REMOSAIC`; este parche intenta hacer que el HAL
entregue Bayer regular en lugar del mosaico Quad Bayer que produce el tinte rosa.

El ZIP incluye `system.prop` para exponer las tres cámaras a aplicaciones
Camera2. Instálalo como actualización en APatch y reinicia. Esta ruta nueva
requiere validación física; si camerahalserver no inicia, vuelve a v0.2.
Consulta `docs/VERSION_HISTORY.md` en el proyecto.
