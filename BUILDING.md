# 本机构建与实机测试

本分支为原作者 Python／PySide6／FFmpeg 项目的 `joseph/optimization` 分支，作者基线 `0.5.1`，当前 `0.5.1-opt.8`。与独立 Swift 工程无关。此仓库只保存源码和文档，不提供 Release；脚本只在本机生成测试产物，不推送、上传或自动启动应用。

## 所有平台先准备

1. 使用 **64 位 Python 3.11～3.13**。解释器版本和架构决定产物；不交叉编译，不自动构建另一种架构。
2. 从[原作者 v0.5.1 完整 Windows 包](https://github.com/jingh12312-rgb/bailong-desktop-pet/releases/tag/v0.5.1)取出 `outputs/白龙桌宠素材`，放到仓库同名路径；保留素材清单及原目录结构。各平台共用这些原始 WebM，不使用 Swift 工程转换后的素材。
3. FFmpeg 选择顺序为：脚本 `--ffmpeg`／`-FFmpeg` 参数、`BAILONG_BUILD_FFMPEG` 环境变量、仓库 `tools/ffmpeg[.exe]`、`imageio-ffmpeg` 包提供的本机二进制。跨平台复制素材时不要把 Windows 的 ffmpeg.exe 当作 macOS／Linux 解码器。自备 FFmpeg 必须能在构建机器运行，并包含 `libvpx-vp9`。

默认脚本会通过 pip 安装锁定版本的应用与构建依赖，首次需要网络；不改系统 Python。`imageio-ffmpeg` 只用于提供构建时的 FFmpeg，运行包不需要 Python 环境。构建目录只包含清单引用的动画，不复制用户历史、状态文件或整个源码目录。

仓库忽略 `outputs/`、`tools/`、`.venv-build*/`、`.build*/`、`dist-macos/`、`dist-linux/` 和 `发布包/`。缺少素材会直接报出路径。

## Windows：只支持 PowerShell 7+

安装 64 位 Python 3.11～3.13 与 PowerShell 7，在 **pwsh** 中进入仓库：

```powershell
./build-windows.ps1
# 指定解释器及解码器；参数是单个文件路径，不附加命令参数
./build-windows.ps1 -Python 'C:\Python313\python.exe' -FFmpeg 'C:\tools\ffmpeg.exe'
# 已准备好依赖后，仅重新打包
./build-windows.ps1 -SkipInstall
```

Windows PowerShell 5.1 会被 `#Requires -Version 7.0` 拒绝。如果下载文件被本机策略阻止，先检查脚本来源并按所在设备的执行策略处理；脚本不会修改执行策略。

虚拟环境：`.venv-build-windows/`。产物：`发布包/build-v0.5.1-opt.8/BailongPet/`。双击其中的 `BailongPet.exe`。必须携带整个目录，包括 `_internal/`、`tools/`、`outputs/`、`app/sounds/`，不能单独复制 EXE。

`work/build_windows.py` 现在直接整理完整测试目录。原作者的 `work/build_release.py` 保留作历史发行包整理参考，以上入口不调用它，也不生成 GitHub Release。

## macOS：Bash

先安装 Python 3.11～3.13 与 Xcode Command Line Tools（`xcode-select --install`），然后：

```bash
PYTHON=python3.11 bash build-macos.sh
# 自备 FFmpeg
bash build-macos.sh --ffmpeg /absolute/path/to/ffmpeg
# 使用已经安装依赖的环境重新打包
BUILD_VENV="$PWD/.venv" bash build-macos.sh --skip-install
```

虚拟环境默认 `.venv-build-macos/`。产物 `dist-macos/BailongPet.app`，含素材与 FFmpeg，并在资源／Info.plist 更新后进行本地 ad-hoc 签名。没有 Developer ID 签名或公证。Apple Silicon Python 构建 arm64；Intel Python 在 Intel Mac 上构建 x86_64，不自动生成 universal 包。当前只执行过 Apple Silicon 构建。

## Linux：三类发行版

三个入口共用 `work/build_linux.sh` 与 `work/build_linux.py`。默认只创建虚拟环境并安装 Python 依赖；加 **`--install-deps`** 才通过 apt／dnf／pacman 安装 XCB、OpenGL、中文字体和编译工具等系统依赖，非 root 使用 sudo。

```bash
# Debian / Ubuntu 及衍生版
bash build-linux-debian.sh --install-deps

# Fedora / RHEL / Rocky / AlmaLinux 及衍生版
bash build-linux-fedora.sh --install-deps

# Arch / EndeavourOS / Manjaro 及衍生版
bash build-linux-arch.sh --install-deps
```

在对应阵营的机器上选一个脚本运行；不是在同一台机器上执行三个脚本。发行版仓库需包含列出的依赖；脚本不自动启用 EPEL、CRB、RPM Fusion 或其他软件源。RHEL 系缺包时按该机器的软件源策略安装，已准备依赖后省略 `--install-deps`。

如果系统默认 Python 为 3.14+ 或低于 3.11，先准备一个 3.11～3.13 解释器，通过 `PYTHON` 指定，不替换系统 Python。已有 uv 的机器可使用：

```bash
uv python install 3.13
PYTHON="$(uv python find 3.13)" bash build-linux-arch.sh
```

再次构建、自备解码器示例：

```bash
bash build-linux-debian.sh --skip-install
PYTHON=python3.12 bash build-linux-fedora.sh --ffmpeg /absolute/path/to/ffmpeg
```

虚拟环境 `.venv-build-linux-<family>/`；产物 `dist-linux/<family>-<architecture>/BailongPet/`。在桌面会话中运行该目录的 `./run.sh`，携带整个目录。`run.sh` 默认 `QT_QPA_PLATFORM=xcb`，面向 X11／XWayland；它不安装 XWayland 服务，不修改系统桌面设置。原生 Wayland 可显式设置 `QT_QPA_PLATFORM=wayland ./run.sh`，窗口位置、置顶、托盘和吸边须单独验收。

当前生成的是 **PyInstaller 目录包**，不是 deb、rpm、AppImage 或 pacman 安装包。Linux 构建使用目标系统的 glibc 等基础库；应在目标发行版或所支持的最旧兼容环境中构建，不能把一台新系统构建的目录当作通用 Linux 包。固定 PySide6 6.9.2 的官方 wheel 要求 x86_64 glibc 2.28+、aarch64 glibc 2.39+；实际运行下限还受构建系统及其他库影响。

Linux 的全屏自动检测及跟随 Codex 启动未接入；不要把 Windows／macOS 的菜单能力当作 Linux 已实现功能。此轮只增加构建入口，不扩展这些平台功能。现有 Linux 状态文件会写到应用目录，测试产物应放在用户可写目录中。

## 低层 Python 入口

已安装依赖的虚拟环境也可以直接运行对应的 `work/build_windows.py`、`work/build_macos.py` 或 `work/build_linux.py --family debian`，均支持 `--ffmpeg`，并拒绝在错误的操作系统构建。程序入口不变，仍是 `app/pet.py`。

打包资源内的 `BUILD_INFO.json` 记录分支版本、Python、平台、架构和素材文件数量，不包含本机用户名或绝对路径。仓库根目录旧 `BUILD_INFO.json` 与 `RELEASE_NOTES.md` 是作者 v0.5.1 的历史记录，不代表这次构建。

## 性能统计范围

“桌宠运行内存 (RAM) 合计”只包括主进程与 FFmpeg，macOS 两项均为物理占用，Windows／Linux 为 RSS。Codex app-server 及其启动的 Node／Python 等工具进程不计入；它不是整个进程树合计。CPU 行分别标明主进程与解码进程，GPU 保留应用组口径，不能将不同范围的数值混作同一总量。

浮窗显示 CPU／GPU 型号、桌面端与内置 CLI 的 PID／路径／会话状态。硬件查询仅在窗口打开时发起一次，关闭取消；Windows 通过系统 PowerShell 的 CIM 查询，Linux GPU 型号通过 lspci 获取（发行版 pciutils 包）。macOS 按应用 Bundle ID 识别桌面端，Windows 当前识别 Microsoft Store 安装路径，Linux 明确显示尚未接入桌面端识别。候选 CLI 路径与实际运行进程分开标注，不为统计发起 Codex 请求。

## 实机验收记录

当前：macOS Apple Silicon 构建已执行；Windows、Linux 三类发行版尚未实机构建／运行。脚本解析检查和打包通过不等于运行验收。请为每台机器记录：

| 项目 | 记录内容 |
| --- | --- |
| 环境 | 系统／发行版版本、架构、Python、桌面环境、X11 或 Wayland |
| 构建 | Git 提交、应用版本、FFmpeg 来源、成功或完整报错 |
| 播放 | 首次显示、透明边缘、待机／互动／移动／吸边、音效 |
| 窗口 | 置顶、隐藏／召回、多屏、退出；Linux 托盘与合成器行为 |
| 性能 | 相同画质与缓冲下的 RAM、FPS、CPU，注明是否观察 Codex、是否打开其他窗口 |
| 对话 | 新建桌宠对话、同步历史只读、重开后历史保留；使用本机自己的 Codex 登录 |

参考：[PyInstaller 平台与打包说明](https://www.pyinstaller.org/en/stable/usage.html)、[Qt Linux XCB 依赖](https://doc.qt.io/qt-6/linux-requirements.html)、[PySide6 6.9.2 平台包](https://pypi.org/project/PySide6/6.9.2/)。
