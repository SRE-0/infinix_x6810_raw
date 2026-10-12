# X6810 RAW 0.12.0-ois-experimental

OV08A10 Camera2 OIS OFF/ON bridge; v0.11 RAW preserved. Experimental: optical effectiveness not yet measured.

Only upgrades verified v0.11/v0.12 triples. Uses template-module.
Requires exact stock libcam.hal3a.v3.so and libtran_oismgr.so.
Standard OFF/ON controls BU63169 suspend/resume only for OV08A10 and non-stock camera packages.
Stock Transsion package path stays unchanged. OIS_DATA_MODE is not advertised.
Rollback: dist/x6810-raw-v0.11.0-from-v012-rollback.zip
See docs/OIS.md for evidence, limits and recovery.
