"""Read-only ELF inventory, named disassembly and exact existing-module diff."""
from pathlib import Path
import sys, json, re, struct, hashlib
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/mtkcam-raw/src'))
from mtkcam_raw.elf import parse_elf
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
OUT = ROOT / 'dist/analysis'
OUT.mkdir(parents=True, exist_ok=True)
md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)

def disasm(img, start, size):
    off = img.va_to_offset(start)
    if off is None: return []
    return [f'{i.address:08x} [{img.va_to_offset(i.address):08x}] {i.bytes.hex():8s} {i.mnemonic:8s} {i.op_str}' for i in md.disasm(img.data[off:off+size], start)]

def inventory():
    result = []
    for folder in ('stock-binaries', 'local-data/reference-modules', 'modules'):
        for p in sorted((ROOT / folder).rglob('*.so')):
            img = parse_elf(p.read_bytes())
            key = str(p.relative_to(ROOT)).replace('\\', '__').replace('/', '__')
            symbols = [dict(name=s.name, va=hex(s.value), size=s.size) for s in img.symbols]
            (OUT / (key+'.symbols.json')).write_text(json.dumps(symbols,indent=2))
            strings = [m.group().decode('ascii') for m in re.finditer(rb'[ -~]{5,}',img.data)]
            (OUT/(key+'.strings.txt')).write_text('\n'.join(strings),encoding='utf-8')
            selected = [s for s in img.symbols if s.is_function and (any(x in s.name for x in ('updateRawCapability','updatePostRawSensitivityBoost','updateData','constructStaticMetadata','PRO_OVERWRITE','PLATFORM_PROJECT','negotiate','Remosaic','remosaic','property')))]
            lines=[]
            for s in selected:
                lines += ['\n'+s.name+f' size={s.size}'] + disasm(img,s.value,s.size)
            (OUT/(key+'.asm.txt')).write_text('\n'.join(lines),encoding='utf-8')
            result.append(dict(path=str(p.relative_to(ROOT)),size=len(img.data),sha256=img.sha256,machine=struct.unpack_from('<H',img.data,18)[0],symbols=len(symbols),segments=[vars(h) for h in img.load_segments]))
    (OUT/'inventory.json').write_text(json.dumps(result,indent=2))
    a=parse_elf((ROOT/'stock-binaries/libmtkcam_metastore.so').read_bytes())
    b=parse_elf((ROOT/'archive/modules/48mp+raw_KSU/system/vendor/lib64/libmtkcam_metastore.so').read_bytes())
    diffs=[i for i,(x,y) in enumerate(zip(a.data,b.data)) if x!=y]
    words=sorted(set(i//4*4 for i in diffs))
    rows=[]
    for off in words:
        va=a.offset_to_va(off)
        names=[s.name for s in a.symbols if s.is_function and va is not None and s.value<=va<s.value+s.size]
        rows.append(dict(offset=hex(off),va=hex(va) if va is not None else None,old=a.data[off:off+4].hex(),new=b.data[off:off+4].hex(),functions=names,before=disasm(a,va,4) if va is not None else [],after=disasm(b,va,4) if va is not None else []))
    (OUT/'existing-module-diff.json').write_text(json.dumps(dict(changed_bytes=len(diffs),words=rows),indent=2))
    print(json.dumps(dict(inventory=result,existing_module_changed_bytes=len(diffs),changed_instructions=rows),indent=2))

if __name__=='__main__': inventory()
