"""Package original artwork or the explicitly selected four-animation repair set."""
import argparse
import json
from pathlib import Path
import zipfile

from fetch_release_assets import ROOT, ASSET_NAME, ensure_assets, animation_items, animation_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repaired-animations', type=Path,
                        help='含 idle/idle2/drag/landing.png 无损 APNG 的修复目录')
    args = parser.parse_args()
    ensure_assets()
    assets = ROOT / 'outputs/白龙桌宠素材'
    manifest = assets / '素材清单.json'
    data = json.loads(manifest.read_text(encoding='utf-8'))
    replacements = {}
    if args.repaired_animations:
        for item in animation_items(data):
            if item['id'] in ('idle', 'idle2', 'drag', 'landing'):
                source = args.repaired_animations / f"{item['id']}.png"
                if not source.is_file():
                    raise FileNotFoundError(source)
                item['playbackFile'] = f"修复APNG/{item['id']}.png"
                replacements[item['playbackFile']] = source
    paths = animation_paths(data)
    name = 'bailong-repaired-v0.5.1-assets.zip' if replacements else ASSET_NAME
    output = ROOT / '.build/assets' / name
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED) as bundle:
        attribution = (ROOT / 'ASSETS.md').read_text(encoding='utf-8')
        if replacements:
            attribution = attribution.replace('(docs/修复素材备选包.md)', '(修复素材说明.md)')
        bundle.writestr('素材来源.md', attribution)
        if replacements:
            bundle.writestr('outputs/白龙桌宠素材/素材清单.json',
                            json.dumps(data, ensure_ascii=False, indent=2) + '\n')
            instructions = (ROOT / 'docs/修复素材备选包.md').read_text(encoding='utf-8')
            bundle.writestr('修复素材说明.md', instructions.replace('(../ASSETS.md)', '(素材来源.md)'))
        else:
            bundle.write(manifest, manifest.relative_to(ROOT))
        for relative in sorted(paths):
            source = replacements.get(relative, assets / relative)
            bundle.write(source, 'outputs/白龙桌宠素材/' + relative)
    print(f'素材包：{output}\n动画：{len(paths)} 段；体积：{output.stat().st_size / 2**20:.2f} MiB')


if __name__ == '__main__':
    main()
