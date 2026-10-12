# X6810 main-full12-hd48-jpeg-trial

Experimental main JPEG/YUV 4000x3000. Hardware validation pending. Adds JPEG 8000x6000 metadata only; native 48MP unverified.

ENSAYO SIN VALIDACION FISICA. Instalar un solo ZIP en APatch y reiniciar.
Base admitida: v0.11 exacta o cualquiera de estos dos ensayos.
No instalar sobre v0.12/OIS/flash: el instalador rechazara su pareja.
Probar primero main-full12-trial; despues, si funciona, main-full12-hd48-jpeg-trial.
El segundo conserva 12MP y solo agrega JPEG 8000x6000, no RAW/YUV 48MP.
El JPEG HD usa duraciones provisionales de 100ms; no son FPS medidos.
No se fuerza el modo fisico ni remosaic ni se cambia el area activa.
GCam puede no usar JPEG directo ni enumerar tamanos de alta resolucion.
No se garantiza que todos los modos o video usen estas dimensiones.
Volver: instalar x6810-v011-from-main-resolution-rollback.zip y reiniciar.
Si no abre la camara, desactivar x6810_raw12mp en APatch y reiniciar.
No borrar datos de GCam. Ver docs/MAIN_RESOLUTION_TRIALS.md.
