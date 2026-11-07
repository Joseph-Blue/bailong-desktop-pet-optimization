from pathlib import Path
import sys,subprocess,shutil,json
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'app'))
from version import BASE_VERSION, BRANCH_REVISION, VERSION
if sys.platform!='darwin':raise SystemExit('必须在Mac上运行；本脚本不生成Windows包。')
assets=root/'outputs/白龙桌宠素材'
m=json.loads((assets/'素材清单.json').read_text(encoding='utf-8'))
items=[m['idle']]+m.get('additionalIdleAnimations',[])+m['variants']+[v for v in m.get('workAnimations',[]) if v]+m.get('movementAnimations',[])+[m[k] for k in ('dragAnimation','landingAnimation','quotaAnimation') if m.get(k)]
paths=[v.get('playbackFile') or v['file'].replace('.webm','.webp') for v in items]
paths += [v['returnTransition']['file'] for v in items if v.get('returnTransition')]
binaries=[]
if any(Path(path).suffix.lower()=='.webm' for path in paths):
 ffmpeg=root/'tools/ffmpeg'
 if not ffmpeg.is_file():
  found=shutil.which('ffmpeg')
  if not found:raise SystemExit('WebM 素材需要 macOS FFmpeg；请放入 tools/ffmpeg 或安装到 PATH。')
  ffmpeg=Path(found)
 binaries=['--add-binary',f'{ffmpeg}:tools']
# Install requirements-macos.txt in a clean virtual environment first.
import PyInstaller.__main__
PyInstaller.__main__.run(['--noconfirm','--clean','--windowed','--name','BailongPet','--osx-bundle-identifier','com.bailongpet.desktop','--distpath',str(root/'dist-macos'),'--workpath',str(root/'.build-macos'),'--specpath',str(root/'.build-macos'),'--hidden-import','autostart','--hidden-import','mac_autostart','--hidden-import','selftest','--hidden-import','AppKit','--hidden-import','Quartz','--hidden-import','PySide6.QtMultimedia',*binaries,str(root/'app/pet.py')])
resources=root/'dist-macos/BailongPet.app/Contents/Resources'
dest=resources/'outputs/白龙桌宠素材';dest.mkdir(parents=True,exist_ok=True)
for v in items:
 rel=v.get('playbackFile') or v['file'].replace('.webm','.webp');target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(assets/rel,target)
 if v.get('returnTransition'):
  rel=v['returnTransition']['file'];target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(assets/rel,target)
for v in items:v.pop('source',None)
(resources/'app').mkdir(exist_ok=True);shutil.copytree(root/'app/sounds',resources/'app/sounds',dirs_exist_ok=True)
(dest/'素材清单.json').write_text(json.dumps(m,ensure_ascii=False),encoding='utf-8')
import plistlib
p=root/'dist-macos/BailongPet.app/Contents/Info.plist';data=plistlib.loads(p.read_bytes())
data.update(LSUIElement=True,CFBundleShortVersionString=BASE_VERSION,
            CFBundleVersion=str(BRANCH_REVISION),BailongBranchVersion=VERSION)
p.write_bytes(plistlib.dumps(data))
# Re-sign after resources/plist changes. Ad-hoc signing is for local testing only.
subprocess.run(['codesign','--force','--deep','--sign','-',str(root/'dist-macos/BailongPet.app')],check=True)
print('生成了本机构架的未公证测试.app。公开发布前必须进行Mac实机验收、正式签名和公证。')
