#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENTRY=build-macos.sh
DEFAULT_VENV=.build/venvs/macos
source "$ROOT/work/build_shell_common.sh"
parse_build_options "$@"
if [[ "$(uname -s)" != Darwin ]]; then
    echo '请在 macOS 上运行此脚本。' >&2
    exit 1
fi
if [[ "$INSTALL_DEPS" == 1 ]]; then
    echo 'macOS 请先手动安装 Xcode Command Line Tools：xcode-select --install' >&2; exit 1
fi
run_build macos
