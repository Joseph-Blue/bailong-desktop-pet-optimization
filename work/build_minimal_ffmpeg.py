"""Build the WebM/VP9-alpha decoder on Linux, macOS, or WSL for Windows x86_64."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ('FFmpeg-n7.1.5', 'https://codeload.github.com/FFmpeg/FFmpeg/tar.gz/refs/tags/n7.1.5',
     'e3963a50831c985933e1a625ed566ec4c7adb5c012c34fa9f84438e1d61bdacc'),
    ('libvpx-1.17.0', 'https://codeload.github.com/webmproject/libvpx/tar.gz/refs/tags/v1.17.0',
     '1020f184046187baa2985dbde38e0691f49c44088bca7a1842b0236c6081dc0a'),
)


def source_tree(work, name, url, expected):
    archive = work / f'{name}.tar.gz'
    if not archive.exists():
        print(f'下载 {name}', flush=True)
        with urllib.request.urlopen(url, timeout=90) as response, archive.open('wb') as out:
            shutil.copyfileobj(response, out)
    source = work / 'sources' / name
    if not source.exists():
        with tarfile.open(archive) as bundle:
            bundle.extractall(work / 'sources', filter='data')
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=('native', 'windows-x86_64'), default='native')
    parser.add_argument('--work-dir', type=Path, default=ROOT / '.build/ffmpeg')
    parser.add_argument('--jobs', type=int, default=min(os.cpu_count() or 2, 12))
    args = parser.parse_args()
    if sys.platform not in ('linux', 'darwin'):
        parser.error('Windows 版请在 WSL 中运行，并使用 --target windows-x86_64。')
    if not hasattr(tarfile, 'data_filter'):
        parser.error('请使用 Python 3.12 或更新版本。')
    windows = args.target == 'windows-x86_64'
    arch = {'amd64': 'x86_64', 'aarch64': 'arm64'}.get(platform.machine().lower(), platform.machine().lower())
    cross = 'x86_64-w64-mingw32-'
    required = ['make', 'pkg-config', 'perl', cross + 'gcc' if windows else 'cc']
    if windows or arch == 'x86_64':
        required.append('nasm')
    missing = [tool for tool in required if not shutil.which(tool)]
    if missing:
        hint = '；macOS 安装命令：xcode-select --install；brew install pkgconf' if sys.platform == 'darwin' else ''
        parser.error('缺少编译工具：' + ', '.join(missing) + hint)
    target = args.target if windows else f'{sys.platform}-{arch}'
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    ffmpeg, vpx = [source_tree(work, *item) for item in SOURCES]
    # GitHub source archives otherwise pick up this repository's parent Git version.
    (ffmpeg / 'VERSION').write_text('7.1.5\n', encoding='utf-8')
    prefix = work / target
    prefix.mkdir(exist_ok=True)
    env = os.environ.copy()
    env['PKG_CONFIG_LIBDIR'] = str(prefix / 'lib/pkgconfig')
    if windows:
        env['CROSS'] = cross
    else:
        env.pop('CROSS', None)
    commands = []

    def run(command, directory, log):
        commands.append(command)
        print(f'{directory.name}: {log}', flush=True)
        with (directory / log).open('w', encoding='utf-8') as stream:
            subprocess.run(command, cwd=directory, env=env, stdout=stream,
                           stderr=subprocess.STDOUT, check=True)

    vpx_options = [str(vpx / 'configure'), f'--prefix={prefix}', '--disable-vp8',
                   '--disable-vp9-encoder', '--disable-examples', '--disable-tools',
                   '--disable-docs', '--disable-unit-tests', '--disable-shared', '--enable-static',
                   '--enable-pic']
    if windows:
        vpx_options += ['--target=x86_64-win64-gcc']
    if windows or arch == 'x86_64':
        vpx_options += ['--as=nasm']
    ffmpeg_options = [str(ffmpeg / 'configure'), f'--prefix={prefix}', '--pkg-config=pkg-config',
        '--disable-autodetect', '--disable-everything', '--disable-doc', '--disable-debug',
        '--disable-ffplay', '--disable-ffprobe', '--disable-network', '--disable-avdevice',
        '--disable-postproc', '--disable-swresample', '--disable-shared', '--enable-static',
        '--enable-small', '--enable-ffmpeg', '--enable-libvpx', '--enable-decoder=libvpx_vp9',
        '--enable-demuxer=matroska', '--enable-protocol=file,pipe', '--enable-encoder=rawvideo',
        '--enable-muxer=rawvideo', '--enable-filter=scale,fps,format', '--enable-swscale',
        f'--extra-cflags=-I{prefix / "include"}',
        f'--extra-ldflags=-L{prefix / "lib"}' + (' -static' if windows else '')]
    if windows:
        ffmpeg_options += ['--target-os=mingw32', '--arch=x86_64', '--enable-cross-compile',
                           f'--cross-prefix={cross}']
    for component, options in [('vpx', vpx_options), ('ffmpeg', ffmpeg_options)]:
        directory = work / f'build-{component}-{target}'
        directory.mkdir(exist_ok=True)
        run(options, directory, 'configure.log')
        run(['make', f'-j{max(1, args.jobs)}'], directory, 'build.log')
        run(['make', 'install'], directory, 'install.log')
    binary = prefix / 'bin' / ('ffmpeg.exe' if windows else 'ffmpeg')
    notices = prefix / 'bin/ffmpeg-licenses'
    notices.mkdir(exist_ok=True)
    for source, name in [(ffmpeg / 'COPYING.LGPLv2.1', 'FFmpeg-LGPL-2.1.txt'),
                         (vpx / 'LICENSE', 'libvpx-LICENSE.txt'), (vpx / 'PATENTS', 'libvpx-PATENTS.txt')]:
        shutil.copy2(source, notices / name)
    info = dict(ffmpeg='7.1.5', libvpx='1.17.0', target=target,
                sources=[dict(name=name, url=url, sha256=sha) for name, url, sha in SOURCES],
                commands=commands)
    (binary.parent / 'ffmpeg-build.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    print(f'完成：{binary}\n体积：{binary.stat().st_size / 2**20:.2f} MiB', flush=True)


if __name__ == '__main__':
    main()
