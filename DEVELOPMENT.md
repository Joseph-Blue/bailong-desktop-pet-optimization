# 开发说明

本分支为作者 v0.5.1 的 Python／PySide6／FFmpeg 优化分支，作者基线不随 opt 迭代改变。

- 构建、依赖和实机验证统一见 [BUILDING.md](BUILDING.md)。Windows 使用 PowerShell 5.1／7+；macOS 与 Linux 使用 Bash。
- 运行入口 `app/pet.py`，资源定位在 `app/platform_support.py`；有限预加载在 `app/frame_buffer.py`，FFmpeg 管道在 `app/video_frames.py`。
- `work/build_common.py` 共用素材清单、FFmpeg 检查和目录整理；三个 `work/build_*.py` 入口指定目标系统及其打包选项，拒绝交叉编译。
- Windows 自动化入口先通过 `work/check_build_dependencies.py` 检查锁定包，再执行 `pip check`；仅缺失或冲突时安装。`-Zip`／`--zip` 从新构建目录生成本地 ZIP 与 SHA256，取代旧发行脚本在当前流程中的压缩职责。
- 版本来源 `app/version.py`，同步维护 `VERSION.txt`、README、BUILDING 和 CHANGELOG。
- UI 修改必须使用 Qt 官方 `qt-ui-design` skill，具体规范见 [AGENTS.md](AGENTS.md)。该 skill 不参与应用运行和构建。
- 仅将源码和文档提交到私人仓库；不追踪本机素材、程序、构建环境、缓存或用户历史，不创建 Release。
- `work/build_release.py`、根目录旧 `BUILD_INFO.json`／`RELEASE_NOTES.md` 保留原作者发行流程记录，新构建入口不调用旧发行脚本。
- 跨平台分支只修改本仓库，不修改相邻 Swift 工程或历史 Python macOS 移植工程。

## 定向检查

使用构建虚拟环境的 Python，在仓库根目录按改动执行。例如：

```bash
PYTHONPATH=app .venv/bin/python -m unittest test_frame_buffer test_session_reuse
for script in build-macos.sh build-linux-*.sh work/build_linux.sh; do bash -n "$script" || break; done
```

Qt 组件检查可设置 `QT_QPA_PLATFORM=offscreen`。不以 offscreen 检查替代窗口、置顶、透明度和真实对话验收；不自动发送 Codex 请求。

Windows 构建流程离线回归：`python -m unittest discover -s work -p "test_build*.py" -v`。测试会使用已安装的 Windows PowerShell／pwsh，在临时目录中创建测试 venv，并替代 pip 和实际打包模块；不联网安装项目依赖，不执行真实 PyInstaller 构建。ZIP 测试只使用人工测试文件。

2026-11-08：opt.9 的性能默认值、设置持久化、帧率降采样、VP9 透明度、整段预加载与取消切换测试通过；Windows 已读取真实系统已提交内存计数。两个窗口以离屏渲染检查浅色／深色、150% 缩放、16 pt 大字体、窄窗口分栏切换及仅关闭按钮标志。Windows 原生标题栏外观、macOS／Linux 桌面窗口行为仍需实机验收。
