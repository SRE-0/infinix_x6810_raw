# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Executable-code cave discovery and allocation.

A code cave is a region of unused bytes inside a mapped ELF segment
where we can write trampoline code.  Two caves are available in the
target binary: the PLT cave (small, near push_back helpers) and the
LOAD1–LOAD2 gap cave (large, needs LOAD2 extension).
"""

# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from mtkcam_raw.elf import ElfImage, ProgramHeader


@dataclass
class Cave:
    """Available code cave in the executable segment."""
    va: int
    file_offset: int
    size: int
    extend_load: bool = False
    ph_load: Optional[ProgramHeader] = None
    is_gap: bool = False  # True = LOAD1-LOAD2 gap (needs p_offset/p_vaddr)


def find_plt_cave(image: ElfImage) -> Optional[Cave]:
    """
    Find the gap between .text end and .plt start, plus PLT[0]
    (which is dead code when BIND_NOW is set).
    """
    text_sec = image.sections.get(".text")
    plt_sec = image.sections.get(".plt")
    if not text_sec or not plt_sec:
        return None

    text_end = text_sec.offset + text_sec.size
    plt_start = plt_sec.offset

    gap_size = plt_start - text_end if plt_start > text_end else 0
    plt0_size = min(plt_sec.size, 32) if plt_sec.offset > 0 else 0
    available = gap_size + plt0_size

    if available == 0:
        return None

    return Cave(
        va=text_end,
        file_offset=text_end,
        size=available,
    )


def find_load12_gap(image: ElfImage) -> Optional[Cave]:
    """
    Find the zero gap between LOAD1 end and LOAD2 start,
    which can be absorbed into LOAD2 by extending it backwards.
    Requires p_offset / p_vaddr / p_filesz / p_memsz PH changes.
    """
    load_segs = image.load_segments
    if len(load_segs) < 2:
        return None

    load1 = load_segs[0]
    load2 = load_segs[1]

    gap_start = load1.p_offset + load1.p_filesz
    if load2.p_offset <= gap_start:
        return None

    gap_size = load2.p_offset - gap_start

    if gap_size < 32:
        return None

    return Cave(
        va=load2.p_vaddr - (load2.p_offset - gap_start),
        file_offset=gap_start,
        size=gap_size,
        extend_load=True,
        ph_load=load2,
        is_gap=True,
    )


def find_load2_end_extension(image: ElfImage) -> Optional[Cave]:
    """
    Find zero padding after LOAD2 that can be absorbed by extending
    LOAD2 forward (increasing p_filesz / p_memsz).

    This only needs p_filesz / p_memsz changes (no p_offset / p_vaddr).
    """
    load_segs = image.load_segments
    if len(load_segs) < 2:
        return None
    load2 = load_segs[1]

    cave_off = load2.p_offset + load2.p_filesz
    cave_va  = load2.p_vaddr + load2.p_filesz

    avail = 0
    while cave_off + avail < len(image.data) and image.data[cave_off + avail] == 0:
        avail += 1

    if avail < 32:
        return None

    return Cave(
        va=cave_va,
        file_offset=cave_off,
        size=avail,
        extend_load=True,
        ph_load=load2,
        is_gap=False,
    )


@dataclass
class CaveAllocator:
    """
    Shared allocator that tracks consumed space across all known caves.

    Tracks allocation state so independently planned capability and
    stream trampolines cannot overlap.
    """
    _slots: list[Cave] = field(default_factory=list)
    _extend_emitted: set[int] = field(default_factory=set)  # PH indices that got extended

    @classmethod
    def from_image(cls, image: ElfImage) -> CaveAllocator:
        """Discover all caves and return an allocator owning them."""
        slots: list[Cave] = []
        plt = find_plt_cave(image)
        if plt is not None:
            slots.append(plt)
        gap = find_load12_gap(image)
        if gap is not None:
            slots.append(gap)
        ext = find_load2_end_extension(image)
        if ext is not None:
            slots.append(ext)
        return cls(_slots=slots)

    def allocate(
        self,
        size: int,
        *,
        prefer_extend: bool = False,
        prefer_gap: bool = True,
    ) -> Cave:
        """
        Allocate *size* bytes from an available cave slot.

        If *prefer_extend*, choose the slot that supports LOAD2
        extension first.  If *prefer_gap*, prefer gap caves over
        end-of-segment caves (only meaningful w/ prefer_extend).
        Raises ValueError when no slot is big enough.
        """
        def slot_key(s: Cave) -> tuple:
            extend_match = 0 if s.extend_load == prefer_extend else 1
            gap_match = 0 if s.is_gap == prefer_gap else 1
            return (extend_match, gap_match, -s.size)

        ordered = sorted(self._slots, key=slot_key)
        for i, s in enumerate(ordered):
            if s.size >= size:
                ph_idx = s.ph_load.index if s.ph_load else -1
                already_emitted = ph_idx in self._extend_emitted
                result = Cave(
                    va=s.va,
                    file_offset=s.file_offset,
                    size=size,
                    extend_load=s.extend_load and not already_emitted,
                    ph_load=s.ph_load,
                    is_gap=s.is_gap,
                )
                s.va += size
                s.file_offset += size
                s.size -= size
                if result.extend_load and ph_idx >= 0:
                    self._extend_emitted.add(ph_idx)
                # Remove empty slots
                if s.size == 0:
                    self._slots.remove(s)
                return result

        raise ValueError(
            f"No cave available for {size} bytes "
            f"(largest slot has {max(s.size for s in self._slots)}B)"
        )

    @property
    def remaining(self) -> int:
        return sum(s.size for s in self._slots)
