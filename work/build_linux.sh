#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
FAMILY="${1:?需要发行版族：debian、fedora 或 arch}"
shift
INSTALL_DEPS=0
SKIP_INSTALL=0
BUILD_ARGS=(--family "$FAMILY")
while [[ $# -gt 0 ]]; do
    case "$1" in
        --install-deps) INSTALL_DEPS=1; shift ;;
        --skip-install) SKIP_INSTALL=1; shift ;;
        --ffmpeg) BUILD_ARGS+=(--ffmpeg "${2:?--ffmpeg 需要可执行文件路径}"); shift 2 ;;
        -h|--help)
            echo '用法：bash build-linux-<debian|fedora|arch>.sh [--install-deps] [--skip-install] [--ffmpeg 路径]'
            echo '--install-deps 才会使用 sudo 安装系统依赖；默认只在项目虚拟环境安装 Python 依赖。'
            echo '环境：PYTHON=python3.13，BUILD_VENV=虚拟环境目录。'
            exit 0 ;;
        *) echo "未知参数：$1" >&2; exit 1 ;;
    esac
done
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
                libxkbcommon-x11-0 libglib2.0-bin fonts-noto-cjk
            ;;
        fedora)
            "${SUDO[@]}" dnf install -y python3 python3-pip python3-devel gcc binutils \
                libglvnd-glx libglvnd-egl fontconfig dbus-libs libX11-xcb libXrender libXext libSM libICE \
                libxcb xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil \
                libxkbcommon-x11 glib2 google-noto-sans-cjk-fonts
            ;;
        arch)
            "${SUDO[@]}" pacman -S --needed --noconfirm python python-pip base-devel binutils \
                libglvnd fontconfig dbus libx11 libxrender libxext libsm libice \
                libxcb xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil \
                libxkbcommon-x11 glib2 noto-fonts-cjk
            ;;
        *) echo "未知发行版族：$FAMILY" >&2; exit 1 ;;
    esac
fi
cd -- "$ROOT"
VENV="${BUILD_VENV:-$ROOT/.venv-build-linux-$FAMILY}"
if [[ ! -x "$VENV/bin/python" ]]; then
    if [[ "$SKIP_INSTALL" == 1 ]]; then echo '构建环境不存在；请先去掉 --skip-install 运行。' >&2; exit 1; fi
    "${PYTHON:-python3}" work/build_common.py
    "${PYTHON:-python3}" -m venv "$VENV"
fi
"$VENV/bin/python" work/build_common.py
if [[ "$SKIP_INSTALL" == 0 ]]; then
    "$VENV/bin/python" -m pip install -r requirements-build.txt
fi
export PYINSTALLER_CONFIG_DIR="$ROOT/.build-linux/pyinstaller-cache"
"$VENV/bin/python" work/build_linux.py "${BUILD_ARGS[@]}"
