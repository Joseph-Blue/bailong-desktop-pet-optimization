# macOS 适配说明

这里是原作者 Python + PySide6 + FFmpeg 分支，不是 Swift/AppKit 工程。完整构建步骤见 [BUILDING.md](BUILDING.md)。

- Bash 入口：`PYTHON=python3.11 bash build-macos.sh`；低层入口 `work/build_macos.py` 保留。
- 输出 `dist-macos/BailongPet.app`，按当前 Python 架构构建，包含原版 WebM 素材与本机 FFmpeg。当前只执行过 Apple Silicon 构建。
- 素材来自作者原始完整包；无需运行 Windows EXE，不使用 Swift 转换后的 HEVC。
- 用户数据目录为 `~/Library/Application Support/BailongPetOriginal`；不与历史 Python 移植版或 Swift 版混用。
- 已实现 Qt 工具窗口失焦保留、置顶层级和互斥 Space 标志修复，菜单含性能设置、统计与关于。
- 构建后执行本地 ad-hoc 签名；没有正式签名或公证。当前不提供 Release。
- 实机仍需核对多屏、Space、全屏、菜单栏、音效、退出、跟随启动，以及本机 Codex 对话与只读观察。构建通过不代表这些行为已经全部验收。
