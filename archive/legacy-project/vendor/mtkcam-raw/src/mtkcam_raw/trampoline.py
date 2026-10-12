# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Trampoline construction and patch planning.

Builds AArch64 trampoline byte sequences for capability append
and stream-config append.  Plans all patches (cave allocation,
hook redirection, LOAD2 extension) through a shared CaveAllocator.
"""

# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from __future__ import annotations

import struct

from mtkcam_raw.elf import ElfImage
from mtkcam_raw.cave import Cave, CaveAllocator
from mtkcam_raw.aarch64 import (
    movz_w8,
    movk_w8,
    encode_bl,
    encode_branch,
    encode_bcc,
    encode_adr,
    encode_ldrb_offset,
    encode_add_imm,
    encode_subs_imm,
    encode_cbz,
    encode_strb_offset,
    STP_X29_X30_PRE16,
    LDP_X29_X30_POST16,
    STP_X19_X20_PRE16,
    LDP_X19_X20_POST16,
    SUB_X0_X29_0x50,
    ADD_X1_SP_0x10,
    RET,
    strb_w8_sp,
    add_x1_sp,
    w,
)
from mtkcam_raw.patch import PatchRecord
from mtkcam_raw.analysis import BinaryProfile


# Strategy: preserve the slot's original movz value, redirect its
# bl push_back → trampoline.  Trampoline pushes the slot's original
# value, then pushes each extra capability.


def build_capability_trampoline(
    cave_va: int,
    push_back_va: int,
    extra_caps: list[int],
) -> bytes:
    """
    Build trampoline that appends extra capability values.

    On entry: x0=IEntry*, x1=ptr to slot value at sp+0x10.
    Returns to instruction after the original bl push_back.

    Layout (36 + 20*(N-1) bytes for N extra caps):
      stp x29, x30, [sp, #-16]!
      bl push_back              ; push slot's original value
      for each extra cap:
        movz w8, #cap
        strb w8, [sp, #32]      ; past saved frame, reaches orig sp+0x10
        sub x0, x29, #0x50
        add x1, sp, #0x20
        bl push_back
      ldp x29, x30, [sp], #16
      ret
    """
    out = bytearray()
    pos = cave_va

    out += struct.pack("<I", STP_X29_X30_PRE16)
    pos += 4
    out += encode_bl(pos, push_back_va)
    pos += 4

    for cap in extra_caps:
        out += movz_w8(cap)
        pos += 4
        out += struct.pack("<I", strb_w8_sp(32))
        pos += 4
        out += struct.pack("<I", SUB_X0_X29_0x50)
        pos += 4
        out += struct.pack("<I", add_x1_sp(0x20))
        pos += 4
        out += encode_bl(pos, push_back_va)
        pos += 4

    out += struct.pack("<I", LDP_X29_X30_POST16)
    pos += 4
    out += struct.pack("<I", RET)

    return bytes(out)


def make_capability_append_patches(
    image: ElfImage,
    slot_off: int,
    extra_caps: list[int],
    push_back_va: int,
    allocator: CaveAllocator,
) -> list[PatchRecord]:
    """
    Create patches to add capabilities via trampoline append.
    The slot value is preserved; only the bl is redirected.
    Allocates trampoline space from the allocator.
    """
    if not extra_caps:
        return []

    records: list[PatchRecord] = []
    call_va = image.offset_to_va(slot_off + 16)
    if call_va is None:
        raise ValueError(f"Cannot compute VA for offset 0x{slot_off + 16:x}")

    # Compute trampoline size: 16 + 20 * len(extra_caps)
    tramp_size = 16 + 20 * len(extra_caps)
    cave = allocator.allocate(tramp_size)

    new_bl = encode_bl(call_va, cave.va)
    records.append(PatchRecord(
        file_offset=slot_off + 16,
        old_bytes=image.data[slot_off + 16 : slot_off + 20],
        new_bytes=new_bl,
        description=f"redirect slot bl -> cave 0x{cave.va:x}",
    ))

    tramp = build_capability_trampoline(cave.va, push_back_va, extra_caps)
    records.append(PatchRecord(
        file_offset=cave.file_offset,
        old_bytes=image.data[
            cave.file_offset : cave.file_offset + len(tramp)
        ],
        new_bytes=tramp,
        description=f"trampoline ({len(tramp)}B) caps={extra_caps}",
    ))

    _emit_load2_extend(image, cave, records)

    return records


# Each sensor gets a tiny stub: adr x20, cap_data; b shared_body
# Shared body saves frame, pushes original slot value, then iterates
# through the sensor's cap data using x20 as the data pointer.


def _shared_cap_body_size() -> int:
    """Fixed size of the shared cap trampoline body (no variable per-sensor data)."""
    return 68  # bytes (17 instructions)


def _shared_cap_stub_size() -> int:
    """Size of each sensor stub (adr + b)."""
    return 8


def build_shared_cap_trampoline(
    cave_base_va: int,
    push_back_va: int,
    sensor_cap_data: list[tuple[int, list[int]]],
) -> tuple[bytes, list[tuple[int, bytes]]]:
    """
    Build shared cap trampoline: one body + per-sensor stubs.
    
    Layout in cave:
      cave_base:          shared_body (68B)
      cave_base+68:       cap_data[0], cap_data[1], ...
      after all cap_data: stub[0], stub[1], ...
    
    Returns:
      (shared_body_bytes, [(stub_va, stub_bytes), ...])
      where each stub_va is the VA where the stub should be written.
    """
    body_va = cave_base_va
    body = bytearray()

    # x20 is set by the stub via adr (callee-saved, preserved by push_back)
    body += w(STP_X29_X30_PRE16)                       # 0: stp x29,x30,[sp,#-16]!
    body += w(STP_X19_X20_PRE16)                        # 4: stp x19,x20,[sp,#-16]!
    body += encode_bl(body_va + 8, push_back_va)       # 8: bl push_back  (original slot value, x0/x1 unchanged from caller)

    body += encode_ldrb_offset(12, 20)                   # 12: ldrb w12, [x20]  — cap count
    body += encode_add_imm(20, 20, 1)                    # 16: add x20, x20, #1 -> first cap
    done_va = cave_base_va + 56
    body += encode_cbz(body_va + 20, done_va, rd=12)   # 20: cbz w12, done

    # x20 is callee-saved so push_back preserves the advanced pointer
    loop_va = cave_base_va + 24
    body += encode_ldrb_offset(8, 20)                    # 24: ldrb w8, [x20]      — load cap
    body += encode_add_imm(20, 20, 1)                    # 28: add x20, x20, #1   — advance
    body += encode_strb_offset(8, 31, 0x30)             # 32: strb w8, [sp, #0x30] — write to slot (maps to caller's sp+0x10)
    body += w(SUB_X0_X29_0x50)                           # 36: sub x0, x29, #0x50  — IEntry*
    body += encode_add_imm(1, 31, 0x30)                  # 40: add x1, sp, #0x30   — ptr to cap (maps to caller's sp+0x10)
    body += encode_bl(body_va + 44, push_back_va)       # 44: bl push_back
    body += encode_subs_imm(12, 12, 1)                   # 48: subs w12, w12, #1
    body += encode_bcc(body_va + 52, loop_va, 1)        # 52: b.ne loop

    body += w(LDP_X19_X20_POST16)                        # 56: ldp x19,x20,[sp],#16
    body += w(LDP_X29_X30_POST16)                        # 60: ldp x29,x30,[sp],#16
    body += w(RET)                                        # 64: ret

    assert len(body) == 68, f"shared cap body length mismatch: {len(body)}"

    stubs: list[tuple[int, bytes]] = []
    data_offsets: list[int] = []

    body_len = len(body)
    data_offset = cave_base_va + body_len
    for idx, caps in sensor_cap_data:
        data_offsets.append(data_offset)
        data_offset += 1 + len(caps)

    cap_data_total = sum(1 + len(caps) for _, caps in sensor_cap_data)
    aligned_data_total = (cap_data_total + 3) & ~3
    stub_base_va = cave_base_va + body_len + aligned_data_total

    for i, (data_va, (idx, caps)) in enumerate(zip(data_offsets, sensor_cap_data)):
        stub_va = stub_base_va + i * 8
        stub = bytearray()
        stub += encode_adr(stub_va, data_va, rd=20)     # adr x20, cap_data
        stub += encode_branch(stub_va + 4, body_va)      # b shared_body
        stubs.append((stub_va, bytes(stub)))

    return bytes(body), stubs


def make_shared_cap_patches(
    image: ElfImage,
    sensor_slots: list[tuple[str, int, int, list[int]]],
    allocator: CaveAllocator,
) -> list[PatchRecord]:
    """
    Create patches using a shared cap trampoline.
    
    Each sensor_slot: (name, slot_file_offset, push_back_va, [extra_caps])
    Only sensors with non-empty extra_caps are processed.
    
    Allocates trampoline + stubs + data from the shared allocator.
    """
    records: list[PatchRecord] = []

    # Filter out sensors with no missing caps
    active = []
    for name, slot_off, pb_va, caps in sensor_slots:
        if not caps:
            continue
        active.append((name, slot_off, pb_va, caps))

    if not active:
        return []

    # All sensors should use the same push_back_va; verify and use the first
    push_back_va = active[0][2]

    # Calculate total allocation size (cap data aligned to 4 bytes for stub placement)
    body_size = _shared_cap_body_size()
    cap_data_size = sum(1 + len(caps) for _, _, _, caps in active)
    aligned_cap_size = (cap_data_size + 3) & ~3
    stubs_size = len(active) * _shared_cap_stub_size()
    total_size = body_size + aligned_cap_size + stubs_size

    cave = allocator.allocate(total_size)
    cave_va = cave.va

    # Build body and stubs
    sensor_data = [(i, caps) for i, (_, _, _, caps) in enumerate(active)]
    body_bytes, stubs = build_shared_cap_trampoline(cave_va, push_back_va, sensor_data)

    # Build cap data blob
    data_offset = cave_va + body_size
    data_blob = bytearray()
    data_starts: list[int] = []
    for _, _, _, caps in active:
        data_starts.append(data_offset + len(data_blob))
        data_blob.append(len(caps))
        data_blob.extend(caps)
    cap_data_bytes = bytes(data_blob)

    # Combine body + data into the cave
    cave_code = bytearray(body_bytes)
    cave_code.extend(cap_data_bytes)

    # Add stubs to cave
    for stub_va, stub_bytes in stubs:
        stub_offset = stub_va - cave_va
        assert stub_offset >= len(cave_code)
        pad = stub_offset - len(cave_code)
        if pad > 0:
            cave_code.extend(b'\x00' * pad)
        cave_code.extend(stub_bytes)

    # Write cave content
    records.append(PatchRecord(
        file_offset=cave.file_offset,
        old_bytes=image.data[cave.file_offset:cave.file_offset + len(cave_code)],
        new_bytes=bytes(cave_code),
        description=f"shared cap trampoline ({len(cave_code)}B, {len(active)} sensors)",
    ))

    # Redirect each sensor's BL to its stub
    for (name, slot_off, pb_va, caps), (stub_va, _) in zip(active, stubs):
        call_va = image.offset_to_va(slot_off + 16)
        if call_va is None:
            raise ValueError(f"Cannot compute VA for {name} at offset 0x{slot_off + 16:x}")
        new_bl = encode_bl(call_va, stub_va)  # BL — sets x30 = return address for the trampoline
        records.append(PatchRecord(
            file_offset=slot_off + 16,
            old_bytes=image.data[slot_off + 16:slot_off + 20],
            new_bytes=new_bl,
            description=f"[{name}] redirect BL -> stub 0x{stub_va:x}",
        ))

    _emit_load2_extend(image, cave, records)
    return records



def _emit_load2_extend(
    image: ElfImage,
    cave: Cave,
    records: list[PatchRecord],
) -> None:
    """
    If the allocated cave requires LOAD2 extension, emit the
    program-header patches so the new bytes are mapped at runtime.

    Gap cave (is_gap=True):
      Patches p_offset / p_vaddr / p_filesz / p_memsz to absorb
      the LOAD1-LOAD2 gap backward into LOAD2.
    End cave (is_gap=False):
      Patches only p_filesz / p_memsz to extend LOAD2 forward
      into the zero-padding after the segment.

    The extension covers the full available extent, so subsequent
    allocations within the same cave are already mapped.
    """
    if not (cave.extend_load and cave.ph_load):
        return

    ph = cave.ph_load
    ph_off = 0x40 + ph.index * 56

    if cave.is_gap:
        # Extend LOAD2 backward into the gap (all 4 PH updates).
        # Also include end-of-LOAD2 zero padding so the gap emission
        # covers the full extent — no second PH round needed for the
        # end-extension cave.
        gap_bytes = ph.p_offset - cave.file_offset
        end = ph.p_offset + ph.p_filesz
        while end < len(image.data) and image.data[end] == 0:
            end += 1
        total_extend = end - (ph.p_offset + ph.p_filesz) + gap_bytes
        new_fz = ph.p_filesz + total_extend
        new_msz = max(ph.p_memsz, new_fz)

        records.append(PatchRecord(
            file_offset=ph_off + 8,
            old_bytes=image.data[ph_off + 8 : ph_off + 16],
            new_bytes=struct.pack("<Q", cave.file_offset),
            description="LOAD2 p_offset <- cave start",
        ))
        records.append(PatchRecord(
            file_offset=ph_off + 16,
            old_bytes=image.data[ph_off + 16 : ph_off + 24],
            new_bytes=struct.pack("<Q", cave.va),
            description="LOAD2 p_vaddr <- cave VA",
        ))
        records.append(PatchRecord(
            file_offset=ph_off + 32,
            old_bytes=image.data[ph_off + 32 : ph_off + 40],
            new_bytes=struct.pack("<Q", new_fz),
            description=f"LOAD2 p_filesz 0x{ph.p_filesz:x} -> 0x{new_fz:x}",
        ))
        records.append(PatchRecord(
            file_offset=ph_off + 40,
            old_bytes=image.data[ph_off + 40 : ph_off + 48],
            new_bytes=struct.pack("<Q", new_msz),
            description=f"LOAD2 p_memsz 0x{ph.p_memsz:x} -> 0x{new_msz:x}",
        ))
    else:
        # Extend LOAD2 forward into end-of-segment zero padding
        load2_end = ph.p_offset + ph.p_filesz
        padding_end = load2_end
        while padding_end < len(image.data) and image.data[padding_end] == 0:
            padding_end += 1
        total_extend = padding_end - load2_end

        new_fz = ph.p_filesz + total_extend
        new_msz = max(ph.p_memsz, new_fz)

        records.append(PatchRecord(
            file_offset=ph_off + 32,
            old_bytes=image.data[ph_off + 32 : ph_off + 40],
            new_bytes=struct.pack("<Q", new_fz),
            description=f"LOAD2 p_filesz 0x{ph.p_filesz:x} -> 0x{new_fz:x}",
        ))
        records.append(PatchRecord(
            file_offset=ph_off + 40,
            old_bytes=image.data[ph_off + 40 : ph_off + 48],
            new_bytes=struct.pack("<Q", new_msz),
            description=f"LOAD2 p_memsz 0x{ph.p_memsz:x} -> 0x{new_msz:x}",
        ))



def build_stream_trampoline(
    cave_va: int,
    entry_for_va: int,
    push_long_va: int,
    entries: list[tuple[int, ...]],
) -> bytes:
    """
    Build trampoline that calls entryFor, then pushes extra stream entries.

    On entry: x0/x1/x2 already for entryFor call.
    The saved x30 is the return address after the original bl entryFor.
    """
    STR_X8_SP16 = 0xF9000BE8  # str x8, [sp, #0x10]
    STR_XZR_SP16 = 0xF9000BFF  # str xzr, [sp, #0x10]

    out = bytearray()
    pos = cave_va

    out += struct.pack("<I", STP_X29_X30_PRE16)
    pos += 4
    out += encode_bl(pos, entry_for_va)
    pos += 4

    for entry in entries:
        for field in entry:
            if field == 0:
                out += struct.pack("<I", STR_XZR_SP16)
                pos += 4
            elif field <= 0xFFFF:
                out += movz_w8(field)
                out += struct.pack("<I", STR_X8_SP16)
                pos += 8
            else:
                lo = field & 0xFFFF
                hi = (field >> 16) & 0xFFFF
                out += movz_w8(lo)
                out += movk_w8(hi)
                out += struct.pack("<I", STR_X8_SP16)
                pos += 12

            out += struct.pack("<I", SUB_X0_X29_0x50)
            out += struct.pack("<I", ADD_X1_SP_0x10)
            pos += 8
            out += encode_bl(pos, push_long_va)
            pos += 4

    out += struct.pack("<I", LDP_X29_X30_POST16)
    pos += 4
    out += struct.pack("<I", RET)

    return bytes(out)


def _stream_trampoline_size(entries: list[tuple[int, ...]]) -> int:
    """Compute stream trampoline byte size without building it."""
    total = 16  # stp + bl_entry + ldp + ret
    for entry in entries:
        for field in entry:
            if field == 0:
                total += 16   # str_xzr + sub + add + bl
            elif field <= 0xFFFF:
                total += 20   # movz + str + sub + add + bl
            else:
                total += 24   # movz + movk + str + sub + add + bl
    return total


def make_stream_append_patches(
    image: ElfImage,
    hook_va: int,
    profile: BinaryProfile,
    allocator: CaveAllocator,
    entries: list[tuple[int, ...]],
) -> list[PatchRecord]:
    """
    Create patches to append RAW16 stream config entries.
    Allocates trampoline space and LOAD2 extension through
    the shared allocator.
    """
    records: list[PatchRecord] = []

    hook_off = image.va_to_offset(hook_va)
    if hook_off is None:
        raise ValueError(f"Cannot find file offset for VA 0x{hook_va:x}")

    tramp_size = _stream_trampoline_size(entries)
    cave = allocator.allocate(tramp_size)

    orig_bl = image.data[hook_off : hook_off + 4]
    new_bl = encode_bl(hook_va, cave.va)
    records.append(PatchRecord(
        file_offset=hook_off,
        old_bytes=orig_bl,
        new_bytes=new_bl,
        description=f"redirect entryFor -> cave 0x{cave.va:x}",
    ))

    tramp = build_stream_trampoline(
        cave.va, profile.entry_for_va, profile.push_long_va, entries
    )
    records.append(PatchRecord(
        file_offset=cave.file_offset,
        old_bytes=image.data[
            cave.file_offset : cave.file_offset + len(tramp)
        ],
        new_bytes=tramp,
        description=f"stream trampoline ({len(tramp)}B)",
    ))

    _emit_load2_extend(image, cave, records)

    return records



def parse_stream_entries(entry_strs: list[str]) -> list[tuple[int, ...]]:
    """Parse stream entry strings like '32,0xFF0,0xC00,0,...' into tuples."""
    entries: list[tuple[int, ...]] = []
    for s in entry_strs:
        parts: list[int] = []
        for p in s.split(","):
            p = p.strip()
            if p.startswith("0x") or p.startswith("0X"):
                parts.append(int(p, 16))
            else:
                parts.append(int(p))
        entries.append(tuple(parts))
    return entries
