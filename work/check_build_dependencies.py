"""Check pinned build packages without importing Qt or requiring pip.

Exit 0: ready; 10: packages need installation; other errors: invalid input.
"""
from importlib import metadata
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def pinned_requirements(path):
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('-r '):
            yield from pinned_requirements(path.parent / line[3:].strip())
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)', line)
        if not match:
            raise ValueError(f'不支持的依赖声明：{path.name}: {line}')
        yield match.groups()


def missing_dependencies(path=ROOT / 'requirements-build.txt'):
    missing = []
    for name, required in [('pip', None), *pinned_requirements(path)]:
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            installed = None
        if installed is None or (required is not None and installed != required):
            target = f'{name}=={required}' if required else name
            missing.append(f'{target}（当前：{installed or "未安装"}）')
    return missing


if __name__ == '__main__':
    missing = missing_dependencies()
    if missing:
        print('需要补齐构建依赖：\n  ' + '\n  '.join(missing), flush=True)
        raise SystemExit(10)
    print('构建依赖版本检查通过。', flush=True)
