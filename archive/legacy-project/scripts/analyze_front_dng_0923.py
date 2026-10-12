"""Decode supplied and new DNGs; compare spatial CFA phases, preserve originals."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'local-data/tools/imaging'))
import numpy as np
import rawpy
from PIL import Image
OUT=ROOT/'dist/analysis/session-20260923'
rows=[]
for p in [*sorted((ROOT/'logs').glob('*.dng')),*sorted(OUT.glob('PXL*.dng'))]:
    with rawpy.imread(str(p)) as raw:
        a=raw.raw_image_visible.copy()
        phases=[[float(a[y::4,x::4].mean()) for x in range(4)] for y in range(4)]
        rgb=raw.postprocess(use_camera_wb=True)
        dest=OUT/(p.stem+'-libraw.jpg')
        Image.fromarray(rgb).save(dest,quality=95)
        rows.append(dict(file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            size=list(a.shape),pattern=raw.raw_pattern.tolist(),phases_4x4=phases,
            black=raw.black_level_per_channel,white=raw.white_level,
            camera_whitebalance=raw.camera_whitebalance,rgb_xyz_matrix=raw.rgb_xyz_matrix.tolist(),
            percentiles=np.percentile(a,[0,1,50,99,100]).tolist(),
            warning='GCam-exported RAW may include fusion, scaling or cropping; not a direct HAL dump',
            render=str(dest.relative_to(ROOT))))
(OUT/'dng-analysis.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows,indent=2))
