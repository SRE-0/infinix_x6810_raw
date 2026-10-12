"""Read-only follow-up: donor HI1631Q stages, RAW16 calls and ELF mappings.

Writes dist/analysis/front-followup-20260916 only. Does not build modules
or access a phone. Calls through vtables remain unresolved in this audit.
"""
import json
from analyze_binaries import ROOT, parse_elf, md
from inspect_debugdata import all_symbols
from emulate_metadata import emulate, plt_symbols

OUT = ROOT / 'dist/analysis/front-followup-20260916'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    stages = []
    for p in [ROOT / 'stock-binaries/libmtkcam_metastore.so',
              *sorted((ROOT / 'local-data/reference-modules').rglob('libmtkcam_metastore.so'))]:
        a = parse_elf(p.read_bytes())
        for s in a.symbols:
            if s.is_function and s.name.startswith('constructCustStaticMetadata_') and s.name.endswith('SENSOR_DRVNAME_HI1631Q_MIPI_RAW'):
                e = emulate(a, s, True)
                stages.append(dict(path=str(p.relative_to(ROOT)), sha256=a.sha256,
                    symbol=s.name, va=hex(s.value), size=s.size,
                    error=e['error'], metadata=e['metadata']))
    (OUT / 'donor-front-stages.json').write_text(json.dumps(stages, indent=2), encoding='utf-8')

    mappings = []
    for rel in ['stock-binaries/libmtkcam_pipelinepolicy.so',
                'patches/front-v0.7/libmtkcam_pipelinepolicy.so']:
        a = parse_elf((ROOT / rel).read_bytes())
        segments = [dict(offset=hex(s.p_offset), va=hex(s.p_vaddr),
            file_end=hex(s.p_offset+s.p_filesz), memory_end=hex(s.p_vaddr+s.p_memsz),
            flags=s.p_flags, page4k_start=hex(s.p_vaddr & ~4095),
            page4k_end=hex((s.p_vaddr+s.p_memsz+4095) & ~4095)) for s in a.load_segments]
        mappings.append(dict(path=rel, sha256=a.sha256, segments=segments))
    (OUT / 'policy-mappings.json').write_text(json.dumps(mappings, indent=2), encoding='utf-8')

    a = parse_elf((ROOT / 'local-data/device/libs/libmtkcam_hwnode.so').read_bytes())
    symbols = all_symbols(a)
    names = {s.value:s.name for s in symbols if s.is_function}
    names.update(plt_symbols(a))
    functions = []
    for s in symbols:
        if not s.is_function or not s.name.startswith('_ZN12RAW16NodeImp'):
            continue
        if not any(t in s.name for t in ['onProcessFrame', 'unpackRaw10', 'updateDNGMeta']):
            continue
        off = a.va_to_offset(s.value)
        lines = [s.name, f'VA={s.value:#x} size={s.size} sha256={a.sha256}']
        calls = []
        for i in md.disasm(a.data[off:off+s.size], s.value):
            note = ''
            if i.mnemonic in ('bl', 'b') and i.op_str.startswith('#0x'):
                target = int(i.op_str[1:], 16)
                note = names.get(target, '')
                if i.mnemonic == 'bl':
                    calls.append(dict(va=hex(i.address), target=hex(target), symbol=note))
            lines.append(f'{i.address:08x} {i.bytes.hex():8s} {i.mnemonic:8s} {i.op_str}' + (' ; '+note if note else ''))
        label = next(t for t in ['onProcessFrame', 'unpackRaw10', 'updateDNGMeta'] if t in s.name)
        (OUT / (label+'.asm.txt')).write_text('\n'.join(lines)+'\n', encoding='utf-8')
        functions.append(dict(symbol=s.name, va=hex(s.value), size=s.size, calls=calls))
    (OUT / 'raw16-calls.json').write_text(json.dumps(functions, indent=2), encoding='utf-8')
    print(json.dumps(dict(donor_stages=len(stages), emulation_errors=[x['symbol'] for x in stages if x['error']],
        raw16_functions=len(functions), output=str(OUT)), indent=2))


if __name__ == '__main__':
    main()
