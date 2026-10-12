**English** | [Español](docs/es/THIRD_PARTY_NOTICES.md)

# Third-party notices — RAW/OIS/flash

## MediaTek camera research code

`archive/legacy-project/vendor/mtkcam-raw/` comes from [ReCoreShift/mtkcam-raw](https://github.com/ReCoreShift/mtkcam-raw). Existing MPL-2.0 headers and the [original license](archive/legacy-project/vendor/mtkcam-raw/LICENSE) are retained. MPL applies to covered files, not automatically to all proprietary camera binaries or unrelated project files. When distributing covered modifications, preserve notices and make covered source available under MPL; executable distribution has source-availability obligations. [MPL text](https://www.mozilla.org/en-US/MPL/2.0/) and [official FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) control.

## Vendor firmware binaries

`payloads/` and historical vendor `.so` files derive from Infinix/Transsion/MediaTek camera firmware. Original rights remain with their respective holders. SHA-256 manifests establish byte identity, not ownership or permission. No exact X6810-GL firmware redistribution agreement was supplied or established by this review. The project does not relicense these binaries under MPL or Apache.

## Framework executable and AOSP

The integrated flash profile contains a patched cameraserver from the tested GSI. AOSP generally uses Apache-2.0, with exceptions; this does not establish the complete license/provenance of this particular executable or its linked libraries. A complete source/NOTICE mapping for the shipped GSI binary remains unresolved. [AOSP licensing](https://source.android.com/docs/setup/contribute/licenses).

Where Apache-covered material is distributed, preserve the license, required notices and modification identification; retain relevant NOTICE attribution where present. [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) does not license vendor firmware or Google Camera as a whole.

## Separate GCam project

APK, BSG attribution and embedded open-source notices are documented in [infinix_x6810_gcam_port](https://github.com/SRE-0/infinix_x6810_gcam_port). Neither RAW ZIP contains that APK.

## Repository-owned material

No blanket license has been selected for original project scripts, documentation, patches or profiles. Public availability alone does not establish a general permission to modify or redistribute them. GitHub distinguishes public repository access from licensing: [licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository). Separate component licenses remain effective. The disclaimer does not override them.

## External tools

Python/Git/Git LFS, ADB, Apktool, JADX, Frida and analysis dependencies are external development tools; invoking them does not transfer their licenses to every output or to this entire repository. Keep their upstream notices if redistributing them. The release builders use Python's standard library; historical tools have their own requirements and are not bundled as installed dependencies. No comprehensive software bill of materials for third-party firmware/APK internals is claimed.

## Trademarks

Google, Android, Infinix, MediaTek, Transsion and BSG names identify products, compatibility or authors. No endorsement, trademark license or affiliation is claimed.

See [legal review](docs/LEGAL.md) and [disclaimer](DISCLAIMER.md).
