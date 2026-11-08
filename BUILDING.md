# Windows／macOS 构建说明

原作者基线为 **0.5.1 / b102e73**，当前代码标记 **0.5.1-opt.23**。本次发布 Windows x86_64 与 macOS Apple Silicon arm64；Linux 支援暂停，三阵营构建脚本和 RPM 工具已移除。

## 共用要求

- 在对应目标系统构建，不交叉打包应用；使用 64 位 Python 3.11～3.13。
- Windows 使用 PowerShell 5.1／7+；macOS 使用 Bash、Xcode Command Line Tools 与 pkg-config。
- 构建入口复用独立虚拟环境；缺少依赖、版本不符或依赖关系冲突时才安装。`--skip-install`／`-SkipInstall` 只跳过 Python 依赖安装。
- FFmpeg 需要 `libvpx-vp9` 透明解码。Windows 默认使用仓库 `tools/ffmpeg.exe`；macOS 默认自动编译并复用本机精简版。显式参数优先于环境变量和默认路径。
- 源码、运行库与素材需要各自的来源说明和许可文件。运行包整理这些文件，不包含用户账号、对话历史或本机构建路径。

## 素材自动准备

两平台入口、作者原 Windows 构建与发行脚本共用 `work/fetch_release_assets.py`。默认从本私有仓库的 **`v0.5.1-opt.assets.repaired.2`** 下载 `bailong-repaired-v0.5.1-assets.zip`。

需要具有仓库读取权限的 GitHub CLI 登录，或 `GH_TOKEN`／`GITHUB_TOKEN`。下载显示 **已下载／总大小（MB）、百分比、实时网速（MB/s）**。没有登录时不会改用原始素材；访问失败直接报错。

- 已有修复 WebM 清单及全部引用动画：不联网。
- 清单仍为原版／旧 APNG 修复版，或缺少素材：下载修复包，更新清单并补齐文件；原始动画文件保留。
- 下载缓存位于 `.build/downloads/`。可用 `ASSET_REPOSITORY`、`ASSET_RELEASE_TAG`、`ASSET_FILE_NAME` 显式指定下载源。
- 不执行 SHA-256 检查。离线构建需预先准备完整修复素材、依赖和解码器。

```bash
# 单独准备素材
python work/fetch_release_assets.py
# 将当前完整修复素材封装成素材 ZIP
python work/package_assets.py
# 使用本地四段已编码 WebM 替换；其余素材须已在 outputs 中
python work/package_assets.py --repaired-animations /path/to/encoded-webm
```

素材由 **jingh12312-rgb** 原作者提供；当前包为 31 段作者原始 WebM 加四段修复 WebM。修复段保留 720×720、24 FPS 与原时长，使用 VP9 Alpha / CRF 18 编码。默认播放设置仍是 512×512。详见 [ASSETS](ASSETS.md) 与 [修复素材说明](docs/修复素材备选包.md)。

## Windows

```powershell
.\build-windows.ps1
# 同时生成 ZIP
.\build-windows.ps1 -Zip
# 使用指定解释器、解码器
.\build-windows.ps1 -Python 'C:\Python313\python.exe' -FFmpeg 'C:\tools\ffmpeg.exe' -Zip
# 依赖已经齐全
.\build-windows.ps1 -SkipInstall -Zip
```

`-Archive` 等价于 `-Zip`。脚本兼容 PowerShell 5.1／7+；文件保持 UTF-8 with BOM。首次创建环境时选择合适的 64 位 Python，不自动安装 Python或调用 Microsoft Store 别名；缺少时显示安装命令。

默认环境为 `.build/venvs/windows/`；已有环境继续复用，`-Python` 仅用于首次创建。依赖按 `requirements-build.txt` 检查，已满足时跳过安装。

- 目录包：`dist-windows/build-v0.5.1-opt.23/BailongPet/`。
- ZIP：`dist-windows/bailong-desktop-pet-v0.5.1-opt.23-windows-x86_64.zip`。
- 运行整个目录中的 `BailongPet.exe`，不要只复制 EXE。

PowerShell 调用 `work/build_windows_optimized.py`。作者原 `work/build_windows.py`、`work/build_release.py` 保留并单独维护；优化入口不执行原发行脚本。

## macOS

先安装 Xcode Command Line Tools（`xcode-select --install`）和 pkg-config（`brew install pkgconf`）。

