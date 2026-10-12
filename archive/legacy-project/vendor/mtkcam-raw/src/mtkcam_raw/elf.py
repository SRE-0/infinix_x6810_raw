# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
ELF64 parsing — program headers, sections, dynamic symbols, VA translation.
"""

# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from __future__ import annotations

import struct
import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProgramHeader:
    index: int
    p_type: int
    p_flags: int
    p_offset: int
    p_vaddr: int
    p_paddr: int
    p_filesz: int
    p_memsz: int
    p_align: int

    @property
    def is_load(self) -> bool:
        return self.p_type == 1

    @property
    def is_executable(self) -> bool:
        return bool(self.p_flags & 1)

    @property
    def flags_str(self) -> str:
        s = ""
        if self.p_flags & 4:
            s += "R"
        if self.p_flags & 2:
            s += "W"
        if self.p_flags & 1:
            s += "E"
        return s


@dataclass
class Section:
    name: str
    sh_type: int
    flags: int
    addr: int
    offset: int
    size: int
    link: int
    entsize: int

    @property
    def is_executable(self) -> bool:
        return bool(self.flags & 4)

    @property
    def is_allocated(self) -> bool:
        return bool(self.flags & 2)


@dataclass
class Symbol:
    name: str
    value: int
    size: int
    info: int

    @property
    def is_function(self) -> bool:
        stt_func = 0x02
        return (self.info & 0x0F) == stt_func


@dataclass
class ElfImage:
    data: bytes = field(repr=False)
    sha256: str = ""
    phdrs: list[ProgramHeader] = field(default_factory=list)
    sections: dict[str, Section] = field(default_factory=dict)
    symbols: list[Symbol] = field(default_factory=list)

    def va_to_offset(self, va: int) -> Optional[int]:
        for ph in self.phdrs:
            if not ph.is_load:
                continue
            if ph.p_vaddr <= va < ph.p_vaddr + ph.p_filesz:
                return va - ph.p_vaddr + ph.p_offset
        return None

    def offset_to_va(self, file_off: int) -> Optional[int]:
        for ph in self.phdrs:
            if not ph.is_load:
                continue
            if ph.p_offset <= file_off < ph.p_offset + ph.p_filesz:
                return file_off - ph.p_offset + ph.p_vaddr
        return None

    @property
    def load_segments(self) -> list[ProgramHeader]:
        return [ph for ph in self.phdrs if ph.is_load]

    @property
    def executable_load(self) -> Optional[ProgramHeader]:
        for ph in self.phdrs:
            if ph.is_load and ph.is_executable:
                return ph
        return None

    def find_symbols(self, prefix: str = "") -> list[Symbol]:
        if not prefix:
            return list(self.symbols)
        return [s for s in self.symbols if s.name.startswith(prefix)]

    def check_bind_now(self) -> bool:
        DF_BIND_NOW = 0x8
        DF_1_NOW = 0x1
        for ph in self.phdrs:
            if ph.p_type != 2:
                continue
            i = 0
            while i + 16 <= ph.p_filesz:
                d_tag = struct.unpack_from("<q", self.data, ph.p_offset + i)[0]
                d_val = struct.unpack_from("<Q", self.data, ph.p_offset + i + 8)[0]
                if d_tag == 0x1E:
                    if d_val & DF_BIND_NOW:
                        return True
                elif d_tag == 0x6FFFFFFB:
                    if d_val & DF_1_NOW:
                        return True
                elif d_tag == 0:
                    break
                i += 16
        return False


class PT_DYNAMIC_TAGS:
    DT_NULL = 0
    DT_NEEDED = 1
    DT_STRTAB = 5
    DT_SYMTAB = 6
    DT_INIT = 12
    DT_FINI = 13
    DT_FLAGS = 30
    DT_FLAGS_1 = 0x6FFFFFFB
    DT_INIT_ARRAY = 25
    DT_INIT_ARRAYSZ = 27


def read_u64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def read_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def read_u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def parse_elf(data: bytes) -> ElfImage:
    if data[:4] != b"\x7fELF":
        raise ValueError("Not an ELF file")

    ei_class = data[4]
    if ei_class != 2:
        raise ValueError("Only 64-bit ELF is supported")

    e_phoff = read_u64(data, 0x20)
    e_phentsize = read_u16(data, 0x36)
    e_phnum = read_u16(data, 0x38)
    e_shoff = read_u64(data, 0x28)
    e_shentsize = read_u16(data, 0x3A)
    e_shnum = read_u16(data, 0x3C)
    e_shstrndx = read_u16(data, 0x3E)

    image = ElfImage(
        data=data,
        sha256=hashlib.sha256(data).hexdigest(),
    )

    # Program headers
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        ph = ProgramHeader(
            index=i,
            p_type=read_u32(data, off),
            p_flags=read_u32(data, off + 4),
            p_offset=read_u64(data, off + 8),
            p_vaddr=read_u64(data, off + 16),
            p_paddr=read_u64(data, off + 24),
            p_filesz=read_u64(data, off + 32),
            p_memsz=read_u64(data, off + 40),
            p_align=read_u64(data, off + 48),
        )
        image.phdrs.append(ph)

    # Section headers
    sections_raw = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sections_raw.append(
            {
                "name_idx": read_u32(data, off),
                "type": read_u32(data, off + 4),
                "flags": read_u64(data, off + 8),
                "addr": read_u64(data, off + 16),
                "offset": read_u64(data, off + 24),
                "size": read_u64(data, off + 32),
                "link": read_u32(data, off + 40),
                "entsize": read_u64(data, off + 56),
            }
        )

    shstrtab_off: Optional[int] = None
    if e_shstrndx < len(sections_raw):
        shstrtab_off = sections_raw[e_shstrndx]["offset"]

    def section_name(sr: dict) -> str:
        if shstrtab_off is None:
            return ""
        idx = sr["name_idx"]
        end = data.index(b"\x00", shstrtab_off + idx)
        return data[shstrtab_off + idx : end].decode("utf-8", errors="replace")

    dynsym_sr = None
    dynstr_sr = None
    for sr in sections_raw:
        name = section_name(sr)
        sec = Section(
            name=name,
            sh_type=sr["type"],
            flags=sr["flags"],
            addr=sr["addr"],
            offset=sr["offset"],
            size=sr["size"],
            link=sr["link"],
            entsize=sr["entsize"],
        )
        image.sections[name] = sec
        if name == ".dynsym":
            dynsym_sr = sr
        elif name == ".dynstr":
            dynstr_sr = sr

    # Dynamic symbols
    if dynsym_sr and dynstr_sr:
        sym_data = data[
            dynsym_sr["offset"] : dynsym_sr["offset"] + dynsym_sr["size"]
        ]
        str_data = data[
            dynstr_sr["offset"] : dynstr_sr["offset"] + dynstr_sr["size"]
        ]
        entsize = dynsym_sr["entsize"] or 24
        for i in range(0, len(sym_data), entsize):
            if i + entsize > len(sym_data):
                break
            st_name = read_u32(sym_data, i)
            st_value = read_u64(sym_data, i + 8)
            st_size = read_u64(sym_data, i + 16)
            if st_value == 0:
                continue
            end = str_data.index(b"\x00", st_name)
            name = str_data[st_name:end].decode("utf-8", errors="replace")
            image.symbols.append(
                Symbol(name=name, value=st_value, size=st_size, info=sym_data[i + 4])
            )

    return image
