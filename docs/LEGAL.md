**English** | [Español](es/LEGAL.md)

# Legal review — RAW/OIS/flash

| Material | Evidence | Remaining issue |
|---|---|---|
| `mtkcam-raw` research source | Original MPL-2.0 file headers and LICENSE retained | Preserve covered-file notices/source obligations when changing or redistributing |
| Vendor libraries | Firmware provenance and binary hashes | Exact redistribution/modification authorization not established |
| Patched GSI cameraserver | Known binary and patch manifests; AOSP ancestry | Complete fork provenance, license/source and NOTICE mapping not established |
| Original tools/docs/profiles | Project-authored material | No blanket project license selected |

## What this review establishes

This is a component and source review dated **2026-10-12**, not a legal opinion for a particular country. The applicable country, distribution arrangement and exact proprietary agreements have not been established. A public link, successful test, device ownership or “research” label is not automatically a copyright or redistribution permission.

The review distinguishes provenance (where bytes came from), licensing (which rights were granted), engineering compatibility and liability. None substitutes for the others. Hashes establish integrity only. Removing decompiled material improves repository boundaries but does not resolve the rights attached to a retained proprietary binary.

## Warranty and liability

[DISCLAIMER.md](../DISCLAIMER.md) provides a project-specific as-is statement and an exclusion of responsibility to the lawful extent, including device damage, lost data and boot failures. It preserves mandatory rights and non-excludable liability. Similar limitations in upstream licenses are component terms, not proof that one project notice guarantees worldwide enforceability. No universal waiver or choice of jurisdiction is claimed.

[Google's general terms](https://policies.google.com/terms) and [Infinix's published service terms](https://activity.infinixmobility.com/termsuse) illustrate that rights and liability depend on the applicable agreement and law; they are not substituted for an unavailable APK-specific or X6810 firmware agreement. A regional hardware warranty cannot be generalized to all users.

## Before redistributing material

Determine the exact rights holder and agreement for each shipped binary, including modifications; obtain permissions where needed. Keep component license texts and copyright notices. For covered open-source components, satisfy their own notice/source obligations. Assess local reverse-engineering, copyright, trademark, warranty and consumer rules with qualified advice. Do not present this repository's disclaimer as a license grant or legal immunity.

If a rights holder objects, identify the exact path/version, rights basis and requested remedy through the project contact in the README. Attribution alone does not settle permission. This documentation records unresolved provenance and licensing honestly rather than declaring the entire project cleared.

## RAW-specific findings

MPL-2.0 coverage follows its covered source files. It does not turn arbitrary proprietary MediaTek/Transsion libraries into MPL software. The repository retains the covered source and license; inspect upstream headers before changing those files. [Official MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/).

AOSP's default Apache policy is a useful starting point, not the license inventory of the supplied GSI executable. Proprietary linked libraries and fork changes must be assessed separately. No claim is made that Apache-2.0 grants redistribution rights for the complete camera stack. [AOSP license policy](https://source.android.com/docs/setup/contribute/licenses).

[MediaTek website terms](https://www.mediatek.com/terms-of-use) are website terms, not a grant for redistributing X6810 vendor firmware. [Infinix service terms](https://activity.infinixmobility.com/termsuse) similarly do not establish a blanket firmware grant. The exact product agreement remains unavailable. Patch manifests and original binary archives are also subject to the rights in the material they contain.

For operations, RAW replaces vendor camera libraries; flash also replaces a private-framework cameraserver and changes flash transport. Compatibility checks and pulse limits reduce specific engineering risks but do not remove possible hardware, data or boot damage. Android 11 admission is not a warranty of operation. [Third-party notices](../THIRD_PARTY_NOTICES.md).
