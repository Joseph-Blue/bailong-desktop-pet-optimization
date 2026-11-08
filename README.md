# 白龙桌宠 v0.5.1 · 优化与修复

基于 [jingh12312-rgb 原作者 v0.5.1](https://github.com/jingh12312-rgb/bailong-desktop-pet/tree/b102e734f20bb50889af12df5778f1499109f41b)，整理可反哺原项目的性能、界面和平台修复。沿用 Python、PySide6、FFmpeg 及原作者的角色与动作体系。

当前版本 **0.5.1-opt.23**，分支 `joseph/optimization`。仅发布 **Windows x86_64** 与 **macOS Apple Silicon arm64**；Linux 支援暂停，三阵营构建入口已移除。

[原作者版本改动对照](docs/原作者版本改动对照.md) · [构建说明](BUILDING.md) · [开发约定](DEVELOPMENT.md) · [更新记录](CHANGELOG.md) · [素材来源](ASSETS.md)

## 下载与使用

完整运行包见 [Release](https://github.com/Joseph-Blue/bailong-desktop-pet-optimization/releases/tag/v0.5.1-opt.23)。附件按平台完成后上传，页面只列已上传的下载链接。

- Windows：完整解压 ZIP，运行 `BailongPet/BailongPet.exe`；保留同目录的运行库、素材和解码器。
- macOS：解压后运行 `BailongPet.app`。包采用本地 ad-hoc 签名，未做 Apple 公证。
- 对话、额度和任务同步使用用户自己的 Codex 安装与登录；发布包不包含账号或历史记录。

## 相对作者版本的主要改动

| 范围 | 当前实现 |
| --- | --- |
| 动画加载 | 后台按当前动作解码，有限预加载；隐藏暂停，切换取消旧解码 |
| 性能设置 | 默认 512×512、12 帧、素材原帧率；最高 720×720；设置即时生效 |
| 性能统计 | FPS、主进程与 FFmpeg 的 CPU／RAM、帧缓冲、硬件和连接信息；悬停全文、复制信息，无分组“详情”按钮 |
| 任务与气泡 | 外部同步会话只读；工具状态临时显示；任务气泡按实际内容收缩，长结果可滚动，保留气泡“详情” |
| macOS | 修复 Space 标志冲突、失焦隐藏、数据目录冲突；桌宠、气泡及临时输入窗不跟入全屏空间 |
| 构建 | 两平台使用精简 FFmpeg；素材自动下载，显示大小、百分比和网速；不执行 SHA-256 校验 |
| 素材与图标 | 35 段中替换四段 Alpha 修复 WebM；Windows EXE 与 macOS App 图标使用修复 idle 第一帧 |

原作者已有的拖动、吸边、自移动、额度、对话、任务提醒与透明解码不计为本次新增。完整差异与验收状态见 [改动对照](docs/原作者版本改动对照.md)。

## 本地构建

使用目标平台的 64 位 Python 3.11～3.13。

```powershell
# Windows PowerShell 5.1 或 7+
.\build-windows.ps1 -Zip
```

```bash
# macOS；预先安装 Xcode Command Line Tools 与 pkg-config
bash build-macos.sh --archive
```

macOS 首次构建自动编译精简 FFmpeg，之后复用；Windows 使用仓库内的精简 `tools/ffmpeg.exe`。素材下载需要本私有仓库读取权限，可使用 GitHub CLI 登录或 `GH_TOKEN`／`GITHUB_TOKEN`。完整参数见 [BUILDING.md](BUILDING.md)。

## 素材与文档边界

角色素材作者为 **jingh12312-rgb**。默认使用 [修复素材包](docs/修复素材备选包.md)：idle、idle2、drag、landing 保留 720×720、24 FPS 和原时长，以透明 WebM 分发，其余 31 段保留作者原文件。

原作者的 `RELEASE_NOTES.md`、`BUILD_INFO.json`、`先看我-安装说明.txt` 及素材／运行库许可原样保留，记录的是原作版本；本轮说明以本 README、BUILDING、CHANGELOG 和改动对照为准。
