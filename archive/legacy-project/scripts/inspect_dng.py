"""Inspect TIFF/DNG metadata with the standard library; no pixel authenticity claim."""
import argparse, json, struct
from pathlib import Path

TAGS={256:'ImageWidth',257:'ImageLength',258:'BitsPerSample',259:'Compression',262:'PhotometricInterpretation',277:'SamplesPerPixel',33421:'CFARepeatPatternDim',33422:'CFAPattern',50706:'DNGVersion',50710:'CFAPlaneColor',50713:'BlackLevelRepeatDim',50714:'BlackLevel',50717:'WhiteLevel',50721:'ColorMatrix1',50722:'ColorMatrix2',50728:'AsShotNeutral',50829:'ActiveArea',50719:'DefaultCropOrigin',50720:'DefaultCropSize'}
SIZES={1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8,13:4}

def inspect(path):
    data=Path(path).read_bytes()
    if data[:2] not in (b'II',b'MM'): raise ValueError('Not a TIFF/DNG file')
    order='<' if data[:2]==b'II' else '>'
    def read(fmt,off): return struct.unpack_from(order+fmt,data,off)
    if read('H',2)[0]!=42: raise ValueError('Only classic TIFF is supported, not BigTIFF')
    pending=[read('I',4)[0]]; seen=set(); ifds=[]
    while pending:
        off=pending.pop(0)
        if not off or off in seen: continue
        if len(seen)>=128: raise ValueError('Too many TIFF IFDs')
        seen.add(off); n=read('H',off)[0]
        if n>4096 or off+2+12*n+4>len(data): raise ValueError('Invalid IFD bounds')
        row={'ifd_offset':off,'tags':{}}
        for j in range(n):
            p=off+2+12*j; tag,kind,count=read('HHI',p)
            if tag not in TAGS and tag!=330: continue
            size=SIZES.get(kind,0)*count
            if not size or size>1024*1024: continue
            loc=p+8 if size<=4 else read('I',p+8)[0]
            if loc+size>len(data): raise ValueError('Tag outside file')
            if kind in (1,2,6,7): val=list(data[loc:loc+size])
            elif kind in (3,4,8,9,11,12,13):
                fmt={3:'H',4:'I',8:'h',9:'i',11:'f',12:'d',13:'I'}[kind]
                val=list(read(fmt*count,loc))
            elif kind in (5,10):
                vals=read(('I' if kind==5 else 'i')*(count*2),loc)
                val=[f'{vals[i]}/{vals[i+1]}' for i in range(0,len(vals),2)]
            else: continue
            if tag==330: pending.extend(val)
            else: row['tags'][TAGS[tag]]=val
        pending.append(read('I',off+2+n*12)[0]); ifds.append(row)
    cfa=any(r['tags'].get('PhotometricInterpretation')==[32803] for r in ifds)
    linear=any(r['tags'].get('PhotometricInterpretation')==[34892] for r in ifds)
    return dict(file=str(path),size=len(data),ifds=ifds,cfa_ifd_present=cfa,linear_raw_ifd_present=linear,conclusion='Metadata only. CFA tags do not prove sensor provenance; LinearRaw can be a valid processed DNG. Inspect pixel planes and capture results.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('file');args=p.parse_args()
    print(json.dumps(inspect(args.file),indent=2))
