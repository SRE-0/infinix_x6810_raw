"""Bring every checked-in module up to the shared template baseline."""
from module_template import ROOT, apply_template, normalize_module_prop, style_customize


def main():
    modules = sorted(path for path in (ROOT / 'archive/modules').iterdir()
                     if path.is_dir())
    for module in modules:
        apply_template(module)
        normalize_module_prop(module)
        style_customize(module)
    print(f'Migrated {len(modules)} modules from template-module')


if __name__ == '__main__':
    main()