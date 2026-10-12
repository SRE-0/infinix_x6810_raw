# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
AArch64 instruction encoding and decoding helpers.

Provides construction and inspection of the instruction patterns
needed by mtkcam-raw patches (movz, movk, strb, str, B, BL, B.cond,
stp, ldp, ret, ADR, sub, add, svc, cbnz, etc.).
"""

# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from __future__ import annotations

import struct
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from mtkcam_raw.elf import ElfImage


def w(val: int) -> bytes:
    """Pack a 32-bit little-endian word."""
    return struct.pack("<I", val)


def read_word(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


MOVZ_W8_BASE = 0x52800008  # movz w8, #0 — value goes in bits [20:5]
MOVK_W8_BASE = 0x72800008  # movk w8, #0
MOVZ_W1_BASE = 0x52800001  # movz w1, #0
MOVK_W1_BASE = 0x72800001  # movk w1, #0

STRB_W8_SP = 0x390003E8  # strb w8, [sp, #imm12] — imm at bits [21:10]; Rt=8, Rn=31
STR_W8_SP = 0xF9000BE8  # str x8, [sp, #0x10]
STR_XZR_SP = 0xF9000BFF  # str xzr, [sp, #0x10]
STRBWZR_SP16 = 0x390003FF  # strb wzr, [sp, #0x10] — Rt=31, Rn=31 (base; imm12 masked out before compare)

STP_X19_X20_PRE16 = 0xA9BF53F3  # stp x19, x20, [sp, #-16]!
LDP_X19_X20_POST16 = 0xA8C153F3  # ldp x19, x20, [sp], #16

SUB_X0_X29_0x50 = 0xD10143A0  # sub x0, x29, #0x50
ADD_X1_SP_0x10 = 0x910043E1  # add x1, sp, #0x10

STP_X29_X30_PRE16 = 0xA9BF7BFD  # stp x29, x30, [sp, #-16]!
LDP_X29_X30_POST16 = 0xA8C17BFD  # ldp x29, x30, [sp], #16

RET = 0xD65F03C0  # ret

SVC_0 = 0xD4000001  # svc #0
CMP_W0_0 = 0x7100001F  # cmp w0, #0
MOV_W0_WZR = 0x2A1F03E0  # mov w0, wzr
MOV_W1_W0 = 0x2A0003E1  # mov w1, w0
MOV_W2_0x40 = 0x52800802  # mov w2, #0x40
MOV_W2_WZR = 0x2A1F03E2  # mov w2, wzr
MOV_X0_X19 = 0xAA1303E0  # mov x0, x19
MOVN_W0_AT_FDCWD = 0x12800C60  # movn w0, #99 (→ -100 = AT_FDCWD)
SUB_X2_X29_0x50 = 0xD10143A2  # sub x2, x29, #0x50

MOV_W1_C000C = 0x320E87E1  # mov w1, #0xc000c


def strb_w8_sp(imm12: int) -> int:
    """Encode strb w8, [sp, #{imm12}] (unsigned 12-bit)."""
    return STRB_W8_SP | ((imm12 & 0xFFF) << 10)


def add_x1_sp(imm12: int) -> int:
    """Encode ADD X1, SP, #{imm12} (12-bit unsigned, LSL #0)."""
    return 0x910003E1 | ((imm12 & 0xFFF) << 10)


def movz(rd: int, value: int) -> bytes:
    """movz w{rd}, #{value} (16-bit immediate)."""
    word = 0x52800000 | ((value & 0xFFFF) << 5) | (rd & 0x1F)
    return w(word)


def movk(rd: int, value: int, shift: int = 0) -> bytes:
    """movk w{rd}, #{value}, lsl #{shift*16} (shift=0..3)."""
    word = 0x72800000 | ((value & 0xFFFF) << 5) | ((shift & 3) << 21) | (rd & 0x1F)
    return w(word)


def movz_w8(value: int) -> bytes:
    return movz(8, value)


def movk_w8(value: int, shift: int = 0) -> bytes:
    return movk(8, value, shift)


def movz_w1(value: int) -> bytes:
    return movz(1, value)


def movk_w1(value: int, shift: int = 0) -> bytes:
    return movk(1, value, shift)


def encode_branch(from_va: int, to_va: int, link: bool = False) -> bytes:
    """Encode B (link=False) or BL (link=True) as 4 LE bytes."""
    offset = (to_va - from_va) // 4
    if offset < -(1 << 25) or offset >= (1 << 25):
        raise ValueError(
            f"Branch out of range: 0x{from_va:x} → 0x{to_va:x} "
            f"(offset {offset:+d}, limit ±{1 << 25})"
        )
    imm26 = offset & 0x3FFFFFF
    opcode = 0x94000000 if link else 0x14000000
    return w(opcode | imm26)


def encode_bl(from_va: int, to_va: int) -> bytes:
    return encode_branch(from_va, to_va, link=True)


def encode_bcc(at_va: int, target_va: int, cond: int) -> bytes:
    """B.cond with condition code 0-15 (EQ=0, NE=1, GE=0xA, LT=0xB, etc.)."""
    offset_insns = (target_va - at_va) // 4
    return w(0x54000000 | ((offset_insns & 0x7FFFF) << 5) | (cond & 0xF))


def encode_beq(at_va: int, target_va: int) -> bytes:
    return encode_bcc(at_va, target_va, 0)


def encode_bge(at_va: int, target_va: int) -> bytes:
    return encode_bcc(at_va, target_va, 0xA)


def encode_cbnz(at_va: int, target_va: int, rd: int = 0) -> bytes:
    """cbnz w{rd}, target."""
    offset_insns = (target_va - at_va) // 4
    return w(0x35000000 | ((offset_insns & 0x3FFFF) << 5) | (rd & 0x1F))


def encode_cbz(at_va: int, target_va: int, rd: int = 12) -> bytes:
    """cbz w{rd}, target."""
    offset_insns = (target_va - at_va) // 4
    return w(0x34000000 | ((offset_insns & 0x3FFFF) << 5) | (rd & 0x1F))


def encode_add_imm(dest: int, src: int, imm12: int) -> bytes:
    """ADD X{dest}, X{src}, #{imm12} (64-bit, LSL #0)."""
    return w(0x91000000 | ((imm12 & 0xFFF) << 10) | ((src & 0x1F) << 5) | (dest & 0x1F))


def encode_subs_imm(dest: int, src: int, imm12: int) -> bytes:
    """SUBS W{dest}, W{src}, #{imm12} (32-bit)."""
    return w(0x71000000 | ((imm12 & 0xFFF) << 10) | ((src & 0x1F) << 5) | (dest & 0x1F))


def encode_movz(rd: int, value: int) -> bytes:
    """MOVZ W{rd}, #{value} (16-bit immediate)."""
    return w(0x52800000 | ((value & 0xFFFF) << 5) | (rd & 0x1F))


def encode_movk(rd: int, value: int, shift: int = 0) -> bytes:
    """MOVK W{rd}, #{value}, LSL #{shift*16} (shift=0..3)."""
    return w(0x72800000 | ((value & 0xFFFF) << 5) | ((shift & 3) << 21) | (rd & 0x1F))


def encode_ldrb_offset(rt: int, rn: int, imm12: int = 0) -> bytes:
    """LDRB W{rt}, [X{rn}, #{imm12}] (unsigned offset)."""
    return w(0x39400000 | ((imm12 & 0xFFF) << 10) | ((rn & 0x1F) << 5) | (rt & 0x1F))


def encode_ldr_offset(rt: int, rn: int, imm12: int) -> bytes:
    """LDR X{rt}, [X{rn}, #{imm12}] (64-bit unsigned offset)."""
    return w(0xF9400000 | ((imm12 & 0xFFF) << 10) | ((rn & 0x1F) << 5) | (rt & 0x1F))


def encode_str_offset(rt: int, rn: int, imm12: int) -> bytes:
    """STR X{rt}, [X{rn}, #{imm12}] (64-bit unsigned offset)."""
    return w(0xF9000000 | ((imm12 & 0xFFF) << 10) | ((rn & 0x1F) << 5) | (rt & 0x1F))


def encode_strb_offset(rt: int, rn: int, imm12: int) -> bytes:
    """STRB W{rt}, [SP, #{imm12}]."""
    return w(0x39000000 | ((imm12 & 0xFFF) << 10) | ((rn & 0x1F) << 5) | (rt & 0x1F))


def encode_sub_imm(dest: int, src: int, imm12: int) -> bytes:
    """SUB X{dest}, X{src}, #{imm12} (64-bit)."""
    return w(0xD1000000 | ((imm12 & 0xFFF) << 10) | ((src & 0x1F) << 5) | (dest & 0x1F))


def encode_adr(at_va: int, target_va: int, rd: int = 0) -> bytes:
    """adr x{rd}, target (pc-relative, ±1MB)."""
    offset = target_va - at_va
    immlo = (offset >> 0) & 3
    immhi = (offset >> 2) & 0x7FFFF
    return w(0x10000000 | (immlo << 29) | (immhi << 5) | rd)


def decode_movz_w8(b: bytes) -> Optional[int]:
    """If bytes are movz w8, #N return N, else None."""
    if len(b) < 4:
        return None
    word = struct.unpack("<I", b[:4])[0]
    if (word & 0xFFE0001F) == MOVZ_W8_BASE:
        return (word >> 5) & 0xFFFF
    return None


def decode_branch_target(data: bytes, file_off: int, image: ElfImage) -> Optional[int]:
    """Decode B or BL at file_off; return target VA or None."""
    word = struct.unpack_from("<I", data, file_off)[0]
    opcode = word >> 26
    if opcode not in (0b000101, 0b100101):
        return None
    imm26 = word & 0x3FFFFFF
    if imm26 & (1 << 25):
        imm26 -= 1 << 26
    from_va = image.offset_to_va(file_off)
    if from_va is None:
        return None
    return from_va + imm26 * 4


def decode_exact_bl(data: bytes, file_off: int, image: ElfImage) -> Optional[int]:
    """Decode BL at file_off; return target VA or None."""
    word = struct.unpack_from("<I", data, file_off)[0]
    if word >> 26 != 0b100101:
        return None
    return decode_branch_target(data, file_off, image)


def is_nop(data: bytes, offset: int) -> bool:
    """Check for AArch64 NOP (d503201f)."""
    return read_word(data, offset) == 0xD503201F


STP_X29_X30_BYTES = w(STP_X29_X30_PRE16)
LDP_X29_X30_BYTES = w(LDP_X29_X30_POST16)
SUB_X0_X29_0x50_BYTES = w(SUB_X0_X29_0x50)
ADD_X1_SP_0x10_BYTES = w(ADD_X1_SP_0x10)
RET_BYTES = w(RET)
