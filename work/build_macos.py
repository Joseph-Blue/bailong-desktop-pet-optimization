"""Build a local ad-hoc-signed macOS app on the current architecture."""
import argparse
from build_common import build_desktop

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', help='本机 FFmpeg 可执行文件路径')
    parser.add_argument('--archive', action='store_true', help='生成完整本地 ZIP')
    args = parser.parse_args()
    output = build_desktop('macos', ffmpeg_arg=args.ffmpeg)
    if args.archive:
        from archive_platform import archive_build
        archive_build(output, 'macos')
