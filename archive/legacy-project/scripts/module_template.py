"""Shared module-template support for all generated Magisk/APatch modules."""
from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'template-module'
BASE_FILES = ('post-fs-data.sh', 'service.sh', 'README.md')
PROP_KEYS = ('id', 'name', 'version', 'versionCode', 'author', 'description')
AUTHOR = 'SRE-0'


def apply_template(module, *, overwrite=False):
    """Seed a module from template-module without deleting module-specific files.

    Existing files are preserved by default because historical modules contain
    tested boot and documentation changes. New package builds can pass
    ``overwrite=True`` when they explicitly want the current template files.
    """
    module = Path(module)
    module.mkdir(parents=True, exist_ok=True)
    for name in BASE_FILES:
        target = module / name
        if overwrite or not target.exists():
            shutil.copyfile(TEMPLATE / name, target)
    return module


def normalize_module_prop(module):
    """Keep module metadata in the same ordered format as template-module."""
    module = Path(module)
    prop = module / 'module.prop'
    values = {}
    for line in prop.read_text(encoding='utf-8').splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            values[key] = value
    missing = [key for key in PROP_KEYS if not values.get(key)]
    if missing:
        raise ValueError(f'{prop}: missing template fields: {", ".join(missing)}')
    values['author'] = AUTHOR
    prop.write_text(''.join(f'{key}={values[key]}\n' for key in PROP_KEYS),
                    encoding='utf-8', newline='\n')


def style_customize_text(current, prop_text):
    """Wrap installer text with the template UI using module metadata text."""
    template = (TEMPLATE / 'customize.sh').read_text(encoding='utf-8')
    prop = dict(line.split('=', 1) for line in
                prop_text.splitlines()
                if '=' in line)
    prefix = template.split('# ==========================================================================', 1)[0]
    prefix = re.sub(r'MODNAME="[^"]*"', f'MODNAME="{prop["name"]}"', prefix)
    prefix = re.sub(r'MODVERSION="[^"]*"', f'MODVERSION="{prop["version"]}"', prefix)
    prefix = re.sub(r'MODAUTHOR="[^"]*"', f'MODAUTHOR="{prop["author"]}"', prefix)
    if 'print_banner' in current and 'print_footer' in current:
        current = re.sub(r'MODNAME="[^"]*"', f'MODNAME="{prop["name"]}"', current)
        current = re.sub(r'MODVERSION="[^"]*"', f'MODVERSION="{prop["version"]}"', current)
        return re.sub(r'MODAUTHOR="[^"]*"', f'MODAUTHOR="{prop["author"]}"', current)
    body = current.splitlines()[1:]
    return prefix + '''# ==========================================================================\n# Module-specific installation logic\n# ==========================================================================\n\nprint_banner\nprint_modname_frame\nprint_module_info\nprint_env_info\nui_print ' '\n\n''' + '\n'.join(body) + '''\n\nprint_footer\n'''


def style_customize(module):
    """Wrap a module-specific installer body with the template installer UI."""
    module = Path(module)
    customize = module / 'customize.sh'
    current = customize.read_text(encoding='utf-8')
    prop_text = (module / 'module.prop').read_text(encoding='utf-8')
    styled = style_customize_text(current, prop_text)
    customize.write_text(styled, encoding='utf-8', newline='\n')