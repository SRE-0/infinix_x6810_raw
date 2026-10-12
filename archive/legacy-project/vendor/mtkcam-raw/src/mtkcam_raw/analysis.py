"""
Binary analysis — find capability blocks, stream config blocks,
and patch sites structurally.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Optional

from mtkcam_raw.aarch64 import (
    MOV_W1_C000C,
    MOVK_W1_BASE,
    STRB_W8_SP,
    STRBWZR_SP16,
    SUB_X0_X29_0x50,
    ADD_X1_SP_0x10,
    read_word,
    decode_movz_w8,
    decode_exact_bl,
    decode_branch_target,
)
from mtkcam_raw.elf import ElfImage
from mtkcam_raw.metadata import (
    TAG_AVAILABLE_STREAM_CONFIGURATIONS,
)


@dataclass
class CapabilitySlot:
    file_offset: int
    value: int
    bl_push_back_offset: int
    push_back_target_va: Optional[int]

    def get_function_va(self) -> Optional[int]:
        return None


@dataclass
class CapabilityBlock:
    sensor_name: str
    function_va: int
    function_size: int
    tag_file_offset: int
    entry_for_call_offset: int
    slots: list[CapabilitySlot] = field(default_factory=list)

    @property
    def values(self) -> list[int]:
        return [s.value for s in self.slots]


@dataclass
class StreamBlock:
    sensor_name: str
    function_va: int
    tag_file_offset: int
    entry_for_call_offset: int
    hook_va: int
    push_long_target_va: Optional[int] = None


@dataclass
class BinaryProfile:
    entry_for_va: int
    push_long_va: int


def discover_binary_profile(image: ElfImage, prefix: str = "") -> BinaryProfile:
    hooks = find_all_stream_hooks(image, prefix)
    if not hooks:
        raise ValueError("No stream hooks found; cannot discover helpers")

    hook = hooks[0]
    entry_for_word = struct.unpack("<I",
        image.data[hook.entry_for_call_offset:
                   hook.entry_for_call_offset + 4])[0]
    if entry_for_word >> 26 != 0b100101:
        raise ValueError(
            f"Hook at 0x{hook.hook_va:x} is not a BL instruction"
        )
    imm26 = entry_for_word & 0x3FFFFFF
    if imm26 & (1 << 25):
        imm26 -= 1 << 26
    entry_for_va = hook.hook_va + imm26 * 4

    scan_start = hook.entry_for_call_offset + 4
    scan_end = min(scan_start + 0x100, len(image.data))
    push_long_va = 0
    for off in range(scan_start, scan_end):
        w = struct.unpack_from("<I", image.data, off)[0]
        if w >> 26 == 0b100101:
            t = decode_branch_target(image.data, off, image)
            if t is not None and t != entry_for_va:
                push_long_va = t
                break

    if not push_long_va:
        raise ValueError("Could not discover push_long_va from binary")

    return BinaryProfile(entry_for_va=entry_for_va,
                         push_long_va=push_long_va)


@dataclass
class PatchSite:
    kind: str
    sensor_name: str
    function_va: int
    file_offset: int


def find_capability_block(
    image: ElfImage,
    func_va: int,
    func_size: int,
) -> Optional[CapabilityBlock]:
    func_off = image.va_to_offset(func_va)
    if func_off is None:
        return None

    scan_size = func_size if func_size > 0 else 0x800
    body = image.data[func_off : func_off + scan_size]

    tag_pattern = struct.pack("<I", MOV_W1_C000C)
    tag_pos = body.find(tag_pattern)
    if tag_pos < 0:
        return None

    tag_file_off = func_off + tag_pos
    entry_for_off = tag_file_off + 4

    slots: list[CapabilitySlot] = []
    i = tag_pos + 4
    end = min(len(body), tag_pos + 0x100)

    IMM_MASK = 0xFFC003FF
    STRB_W8_BASE = STRB_W8_SP
    STRB_WZR_BASE = STRBWZR_SP16 & IMM_MASK
    SUB_X0_X29_BASE = SUB_X0_X29_0x50 & IMM_MASK
    ADD_X1_SP_BASE = ADD_X1_SP_0x10 & IMM_MASK

    while i < end - 4:
        w = read_word(body, i)

        if (w & IMM_MASK) == STRB_WZR_BASE:
            w4 = read_word(body, i + 4)
            w8 = read_word(body, i + 8)
            if (
                i + 12 < end
                and (w4 & IMM_MASK) == SUB_X0_X29_BASE
                and (w8 & IMM_MASK) == ADD_X1_SP_BASE
            ):
                bl_off = func_off + i + 12
                bl_target = decode_exact_bl(
                    image.data, bl_off, image
                )
                slots.append(CapabilitySlot(
                    file_offset=func_off + i,
                    value=0,
                    bl_push_back_offset=bl_off,
                    push_back_target_va=bl_target,
                ))
                i += 16
                continue

        n = decode_movz_w8(body[i : i + 4])
        if n is not None:
            if i + 4 < end:
                w4 = read_word(body, i + 4)
                if (w4 & IMM_MASK) == STRB_W8_BASE:
                    w8 = read_word(body, i + 8)
                    w12 = read_word(body, i + 12)
                    if (
                        i + 12 < end
                        and (w8 & IMM_MASK) == SUB_X0_X29_BASE
                        and (w12 & IMM_MASK) == ADD_X1_SP_BASE
                    ):
                        bl_off = func_off + i + 16
                        bl_target = decode_exact_bl(
                            image.data, bl_off, image
                        )
                        slots.append(CapabilitySlot(
                            file_offset=func_off + i,
                            value=n,
                            bl_push_back_offset=bl_off,
                            push_back_target_va=bl_target,
                        ))
                        i += 20
                        continue

        if (w & IMM_MASK) == SUB_X0_X29_BASE and len(slots) > 0:
            break

        i += 4

    if not slots:
        return None

    return CapabilityBlock(
        sensor_name="",
        function_va=func_va,
        function_size=func_size,
        tag_file_offset=tag_file_off,
        entry_for_call_offset=entry_for_off,
        slots=slots,
    )


def find_stream_block(
    image: ElfImage,
    func_va: int,
    func_size: int,
    hook_va: int,
) -> Optional[StreamBlock]:
    func_off = image.va_to_offset(func_va)
    if func_off is None:
        return None

    hook_off = image.va_to_offset(hook_va)
    if hook_off is None:
        return None

    return StreamBlock(
        sensor_name="",
        function_va=func_va,
        tag_file_offset=hook_off - 8,
        entry_for_call_offset=hook_off,
        hook_va=hook_va,
    )


def find_sensor_symbols(image: ElfImage, prefix: str = "") -> list:
    if not prefix:
        return []
    return [
        s for s in image.symbols
        if s.name.startswith(prefix)
    ]


def analyze_all_capabilities(
    image: ElfImage,
    prefix: str = "",
) -> list[CapabilityBlock]:
    results: list[CapabilityBlock] = []
    for sym in find_sensor_symbols(image, prefix):
        block = find_capability_block(
            image, sym.value, sym.size
        )
        if block is not None:
            from mtkcam_raw.metadata import sensor_short_name
            block.sensor_name = sensor_short_name(sym.name, prefix)
            results.append(block)
    return results


def find_all_stream_hooks(
    image: ElfImage,
    prefix: str = "",
) -> list[StreamBlock]:
    TAG_STREAM = TAG_AVAILABLE_STREAM_CONFIGURATIONS
    tag_lo = TAG_STREAM & 0xFFFF
    tag_hi_shifted = (TAG_STREAM >> 16) & 0xFFFF

    results: list[StreamBlock] = []
    for sym in find_sensor_symbols(image, prefix):
        func_off = image.va_to_offset(sym.value)
        if func_off is None:
            continue
        scan_size = sym.size if sym.size > 0 else 0x800
        body = image.data[func_off : func_off + scan_size]

        movk_pattern = struct.pack(
            "<I", MOVK_W1_BASE | ((tag_hi_shifted & 0xFFFF) << 5) | (1 << 21)
        )

        pos = 0
        while pos < len(body) - 12:
            w = read_word(body, pos)
            if (w & 0xFFE0001F) == 0x52800001:
                if (w >> 5) & 0xFFFF == tag_lo:
                    if pos + 8 < len(body):
                        w2 = read_word(body, pos + 4)
                        if w2 == struct.unpack(
                            "<I", movk_pattern
                        )[0]:
                            w3 = read_word(body, pos + 8)
                            if (w3 >> 26) == 0b100101:
                                hook_va = sym.value + pos + 8
                                push_long_target = decode_branch_target(
                                    image.data, func_off + pos + 8, image
                                )
                                from mtkcam_raw.metadata import sensor_short_name
                                name = sensor_short_name(sym.name, prefix)
                                block = StreamBlock(
                                    sensor_name=name,
                                    function_va=sym.value,
                                    tag_file_offset=func_off + pos,
                                    entry_for_call_offset=func_off + pos + 8,
                                    hook_va=hook_va,
                                    push_long_target_va=push_long_target,
                                )
                                results.append(block)
                                break
                pos += 4
            else:
                pos += 4

    return results
