# 本机构建与实机测试

本分支为原作者 Python／PySide6／FFmpeg 项目的 `joseph/optimization` 分支，作者基线 `0.5.1`，当前 `0.5.1-opt.9`。与独立 Swift 工程无关。此仓库只保存源码和文档，不提供 Release；脚本只在本机生成测试产物，不推送、上传或自动启动应用。

## 所有平台先准备

### 哪些环境是必需的？

先区分三个场景：运行已打好的完整包、从源码运行、从源码打包。以下以 Windows 为例：

| 项目 | 运行完整包 | 源码运行／构建 |
| --- | --- | --- |
| Python | 不需另装，包内包含解释器 | 需要。本分支构建检查要求 **64 位 Python 3.11～3.13**；版本范围是分支当前的支持策略，不是所有 PyInstaller 项目的通用限制 |
| PySide6、Pillow、psutil | 包内包含 | 需要，版本见 `requirements.txt`；构建脚本自动检查和补齐 |
| PyInstaller 6.22.3 | 不需要 | 仅打包需要；源码运行不需要 |
| FFmpeg | 当前 WebM 素材需要，完整包内包含 | 当前 WebM 素材需要支持 `libvpx-vp9` 的本机二进制；不要求全局安装或加入 PATH |
| imageio-ffmpeg | 不需要 Python 包 | 默认构建依赖，提供 FFmpeg；手动流程已有合适 FFmpeg 时可替代它 |
| PowerShell 7 | 不需要 | 不必安装，自动化脚本支持系统自带的 Windows PowerShell 5.1；直接使用 Python 入口也不依赖 PS 脚本 |
| 虚拟环境 | 不需要 | 是默认脚本的隔离方式，不是 PyInstaller 的硬性要求；不必手动激活 |
| `.build-tools` | 不需要 | 原作的包安装目录约定，本分支不需要 |
| Visual Studio／Qt SDK／Conda／uv | 不需要 | Windows 默认使用预编译 wheel，不要求这些工具；不要为本脚本额外安装整套开发工具链 |
| Codex 安装与登录 | 只在使用对话、额度和同步功能时需要 | 构建本身不需要登录，也不读取聊天数据 |

64 位 Windows 不代表命令 `python` 一定是 64 位。Python 版本、位数与当前依赖的可用 wheel 都要匹配；Windows ARM64 尚未实机验收，不把“64 位”当作 ARM64 已支持的承诺。

### 素材与解释器

