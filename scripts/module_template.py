"""Render the SRE-0 template with module-specific installer logic."""
from pathlib import Path
import re


def render_installer(root: Path, name: str, version: str, link: str, logic: str) -> str:
    template = (root / 'template-module/customize.sh').read_text(encoding='utf-8')
    marker = '# =========================================================================='
    header, separator, _ = template.partition(marker)
    if not separator:
        raise ValueError('Template installer sequence marker is missing')
    for key, value in {'MODNAME': name, 'MODVERSION': version, 'MODLINK': link}.items():
        if any(char in value for char in '\"`$\\\n\r'):
            raise ValueError(f'Unsafe template metadata: {key}')
        header, count = re.subn(rf'^{key}=.*$', f'{key}="{value}"', header, flags=re.M)
        if count != 1:
            raise ValueError(f'Template metadata missing: {key}')
    return header + '''SKIPUNZIP=0
print_banner
print_modname_frame
print_module_info
print_env_info
ui_print ' '
''' + logic.removeprefix('#!/system/bin/sh\n').removeprefix('SKIPUNZIP=0\n') + '\nprint_footer\n'
