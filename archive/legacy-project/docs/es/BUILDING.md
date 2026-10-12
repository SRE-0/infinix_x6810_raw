# Construcción y publicación

## Preparar el clon

El APK modificado y la biblioteca nativa de GCam superan el límite normal de
100 MB de GitHub; se almacenan con Git LFS.

```powershell
git lfs install
git clone <URL-del-repositorio>
cd raw-camera-infinix-x6810
git lfs pull
```

Sin LFS, el módulo de GCam no tendrá los payloads necesarios para construirse.

## Crear paquetes localmente

Desde la raíz, con Python 3.11 o superior:

```powershell
python scripts/package_github_release.py --raw-version v001 --output-dir dist/github-release
```

El comando crea el ZIP completo del módulo RAW seleccionado, construye el
módulo GCam con validación de hashes, copia el XML y genera `SHA256SUMS.txt`.
No instala nada en el teléfono. El directorio de salida debe ser nuevo.

Para reconstruir los módulos RAW desde el código y manifests, instala las
dependencias de construcción y ejecuta:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r scripts\requirements.txt
.venv\Scripts\python.exe scripts\build_single_flash_api.py
.venv\Scripts\python.exe scripts\verify_single_flash_api.py
.venv\Scripts\python.exe scripts\package_camera_module.py
```

Los constructores parten de una biblioteca con hash conocido. Conserva los
originales de `stock-binaries/`; no los sustituyas por binarios de otra ROM.

Los constructores de parches binarios requieren los binarios stock incluidos
en `stock-binaries/`. Consulta [scripts/README.md](../../scripts/README.md) y
los manifests de `patches/` antes de cambiar offsets o hashes.

## Crear una release con GitHub Actions

Después de subir y fusionar estos archivos en `main`, abre **Actions → Create
X6810 release → Run workflow**. Indica un tag único y selecciona `v000` o
`v001`. El flujo adjunta el módulo RAW completo, el módulo GCam, el XML y sus
checksums. Sólo acepta ejecuciones iniciadas o reintentadas por `sre-0` desde
`main`; la cuenta debe tener permiso de escritura y Actions debe estar
habilitado en el repositorio.

El APK de GCam va en Git LFS. Revisa las cuotas de almacenamiento y tráfico LFS
del plan de GitHub antes de publicar clones grandes. La creación de la release
no se ha ejecutado desde este espacio de trabajo.
