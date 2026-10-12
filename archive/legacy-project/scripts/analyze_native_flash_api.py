"""Locate native framework flash paths by string references and unwind entries."""
import argparse,bisect,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'dist/python-deps'),str(ROOT/'vendor/mtkcam-raw/src')]
from mtkcam_raw.elf import parse_elf
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('binary',type=Path);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();e=parse_elf(a.binary.read_bytes());a.output.mkdir(parents=True,exist_ok=True)
md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
targets={}
for m in re.finditer(rb'[ -~]{6,}\x00',e.data):
 if re.search(rb'HIDL does not support.*torch|fixupTorchStrength|TorchStrength|torch strength|torchStrength|flash strength|FlashStrength|VNDK filter|Vndk|vndk|MTK_FLASH_MODE',m.group()):
  va=e.offset_to_va(m.start())
  if va is not None:targets[va]=m.group()[:-1].decode()
starts=[]
if '.eh_frame_hdr' in e.sections:
 s=e.sections['.eh_frame_hdr'];data=e.data[s.offset:s.offset+s.size]
 if data[:4]==bytes([1,0x1b,3,0x3b]):
  count=struct.unpack_from('<I',data,8)[0]
  starts=[s.addr+struct.unpack_from('<i',data,12+8*i)[0] for i in range(count)]
refs=[]
for s in e.sections.values():
 if not s.is_executable:continue
 known={}
 for addr,size,mn,op in md.disasm_lite(e.data[s.offset:s.offset+s.size],s.addr):
  operands=op.split(', ');value=None
  if mn in ('adrp','adr') and len(operands)==2:
   value=int(operands[1][1:],16);known[operands[0]]=value
  elif mn=='add' and len(operands)==3 and operands[1] in known and operands[2].startswith('#'):
   value=known[operands[1]]+int(operands[2][1:],0);known[operands[0]]=value
  elif operands[0] in known and mn not in ('str','stp','cmp','tst','cbz','cbnz'):
   known.pop(operands[0],None)
  if value in targets:
   idx=bisect.bisect_right(starts,addr)-1
   refs.append(dict(reference=hex(addr),string=targets[value],string_va=hex(value),
                    function=hex(starts[idx]) if idx>=0 else None,
                    end=hex(starts[idx+1]) if 0<=idx<len(starts)-1 else None))
  if mn in ('bl','blr'):known={}
(a.output/'references.json').write_text(json.dumps(dict(sha256=e.sha256,segments=[vars(x) for x in e.load_segments],references=refs),indent=2))
with (a.output/'references.asm.txt').open('w') as f:
 for r in refs:
  addr=int(r['reference'],16);start=int(r['function'],16) if r['function'] else addr-64
  end=int(r['end'],16) if r['end'] else addr+100
  if end-start>1200:start=max(start,addr-96);end=min(end,addr+160)
  off=e.va_to_offset(start);f.write('\n'+str(r)+'\n')
  for va,size,mn,op in md.disasm_lite(e.data[off:off+end-start],start):f.write(f'{va:08x}: {mn:8} {op}\n')
print('Strings',len(targets),'references',len(refs),'unwind functions',len(starts))
