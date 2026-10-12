# X6810-GL camera modules

The project ships two systemless variants: `raw` (RAW16 + processed HD48 JPEG + telephoto OIS)
and `raw-flash` (RAW + OIS + TORCH/SINGLE and processed HD48 JPEG).
Build both with `python scripts/build.py`; validate offline with
`python scripts/validate.py` (Python 3.11+, POSIX sh/Git Bash).

RAW accepts API 30+ only with known vendor binary tuples and the original OIS
manager. Flash currently requires its exact Android 16 GSI/API 36 framework
profile. Android 11 and future versions have not been device-tested. Historical
device evidence is Android 16 GSI only; repackaged 1.1.0 builds have not been newly device-tested.
The owner confirms telephoto OIS works correctly and external BSG V32 works
perfectly with the [recommended V32 profile](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/profiles/x6810-gcam-bsg-9.7-v32-recommended.xml).
Any compatible external GCam can be installed; the system GCam module is optional.
Combined flash APIs start at API 35, but the supplied framework ELF is API 36.

Install one variant via APatch and reboot. Both use `x6810_raw12mp`; switch by
updating that module and rebooting. Disable/remove it and reboot to recover.
Do not bypass unknown binary hashes. The archived research tree is separate
from the maintained build commands.

See [compatibility](../COMPATIBILITY.md), [installation](../INSTALLATION.md),
[architecture](../DEVELOPMENT.md) and [audit](../AUDIT.md).
GCam is independent: [infinix_x6810_gcam_port](https://github.com/SRE-0/infinix_x6810_gcam_port).
