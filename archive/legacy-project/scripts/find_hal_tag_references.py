"""Find AArch64 materializations of a vendor tag (candidate references, not proof of use)."""
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/mtkcam-raw/src'))
from mtkcam_raw.elf import parse_elf
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('binary', type=Path)
p.add_argument('tag', type=lambda s:int(s,0))
a=p.parse_args(); elf=parse_elf(a.binary.read_bytes())
md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
for section in elf.sections.values():
    if not section.is_executable: continue
    instructions=list(md.disasm(elf.data[section.offset:section.offset+section.size],section.addr))
    for index,ins in enumerate(instructions):
        if ins.mnemonic != 'mov' or not ins.op_str.endswith(', #'+hex(a.tag & 65535)): continue
        reg=ins.op_str.split(',')[0]
        if not any(x.mnemonic=='movk' and x.op_str==f'{reg}, #{hex(a.tag >> 16)}, lsl #16' for x in instructions[index+1:index+8]):continue
        owners=[s.name for s in elf.symbols if s.is_function and s.value<=ins.address<s.value+s.size]
        print(hex(ins.address),owners)
        for x in instructions[max(0,index-5):index+15]:print(f'{x.address:08x} {x.mnemonic} {x.op_str}')
