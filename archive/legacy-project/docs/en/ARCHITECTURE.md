# Camera architecture

## Sensors and streams

| Camera | Sensor | Validated RAW16 |
|---|---|---:|
| Main | S5KGM1ST | 4000×3000 |
| Telephoto | OV08A10 | 3264×2448 |
| Front | HI1631Q | 2320×1744 binned |

The module changes MediaTek HAL metadata and policy decisions. Libraries are
mounted as a systemless overlay under `system/vendor`; firmware and the
physical vendor partition are left in place. The installer checks the device,
API, and accepted hashes, and saves the originals so APatch can disable the
module.

`libmtkcam_metastore.so` advertises streams and capabilities;
`libmtkcam_pipelinepolicy.so` constrains front binned stream selection and the
RAW buffer minimum; flash and OIS bridges live in the corresponding HAL
libraries. Each change is described by manifests and assembly listings in
`patches/`.

## Scope

The 8000×6000 JPEG output is processed from a measured 4000×3000 input. It is
not RAW48 or a proven native 48 MP sensor readout. The front camera uses the
2320×1744 binned output; it does not advertise the 4640×3488 Quad Bayer array
as a conventional 2×2 Bayer CFA.

`LEVEL_3` is the level declared by the HAL; it does not certify CTS compliance
or every stream combination. For measurements and earlier version results,
see the [HD48 report](../HD48_DEVICE_RESULTS.md) and
[version history](../VERSION_HISTORY.md).
