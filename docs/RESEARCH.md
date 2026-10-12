# Investigaciones y evidencia

Los informes anteriores quedan congelados con sus fechas y conclusiones. Sus
rutas/comandos pueden depender de datos locales que ya no existen. No equivalen
a instrucciones vigentes de release; consulta [desarrollo](DEVELOPMENT.md).

| Tema | Informe de referencia |
|---|---|
| RAW, frontal y buffers | [Historial](../archive/legacy-project/docs/VERSION_HISTORY.md) |
| Formato y deltas binarios | [Parches](../archive/legacy-project/docs/BINARY_PATCHES.md) |
| OIS y alcance teleobjetivo | [OIS](../archive/legacy-project/docs/OIS.md) |
| JPEG HD48 | [Resultados](../archive/legacy-project/docs/HD48_DEVICE_RESULTS.md) |
| Intensidad TORCH/SINGLE | [API flash](../archive/legacy-project/docs/FLASH_CAMERA2_API.md) |
| GCam, arranque y APK | [Investigación en GCam](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/docs/RESEARCH.md) |

[Archivo original](../archive/legacy-project/README.md) ·
[Inventario y grupos por contenido](inventory.json).

Actualización del 12 de octubre de 2026: el propietario confirma que OIS del
teleobjetivo funciona correctamente y que GCam V32 funciona perfectamente con
su perfil recomendado. Esa confirmación actualiza el estado provisional del
informe OIS histórico; consulta [compatibilidad vigente](COMPATIBILITY.md).

Los scripts históricos conservan imports y la estructura relativa original en
`archive/legacy-project/`. Las herramientas GCam se trasladaron al otro repo:
los scripts de releases combinados quedan retirados y no son comandos públicos.
No ejecutes automáticamente scripts de prueba/colección: pueden cambiar el
estado del teléfono. Esta reorganización no ejecutó ninguno.
