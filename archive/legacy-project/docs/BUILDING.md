# Building

Use the concise, maintained guides:

- [Construcción y publicación (español)](es/BUILDING.md)
- [Building and publishing (English)](en/BUILDING.md)

The RAW source rebuild uses the exact base module, manifests, and stock
libraries. The GitHub release workflow packages complete RAW/GCam modules and
the BSG V18 XML overlay; it does not connect to a phone. Local generated
archives remain under the ignored `dist/` directory.
