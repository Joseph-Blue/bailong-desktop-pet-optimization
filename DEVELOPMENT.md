# 开发说明

本仓库整理面向原作者 v0.5.1 的优化和修复；作者基线为 `b102e73`，版本只调整 `opt` 后缀。当前交付 Windows x86_64 与 macOS arm64，Linux 支援暂停。

## 代码与入口

| 位置 | 职责 |
| --- | --- |
| `app/pet.py` | 桌宠、动作、气泡和托盘 |
| `app/frame_buffer.py`、`app/video_frames.py` | 当前动作有限预加载与透明解码 |
| `app/performance_preferences.py`、`app/performance_settings.py` | 性能默认值、持久化和即时设置 |
| `app/diagnostics.py`、`app/performance_metrics.py` | 性能统计与平台资源采样 |
| `app/chat_ui.py`、`app/task_activity.py`、`app/desktop_task_sync.py` | 自有会话、外部只读观察与临时工具状态 |
| `app/platform_support.py` | 平台窗口、资源与用户数据路径 |
| `build-windows.ps1`、`work/build_windows_optimized.py` | Windows 完整包与 ZIP |
| `build-macos.sh`、`work/build_macos.py` | macOS 本机架构应用与 ZIP |
| `work/build_common.py` | 两平台素材、运行库、图标与许可整理 |
| `work/build_minimal_ffmpeg.py` | 精简解码器编译；保留 WSL 编译 Windows 解码器的工具用途 |
| `work/fetch_release_assets.py`、`work/package_assets.py` | 默认修复素材的下载与封装 |

macOS 默认复用 `.build/ffmpeg/darwin-<架构>/bin/ffmpeg`，缺失时自动编译；Windows 默认使用 `tools/ffmpeg.exe`。显式 FFmpeg 参数优先。具体依赖与命令见 [BUILDING.md](BUILDING.md)。

## 协作与追踪

- 原作者目录及相邻 Swift／旧 Python 移植工程只作只读参考，按需移植具体逻辑，不整仓复制。
- 原 Windows 入口 `work/build_windows.py`、`work/build_release.py` 保留；PowerShell 使用独立优化入口。
- Linux 三阵营脚本、RPM 工具和 CI 任务已移除。运行源码中的既有平台分支保留，不作为当前支持或发布承诺。
- 不新增猜测性兼容层或静默吞错。Qt 界面沿用系统字体、原生控件与平台字号；不再要求安装 `qt-ui-design` skill。
- 版本来源为 `app/version.py`，同步 `VERSION.txt`、当前文档与工作流默认标签。
- 本地提交、推送和发布按当次授权执行。CI 允许两平台分批上传，不用一个平台的失败阻塞另一个已有产物。

| 内容 | Git 处理 |
| --- | --- |
| 应用源码、构建脚本、依赖清单、我们维护的说明 | 追踪 |
| 作者原有测试、音效、来源和许可 | 保留；不自动执行测试或自检 |
| `app/icons/repaired-idle.png` | 用户指定的构建图标，追踪 |
| `tools/ffmpeg.exe`、来源记录与许可 | 用户指定的 Windows 精简解码器，追踪 |
| 原作者 `BUILD_INFO.json`、`RELEASE_NOTES.md`、原始安装说明 | 保留原样，作为作者发行记录 |
| 动画、`.build*/`、`dist-*`、虚拟环境、缓存、用户数据、本地验证脚本 | 不追踪；动画通过独立素材 Release 提供 |

## 检查与验收

代码修改只做必要语法、静态与差异检查；构建属于当前授权时再执行。不自动运行 SHA-256、测试、自检、冒烟、截图或视觉流程。

构建成功与实机验收分别记录。历史 opt 版本的检查结果见 [CHANGELOG.md](CHANGELOG.md)，不作为当前版本已验收的依据。文档修改只检查格式和本地链接。

## 文档分工

- [README](README.md)：当前交付范围、下载与快速入口。
- [改动对照](docs/原作者版本改动对照.md)：只对照作者 v0.5.1 的最终改动。
- [BUILDING](BUILDING.md)：Windows／macOS 的构建、素材和发布。
- [MAC适配说明](MAC适配说明.md)：macOS 平台差异与验收边界。
- [ASSETS](ASSETS.md)、[修复素材说明](docs/修复素材备选包.md)：来源、替换范围与参数。
- [CHANGELOG](CHANGELOG.md)：保留历史迭代，当前支持范围以 README 为准。
