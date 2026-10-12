"""Recompute FPS from saved Camera3 frame counters, matching streams by format/size."""
from pathlib import Path
import re
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'dist/analysis/preview-native-20260924'
LABELS = ('baseline', 'max6', 'slot38-max6', 'rawcollection6',
          'rawcollection6-front', 'rawcollection6-tele',
          'v011-main', 'v011-front', 'v011-tele', 'restored-v010', 'boot-v011')


def parse(label, index):
    text = (OUT/f'{label}-t{index}.txt').read_text()
    streams = {}
    for block in re.split(r'Stream\[\d+\]: Output', text)[1:]:
        size = re.search(r'Dims: (\d+) x (\d+), format (0x[\da-f]+)', block)
        frame = re.search(r'Frames produced: (\d+), last timestamp: (\d+) ns', block)
        if not size or not frame:
            continue
        key = (int(size[1]), int(size[2]), size[3])
        assert key not in streams, 'Ambiguous streams with identical dimensions/format'
        streams[key] = dict(frames=int(frame[1]), timestamp=int(frame[2]),
                            max_hal_buffers=int(re.search(r'max HAL buffers: (\d+)', block)[1]))
    return text, streams


def main():
    results = []
    for label in LABELS:
        _, before = parse(label, 0)
        text, after = parse(label, 1)
        assert before.keys() == after.keys()
        rows = []
        for key, current in after.items():
            initial = before[key]
            dt = (current['timestamp']-initial['timestamp'])/1e9
            dn = current['frames']-initial['frames']
            assert dt >= 0 and dn >= 0
            rows.append(dict(size=list(key[:2]), format=key[2],
                             max_hal_buffers=current['max_hal_buffers'],
                             delta_frames=dn, delta_sensor_seconds=dt,
                             fps=dn/dt if dt > 0 else None))
        row = dict(label=label, streams=rows)
        for tag in ('exposureTime', 'frameDuration'):
            row[tag] = int(re.search(r'android.sensor.'+tag+r'[^\n]*\n\s*\[([\d ]+)', text)[1])
        results.append(row)
    (OUT/'measurements.json').write_text(json.dumps(results, indent=2)+'\n')
    for row in results:
        raw = next(x for x in row['streams'] if x['format'] == '0x20')
        print(f"{row['label']}: {raw['size']}, HAL={raw['max_hal_buffers']}, {raw['fps']:.4f} FPS")


if __name__ == '__main__':
    main()
