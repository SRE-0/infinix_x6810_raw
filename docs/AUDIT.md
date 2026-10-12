# Auditoría y reorganización — 12 de octubre de 2026

Se examinó el árbol público completo: 752 archivos originales
(1251.7 MiB, incluidos paquetes GCam locales).
Se verificó la preservación byte a byte mediante SHA-256 antes y después de la
migración. El inventario excluye rutas personales y contenido privado.

Problemas encontrados: 131 archivos directos de herramientas/scripts públicos,
20 directorios de módulos históricos, dos árboles de release completos, documentación bilingüe
duplicada y releases RAW/GCam acoplados al APK de Downloads. El instalador RAW
actual exigía SDK 36 y reemplazaba un framework de una GSI concreta. Los ensayos
GCam 0.5.0 y el release original firmado 0.7.0 coexistían y podían confundirse.
Había un ZIP generado de más de 500 MiB junto a las fuentes del módulo.

Cambios realizados:

- Dos repositorios independientes con referencias cruzadas: RAW/OIS/flash y GCam.
- Constructor RAW único y dos variantes fijadas por hash; RAW + OIS no reemplaza
  framework ni incorpora el puente de intensidad flash.
- RAW admite API 30+ con vendor/OIS conocidos; flash conserva un perfil SDK 36
  exacto. No se declara soporte probado en Android 11 ni en versiones futuras.
- Fuentes históricas agrupadas en un archivo, sin mezclarse con scripts activos.
- README, compatibilidad, instalación, desarrollo y evidencia con una referencia
  principal por tema; informes originales conservados como historia.
- ZIP y APK experimental fuera de Git; binarios versionados mediante Git LFS.
- CI y publicación RAW independientes de GCam y de Downloads del usuario.

El inventario registra 57 grupos con contenido idéntico. Las copias
históricas se conservan deliberadamente para reproducir cada ensayo; los releases
nuevos generan sus árboles desde entradas fijadas y una sola implementación.
No se deduplicaron los archivos de datos privados ni se borraron investigaciones.

Queda por validar: empaquetado 1.0.0 en hardware, Android 11 real, otras versiones
GSI/framework, eficacia óptica OIS y calibración de intensidad flash. Las pruebas
offline verifican política y bytes; no sustituyen esas mediciones.

La estructura histórica conserva rutas relativas e imports. Los antiguos scripts
de releases combinados y enlaces a GCam son referencias retiradas; usa los dos
comandos mantenidos y [el repositorio GCam](https://github.com/SRE-0/infinix_x6810_gcam_port).
No se ejecutaron tareas móviles ARTEMIS ni se conectó ADB al dispositivo, conforme a la instrucción
del usuario. Datos locales de `research/`, `.local-private/` y `dist/` no entran
en el inventario ni en la publicación.
