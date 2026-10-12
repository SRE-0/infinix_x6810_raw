"""Build hash-locked OV08A10 OIS candidate over v0.11. No device writes."""
import sys,json,struct,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'dist/python-deps'),str(ROOT/'vendor/mtkcam-raw/src')]
from build_raw_patch import parse_elf,plt_symbols,emulate,disasm,branch
from keystone import Ks,KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN
KS=Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN)
DEST=ROOT/'patches/v0.12-ois-trial'

def patch(source,expected,hook,assembly,label):
 a=parse_elf(source.read_bytes())
 if a.sha256!=expected:raise ValueError('Unexpected input SHA256: '+a.sha256)
 rx=a.executable_load;start=(rx.p_offset+rx.p_filesz+15)&~15
 assert rx.p_vaddr==rx.p_offset
 code=bytes(KS.asm(assembly,addr=start)[0]);end=start+len(code)
 assert not any(a.data[start:end])
 assert end<=min(h.p_offset for h in a.load_segments if h.p_offset>rx.p_offset)
 assert not any(s.size and s.offset<end and start<s.offset+s.size for s in a.sections.values())
 b=bytearray(a.data);changes=[]
 def change(off,new):
  changes.append(dict(offset=hex(off),old=b[off:off+len(new)].hex(),new=new.hex()));b[off:off+len(new)]=new
 change(hook,branch(hook,start));change(start,code)
 ph=struct.unpack_from('<Q',b,32)[0]+rx.index*struct.unpack_from('<H',b,54)[0]
 for field in (32,40):change(ph+field,struct.pack('<Q',end-rx.p_offset))
 out=parse_elf(bytes(b));assert len(a.data)==len(b)
 DEST.mkdir(parents=True,exist_ok=True);(DEST/source.name).write_bytes(b)
 (DEST/(label+'.asm.txt')).write_text(assembly+'\n\n'+'\n'.join(disasm(out,start,len(code))))
 manifest=dict(input_sha256=a.sha256,output_sha256=out.sha256,hook=hex(hook),cave_start=hex(start),cave_end=hex(end),changes=changes,hardware_validated=False)
 (DEST/(label+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
 return a,out,manifest

def main():
 msrc=ROOT/'archive/modules/x6810_raw_v011/system/vendor/lib64/libmtkcam_metastore.so';a=parse_elf(msrc.read_bytes());plt=plt_symbols(a)
 def sym(part):return next(k for k,v in plt.items() if part in v)
 assembly=f'''
 stp x19,x30,[sp,#-96]!
 mov x19,x0
 add x0,sp,#16
 mov w1,#3
 movk w1,#9,lsl #16
 bl {sym('IEntryC1Ej')}
 strb wzr,[sp,#80]
 add x0,sp,#16
 add x1,sp,#80
 bl {sym('IEntry9push_backERKh')}
 mov w8,#1
 strb w8,[sp,#80]
 add x0,sp,#16
 add x1,sp,#80
 bl {sym('IEntry9push_backERKh')}
 mov x0,x19
 mov w1,#3
 movk w1,#9,lsl #16
 add x2,sp,#16
 bl {sym('IMetadata6update')}
 mov w19,w0
 add x0,sp,#16
 bl {sym('IEntryD1Ev')}
 mov w0,w19
 ldp x19,x30,[sp],#96
 ret
 '''
 old,new,manifest=patch(msrc,'a05f038d7e638f597f751750cafc0e0c9d788be85588e52afbfeff9e583759d5',0x30800,assembly,'metadata')
 name='constructCustStaticMetadata_PLATFORM_PRO_OVERWRITE_SENSOR_DRVNAME_OV08A10_MIPI_RAW';s=next(s for s in old.symbols if s.name==name)
 result=emulate(new,s,True);assert result['error'] is None,result
 assert result['metadata']['0x90003']['values']==[0,1],result
 count=0
 for s in old.symbols:
  if s.name.startswith('constructCustStaticMetadata_PLATFORM_') and ('PROJECT_' in s.name or 'PRO_OVERWRITE_' in s.name) and s.name!=name:
   x,y=emulate(old,s,True),emulate(new,s,True);assert x==y and x['error'] is None,s.name;count+=1
 print('Unchanged constructors',count)
 # Non-stock-package fallback only. Standard Camera2 ON/OFF supersedes vendor defaults.
 # x20=Hal3AAdapter3, x21=app request metadata. SensorDev 4 is the verified telephoto.
 assembly='''
 ldr w8,[x20,#0x28]
 cmp w8,#4
 b.ne original
 sub sp,sp,#96
 stp x19,x30,[sp,#64]
 mov x8,sp
 mov x0,x21
 mov w1,#4
 movk w1,#8,lsl #16
 mov w2,wzr
 bl 0x2d06a0
 mov x0,sp
 bl 0x2d06c0
 cbnz w0,missing
 mov x0,sp
 mov w1,wzr
 bl 0x2d0720
 cmp w0,#1
 mov w19,#1
 b.ne read_done
 mov w19,#3
 b read_done
 missing:
 mov w19,#1
 read_done:
 mov x0,sp
 bl 0x2cfbb0
 ldr w8,[x20,#0x344]
 cmp w8,w19
 b.eq done
 ldr x0,[x20,#0xe0]
 cbz x0,done
 ldr w8,[x0,#8]
 tbnz w8,#31,done
 ldr w8,[x0,#0xc8]
 cmp w8,#1
 b.ne done
 cmp w19,#3
 mov w1,#2
 b.ne command
 mov w1,#1
 command:
 ldr x8,[x0]
 ldr x8,[x8,#0xb8]
 mov x2,xzr
 blr x8
 str w19,[x20,#0x344]
 done:
 ldp x19,x30,[sp,#64]
 add sp,sp,#96
 b 0x25cd74
 original:
 ldrb w8,[x20,#0xe8]
 b 0x25c9e4
 '''
 _,_,manifest=patch(ROOT/'stock-binaries/libcam.hal3a.v3.so','93ae38c9efcbfeffc0fe1e9a0c16c472a8b782f18b4a7fc01e32ca1e12ed2b0b',0x25c9e0,assembly,'control')
 print(json.dumps({k:v for k,v in manifest.items() if k!='changes'}))
if __name__=='__main__':main()