```bash
bash build-macos.sh --archive
bash build-macos.sh --python python3.13 --archive
bash build-macos.sh --ffmpeg /absolute/path/to/ffmpeg --archive
bash build-macos.sh --skip-install --archive
```

默认环境为 `.build/venvs/macos/`。`PYTHON`、`BUILD_VENV`、`BAILONG_BUILD_FFMPEG` 可覆盖默认值，命令行参数优先；路径按调用位置解析，不附加命令参数。

Bash 与 Python 入口都默认使用 `.build/ffmpeg/darwin-<架构>/bin/ffmpeg`。首次缺失时下载固定版本源码并编译，之后复用；编译失败直接报错，不回退通用版。`--skip-install` 不跳过首次解码器编译。

- 应用：`dist-macos/BailongPet.app`。
- arm64 ZIP：`dist-macos/bailong-desktop-pet-v0.5.1-opt.23-macos-arm64.zip`。
- 构建后执行本地 ad-hoc 签名，归档保留应用目录结构；未做 Apple 公证。
- 当前发布与本轮构建目标为 Apple Silicon。Intel 本机架构构建能力保留，但不提供本轮 Intel Release 附件，也未做 Intel 实机验收。

macOS 的数据目录、全屏与填充区别见 [MAC适配说明](MAC适配说明.md)。

## 低层入口与输出

已准备依赖的环境可直接运行：

```powershell
python work/build_windows_optimized.py --zip
```

```bash
python work/build_macos.py --archive
```

两者均支持 `--ffmpeg`。缓存和中间产物放 `.build/`，程序和 ZIP 放 `dist-windows/`、`dist-macos/`。重复构建会更新对应版本的产物；用户数据不应保存于构建产物中。

应用图标源为 `app/icons/repaired-idle.png`。`work/build_icons.py` 在构建时生成 ICO／ICNS，无需额外图标工具；图标保留透明背景，不重绘角色。

## 精简 FFmpeg

固定源码为 FFmpeg 7.1.5 与 libvpx 1.17.0。只保留 WebM／VP9 Alpha 解码、缩放、帧率调整、RGBA 输出、本地文件和管道；不含网络协议、音频处理和通用转码功能。

Windows 精简版、版本记录和许可文件在 `tools/` 追踪。macOS 从源码构建并将解码器与许可一起放入应用。每个应用包只保留一份解码器。

```bash
# macOS：生成本机架构精简版
python3 work/build_minimal_ffmpeg.py
# WSL：生成 Windows x86_64 解码器，仅为编译工具用途
python3 work/build_minimal_ffmpeg.py --target windows-x86_64
```

编译需要 C 编译器、make、pkg-config、Perl，以及支持 tarfile 安全解包过滤的 Python。x86_64 需要 NASM，Windows 目标另需 MinGW-w64。保留 WSL 编译工具用途不代表恢复 Linux 应用支持。

## Release 构建

工作流 **Build and release Windows and macOS** 从 `release_tag` 对应源码构建，默认标签为 `v0.5.1-opt.23`。

- Windows x86_64 在 Windows runner 构建；macOS arm64 在 Apple Silicon runner 构建。
- `build_macos` 可关闭远端 Mac 构建，以复用已经上传的本地 Mac 包。
- `artifact_run_id` 可复用既有运行中的指定 Windows／Mac artifact，不收集其他平台产物。
- 任一平台成功即可发布其附件；另一平台随后补传到同一 Release。已有附件保留，发布说明按实际附件生成下载链接。
- 发布不生成 SHA-256 附件，不运行应用自检或实机测试。

当前 CI 及下载页面只提供 Windows／macOS。原作者的历史安装说明、`RELEASE_NOTES.md`、根目录 `BUILD_INFO.json` 保留，不用于描述本次包内容。

## 验收与资源口径

构建成功不代表运行验收。每个平台分别确认透明边缘、动作切换、气泡、输入法、音效、全屏切换与退出。macOS 的“填充”和“全屏”分别确认；本轮 Windows 交互逻辑不因 Mac 修复而改动。

统计中的 RAM 合计为主进程与 FFmpeg，不包含 Codex 及其工具进程；macOS 使用物理占用，Windows 使用 RSS。Windows 私有提交量不等于页文件写入量；macOS Swap 换入是累计量。长硬件名称和路径可悬停查看全文，复制信息保留完整数据，性能统计没有分组“详情”按钮。
