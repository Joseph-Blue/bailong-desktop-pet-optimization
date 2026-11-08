"""Check a frozen app offline and archive it with a SHA256 sidecar."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from version import VERSION


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=('macos', 'linux'), required=True)
    parser.add_argument('--family', choices=('debian', 'fedora', 'arch'))
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    output = args.directory.resolve()
    mac = args.platform == 'macos'
    resources = output / 'Contents/Resources' if mac else output
    executable = output / ('Contents/MacOS/BailongPet' if mac else 'BailongPet')
    original_files = {p.resolve() for p in resources.rglob('*') if p.is_file()}
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen',
               BAILONG_DATA_DIR=str(ROOT / '.build-release/check-data'))
    subprocess.run([str(executable), '--self-test'], env=env, check=True, timeout=180)
    report_path = resources / '检查报告.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if not report['passed'] or not report['frozen']:
        raise RuntimeError(report)
    for path in resources.rglob('*'):
        if path.is_file() and path.resolve() not in original_files:
            path.unlink()
    info_path = resources / 'BUILD_INFO.json'
    info = json.loads(info_path.read_text(encoding='utf-8'))
    info.update(validation='frozen offline self-test passed', buildOS=platform.platform(),
                libc=platform.libc_ver() if not mac else None)
    info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    target = 'macos-arm64' if mac else f'linux-{args.family}-x86_64'
    artifacts = ROOT / '.build-release/artifacts'
    artifacts.mkdir(parents=True, exist_ok=True)
    stem = f'bailong-desktop-pet-v{VERSION}-{target}'
    if mac:
        subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(output)], check=True)
        subprocess.run(['codesign', '--verify', '--deep', '--strict', str(output)], check=True)
        archive = artifacts / (stem + '.zip')
        subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(output), str(archive)], check=True)
    else:
        archive = artifacts / (stem + '.tar.gz')
        with tarfile.open(archive, 'w:gz', dereference=False) as bundle:
            bundle.add(output, arcname=output.name)
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    Path(str(archive)+'.sha256').write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
    (artifacts / (stem + '-checks.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(archive)


if __name__ == '__main__':
    main()
