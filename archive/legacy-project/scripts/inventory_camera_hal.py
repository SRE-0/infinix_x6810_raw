"""Inventory extracted camera ELF files without modifying them."""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/mtkcam-raw/src'))
from mtkcam_raw.elf import parse_elf

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    inventory = []
    for path in sorted(args.directory.glob('*.so')):
        elf = parse_elf(path.read_bytes())
        strings = [m.group().decode('ascii') for m in re.finditer(rb'[ -~]{5,}', elf.data)]
        symbols = [dict(name=s.name, address=hex(s.value), size=s.size) for s in elf.symbols]
        (args.output / (path.name + '.strings.txt')).write_text('\n'.join(strings), encoding='utf-8')
        (args.output / (path.name + '.symbols.json')).write_text(json.dumps(symbols, indent=2), encoding='utf-8')
        inventory.append(dict(file=path.name, size=len(elf.data), sha256=elf.sha256,
                              symbols=len(symbols), properties=sorted(set(s for s in strings if
                              re.match(r'^(vendor\.|persist\.|debug\.|ro\.)', s)))))
    (args.output / 'inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    print(f'Inventoried {len(inventory)} libraries')

if __name__ == '__main__':
    main()
