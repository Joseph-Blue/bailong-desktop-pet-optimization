"""Build a complete Windows onedir folder, including assets and FFmpeg."""
import argparse
from build_common import build_desktop

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', help='本机 FFmpeg 可执行文件路径')
    args = parser.parse_args()
    build_desktop('windows', ffmpeg_arg=args.ffmpeg)
