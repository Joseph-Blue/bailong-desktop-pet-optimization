#!/usr/bin/env bash
# Bash interface for the macOS build entry point.

parse_build_options() {
    BUILD_PYTHON="${PYTHON:-}"
    BUILD_FFMPEG="${BAILONG_BUILD_FFMPEG:-}"
    SKIP_INSTALL=0
    ARCHIVE=0
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --python) BUILD_PYTHON="${2:?--python 需要解释器路径或命令名}"; shift 2 ;;
            --ffmpeg) BUILD_FFMPEG="${2:?--ffmpeg 需要可执行文件路径}"; shift 2 ;;
            --skip-install) SKIP_INSTALL=1; shift ;;
            --archive) ARCHIVE=1; shift ;;
            -h|--help)
                echo "用法：bash $ENTRY [--python 路径或命令] [--ffmpeg 路径] [--skip-install] [--archive]"
                echo '自动选择已安装的 64 位 Python 3.11～3.13；复用独立构建环境，按需补齐依赖。'
                echo '默认准备修复 WebM 素材；更新播放清单，保留已有动画文件。'
                if [[ "$ENTRY" == build-macos.sh ]]; then
                    echo '默认使用精简 FFmpeg；首次自动编译，后续复用。需 Xcode Command Line Tools 和 pkg-config。'
                fi
                echo '--skip-install：仅检查和构建，不创建环境或安装依赖。'
                echo '--archive：生成完整 macOS ZIP。'
                echo '环境变量：PYTHON、BUILD_VENV、BAILONG_BUILD_FFMPEG。命令行参数优先。'
                exit 0 ;;
            *) echo "未知参数：$1；使用 --help 查看用法。" >&2; exit 1 ;;
        esac
    done
    # Resolve caller-relative paths before entering the repository.
    BUILD_ENV="${BUILD_VENV:-$ROOT/$DEFAULT_VENV}"
    if [[ "$BUILD_ENV" != /* ]]; then BUILD_ENV="$PWD/$BUILD_ENV"; fi
    if [[ -n "$BUILD_PYTHON" && ! -x "$BUILD_ENV/bin/python" ]]; then
        BUILD_PYTHON="$(command -v -- "$BUILD_PYTHON")" || {
            echo '找不到指定的 Python。' >&2; exit 1;
        }
        if [[ "$BUILD_PYTHON" != /* ]]; then BUILD_PYTHON="$PWD/$BUILD_PYTHON"; fi
    fi
    if [[ -n "$BUILD_FFMPEG" && "$BUILD_FFMPEG" != /* ]]; then BUILD_FFMPEG="$PWD/$BUILD_FFMPEG"; fi
}

run_build() {
    local target=macos candidate dependency_exit needs_install=0
    local venv_python="$BUILD_ENV/bin/python"
    local requirements=(-r requirements-build.txt)
    local checks=(work/check_build_dependencies.py)
    local build_args=("work/build_$target.py")
    requirements+=(-r requirements-macos.txt)
    checks+=(--requirements requirements-macos.txt)
    cd -- "$ROOT"
    export PYTHONUTF8=1
    export PYINSTALLER_CONFIG_DIR="$ROOT/.build/cache/pyinstaller-$target"
    export PYTHONPYCACHEPREFIX="$ROOT/.build/cache/python"
    if [[ ! -x "$venv_python" ]]; then
        if [[ "$SKIP_INSTALL" == 1 ]]; then
            echo '构建环境不存在；请先去掉 --skip-install 运行。' >&2; exit 1
        fi
        if [[ -z "$BUILD_PYTHON" ]]; then
            for candidate in python3.13 python3.12 python3.11 python3; do
                if command -v "$candidate" >/dev/null 2>&1 &&
                    "$candidate" -c 'import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,13) and sys.maxsize > 2**32 else 1)' 2>/dev/null; then
                    BUILD_PYTHON="$(command -v "$candidate")"; break
                fi
            done
        fi
        if [[ -z "$BUILD_PYTHON" ]]; then
            echo '未找到 64 位 Python 3.11～3.13。请手动安装，或用 --python 指定解释器。' >&2
            exit 1
        fi
        "$BUILD_PYTHON" work/build_common.py
        echo "创建构建环境，使用 Python：$BUILD_PYTHON"
        "$BUILD_PYTHON" -m venv "$BUILD_ENV"
    elif [[ -n "$BUILD_PYTHON" ]]; then
        echo "复用 $BUILD_ENV；--python 仅用于首次创建。"
    fi
    "$venv_python" work/build_common.py
    echo '检查构建依赖及版本...'
    if "$venv_python" "${checks[@]}"; then
        if ! "$venv_python" -m pip check; then needs_install=1; fi
    else
        dependency_exit=$?
        if [[ "$dependency_exit" != 10 ]]; then return "$dependency_exit"; fi
        needs_install=1
    fi
    if [[ "$needs_install" == 1 ]]; then
        if [[ "$SKIP_INSTALL" == 1 ]]; then
            echo '构建依赖缺失、版本不符或存在冲突；去掉 --skip-install 可自动补齐。' >&2; exit 1
        fi
        if ! "$venv_python" -m pip --version; then "$venv_python" -m ensurepip --upgrade; fi
        echo '补齐构建依赖...'
        "$venv_python" -m pip install "${requirements[@]}"
        "$venv_python" "${checks[@]}"
        "$venv_python" -m pip check
    else
        echo '依赖已满足，跳过安装。'
    fi
    if [[ -n "$BUILD_FFMPEG" ]]; then build_args+=(--ffmpeg "$BUILD_FFMPEG"); fi
    if [[ "$ARCHIVE" == 1 ]]; then build_args+=(--archive); fi
    echo '打包程序、素材和 FFmpeg...'
    "$venv_python" "${build_args[@]}"
}
