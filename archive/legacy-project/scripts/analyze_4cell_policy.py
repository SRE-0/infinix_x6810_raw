"""Annotate MediaTek's stripped 4Cell sensor-setting policy.

This is a read-only reverse-engineering helper.  It recovers the mini debug
symbols from .gnu_debugdata and resolves simple AArch64 ADR/ADRP+ADD string
references inside the 4Cell policy function.
"""
from inspect_debugdata import all_symbols
from emulate_metadata import parse_elf, plt_symbols
from analyze_binaries import ROOT, OUT, md
import re


LIB = ROOT / "stock-binaries/libmtkcam_pipelinepolicy.so"
TARGET_4CELL = (
    "_ZZN5NSCam2v38pipeline6policy44"
    "makePolicy_Configuration_SensorSetting_4CellEvENK3$_4clERKNS2_"
    "34Configuration_SensorSetting_ParamsE"
)
TARGET_DEFAULT = (
    "_ZNSt3__110__function6__funcIZN5NSCam2v38pipeline6policy46"
    "makePolicy_Configuration_SensorSetting_DefaultEvE3$_4NS_9allocatorIS6_EEFiRKNS5_"
    "34Configuration_SensorSetting_ParamsEEEclESB_"
)


def c_string(data, off):
    if off is None or off < 0 or off >= len(data):
        return None
    end = data.find(b"\0", off, min(len(data), off + 512))
    if end < 0:
        return None
    raw = data[off:end]
    if len(raw) < 4 or any(c < 0x20 or c > 0x7e for c in raw):
        return None
    return raw.decode("ascii")


def main():
    image = parse_elf(LIB.read_bytes())
    symbols = {s.name: s for s in all_symbols(image)}
    plt = plt_symbols(image)
    for target, label in ((TARGET_4CELL, "4cell"), (TARGET_DEFAULT, "default")):
        symbol = symbols[target]
        off = image.va_to_offset(symbol.value)
        instructions = list(md.disasm(image.data[off:off + symbol.size], symbol.value))
        pages = {}
        lines = [f"{target} va={symbol.value:#x} size={symbol.size}"]
        for insn in instructions:
            comment = []
            ops = [x.strip() for x in insn.op_str.split(",")]
            if insn.mnemonic == "adrp" and len(ops) == 2:
                try:
                    pages[ops[0]] = int(ops[1].replace("#", ""), 0)
                except ValueError:
                    pass
            elif insn.mnemonic == "adr" and len(ops) == 2:
                try:
                    addr = int(ops[1].replace("#", ""), 0)
                    value = c_string(image.data, image.va_to_offset(addr))
                    if value:
                        comment.append(repr(value))
                except ValueError:
                    pass
            elif insn.mnemonic == "add" and len(ops) >= 3 and ops[1] in pages:
                try:
                    addr = pages[ops[1]] + int(ops[2].replace("#", ""), 0)
                    pages[ops[0]] = addr
                    value = c_string(image.data, image.va_to_offset(addr))
                    if value:
                        comment.append(f"{addr:#x} {value!r}")
                except ValueError:
                    pass
            if insn.mnemonic in ("bl", "b"):
                match = re.search(r"0x[0-9a-f]+", insn.op_str)
                if match:
                    dest = int(match.group(), 16)
                    if dest in plt:
                        comment.append(plt[dest])
                    else:
                        names = [s.name for s in symbols.values() if s.value == dest]
                        comment.extend(names[:1])
            suffix = " ; " + " | ".join(comment) if comment else ""
            lines.append(
                f"{insn.address:08x} [{image.va_to_offset(insn.address):08x}] "
                f"{insn.bytes.hex():8s} {insn.mnemonic:8s} {insn.op_str}{suffix}"
            )
        dest = OUT / f"libmtkcam_pipelinepolicy-{label}.annotated.asm.txt"
        dest.write_text("\n".join(lines), encoding="utf-8")
        print(dest)

    # Find the same diagnostic strings outside this one function.  MediaTek
    # splits 4Cell selection and RAW-type selection between policy units.
    interesting = (
        "raw.type", "P2ProcessRaw", "tran_checkis4cell", "Dng capturing",
        "processed-raw", "pure-raw", "add raw16", "is4Cell:",
    )
    functions = sorted(
        (s for s in symbols.values() if s.is_function and s.size),
        key=lambda s: s.value,
    )
    refs = []
    for section in image.sections.values():
        if section.name != ".text":
            continue
        code = image.data[section.offset:section.offset + section.size]
        pages = {}
        for insn in md.disasm(code, section.addr):
            ops = [x.strip() for x in insn.op_str.split(",")]
            addr = None
            if insn.mnemonic == "adrp" and len(ops) == 2:
                try:
                    pages[ops[0]] = int(ops[1].replace("#", ""), 0)
                except ValueError:
                    pass
            elif insn.mnemonic == "adr" and len(ops) == 2:
                try:
                    addr = int(ops[1].replace("#", ""), 0)
                except ValueError:
                    pass
            elif insn.mnemonic == "add" and len(ops) >= 3 and ops[1] in pages:
                try:
                    addr = pages[ops[1]] + int(ops[2].replace("#", ""), 0)
                    pages[ops[0]] = addr
                except ValueError:
                    pass
            value = c_string(image.data, image.va_to_offset(addr)) if addr is not None else None
            if value and any(term in value for term in interesting):
                owner = next((s.name for s in functions if s.value <= insn.address < s.value + s.size), "<unknown>")
                refs.append(f"{insn.address:#x}\t{owner}\t{value}")
    xdest = OUT / "libmtkcam_pipelinepolicy-raw-string-xrefs.txt"
    xdest.write_text("\n".join(refs), encoding="utf-8")
    print(xdest)


if __name__ == "__main__":
    main()
