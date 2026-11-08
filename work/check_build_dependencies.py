"""Check pinned build packages without importing Qt or requiring pip.

Exit 0: ready; 10: packages need installation; other errors: invalid input.
"""
from importlib import metadata
import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def pinned_requirements(path):
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('-r '):
            yield from pinned_requirements(path.parent / line[3:].strip())
            continue
        line, separator, marker = line.partition(';')
        if separator:
            platform_marker = re.fullmatch(r"\s*sys_platform\s*==\s*['\"]([^'\"]+)['\"]\s*", marker)
            if not platform_marker:
                raise ValueError(f'不支持的环境条件：{marker}')
            if sys.platform != platform_marker[1]:
                continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)(?:==([A-Za-z0-9_.+!-]+))?', line.strip())
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--requirements', type=Path, action='append', default=[])
    args = parser.parse_args()
    missing = missing_dependencies()
    for path in args.requirements:
        missing.extend(missing_dependencies(path))
    if missing:
        print('需要补齐构建依赖：\n  ' + '\n  '.join(missing), flush=True)
        raise SystemExit(10)
    print('构建依赖版本检查通过。', flush=True)
