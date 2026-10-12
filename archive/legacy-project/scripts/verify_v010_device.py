"""Verify published maxima, durations, unchanged other cameras and actual captures."""
from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'dist/analysis/session-20260924-v010'
def read(name):
    text=(P/name).read_text();result={}
    parts=re.split(r'(?m)^== Camera HAL device device@3\.6/internal/(\d+) \(v3\.6\) static information: ==\s*$',text)
    for i in range(1,len(parts),2):
        block=parts[i+1].split('## Camera device')[0]
        result[parts[i]]={m.group(1):m.group(2).strip() for m in re.finditer(r'(?m)^      ([\w.]+) (\([^\n]+\n(?:        [^\n]*\n)*)',block)}
    return result
def tuples(value):
    body=value.split('\n',1)[1].replace('OUTPUT','0').replace('INPUT','1')
    values=[int(x) for x in re.findall(r'-?\d+',body)]
    assert len(values)%4==0
    return [values[i:i+4] for i in range(0,len(values),4)]
before,after=read('camera-before.txt'),read('camera-trial.txt')
changes={}
for id in before:
    changes[id]={k:dict(before=before[id].get(k),after=after[id].get(k)) for k in before[id].keys()|after[id].keys() if before[id].get(k)!=after[id].get(k)}
    if id!='1':assert not changes[id],(id,changes[id])
assert set(changes['1'])<=set('android.jpeg.maxSize android.scaler.availableStreamConfigurations android.scaler.availableMinFrameDurations android.scaler.availableStallDurations'.split()),changes['1'].keys()
old_jpeg=int(re.findall(r'\[(\d+) ',before['1']['android.jpeg.maxSize'])[0])
new_jpeg=int(re.findall(r'\[(\d+) ',after['1']['android.jpeg.maxSize'])[0])
assert new_jpeg>old_jpeg
for photo in (P/'probe').glob('*.jpg'):assert photo.stat().st_size<=new_jpeg
front=after['1'];streams=tuples(front['android.scaler.availableStreamConfigurations'])
formats=sorted({s[0] for s in streams if s[3]==0})
assert formats==[32,33,34,35,842094169],formats
for fmt in formats:
    entries=[s for s in streams if s[0]==fmt and s[3]==0]
    assert [fmt,2320,1744,0] in entries
    assert all(s[1]<=2320 and s[2]<=1744 for s in entries)
    for tag in ('android.scaler.availableMinFrameDurations','android.scaler.availableStallDurations'):
        assert any(s[:3]==[fmt,2320,1744] for s in tuples(front[tag])),(fmt,tag)
for fmt in (34,35):assert [fmt,2320,1744,1] in streams
tests=[]
for label in [f'camera1-in{fmt}-out{out}' for fmt in (34,35) for out in (35,256)]+[f'camera1-direct{fmt}' for fmt in (32,34,35,256,842094169)]:
    text=(P/'probe'/f'{label}.txt').read_text()
    assert f'PASS {label}' in text and '2320x1744' in text and 'FAIL' not in text,label
    tests.append(dict(case=label,passed=True))
report=dict(static_changes=changes,other_camera_metadata_identical=True,max_size=[2320,1744],output_formats=formats,tests=tests,
    note='YV12 requested via ImageReader returns format=35 with planar Y/U/V; PRIVATE image has no CPU-accessible planes')
(ROOT/'dist/verification/front-v0.10-device.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: all five formats max 2320x1744, durations and both inputs; nine capture paths; other five cameras unchanged.')
print('Front changed tags:',list(changes['1']))
