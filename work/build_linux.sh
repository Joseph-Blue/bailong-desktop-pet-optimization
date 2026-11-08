#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
FAMILY="${1:?需要发行版族：debian、fedora 或 arch}"
shift
ENTRY="build-linux-$FAMILY.sh"
DEFAULT_VENV=".build/venvs/linux-$FAMILY"
source "$ROOT/work/build_shell_common.sh"
parse_build_options "$@"
if [[ "$(uname -s)" != Linux ]]; then echo '请在对应 Linux 发行版上运行。' >&2; exit 1; fi
if [[ "$INSTALL_DEPS" == 1 ]]; then
    SUDO=()
    if [[ "$EUID" != 0 ]]; then SUDO=(sudo); fi
    case "$FAMILY" in
        debian)
            "${SUDO[@]}" apt-get update
            "${SUDO[@]}" apt-get install -y python3 python3-venv python3-pip python3-dev build-essential binutils \
                libgl1 libegl1 libfontconfig1 libdbus-1-3 libx11-xcb1 libxrender1 libxext6 libsm6 libice6 \
                libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 \
                libxcb-xinerama0 libxcb-xkb1 libxcb-randr0 libxcb-shape0 libxcb-xfixes0 \
                libxkbcommon-x11-0 libglib2.0-bin fonts-noto-cjk pulseaudio-utils
            ;;
        fedora)
            "${SUDO[@]}" dnf install -y python3 python3-pip python3-devel gcc binutils \
                libglvnd-glx libglvnd-egl fontconfig dbus-libs libX11-xcb libXrender libXext libSM libICE \
                libxcb xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil \
                libxkbcommon-x11 glib2 google-noto-sans-cjk-fonts pulseaudio-utils
            ;;
        arch)
            "${SUDO[@]}" pacman -S --needed --noconfirm python python-pip base-devel binutils \
                libglvnd fontconfig dbus libx11 libxrender libxext libsm libice \
                libxcb xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil \
                libxkbcommon-x11 glib2 noto-fonts-cjk libpulse
            ;;
        *) echo "未知发行版族：$FAMILY" >&2; exit 1 ;;
    esac
fi
run_build linux "$FAMILY"
