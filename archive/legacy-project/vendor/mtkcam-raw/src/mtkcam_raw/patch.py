# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Patch application — write verified byte changes to an ELF binary.

Separates patch *strategy* (what to change and why) from
patch *application* (byte-level writing with verification).
"""

# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PatchRecord:
    """One atomic byte-range change."""
    file_offset: int
    old_bytes: bytes
    new_bytes: bytes
    description: str = ""


@dataclass
class PatchResult:
    """Result of applying patches to an ELF."""
    input_sha256: str
    output_sha256: str = ""
    records: list[PatchRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def changed_bytes(self) -> int:
        return sum(len(r.old_bytes) for r in self.records)



def apply_patches(
    data: bytearray,
    patches: list[PatchRecord],
) -> PatchResult:
    """
    Apply a list of PatchRecord to a mutable bytearray.
    Verifies expected original bytes before each change.
    """
    result = PatchResult(
        input_sha256=hashlib.sha256(bytes(data)).hexdigest(),
    )

    for patch in patches:
        if patch.file_offset + len(patch.old_bytes) > len(data):
            result.errors.append(
                f"Offset 0x{patch.file_offset:x} exceeds file size"
            )
            continue

        actual = bytes(
            data[patch.file_offset : patch.file_offset + len(patch.old_bytes)]
        )
        if actual != patch.old_bytes:
            result.errors.append(
                f"Offset 0x{patch.file_offset:x}: expected "
                f"{patch.old_bytes.hex()} but found {actual.hex()}"
            )
            continue

        data[patch.file_offset : patch.file_offset + len(patch.new_bytes)] = (
            patch.new_bytes
        )
        result.records.append(patch)

    result.output_sha256 = hashlib.sha256(bytes(data)).hexdigest()
    return result



def write_patched_file(
    in_path: Path,
    out_path: Path,
    patches: list[PatchRecord],
) -> PatchResult:
    """Read input, apply patches with verification, write output."""
    data = bytearray(in_path.read_bytes())

    max_end = max(
        (p.file_offset + len(p.new_bytes)) for p in patches
    ) if patches else 0
    if max_end > len(data):
        data.extend(b"\x00" * (max_end - len(data)))

    result = apply_patches(data, patches)

    if result.is_valid:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(bytes(data))

    return result
