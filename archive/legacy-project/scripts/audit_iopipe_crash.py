"""Read-only audit of the exact iopipe crash site using the project's Python runtime."""
import json
from analyze_binaries import ROOT, parse_elf, md
from emulate_metadata import plt_symbols

out = ROOT / 'dist/analysis/iopipe-20260919'
out.mkdir(parents=True, exist_ok=True)
a = parse_elf((ROOT / 'stock-binaries/libcam.iopipe.so').read_bytes())
sec = a.sections['.note.gnu.build-id']
build_id = a.data[sec.offset + 16:sec.offset + sec.size].hex()
symbol = next(s for s in a.symbols if s.is_function and s.value <= 0x740c8 < s.value+s.size)
names = {s.value: s.name for s in a.symbols}
names.update(plt_symbols(a))
offset = a.va_to_offset(symbol.value)
instructions = list(md.disasm(a.data[offset:offset+symbol.size], symbol.value))
lines = []
for i in instructions:
    annotation = ''
    if i.mnemonic in ('bl', 'b') and i.op_str.startswith('#0x'):
        annotation = names.get(int(i.op_str[1:], 16), '')
    lines.append(f'{i.address:08x} [{a.va_to_offset(i.address):08x}] {i.bytes.hex()} {i.mnemonic:8s} {i.op_str} {annotation}')
(out/'dequeResponse.asm.txt').write_text('\n'.join(lines), encoding='utf-8')
crash = next(i for i in instructions if i.address == 0x740c8)
result = dict(sha256=a.sha256, bytes=len(a.data), build_id=build_id,
              matches_crash_build=build_id == '90499f346947a4195ab3e342bcc25b4b',
              symbol=symbol.name, start=hex(symbol.value), size=symbol.size,
              fault_instruction=f'{crash.mnemonic} {crash.op_str}',
              crash_registers={'x9':'0x3', 'x20':'0xb40000710cde8f10'},
              effective_address=hex(3+0x148),
              source_log='logs/18_09-15-41-06_951.log',
              interpretation='Invalid virtual-dispatch table pointer; object register is non-null. Origin of invalid contents is not established.')
(out/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
