"""Read-only function and property comparison; donor stock binaries unavailable."""
from inspect_debugdata import all_symbols
from analyze_binaries import ROOT, OUT, parse_elf, disasm, md
from difflib import SequenceMatcher
import re
import json


def normalized(a,s):
    result=[];off=a.va_to_offset(s.value)
    for i in md.disasm(a.data[off:off+s.size],s.value):
        operands=i.op_str
        if i.mnemonic in ('bl','adr','adrp'):operands='ADDRESS'
        elif i.mnemonic.startswith('b') or i.mnemonic in ('cbz','cbnz','tbz','tbnz'):
            operands=re.sub(r'#0x[0-9a-f]+$','TARGET',operands)
        result.append(i.mnemonic+' '+operands)
    return result


def main():
    paths=[ROOT/'stock-binaries/libmtkcam_3rdparty.customer.so',
           *sorted((ROOT/'local-data/reference-modules').rglob('*customer.so'))]
    original=parse_elf(paths[0].read_bytes())
    stock_symbols={s.name:s for s in all_symbols(original) if s.is_function}
    rows=[]
    for p in paths:
        a=parse_elf(p.read_bytes());functions=[]
        for s in all_symbols(a):
            if not s.is_function or not ('9negotiateE' in s.name or 'customer_get_' in s.name):continue
            if 'Interceptor' in s.name or 'St3' in s.name:continue
            row=dict(name=s.name,va=hex(s.value),size=s.size,entry=disasm(a,s.value,min(16,s.size)))
            if s.name in stock_symbols:
                x=normalized(original,stock_symbols[s.name]);y=normalized(a,s)
                row['normalized_similarity']=SequenceMatcher(None,x,y,autojunk=False).ratio()
                row['normalized_equal']=x==y
            functions.append(row)
        rows.append(dict(path=str(p.relative_to(ROOT)),size=len(a.data),sha256=a.sha256,functions=functions,
            properties=sorted(set(m.group().decode() for m in re.finditer(rb'(?:persist\.)?vendor\.[A-Za-z0-9_.]+',a.data)))))
    report=dict(limitation='Cross-firmware comparison, not a stock/mod diff. Address normalization can hide changed calls or data references; equality is not semantic identity.',libraries=rows)
    (OUT/'customer-comparison-20260913.json').write_text(json.dumps(report,indent=2)+'\n')
    for r in rows:print(r['path'],r['size'],len(r['functions']),'functions')


if __name__=='__main__':main()
