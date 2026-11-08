"""Archive a platform package."""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from version import VERSION


def archive_build(directory, target):
    output = Path(directory).resolve()
    resources = output / 'Contents/Resources'
    info_path = resources / 'BUILD_INFO.json'
    info = json.loads(info_path.read_text(encoding='utf-8'))
    info.update(validation='built; runtime acceptance pending', buildOS=platform.platform())
    info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    arch = info['architecture']
    target = f'macos-{arch}'
    artifacts = output.parent
    artifacts.mkdir(parents=True, exist_ok=True)
    stem = f'bailong-desktop-pet-v{VERSION}-{target}'
    subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(output)], check=True)
    archive = artifacts / (stem + '.zip')
    subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(output), str(archive)], check=True)
    print(archive)
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=('macos',), required=True)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    archive_build(args.directory, args.platform)


if __name__ == '__main__':
    main()
