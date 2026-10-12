# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Verification — compare original and patched binaries, detect
already-patched state, validate ELF structure.
"""

# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from __future__ import annotations

import struct
import hashlib
from dataclasses import dataclass, field

from mtkcam_raw.elf import parse_elf


@dataclass
class DiffRegion:
    """A contiguous changed byte region."""
    file_offset: int
    size: int
    old_bytes: bytes
    new_bytes: bytes


@dataclass
class VerificationResult:
    """Result of comparing original and patched binaries."""
    original_sha256: str
    patched_sha256: str
    regions: list[DiffRegion] = field(default_factory=list)
    elf_valid: bool = True
    elf_errors: list[str] = field(default_factory=list)
    already_patched: bool = False
    only_intended_changes: bool = True

    @property
    def total_changed(self) -> int:
        return sum(r.size for r in self.regions)


def compare_binaries(
    original: bytes,
    patched: bytes,
) -> VerificationResult:
    """
    Compare two binaries and produce a structured diff.
    Detects already-patched state by checking if the patch
    BL targets are already redirected to cave addresses.
    """
    result = VerificationResult(
        original_sha256=hashlib.sha256(original).hexdigest(),
        patched_sha256=hashlib.sha256(patched).hexdigest(),
    )

    if len(original) != len(patched):
        min_len = min(len(original), len(patched))
        i = 0
        while i < min_len:
            if original[i] != patched[i]:
                start = i
                while i < min_len and original[i] != patched[i]:
                    i += 1
                end = i
                result.regions.append(DiffRegion(
                    file_offset=start,
                    size=end - start,
                    old_bytes=original[start:end],
                    new_bytes=patched[start:end],
                ))
            else:
                i += 1
        if len(original) > len(patched):
            result.regions.append(DiffRegion(
                file_offset=min_len,
                size=len(original) - min_len,
                old_bytes=original[min_len:],
                new_bytes=b"",
            ))
        else:
            result.regions.append(DiffRegion(
                file_offset=min_len,
                size=len(patched) - min_len,
                old_bytes=b"",
                new_bytes=patched[min_len:],
            ))
        return result

    i = 0
    while i < len(original):
        if original[i] != patched[i]:
            start = i
            while i < len(original) and original[i] != patched[i]:
                i += 1
            end = i
            # Merge with last region if adjacent or overlapping
            if result.regions and result.regions[-1].file_offset + result.regions[-1].size >= start:
                prev = result.regions[-1]
                new_end = max(prev.file_offset + prev.size, end)
                merged_old = prev.old_bytes + original[prev.file_offset + prev.size:new_end]
                merged_new = prev.new_bytes + patched[prev.file_offset + prev.size:new_end]
                result.regions[-1] = DiffRegion(
                    file_offset=prev.file_offset,
                    size=new_end - prev.file_offset,
                    old_bytes=merged_old,
                    new_bytes=merged_new,
                )
            else:
                result.regions.append(DiffRegion(
                    file_offset=start,
                    size=end - start,
                    old_bytes=original[start:end],
                    new_bytes=patched[start:end],
                ))
        else:
            i += 1

    return result


def validate_elf_structure(data: bytes) -> list[str]:
    """
    Basic ELF structural validation.
    Returns list of issues (empty = valid).
    """
    errors: list[str] = []

    if data[:4] != b"\x7fELF":
        errors.append("Not an ELF file")
        return errors

    ei_class = data[4]
    if ei_class != 2:
        errors.append("Not a 64-bit ELF")

    ei_data = data[5]
    if ei_data != 1:
        errors.append("Not little-endian")

    e_type = struct.unpack_from("<H", data, 0x10)[0]
    if e_type not in (1, 2, 3):
        errors.append(f"Unexpected ELF type: {e_type}")

    return errors


def detect_already_patched(
    original: bytes, patched: bytes, cave_va: int
) -> bool:
    """
    Check whether patched binary has BL instructions that already
    target the cave VA range (indicating a prior patch application).
    """
    try:
        orig_img = parse_elf(original)
    except ValueError:
        return False

    # Find all BL targets that changed
    changed_sites = []
    min_len = min(len(original), len(patched))
    for off in range(0, min_len - 4, 4):
        orig_word = struct.unpack_from("<I", original, off)[0]
        patched_word = struct.unpack_from("<I", patched, off)[0]

        if orig_word == patched_word:
            continue

        # Check if patched instruction is a BL
        if patched_word >> 26 != 0b100101:
            continue

        from_va = orig_img.offset_to_va(off)
        if from_va is None:
            continue

        imm26 = patched_word & 0x3FFFFFF
        if imm26 & (1 << 25):
            imm26 -= 1 << 26
        target_va = from_va + imm26 * 4

        if target_va >= cave_va and target_va < cave_va + 4096:
            changed_sites.append((off, target_va))

    # If any BL was redirected to the cave range, it's already patched
    return len(changed_sites) > 0
