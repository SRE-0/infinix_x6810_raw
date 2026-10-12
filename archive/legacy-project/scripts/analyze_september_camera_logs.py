"""Extract reproducible evidence from the September 18/19 attachments; no device writes."""
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist/analysis/camera-logs-20260919'
OUT.mkdir(parents=True, exist_ok=True)
result = {}
patterns = {
    'configuration': r'\[1-hidl-session::configureStreams_3_6\]|\[1-session::checkStream\]|select size\(|\[updateStreamConfiguration\]|\[determineScenRaw16\]',
    'stride_errors': r'enqueue_img_stride.*<.*query_img_stride',
    'fatal_signals': r'Fatal signal',
    'capture_failures': r'(?i)onCaptureFailed|captureFailed',
    'crash_trace': r'F DEBUG.*(?:#\d\d pc|Cause:|Build fingerprint|Kernel Release|Evolution X|signal 11)',
    'geometry_fixes': r'FIX_SENSOR_INFO_',
}
for filename in ['18_09-15-41-06_951.log', 'sgcam.log']:
    path = ROOT / 'logs' / filename
    raw = path.read_bytes()
    lines = raw.decode('utf-8-sig', errors='replace').splitlines()
    events = {key: [{'line': n, 'text': line} for n, line in enumerate(lines, 1)
                    if re.search(pattern, line)] for key, pattern in patterns.items()}
    result[filename] = {'sha256': hashlib.sha256(raw).hexdigest(), 'lines': len(lines),
                        'counts': {k: len(v) for k, v in events.items()}, 'events': events}
    (OUT / (filename + '.evidence.txt')).write_text('\n\n'.join(
        key + '\n' + '\n'.join(f"{e['line']}: {e['text']}" for e in values)
        for key, values in events.items()), encoding='utf-8')

with (ROOT / 'local-data/logs/Camara_Frontal_Camera2_API.csv').open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
result['csv'] = {'rows': len(rows), 'categories': dict(Counter(r['Category / Parameter'] for r in rows)), 'rows_data': rows}
xml = ET.parse(ROOT / 'local-data/logs/settigs.xml').getroot()
names = [el.attrib.get('name') for el in xml]
result['xml'] = {'entries': len(names), 'duplicate_names': [n for n, count in Counter(names).items() if count > 1],
                 'settings': {el.attrib.get('name'): el.attrib.get('value', el.text) for el in xml}}
(OUT / 'evidence.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({k: v.get('counts', {'entries_or_rows': v.get('entries', v.get('rows'))}) for k, v in result.items()}, indent=2))
