# 开发说明

本分支为作者 v0.5.1 的 Python／PySide6／FFmpeg 优化分支，作者基线不随 opt 迭代改变。

- 构建、依赖和实机验证统一见 [BUILDING.md](BUILDING.md)。Windows 只使用 PowerShell 7+；macOS 与 Linux 使用 Bash。
- 运行入口 `app/pet.py`，资源定位在 `app/platform_support.py`；有限预加载在 `app/frame_buffer.py`，FFmpeg 管道在 `app/video_frames.py`。
- `work/build_common.py` 共用素材清单、FFmpeg 检查和目录整理；三个 `work/build_*.py` 入口只指定目标系统，拒绝交叉编译。
- 版本来源 `app/version.py`，同步维护 `VERSION.txt`、README、BUILDING 和 CHANGELOG。
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
