"""Build a complete Windows onedir folder, including assets and FFmpeg."""
import argparse
import hashlib
from pathlib import Path
import platform
import shutil
import zipfile
from build_common import build_desktop
from version import VERSION


def archive_build(output):
    """Archive the freshly built directory, without running the legacy release script."""
    arch = platform.machine().lower()
    arch = {'amd64': 'x86_64', 'x64': 'x86_64', 'aarch64': 'arm64'}.get(arch, arch)
    name = output.parent.parent / f'bailong-desktop-pet-v{VERSION}-windows-{arch}'
    archive = Path(shutil.make_archive(str(name), 'zip', root_dir=output.parent,
                                      base_dir=output.name))
    with zipfile.ZipFile(archive) as bundle:
        damaged = bundle.testzip()
        if damaged:
            raise RuntimeError(f'ZIP 校验失败：{damaged}')
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    checksum = archive.with_suffix('.zip.sha256')
    checksum.write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
    print(f'本地 ZIP：{archive}\nSHA256：{checksum}', flush=True)
    return archive


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', help='本机 FFmpeg 可执行文件路径')
    parser.add_argument('--zip', action='store_true', help='构建完成后生成本地 ZIP 和 SHA256 文件')
    args = parser.parse_args(argv)
    output = build_desktop('windows', ffmpeg_arg=args.ffmpeg)
    if args.zip:
        archive_build(output)


if __name__ == '__main__':
    main()
