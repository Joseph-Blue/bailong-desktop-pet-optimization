# 开发说明

本分支为作者 v0.5.1 的 Python／PySide6／FFmpeg 优化分支，作者基线不随 opt 迭代改变。

- 构建、依赖和实机验证统一见 [BUILDING.md](BUILDING.md)。Windows 使用 PowerShell 5.1／7+；macOS 与 Linux 使用 Bash。
- 运行入口 `app/pet.py`，资源定位在 `app/platform_support.py`；有限预加载在 `app/frame_buffer.py`，FFmpeg 管道在 `app/video_frames.py`。
- `work/build_common.py` 共用素材清单、FFmpeg 检查和目录整理；优化入口为 `work/build_windows_optimized.py`、`work/build_macos.py` 和 `work/build_linux.py`，指定目标系统及其打包选项，拒绝交叉编译。
- Windows 自动化入口先通过 `work/check_build_dependencies.py` 检查锁定包，再执行 `pip check`；仅缺失或冲突时安装。`-Zip`／`--zip` 从新构建目录生成本地 ZIP 与 SHA256，取代旧发行脚本在当前流程中的压缩职责。
- 版本来源 `app/version.py`，同步维护 `VERSION.txt`、README、BUILDING 和 CHANGELOG。
- UI 修改必须使用 Qt 官方 `qt-ui-design` skill，具体规范见 [AGENTS.md](AGENTS.md)。该 skill 不参与应用运行和构建。
- 私人仓库追踪源码、文档和指定的 Windows 精简 FFmpeg；应用包通过 Release 交付。本机素材、构建环境、缓存与用户历史不入 Git。
- `work/build_windows.py` 保留作者原版内容，配合原发行脚本 `work/build_release.py` 使用；后者维护当前运行模块清单。根目录旧 `BUILD_INFO.json`／`RELEASE_NOTES.md` 保留作者发行记录。PS 自动化入口使用独立优化版，不调用原发行脚本。
- 跨平台分支只修改本仓库，不修改相邻 Swift 工程或历史 Python macOS 移植工程。

## 文件追踪范围

| 内容 | 处理方式 |
| --- | --- |
| `app/` 运行源码、依赖清单 | 追踪，运行和构建需要 |
| 作者原有测试与 `app/selftest.py` | 继续追踪，保留原有检查能力 |
| `build-windows.ps1`、各平台构建入口、`work/` 构建模块和 hook | 追踪，原 Windows 脚本与优化版并存 |
| `app/sounds/` 音效与许可说明 | 保留作者原有文件 |
| README、构建／开发／优化说明、CHANGELOG、版本与项目约定 | 追踪 |
| 作者原有 `BUILD_INFO.json`、`RELEASE_NOTES.md`、安装说明 | 保留历史发行记录 |
| 本分支新增的 11 个测试文件 | 取消追踪，保留本地并按文件名忽略 |
| `.build*/`、虚拟环境、程序包、视觉检查截图、缓存、日志、用户数据 | 不追踪 |
| `outputs/`、`work/video-deps/` | 不追踪；素材在构建时准备 |
| `tools/ffmpeg.exe`、版本记录与许可 | 按用户要求追踪 Windows x86_64 精简解码器 |

忽略规则不删除本地文件，也不改写已有 Git 历史。视觉校验产物存放在 `.build-ui-review/`，已被 `.build*/` 覆盖。

## 定向检查

使用构建虚拟环境的 Python，在仓库根目录按改动执行。例如：

```bash
PYTHONPATH=app .venv/bin/python -m unittest test_chat test_session_reuse
for script in build-macos.sh build-linux-*.sh work/build_linux.sh; do bash -n "$script" || break; done
```

Qt 组件检查可设置 `QT_QPA_PLATFORM=offscreen`。不以 offscreen 检查替代窗口、置顶、透明度和真实对话验收；不自动发送 Codex 请求。

本分支新增的构建、性能和界面验证脚本只保留在本机，不作为仓库使用或构建的前置条件。后续临时检查同样放入忽略目录。

2026-11-08：opt.9 的性能默认值、设置持久化、帧率降采样、VP9 透明度、整段预加载与取消切换测试通过；Windows 已读取真实系统已提交内存计数。两个窗口以离屏渲染检查浅色／深色、150% 缩放、16 pt 大字体、窄窗口分栏切换及仅关闭按钮标志。Windows 原生标题栏外观、macOS／Linux 桌面窗口行为仍需实机验收。

opt.9 布局修正：使用长 CPU／GPU 名称和 13 个桌面进程验证等宽双栏、窄窗口排列与复制全文；路径链接指向所在目录。Windows PowerShell 5.1／7 的解释器失败路径显示 winget 手动安装命令，测试不执行安装。

opt.10：构建瘦身规则见 `work/hooks/windows/` 和 `work/build_common.py`。增加界面或素材格式时复核插件排除清单。保留 PyInstaller 上游 Qt 依赖收集逻辑，不在打包后按 DLL 名称批量删除运行库。

opt.13：35 段动画完整 RGBA 输出与原 FFmpeg 逐字节一致，Windows 冻结 EXE 离线自检通过；新增 macOS arm64 和三类 Linux x86_64 自动构建。
