"""Read camera libraries through adb root without staging files on the phone."""
import argparse
import re
import subprocess
import hashlib
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    adb = ['adb', '-s', args.serial, 'exec-out', 'su', '--no-pty', '-c']
    names = subprocess.check_output(adb + ['ls /vendor/lib64'], timeout=30).decode().splitlines()
    args.output.mkdir(parents=True, exist_ok=True)
    count = 0
    for name in names:
        if not re.fullmatch(r'(?:lib(?:cam|Camera|mtkcam|3a|Tran|tran|camera|feature|vidhance|arcsoft|mfll).*|.*mipi_raw.*)\.so', name):
            continue
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', name):
            continue
        expected = subprocess.check_output(adb + ['sha256sum /vendor/lib64/' + name], timeout=30).decode().split()[0]
        existing = args.output / name
        if existing.is_file() and hashlib.sha256(existing.read_bytes()).hexdigest() == expected:
            count += 1
            continue
        data = subprocess.check_output(adb + ['cat /vendor/lib64/' + name], timeout=30)
        if not data.startswith(b'\x7fELF'):
            raise RuntimeError('Not ELF: ' + name)
        if hashlib.sha256(data).hexdigest() != expected:
            raise RuntimeError('Transfer hash mismatch: ' + name)
        (args.output / name).write_bytes(data)
        count += 1
    print(f'Collected {count} ELF libraries')

if __name__ == '__main__':
    main()
