# 项目约定

## UI 修改必用 skill

修改本项目的 Qt 窗口、控件、布局或界面文案前，必须读取并应用
`$CODEX_HOME/skills/qt-ui-design/SKILL.md`（默认 `~/.codex/skills/qt-ui-design/SKILL.md`）。
来源：[Qt 官方 qt-ui-design](https://github.com/TheQtCompanyRnD/agent-skills/tree/main/skills/qt-ui-design)。
未安装时通过 skill-installer 安装该 skill。它是本项目的 UI 工作规范，不是应用运行或构建依赖。

- 保持 PySide6 Widgets，使用系统字体、原生控件和 QPalette；不引入 QML、网页组件或自绘窗口标题栏。
- 面向 Windows、macOS、Linux 桌面，支持简体中文、鼠标及键盘；以 Windows 150% 缩放验收，补查浅色、深色、大字体和窄窗口。
- 性能设置左栏为分辨率、运行帧率；右栏为预加载帧数、整段动画预加载。窄窗口按栏上下排列。
- 性能统计按播放、资源、硬件与版本、连接与任务分组分栏。两个性能窗口标题栏只保留关闭 X，不重复添加底部关闭按钮，Escape 关闭。
- UI 文案直接表达名称、数值和状态，禁止防御性、模棱两可或重复解释的文字。统计失败显示实际错误，不把失败写成零。
- Windows 显示系统虚拟内存已提交量与上限；Linux/macOS 显示 Swap 已用与总量。只展示当前平台已实现的指标。
- 性能默认值统一维护在 `app/performance_preferences.py`，保留用户已有有效设置。范围和档位参照独立 Swift 项目；不修改相邻工程。
- 检查键盘焦点、滑条与输入框同步、开关状态、DPI 和文字裁切；离屏截图只验证布局，实机窗口行为单独记录。

## 交付

- 同步更新版本和 CHANGELOG。仅按用户授权本地提交或推送。
- 不提交素材、虚拟环境、构建产物、用户配置和账号数据。
