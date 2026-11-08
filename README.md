# 白龙桌宠 · Python / Qt 优化分支

基于 [原作者 v0.5.1](https://github.com/jingh12312-rgb/bailong-desktop-pet)，基线提交 `b102e73`。沿用 Python、PySide6、FFmpeg 和原始动画素材，维护 Windows、macOS、Linux 构建入口。

当前版本 **0.5.1-opt.23**，分支 `joseph/optimization`。`opt.N` 表示本分支的迭代号，界面版本同时显示平台和架构。

[与原作者版本的改动对照](docs/原作者版本改动对照.md) · [构建说明](BUILDING.md) · [更新记录](CHANGELOG.md) · [开发约定](DEVELOPMENT.md) · [给原作者的优化说明](优化说明.md)

私有仓库 [Release](https://github.com/Joseph-Blue/bailong-desktop-pet-optimization/releases) 提供 Windows x86_64、macOS arm64 和 Debian / Arch / Fedora x86_64 五种完整运行包；也可按构建说明在目标系统本地构建。

opt.23 修复任务气泡空白、性能设置改为即时生效、关闭角色窗口系统阴影，并为构建接入素材自动下载；macOS Apple Silicon 本地产物已更新，约 292 MB；应用 Release 尚未发布，界面效果待实机验收。

素材由 **jingh12312-rgb** 原作者提供。本仓库的[独立素材包](https://github.com/Joseph-Blue/bailong-desktop-pet-optimization/releases/tag/v0.5.1-opt.assets.1)仅整理原始动画、清单及来源说明。所有构建脚本默认使用仅替换四段动画的[修复素材包](docs/修复素材备选包.md)，原始包保留供手动选择。下载私有仓库附件需要具有仓库读取权限的 GitHub 登录或 token。Windows EXE 与 macOS App 图标统一使用修复 idle 的第一帧。详见 [素材来源](ASSETS.md)。

## 实现变化

| 部分 | 当前实现 |
| --- | --- |
| 动画播放 | FFmpeg 通过管道输出透明 RGBA 帧，按当前动作解码；隐藏时暂停 |
| 加载速度 | 首批画面就绪即播放，大幅缩短启动和切换动作的加载等待；后续画面随播放补充 |
| 默认设置 | 512×512、12 帧预加载、素材原帧率；整段预加载关闭 |
| 可调档位 | 满帧 / 20 / 15 FPS；预加载 6～240 帧，输入框与滑条同步 |
| 性能界面 | 设置即时保存并生效，无“应用”按钮；双栏布局，窄窗口上下排列；长字段省略，悬停显示全文，支持复制完整信息 |
| 资源统计 | 运行内存 (RAM) 分列主进程与 FFmpeg；换页按主进程统计，Windows 私有提交量标“仅供参考” |
| 工具调用 | 显示临时进度和执行状态，长内容截断，不写入历史消息 |
| 字体 | Windows 沿用原作微软雅黑，其他平台使用系统字体；字号跟随系统，气泡缩小时保留正文大小 |
| Windows 包 | 精简 FFmpeg；排除软件 OpenGL、PDF 图片、Qt 虚拟键盘和 Pillow AVIF 组件，保留 QtMultimedia |

## Windows 构建

需要 **64 位 Python 3.11～3.13**、**PowerShell 5.1 或 7+**。直接运行以下命令；默认自动准备修复 WebM 素材，显示大小、百分比和网速，已有动画保留：

```powershell
.\build-windows.ps1 -Zip
```

脚本创建 `.build/venvs/windows`，检查并补齐 Python 依赖，生成完整目录包和 ZIP。缺少合适 Python 时给出手动安装命令，例如 `winget install --id Python.Python.3.13 --exact`。

仓库追踪 `tools/ffmpeg.exe`：FFmpeg **7.1.5** + libvpx **1.17.0**，面向 Windows x86_64，保留 WebM / VP9 透明解码、缩放、帧率调整和 RGBA 输出。普通打包直接使用它。重编译见 [精简 FFmpeg](BUILDING.md#精简-ffmpeg)。

产物：`dist-windows/build-v0.5.1-opt.23/BailongPet/`。完整解压后运行 `BailongPet.exe`；用户机器无需另装 Python 或 FFmpeg。

opt.13 Windows 完整包约 **191.76 MiB ZIP / 256.67 MiB 解压后**，包含全部原始素材与依赖许可；此前 opt.11 目录为 349.31 MiB。

作者原入口 `work/build_windows.py`、`work/build_release.py` 继续保留。PowerShell 调用独立的 `work/build_windows_optimized.py`。

## macOS 与 Linux

| 平台 | 构建命令 |
| --- | --- |
| macOS | `bash build-macos.sh` |
| Debian / Ubuntu | `bash build-linux-debian.sh --install-deps` |
| Fedora / RHEL 系 | `bash build-linux-fedora.sh --install-deps` |
| Arch 系 | `bash build-linux-arch.sh --install-deps` |

应用包在目标系统构建。macOS 默认自动编译并复用本平台精简 FFmpeg，需要 Xcode Command Line Tools 与 pkg-config（`brew install pkgconf`）；可通过 `--ffmpeg` 指定。Linux 使用本平台 FFmpeg，跳过 Windows `.exe`。Linux 的 `--install-deps` 会安装系统依赖。

各入口均自动选择 64 位 Python 3.11～3.13，并按需补齐虚拟环境依赖。参数对应：Windows `-Python` / `-FFmpeg` / `-SkipInstall` / `-Archive`（或 `-Zip`），Bash `--python` / `--ffmpeg` / `--skip-install` / `--archive`。压缩产物：Windows、macOS 为 ZIP，Linux 为保留符号链接的 tar.gz；均只在本地生成。

Fedora 可使用 `bash build-linux-fedora.sh --rpm` 生成本地 RPM 试装包，需预装 `rpm-build`、`desktop-file-utils`。RPM 与 Fedora 压缩包均放在 `dist-linux/fedora-<architecture>/`；RPM 中间文件放 `.build/work/rpm/`，不加入 Git。

GitHub Actions 分别在 Windows、macOS Apple Silicon arm64、Debian 12、Fedora 44 和 Arch 环境构建；五个平台成功后，上传完整运行包到同一私有 Release。

Linux 短音效使用系统 `paplay`，Debian/Ubuntu、Fedora 安装 `pulseaudio-utils`，Arch 安装 `libpulse`。QtMultimedia 不再随 Linux 包分发；GTK 主题、桌面门户和输入法插件继续保留。

## 代码位置

| 文件 | 职责 |
| --- | --- |
| `app/pet.py` | 桌宠窗口、动作切换、气泡和托盘 |
| `app/video_frames.py`、`app/frame_buffer.py` | 解码管道与帧缓冲 |
| `app/performance_preferences.py` | 性能默认值与设置持久化 |
| `app/diagnostics.py`、`app/performance_metrics.py` | 统计窗口与资源采样 |
| `app/chat_ui.py`、`app/task_activity.py` | 对话界面与临时工具进度 |
| `work/build_common.py` | 共用打包、资源和许可文件整理 |
| `work/fetch_release_assets.py`、`work/package_assets.py` | 默认准备四段修复素材、生成带原作者来源说明的独立素材包 |
| `work/build_minimal_ffmpeg.py` | 固定源码版本、记录来源、编译精简解码器 |

## 数据与来源

对话、额度和桌面同步使用用户本机 Codex。macOS 历史保存在 `~/Library/Application Support/BailongPetOriginal`，与独立 Swift 工程分开。

素材来源见 [ASSETS.md](ASSETS.md)。FFmpeg 及 libvpx 的版本、源码地址和 SHA256 位于 `tools/ffmpeg-build.json`，许可位于 `tools/ffmpeg-licenses/`。本地构建产物会收集必需的依赖许可。
