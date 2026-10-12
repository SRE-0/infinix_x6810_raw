# Binary patch catalog

Each patch directory groups a modified binary with its manifest and, where
available, the assembly listing used to review the change. The active v001
RAW module combines the manifests in `native-torch/` and `single-flash-api/`.
Other directories preserve earlier experiments and revisions.

Keep original hashes, offsets, before/after bytes, and patch rationale in each
manifest. The original libraries live in `stock-binaries/`; the corresponding
modified payloads are copied into complete module trees under `modules/`.
Do not install a patch directory directly on a device.
