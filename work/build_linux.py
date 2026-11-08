"""Build an unpacked Linux test app on its target distribution and architecture."""
import argparse
from build_common import build_desktop

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', required=True, choices=('debian', 'fedora', 'arch'))
    parser.add_argument('--ffmpeg', help='本机 FFmpeg 可执行文件路径')
    parser.add_argument('--archive', action='store_true', help='生成完整本地 tar.gz')
    parser.add_argument('--rpm', action='store_true', help='生成 Fedora 本地 RPM')
    args = parser.parse_args()
    if args.rpm and args.family != 'fedora':
        parser.error('--rpm 仅支持 Fedora')
    output = build_desktop('linux', family=args.family, ffmpeg_arg=args.ffmpeg)
    if args.archive:
        from archive_platform import archive_build
        archive_build(output, 'linux', args.family)
    if args.rpm:
        from build_rpm import build_rpm
        build_rpm(output)
