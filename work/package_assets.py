"""Package original animation files and attribution without application binaries."""
import json
from pathlib import Path
import zipfile

from fetch_release_assets import ROOT, ASSET_NAME, ensure_assets, animation_paths


def main():
    ensure_assets()
    assets = ROOT / 'outputs/白龙桌宠素材'
    manifest = assets / '素材清单.json'
    paths = animation_paths(json.loads(manifest.read_text(encoding='utf-8')))
    output = ROOT / '.build/assets' / ASSET_NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED) as bundle:
        bundle.write(ROOT / 'ASSETS.md', '素材来源.md')
        bundle.write(manifest, manifest.relative_to(ROOT))
        for relative in sorted(paths):
            source = assets / relative
            bundle.write(source, source.relative_to(ROOT))
    print(f'素材包：{output}\n动画：{len(paths)} 段；体积：{output.stat().st_size / 2**20:.2f} MiB')


if __name__ == '__main__':
    main()
