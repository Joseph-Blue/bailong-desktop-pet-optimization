# macOS 适配说明

本工程是在原作者 Python／PySide6／FFmpeg 源码上做适配和修复，窗口仍为 Qt；不是相邻的 Swift/AppKit 工程。

## 构建与资源

- 入口：`bash build-macos.sh --archive`；直接 Python 入口为 `work/build_macos.py`。
- 需要 64 位 Python 3.11～3.13、Xcode Command Line Tools 与 pkg-config（`brew install pkgconf`）。
- 默认自动编译并复用本机架构精简 FFmpeg；保留透明 VP9 解码、缩放、帧率调整和 RGBA 输出。可用 `--ffmpeg` 指定其他解码器。
- 默认下载完整修复素材包：31 段作者原始 WebM 加四段 720×720、24 FPS 修复 WebM。最高播放画质 720×720，默认 512×512。
- 产物为 `dist-macos/BailongPet.app` 与对应 ZIP；Windows EXE 不参与 Mac 运行，也不使用 Swift 工程的 HEVC 运行素材。
- 当前发布 Apple Silicon arm64。本机架构构建能力不等于 Intel 已验收或本轮提供 Intel 包。
- 应用采用本地 ad-hoc 签名，未做 Developer ID 签名或公证。完整步骤见 [BUILDING.md](BUILDING.md)。

## 平台修复

- Qt 工具窗口清除与 `CanJoinAllSpaces` 冲突的 `MoveToActiveSpace`；保持失焦可见与浮动层级。
- 参照用户指定原生工程，桌宠、气泡和临时输入窗使用 `FullScreenNone`，不跟入全屏空间。辅助检测遍历前台普通窗口并比较完整屏幕边界，不扣安全区域，不使用系统呈现状态判断。
- “填充”与“全屏”分别处理；这套 Qt 实现的实际切换效果仍需用户确认。Windows 检测逻辑不变。
- 默认数据目录为 `~/Library/Application Support/BailongPetOriginal`，避免与旧 Python 移植版历史格式冲突；显式数据目录配置保留。
- Codex 查找在显式配置之后优先使用桌面应用内置 CLI；外部同步记录只读，桌宠不接管外部写入权。
- 输入提示使用 Command+Enter，性能设置即时生效；性能统计移除“详情”按钮，气泡详情保留。

## 验收

已执行 Apple Silicon 本地构建和签名。多屏、Space、填充与全屏、临时输入窗、菜单栏、音效、退出和 Codex 对话效果由用户实机确认；编译通过不代替上述验收。
