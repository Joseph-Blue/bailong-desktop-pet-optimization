# 白龙桌宠 · Python / Qt 优化分支

基于 [原作者 v0.5.1](https://github.com/jingh12312-rgb/bailong-desktop-pet)，基线提交 `b102e73`。沿用 Python、PySide6、FFmpeg 和原始动画素材，维护 Windows、macOS、Linux 构建入口。

当前版本 **0.5.1-opt.14**，分支 `joseph/optimization`。`opt.N` 表示本分支的迭代号，界面版本同时显示平台和架构。

[下载](https://github.com/Joseph-Blue/bailong-desktop-pet-optimization/releases) · [构建说明](BUILDING.md) · [更新记录](CHANGELOG.md) · [开发约定](DEVELOPMENT.md) · [给原作者的优化说明](优化说明.md)

## 实现变化

| 部分 | 当前实现 |
| --- | --- |
| 动画播放 | FFmpeg 通过管道输出透明 RGBA 帧，按当前动作解码；隐藏时暂停 |
| 默认设置 | 512×512、12 帧预加载、素材原帧率；整段预加载关闭 |
| 可调档位 | 满帧 / 20 / 15 FPS；预加载 6～240 帧，输入框与滑条同步 |
| 性能界面 | 双栏布局，窄窗口上下排列；长字段省略，悬停和详情显示全文 |
| 资源统计 | 运行内存 (RAM) 分列主进程与 FFmpeg；换页按主进程统计，Windows 私有提交量标“仅供参考” |
| 工具调用 | 显示临时进度和执行状态，长内容截断，不写入历史消息 |
| 字体 | Windows 沿用原作微软雅黑，其他平台使用系统字体；字号跟随系统，气泡缩小时保留正文大小 |
| Windows 包 | 精简 FFmpeg；排除软件 OpenGL、PDF 图片、Qt 虚拟键盘和 Pillow AVIF 组件，保留 QtMultimedia |

## Windows 构建

需要 **64 位 Python 3.11～3.13**、**PowerShell 5.1 或 7+**。将原作者完整包内的 `outputs/白龙桌宠素材` 放到仓库同名目录，再运行：

```powershell
.\build-windows.ps1 -Zip
```

脚本创建 `.venv-build-windows`，检查并补齐 Python 依赖，生成完整目录包和 ZIP。缺少合适 Python 时给出手动安装命令，例如 `winget install --id Python.Python.3.13 --exact`。

仓库追踪 `tools/ffmpeg.exe`：FFmpeg **7.1.5** + libvpx **1.17.0**，面向 Windows x86_64，保留 WebM / VP9 透明解码、缩放、帧率调整和 RGBA 输出。普通打包直接使用它。重编译见 [精简 FFmpeg](BUILDING.md#精简-ffmpeg)。

产物：`发布包/build-v0.5.1-opt.14/BailongPet/`。完整解压后运行 `BailongPet.exe`；用户机器无需另装 Python 或 FFmpeg。

opt.13 Windows 完整包约 **191.76 MiB ZIP / 256.67 MiB 解压后**，包含全部原始素材与依赖许可；此前 opt.11 目录为 349.31 MiB。

作者原入口 `work/build_windows.py`、`work/build_release.py` 继续保留。PowerShell 调用独立的 `work/build_windows_optimized.py`。

## macOS 与 Linux

| 平台 | 构建命令 |
| --- | --- |
| macOS | `PYTHON=python3.11 bash build-macos.sh` |
| Debian / Ubuntu | `bash build-linux-debian.sh --install-deps` |
| Fedora / RHEL 系 | `bash build-linux-fedora.sh --install-deps` |
| Arch 系 | `bash build-linux-arch.sh --install-deps` |

应用包在目标系统构建。macOS / Linux 使用本平台 FFmpeg，跳过 Windows `.exe`；可通过 `--ffmpeg` 指定，或使用 imageio-ffmpeg 提供的本机版本。Linux 的 `--install-deps` 会安装系统依赖。

Windows x86_64 是本次本机构建平台。macOS Apple Silicon arm64、Debian / Ubuntu、Fedora、Arch x86_64 使用独立自动构建任务，完成后上传到同一 Release。

## 代码位置

| 文件 | 职责 |
| --- | --- |
| `app/pet.py` | 桌宠窗口、动作切换、气泡和托盘 |
| `app/video_frames.py`、`app/frame_buffer.py` | 解码管道与帧缓冲 |
| `app/performance_preferences.py` | 性能默认值与设置持久化 |
| `app/diagnostics.py`、`app/performance_metrics.py` | 统计窗口与资源采样 |
| `app/chat_ui.py`、`app/task_activity.py` | 对话界面与临时工具进度 |
| `work/build_common.py` | 共用打包、资源和许可文件整理 |
| `work/build_minimal_ffmpeg.py` | 固定源码版本、校验摘要、编译精简解码器 |

## 数据与来源

对话、额度和桌面同步使用用户本机 Codex。macOS 历史保存在 `~/Library/Application Support/BailongPetOriginal`，与独立 Swift 工程分开。

素材来源见 [ASSETS.md](ASSETS.md)。FFmpeg 及 libvpx 的版本、源码地址和 SHA256 位于 `tools/ffmpeg-build.json`，许可位于 `tools/ffmpeg-licenses/`。Release 随包提供依赖许可和精简解码器源码附件。
