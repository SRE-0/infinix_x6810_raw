"""Host checks for the shared template baseline."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from module_template import AUTHOR, BASE_FILES, TEMPLATE


def main():
    modules = sorted(path for path in (ROOT / 'modules').iterdir()
                     if path.is_dir())
    assert modules, 'No modules found'
    for module in modules:
        for name in BASE_FILES:
            assert (module / name).is_file(), f'{module.name}: missing {name}'
        prop = (module / 'module.prop').read_text(encoding='utf-8').splitlines()
        assert [line.split('=', 1)[0] for line in prop] == [
            'id', 'name', 'version', 'versionCode', 'author', 'description']
        assert 'author=' + AUTHOR in prop
        customize = (module / 'customize.sh').read_text(encoding='utf-8')
        assert 'print_banner' in customize
        assert 'print_footer' in customize
    print(f'PASS: {len(modules)} modules contain the template baseline')


if __name__ == '__main__':
    main()
