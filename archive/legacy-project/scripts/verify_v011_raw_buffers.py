"""Emulate the actual binary hook and setter, including limits already above six."""
from emulate_metadata import *
from build_v011_raw_buffers import DEST, HOOK, SOURCE_SHA

b = (DEST/'libmtkcam_pipelinepolicy.so').read_bytes()
a = parse_elf(b)
m = json.loads((DEST/'raw-buffers-manifest.json').read_text())
source = (ROOT/'patches/front-v0.10-full-binned/libmtkcam_pipelinepolicy.so').read_bytes()
assert hashlib.sha256(source).hexdigest() == SOURCE_SHA
assert hashlib.sha256(b).hexdigest() == m['output_sha256']
replay = bytearray(source)
for c in m['changes']:
    off = int(c['offset'], 16); old = bytes.fromhex(c['old']); new = bytes.fromhex(c['new'])
    assert source[off:off+len(old)] == old
    replay[off:off+len(new)] = new
assert replay == b
# The front sensor selector and its code cave must remain byte-identical.
assert b[0x488a4:0x488a8] == source[0x488a4:0x488a8]
assert b[0x9fb90:0x9fbd8] == source[0x9fb90:0x9fbd8]
cases = []
for original in (0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 37, 0xffffffff):
    u = Uc(UC_ARCH_ARM64, UC_MODE_ARM); u.mem_map(0, 0x200000)
    for ph in a.load_segments:
        u.mem_write(ph.p_vaddr, b[ph.p_offset:ph.p_offset+ph.p_filesz])
    # Continue through the real virtual-call sequence at 0x5a0bc.
    u.mem_map(0x1000000, 0x10000)
    obj, vt, setter = 0x1001000, 0x1002000, 0x1003000
    u.mem_write(obj, struct.pack('<Q', vt))
    u.mem_write(vt-0x78, struct.pack('<Q', 0))
    u.mem_write(vt+0x28, struct.pack('<Q', setter))
    u.reg_write(UC_ARM64_REG_X8, vt)
    u.reg_write(UC_ARM64_REG_X23, obj)
    u.reg_write(UC_ARM64_REG_X19, original)
    u.reg_write(UC_ARM64_REG_SP, 0x1008000)
    calls = []
    def stop(uc, pc, size, _):
        if pc == setter:
            calls.append([uc.reg_read(UC_ARM64_REG_X0), uc.reg_read(UC_ARM64_REG_X1)])
            uc.emu_stop()
    u.hook_add(UC_HOOK_CODE, stop)
    u.emu_start(HOOK, 0, count=30)
    assert calls == [[obj, max(original, 6)]], (original, calls)
    assert u.reg_read(UC_ARM64_REG_X19) == original
    assert u.reg_read(UC_ARM64_REG_SP) == 0x1008000
    cases.append(dict(original=original, setter_count=calls[0][1]))
output = ROOT/'dist/verification/v0.11-raw-buffers.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(dict(cases=cases, exact_replay=True, front_patch_preserved=True), indent=2)+'\n')
print('PASS: 12 actual hook/setter paths, larger counts preserved, exact replay, front patch preserved')
