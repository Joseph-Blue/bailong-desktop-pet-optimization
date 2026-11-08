# 白龙桌宠 · 原技术栈优化分支

基于 [jingh12312-rgb/bailong-desktop-pet](https://github.com/jingh12312-rgb/bailong-desktop-pet) 的 `b102e73 / v0.5.1`，保留 Python + PySide6 + FFmpeg 和作者原始素材。与独立 Swift/AppKit 项目分开维护。

当前版本 **0.5.1-opt.11**，分支 **joseph/optimization**。作者版本号保留，`opt.N` 是本分支的 SemVer 预发布迭代号。私人源码仓库：[Joseph-Blue/bailong-desktop-pet-optimization](https://github.com/Joseph-Blue/bailong-desktop-pet-optimization)。**本仓库不提供 Release，也不上传构建产物或动画素材。**

## 本分支的变化

- 动画按需解码，各平台默认 512×512、12 帧缓冲、满帧；帧率档位与 Swift 版一致，为满帧／20／15 FPS，保持动作时长和 VP9 透明度。当前素材满帧为 24 或 30 FPS。
- 缓冲支持输入框与 6～240 帧滑条；整段动画预加载默认关闭，开启时仅预加载当前动作，保留并禁用缓冲设置。
- 性能设置和统计采用双栏布局，窄窗口自动上下排列。统计显示 FPS、CPU、CPU／GPU 型号和运行内存 (RAM)，GPU 摘要优先显示已识别的独显，长字段悬停显示全文。桌宠运行内存 (RAM) 为主进程与 FFmpeg 合计，换页数据单独按主进程统计。
- macOS 窗口置顶、跨 Space、独立历史目录、Codex 可执行文件定位及 Command 提示修正。
- 桌宠自有对话与 Codex 只读同步记录区分，避免误恢复外部占用的会话。工具调用显示为临时进度，长内容省略、不写入聊天历史；单次调用失败不再触发持续任务告警。
- Windows、macOS 和三类 Linux 构建入口随源码维护。FFmpeg 仅保留一份，Windows 构建排除未使用的 PDF、Qt 虚拟键盘和 Pillow AVIF 组件。

给原作者的说明见 [优化说明.md](优化说明.md)。详细变化见 [CHANGELOG.md](CHANGELOG.md)，完整准备、命令、产物路径和实机验收见 [BUILDING.md](BUILDING.md)。

## 构建入口

先将[原作者 v0.5.1 完整包](https://github.com/jingh12312-rgb/bailong-desktop-pet/releases/tag/v0.5.1)中的 `outputs/白龙桌宠素材` 放入本仓库同名路径，并准备 64 位 Python 3.11～3.13。

| 平台 | 本机命令 |
| --- | --- |
| Windows · PowerShell 5.1／7+ | `./build-windows.ps1` |
| macOS · Bash | `PYTHON=python3.11 bash build-macos.sh` |
| Debian / Ubuntu | `bash build-linux-debian.sh --install-deps` |
| Fedora / RHEL 系 | `bash build-linux-fedora.sh --install-deps` |
| Arch 系 | `bash build-linux-arch.sh --install-deps` |

各平台构建自己的架构，不能在 Mac 生成 Windows／Linux 程序。脚本默认创建独立虚拟环境并打包；Windows 会先检查 Python、pip 和锁定依赖，仅在缺失、版本不符或存在依赖冲突时补装。Linux 的 `--install-deps` 才会安装系统依赖。可指定 FFmpeg，或使用构建依赖提供的本机版本，详见构建文档。

Windows 使用 `./build-windows.ps1 -Zip` 可同时生成完整本地 ZIP 和 SHA256；依赖齐全后可加 `-SkipInstall`。不必安装 PowerShell 7，也不必手工准备原作的 `.build-tools` 或旧 FFmpeg 路径。运行已构建的完整包不需要另装 Python／PyInstaller。所需环境、原作步骤对应关系与手动命令见 [BUILDING.md](BUILDING.md)。

macOS Apple Silicon 已执行构建；Windows／Linux 脚本待对应实机验证。Linux 的全屏自动检测、跟随启动尚未接入，原生 Wayland 窗口行为也未验收。

## 运行与数据

源码运行：安装 `requirements.txt`；macOS 另安装 `requirements-macos.txt`，然后执行 `python app/pet.py`，并准备可用 FFmpeg。无 Codex 时可使用普通桌宠功能；对话、额度与同步使用本机的 Codex 安装和登录。

macOS 原技术栈版的用户历史位于 `~/Library/Application Support/BailongPetOriginal`，不与 Swift 版共享。构建不读取账号、密钥或聊天正文，不把用户数据放入产物。

## 来源与许可

保留原作者提交历史和来源。源码尚未指定开源许可证；公开可见不代表授予任意使用或再分发许可。角色素材说明见 [ASSETS.md](ASSETS.md)，运行库遵循各自许可证。原作者的 Release 链接仅用于取得素材，不是本分支的发行入口。本项目非 OpenAI 官方产品。
