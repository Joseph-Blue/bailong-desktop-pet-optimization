#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(uname -s)" != Darwin ]]; then
    echo '请在 macOS 上运行此脚本。' >&2
    exit 1
fi
SKIP_INSTALL=0
BUILD_ARGS=(work/build_macos.py)
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-install) SKIP_INSTALL=1; shift ;;
        --ffmpeg) BUILD_ARGS+=(--ffmpeg "${2:?--ffmpeg 需要可执行文件路径}"); shift 2 ;;
        -h|--help)
            echo '用法：bash build-macos.sh [--skip-install] [--ffmpeg 路径]'
            echo '环境：PYTHON=python3.11，BUILD_VENV=虚拟环境目录（默认 .venv-build-macos）'
            exit 0 ;;
        *) echo "未知参数：$1" >&2; exit 1 ;;
    esac
done
cd -- "$ROOT"
VENV="${BUILD_VENV:-$ROOT/.venv-build-macos}"
if [[ ! -x "$VENV/bin/python" ]]; then
    if [[ "$SKIP_INSTALL" == 1 ]]; then echo '构建环境不存在；请先去掉 --skip-install 运行。' >&2; exit 1; fi
    "${PYTHON:-python3}" work/build_common.py
    "${PYTHON:-python3}" -m venv "$VENV"
fi
"$VENV/bin/python" work/build_common.py
if [[ "$SKIP_INSTALL" == 0 ]]; then
    "$VENV/bin/python" -m pip install -r requirements-build.txt -r requirements-macos.txt
fi
export PYINSTALLER_CONFIG_DIR="$ROOT/.build-macos/pyinstaller-cache"
"$VENV/bin/python" "${BUILD_ARGS[@]}"
