"""Compare actual HAL static tags and validate four on-device reprocessing results."""
from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'dist/analysis/session-20260924'
def read(name):
    text=(P/name).read_text()
    result={}
    parts=re.split(r'(?m)^== Camera HAL device device@3\.6/internal/(\d+) \(v3\.6\) static information: ==\s*$',text)
    for i in range(1,len(parts),2):
        block=parts[i+1].split('## Camera device')[0]
        tags={m.group(1):m.group(2).strip() for m in re.finditer(r'(?m)^      ([\w.]+) (\([^\n]+\n(?:        [^\n]*\n)*)',block)}
        result[parts[i]]=tags
    return result
before,after=read('camera-before.txt'),read('camera-v09.txt')
changes={}
for id in before:
    changes[id]={k:dict(before=before[id].get(k),after=after[id].get(k)) for k in before[id].keys()|after[id].keys() if before[id].get(k)!=after[id].get(k)}
    if id!='1':assert not changes[id],(id,changes[id])
front=after['1']
for word in ('RAW','PRIVATE_REPROCESSING','YUV_REPROCESSING'):assert word in front['android.request.availableCapabilities']
assert '[1 ]' in front['android.request.maxNumInputStreams']
assert '[34 2 35 33 ]' in front['android.scaler.availableInputOutputFormatsMap']
assert '[35 2 35 33 ]' in front['android.scaler.availableInputOutputFormatsMap']
assert '[34 1968 864 INPUT ]' in front['android.scaler.availableStreamConfigurations']
assert '[35 1968 864 INPUT ]' in front['android.scaler.availableStreamConfigurations']
tests=[]
for fmt in (34,35):
    for out in (35,256):
        label=f'camera1-in{fmt}-out{out}'
        text=(P/'probe'/f'{label}.txt').read_text()
        assert f'PASS {label}' in text and 'FAIL' not in text
        tests.append(dict(case=label,passed=True,evidence=str((P/'probe'/f'{label}.txt').relative_to(ROOT))))
report=dict(static_changes=changes,other_camera_tags_identical=True,input_size=[1968,864],functional_tests=tests,
    limitation='Four single-frame paths at the advertised input size, not all mandatory stream combinations or CTS certification')
(ROOT/'dist/verification/front-v0.9-device.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: other five camera metadata sets identical; four real reprocess paths. Front changed tags:')
print('\n'.join(changes['1']))
