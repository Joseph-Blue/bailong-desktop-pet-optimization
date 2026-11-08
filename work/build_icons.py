"""Export Windows/macOS application icons from the repaired idle first frame."""
import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def build_icon(target):
    suffix = {'windows': 'ico', 'macos': 'icns'}[target]
    output = ROOT / '.build/icons' / f'BailongPet.{suffix}'
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(ROOT / 'app/icons/repaired-idle.png') as source:
        image = source.convert('RGBA')
        if target == 'windows':
            image.save(output, format='ICO', sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
        else:
            image.save(output, format='ICNS')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=('windows', 'macos', 'both'), default='both')
    args = parser.parse_args()
    for target in (('windows', 'macos') if args.target == 'both' else (args.target,)):
        print(build_icon(target))
