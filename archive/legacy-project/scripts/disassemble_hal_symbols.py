"""Disassemble functions selected by a symbol-name regular expression."""
import argparse
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/mtkcam-raw/src'))
from mtkcam_raw.elf import parse_elf
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('binary', type=Path)
p.add_argument('pattern')
args = p.parse_args()
elf = parse_elf(args.binary.read_bytes())
md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
for symbol in elf.symbols:
    if not symbol.is_function or not symbol.size or not re.search(args.pattern, symbol.name): continue
    offset = elf.va_to_offset(symbol.value)
    if offset is None: continue
    print('\n' + symbol.name + ' @ ' + hex(symbol.value))
    for ins in md.disasm(elf.data[offset:offset+symbol.size], symbol.value):
        print(f'{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}')