1. 使用 **64 位 Python 3.11～3.13**。解释器版本和架构决定产物；不交叉编译，不自动构建另一种架构。
2. 从[原作者 v0.5.1 完整 Windows 包](https://github.com/jingh12312-rgb/bailong-desktop-pet/releases/tag/v0.5.1)取出 `outputs/白龙桌宠素材`，放到仓库同名路径；保留素材清单及原目录结构。各平台共用这些原始 WebM，不使用 Swift 工程转换后的素材。
3. FFmpeg 选择顺序为：脚本 `--ffmpeg`／`-FFmpeg` 参数、`BAILONG_BUILD_FFMPEG` 环境变量、仓库 `tools/ffmpeg[.exe]`、`imageio-ffmpeg` 包提供的本机二进制。跨平台复制素材时不要把 Windows 的 ffmpeg.exe 当作 macOS／Linux 解码器。自备 FFmpeg 必须能在构建机器运行，并包含 `libvpx-vp9`。

Windows 默认脚本先检查已安装依赖，缺失、版本不符或依赖关系冲突时才通过 pip 补齐；macOS／Linux 默认执行 pip 安装。没有本地缓存时安装需要网络；都不改系统 Python 的包。`imageio-ffmpeg` 只用于提供构建时的 FFmpeg，运行包不需要 Python 环境。构建目录只包含清单引用的动画，不复制用户历史、状态文件或整个源码目录。

仓库忽略 `outputs/`、`tools/`、`.venv-build*/`、`.build*/`、`dist-macos/`、`dist-linux/` 和 `发布包/`。缺少素材会直接报出路径。

## Windows：PowerShell 5.1／7+

安装 64 位 Python 3.11～3.13，在系统自带的 **Windows PowerShell 5.1** 或 **PowerShell 7+（pwsh）** 中进入仓库，无需专门安装 PowerShell 7：

```powershell
./build-windows.ps1
# 同时生成完整本地 ZIP 和 SHA256 校验文件
./build-windows.ps1 -Zip
# 指定解释器及解码器；参数是单个文件路径，不附加命令参数
./build-windows.ps1 -Python 'C:\Python313\python.exe' -FFmpeg 'C:\tools\ffmpeg.exe'
# 已准备好依赖后，仅重新打包
./build-windows.ps1 -SkipInstall
# 依赖齐全时重新打包并压缩；依赖不齐全会停止
./build-windows.ps1 -SkipInstall -Zip
```

脚本按以下顺序执行：

1. 复用已有 `.venv-build-windows`；首次运行时，使用显式 `-Python`，或依次探测 PATH 的 `python.exe` 和 `py -0p` 登记的解释器，选择满足版本与位数要求的解释器。不自动下载 Python，也不调用 Microsoft Store 安装别名。
2. 首次创建独立虚拟环境并检查解释器。整个流程直接调用环境内的 `python.exe`，无需运行 `Activate.ps1`。
3. 检查 pip 和 `requirements-build.txt`（含 `requirements.txt`）中的锁定版本；版本满足后再执行 `pip check` 检查依赖关系。
4. 依赖缺失、版本不符或关系冲突时，默认调用 pip 安装锁定依赖；pip 缺失时先通过 Python 自带的 `ensurepip` 补齐。安装后重新检查，仍有错误则中止。依赖已满足时跳过安装；`-SkipInstall` 遇到缺失或冲突只报错。
5. 校验素材及 FFmpeg 的 `libvpx-vp9` 解码器，再用 PyInstaller 打包，整理素材、音效和解码器。
6. 使用 `-Zip` 时压缩刚生成的整个 `BailongPet` 目录，校验 ZIP 并生成 SHA256 文件。

`Get-Help .\build-windows.ps1 -Detailed` 可查看参数说明。脚本不会自动下载角色素材；请先按上文准备。FFmpeg 默认从 `imageio-ffmpeg` 的本机 wheel 取得，不需要按原作旧路径手工摆放。

也可从终端使用 `powershell.exe -NoProfile -File .\build-windows.ps1` 或 `pwsh -NoProfile -File .\build-windows.ps1`。如果下载文件被本机策略阻止，先检查脚本来源并按所在设备的执行策略处理；脚本不会修改执行策略。

`-Python` 仅在首次创建虚拟环境时生效；已有环境会继续复用，需要更换解释器时先移走 `.venv-build-windows/`。参数是可执行文件路径或命令名，不能写成 `-Python 'py -3.13'`。可先用 `py -0p` 查看已安装解释器，再传入对应的 `python.exe` 路径。`-Python`、`-FFmpeg` 及 `BAILONG_BUILD_FFMPEG` 中的相对路径均相对于调用脚本时的目录解析；构建完成或失败后恢复原工作目录与脚本修改的环境变量。

维护此脚本时保存为 **UTF-8 with BOM**：Windows PowerShell 5.1 可能将无 BOM 的 UTF-8 脚本按系统代码页解读，导致中文错误或解析失败。脚本兼容两种 PowerShell 不代表支持旧版 Windows；Python、Qt 与 FFmpeg 的系统及架构要求仍需满足。

虚拟环境：`.venv-build-windows/`。产物：`发布包/build-v0.5.1-opt.9/BailongPet/`。双击其中的 `BailongPet.exe`。必须携带整个目录，包括 `_internal/`、`tools/`、`outputs/`、`app/sounds/`，不能单独复制 EXE。

在 x64 解释器下使用 `-Zip`，另生成 `发布包/bailong-desktop-pet-v0.5.1-opt.9-windows-x64.zip` 和同名 `.zip.sha256` 文件。ZIP 内保留顶层 `BailongPet/`，解压后直接使用。相同版本再次构建会替换该版本的目录包和 ZIP；不要在构建产物内保存唯一一份用户数据。ZIP 是本地测试包，不自动上传或创建 Release，也不调用旧脚本生成历史发行文案及许可证汇总。

`work/build_windows.py` 现在直接整理完整测试目录。原作者的 `work/build_release.py` 保留作历史发行包整理参考，以上入口不调用它，也不生成 GitHub Release。

### 与原作构建说明的对应关系

| 原作步骤 | 本分支的处理 |
| --- | --- |
| `python -m pip install --target .build-tools pyinstaller==6.22.3` | 改为在 `.venv-build-windows` 内安装 `requirements-build.txt`，包含同版本 PyInstaller 及应用依赖。`.build-tools` 是普通目录，不是虚拟环境；当前入口不会自动将它加入 Python 模块搜索路径，不能只执行这条旧命令就认为依赖已就绪 |
| `python work/build_windows.py` | 仍保留，但必须用已安装依赖的解释器。新入口直接生成完整目录包，而非只生成裸 EXE |
| FFmpeg 放到 `work/video-deps/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe` | 这是旧 ZIP 脚本硬编码的位置；新入口用 `-FFmpeg` 指定，或放到 `tools/ffmpeg.exe`，也可使用默认依赖提供的版本 |
| 保留 `outputs` 素材 | 仍需要，清单及引用文件必须完整；默认脚本不下载素材 |
| `python work/build_release.py` 整理 ZIP | 当前流程用 `./build-windows.ps1 -Zip`，或 Python 入口的 `--zip`。旧脚本含固定 FFmpeg 路径、旧版文案和旧 PyInstaller 中间文件路径，不作为本分支入口 |

如果要使用原作完整包中的 FFmpeg，可将其 `tools/ffmpeg.exe` 复制到本仓库 `tools/ffmpeg.exe`，或直接传入该文件的完整路径，不需要复制整个 `work/video-deps`。

### 手动执行同一流程

不想使用 PS 自动化入口时，可在任意终端按步骤调用 Python；下面为 PowerShell 写法，所有命令在仓库根目录执行，每一步成功后再继续。示例路径要替换为自己的 64 位解释器：

```powershell
& 'C:\Python313\python.exe' work/build_common.py
& 'C:\Python313\python.exe' -m venv .venv-build-windows
& '.\.venv-build-windows\Scripts\python.exe' -m pip install -r requirements-build.txt
& '.\.venv-build-windows\Scripts\python.exe' work/check_build_dependencies.py
& '.\.venv-build-windows\Scripts\python.exe' -m pip check
& '.\.venv-build-windows\Scripts\python.exe' work/build_windows.py --zip
# 自备 FFmpeg 时，给最后一步加 --ffmpeg 'C:\tools\ffmpeg.exe'
```

也可以使用自己管理的已有 Python 环境，不创建上述 venv，但依赖安装和构建必须使用同一个解释器。`work/build_windows.py` 本身不安装依赖。若自备 FFmpeg 且不安装 `imageio-ffmpeg`，在手动环境安装 `requirements.txt` 和 `pyinstaller==6.22.3` 即可；自动化 PS 入口始终遵循完整 `requirements-build.txt`。

### 常见问题

| 现象 | 处理 |
| --- | --- |
| 找不到合适 Python／提示使用 64 位 | `py -0p` 查看解释器，使用 `-Python` 指定路径；可用 `python -c "import sys,struct; print(sys.executable); print(sys.version); print(struct.calcsize('P')*8)"` 核对默认解释器 |
| 换了 `-Python` 却仍用旧版本 | 参数仅负责创建环境，先将已有 `.venv-build-windows` 移走，再运行脚本；不要从 Mac 复制虚拟环境到 Windows |
| pip 安装失败／没有匹配的发行包 | 检查当前 Python、位数、网络和软件源是否提供锁定版本的 wheel；脚本会中止，不把失败安装当成成功 |
| 缺 pip 且 `ensurepip` 不可用 | 使用包含 venv／ensurepip 的完整 Python 发行版；嵌入式 Python 压缩包不等同于完整开发环境 |
| 依赖安装后 `pip check` 仍失败 | 环境可能混入额外冲突包，保留日志，移走构建 venv 后重建；脚本不强行卸载未知包 |
| 禁止执行脚本 | 这是 PowerShell 执行策略问题，5.1 和 7 都可能遇到；按设备策略处理，或使用上面的手动 Python 命令 |
| 缺少素材／解码器 | 补齐报错文件；检查 FFmpeg 来源是否对应 Windows，以及是否包含 `libvpx-vp9` |
| EXE 不能运行／窗口行为异常 | 目录完整、打包成功仍不等于实机运行通过；保留构建日志并按文末验收表测试 |

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

已安装依赖的虚拟环境也可以直接运行对应的 `work/build_windows.py`、`work/build_macos.py` 或 `work/build_linux.py --family debian`，均支持 `--ffmpeg`，并拒绝在错误的操作系统构建。Windows 入口额外支持 `--zip`。程序入口不变，仍是 `app/pet.py`。

打包资源内的 `BUILD_INFO.json` 记录分支版本、Python、平台、架构和素材文件数量，不包含本机用户名或绝对路径。仓库根目录旧 `BUILD_INFO.json` 与 `RELEASE_NOTES.md` 是作者 v0.5.1 的历史记录，不代表这次构建。

## 性能设置

默认分辨率 512×512、预加载 12 帧、满帧，整段动画预加载关闭。运行帧率档位为满帧／20／15 FPS，与 Swift 版一致；满帧使用素材帧率，当前素材为 24 或 30 FPS。预加载帧数支持输入和 6～240 帧滑条。整段预加载只加载当前动作，开启时保留并禁用帧数设置。应用后重播当前动作并保存设置；已有有效设置继续保留。

## 性能统计范围

“桌宠 RAM”只包括主进程与 FFmpeg，macOS 两项均为物理占用，Windows／Linux 为 RSS。Codex app-server 及其启动的 Node／Python 等工具进程不计入；它不是整个进程树合计。CPU 行分别标明主进程与解码进程，GPU 保留应用组口径，不能将不同范围的数值混作同一总量。

Windows 显示系统虚拟内存已提交量／上限，Linux 与 macOS 显示系统 Swap 已用／总量。GPU 使用率、进程压缩内存与换入计数仅在 macOS 显示。

浮窗显示 CPU／GPU 型号、桌面端与内置 CLI 的 PID／路径／会话状态。硬件查询仅在窗口打开时发起一次，关闭取消；Windows 通过系统 PowerShell 的 CIM 查询，Linux GPU 型号通过 lspci 获取（发行版 pciutils 包）。macOS 按应用 Bundle ID 识别桌面端，Windows 当前识别 Microsoft Store 安装路径，Linux 明确显示尚未接入桌面端识别。候选 CLI 路径与实际运行进程分开标注，不为统计发起 Codex 请求。

## 实机验收记录

当前：macOS Apple Silicon 构建已执行；Windows、Linux 三类发行版尚未实机构建／运行。脚本解析检查和打包通过不等于运行验收。请为每台机器记录：

2026-11-08：Windows 构建入口已在 Windows PowerShell 5.1.26100.9711 和 PowerShell 7.6.9 下进行离线流程回归，覆盖自动选择 Python、首次创建／复用环境、依赖检查及补齐、跳过安装、中文／空格／方括号路径、失败中止及工作目录／环境变量恢复。另测试 ZIP 内容、SHA256 和构建失败时不执行压缩。测试使用替代构建模块和 pip 模块，不执行真实项目依赖安装与 PyInstaller 打包；本机默认 Python 为 3.11.0rc1 32 位，实际构建需另选合适解释器。复测命令：`python -m unittest discover -s work -p "test_build*.py" -v`；测试会使用临时子进程的执行策略参数，不更改用户或系统策略。

| 项目 | 记录内容 |
| --- | --- |
| 环境 | 系统／发行版版本、架构、Python、桌面环境、X11 或 Wayland |
| 构建 | Git 提交、应用版本、FFmpeg 来源、成功或完整报错 |
| 播放 | 首次显示、透明边缘、待机／互动／移动／吸边、音效 |
| 窗口 | 置顶、隐藏／召回、多屏、退出；Linux 托盘与合成器行为 |
| 性能 | 相同画质与缓冲下的 RAM、FPS、CPU，注明是否观察 Codex、是否打开其他窗口 |
| 对话 | 新建桌宠对话、同步历史只读、重开后历史保留；使用本机自己的 Codex 登录 |

参考：[PyInstaller 平台与打包说明](https://www.pyinstaller.org/en/stable/usage.html)、[pip 安装与 --target](https://pip.pypa.io/en/stable/cli/pip_install/)、[Qt Linux XCB 依赖](https://doc.qt.io/qt-6/linux-requirements.html)、[PySide6 6.9.2 平台包](https://pypi.org/project/PySide6/6.9.2/)。
