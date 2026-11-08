"""Wrap a locally built Fedora onedir application in an installable RPM."""
import argparse
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from version import BASE_VERSION, BRANCH_REVISION, VERSION


def build_rpm(directory):
    directory = Path(directory).resolve()
    info = json.loads((directory / 'BUILD_INFO.json').read_text(encoding='utf-8'))
    if sys.platform != 'linux' or info['linuxFamily'] != 'fedora':
        raise SystemExit('RPM 入口使用 Fedora 上构建的 Linux 目录包。')
    if info['version'] != VERSION:
        raise SystemExit('目录包版本与源码不一致；请先重新构建。')
    arch = info['architecture']
    work = ROOT / '.build/work/rpm'
    work.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='build-', dir=work))
    payload = stage / 'payload'
    application = payload / 'opt/bailong-desktop-pet'
    # Copy only the application payload, never state files from a running bundle.
    application.mkdir(parents=True)
    for name in ('BailongPet', '_internal', 'outputs', 'tools', 'licenses', 'BailongPet.png',
                 'run.sh', 'VERSION.txt', 'BUILD_INFO.json', 'ASSETS.md', 'README.md',
                 'BUILDING.md', 'CHANGELOG.md', '优化说明.md'):
        source = directory / name
        if source.is_dir():
            shutil.copytree(source, application / name, symlinks=True)
        else:
            shutil.copy2(source, application / name)
    shutil.copytree(directory / 'app/sounds', application / 'app/sounds')
    bin_dir = payload / 'usr/bin'
    bin_dir.mkdir(parents=True)
    (bin_dir / 'bailong-desktop-pet').symlink_to('/opt/bailong-desktop-pet/BailongPet')
    desktop = payload / 'usr/share/applications/bailong-desktop-pet.desktop'
    desktop.parent.mkdir(parents=True)
    desktop.write_text('''[Desktop Entry]
Type=Application
Name=Bailong Desktop Pet
Name[zh_CN]=白龙桌宠
Comment=Animated desktop companion
Exec=bailong-desktop-pet
Icon=bailong-desktop-pet
Terminal=false
Categories=Game;
StartupWMClass=BailongPet
''', encoding='utf-8')
    icon = payload / 'usr/share/icons/hicolor/256x256/apps/bailong-desktop-pet.png'
    icon.parent.mkdir(parents=True)
    shutil.copy2(directory / 'BailongPet.png', icon)
    subprocess.run(['desktop-file-validate', str(desktop)], check=True)
    spec = stage / 'bailong-desktop-pet.spec'
    spec.write_text(f'''%global debug_package %{{nil}}
%global __os_install_post %{{nil}}
Name: bailong-desktop-pet
Version: {BASE_VERSION}
Release: 0.opt.{BRANCH_REVISION}%{{?dist}}
Summary: Animated Bailong desktop companion
License: LicenseRef-Proprietary
URL: https://github.com/Joseph-Blue/bailong-desktop-pet-optimization
BuildArch: {arch}
AutoReqProv: no
Requires: glibc >= {platform.libc_ver()[1]}
Requires: libX11, libX11-xcb, libxcb, libXrender, libXext, libSM, libICE
Requires: libxkbcommon-x11, xcb-util-cursor, xcb-util-wm, xcb-util-image
Requires: xcb-util-keysyms, xcb-util-renderutil
Requires: libglvnd-glx, libglvnd-egl, fontconfig, dbus-libs
Requires: pulseaudio-utils, xorg-x11-server-Xwayland

%description
Local Fedora test package of Bailong Desktop Pet {VERSION}.
Includes the Python/Qt runtime, FFmpeg, animation assets and dependency licenses.
User data is stored separately in the user's XDG data directory.

%install
mkdir -p "%{{buildroot}}"
cp -a "{payload}/." "%{{buildroot}}/"

%files
/opt/bailong-desktop-pet
/usr/bin/bailong-desktop-pet
/usr/share/applications/bailong-desktop-pet.desktop
/usr/share/icons/hicolor/256x256/apps/bailong-desktop-pet.png
''', encoding='utf-8')
    artifacts = directory.parent
    artifacts.mkdir(parents=True, exist_ok=True)
    subprocess.run(['rpmbuild', '-bb', str(spec), '--define', f'_topdir {stage}',
                    '--define', f'_rpmdir {artifacts}', '--define', '_rpmfilename %{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}.rpm',
                    '--define', f'_buildrootdir {stage}/BUILDROOT',
                    '--define', '_binary_payload w3.zstdio'], check=True)
    print(f'本地 RPM：{artifacts}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    build_rpm(args.directory)
