"""Build an unpacked Linux test app on its target distribution and architecture."""
import argparse
from build_common import build_desktop

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', required=True, choices=('debian', 'fedora', 'arch'))
    parser.add_argument('--ffmpeg', help='本机 FFmpeg 可执行文件路径')
    args = parser.parse_args()
    build_desktop('linux', family=args.family, ffmpeg_arg=args.ffmpeg)
