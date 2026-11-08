# 白龙桌宠 {{TAG}}

五个平台独立构建的完整运行包，包含 Python/Qt、FFmpeg、完整动画和音效。解压整个目录后运行，保留附带的依赖和素材文件。

## 下载

| 平台 | 完整运行包 |
| --- | --- |
| Windows x86_64 | [下载 ZIP](https://github.com/{{REPO}}/releases/download/{{TAG}}/bailong-desktop-pet-{{TAG}}-windows-x86_64.zip) |
| macOS Apple Silicon arm64 | [下载 ZIP](https://github.com/{{REPO}}/releases/download/{{TAG}}/bailong-desktop-pet-{{TAG}}-macos-arm64.zip) |
| Debian / Ubuntu x86_64 | [下载 tar.gz](https://github.com/{{REPO}}/releases/download/{{TAG}}/bailong-desktop-pet-{{TAG}}-linux-debian-x86_64.tar.gz) |
| Arch Linux x86_64 | [下载 tar.gz](https://github.com/{{REPO}}/releases/download/{{TAG}}/bailong-desktop-pet-{{TAG}}-linux-arch-x86_64.tar.gz) |
| Fedora 44 x86_64 | [下载 tar.gz](https://github.com/{{REPO}}/releases/download/{{TAG}}/bailong-desktop-pet-{{TAG}}-linux-fedora-x86_64.tar.gz) |

Linux 包按发行版阵营区分。Fedora 包在 Fedora 44 构建；Debian 包在 Debian 12 构建；Arch 包在当前 Arch 环境构建。使用自己的阵营包。

## 运行

- Windows：运行 `BailongPet/BailongPet.exe`。
- macOS：运行 `BailongPet.app`。应用采用本地 ad-hoc 签名，未做 Apple 公证。
- Linux：运行 `BailongPet/BailongPet` 或 `BailongPet/run.sh`。默认使用 X11/XWayland，中文输入通过 IBus 协议接入 fcitx5/IBus；保留用户显式设置的 Qt 环境变量。
- Linux 短音效使用系统 `paplay`。Debian/Ubuntu：`sudo apt install pulseaudio-utils`；Fedora：`sudo dnf install pulseaudio-utils`；Arch：`sudo pacman -S libpulse`。兼容提供 PulseAudio 接口的 PipeWire 桌面。
- Codex 对话、额度与同步功能使用用户自己的 Codex 安装和登录；运行包不包含账号或聊天记录。

## 本轮变化与说明

- 任务进度和完成气泡按实际文字高度收缩，长内容变短时收回空白；长结果仍可滚动。
- 性能设置即时保存并生效，移除“应用”按钮；全新配置和恢复默认使用 512×512。
- 桌宠角色窗口关闭系统阴影；Windows EXE 与 macOS App 使用修复 idle 第一帧图标。
- macOS 修复前台小窗口及刘海安全区域导致的全屏漏判；Windows 检测逻辑不变。
- macOS 构建默认自动编译并复用精简 FFmpeg；素材下载显示已下载／总大小、百分比和实时网速。
- 四段修复素材采用 720×720、24 FPS 的透明 WebM，保留最高画质档位，默认播放仍为 512×512。
- 提供[四段修复备选素材包](https://github.com/{{REPO}}/releases/tag/v0.5.1-opt.assets.repaired.2)，所有构建脚本默认使用该包，原始包另行保留。
- 所有应用构建入口自动准备修复素材；原版清单自动切换，已有动画文件保留。素材来自原作者 **jingh12312-rgb**；下载私有仓库附件需要相应 GitHub 权限。

[更新记录](https://github.com/{{REPO}}/blob/{{TAG}}/CHANGELOG.md) · [构建说明、运行依赖与数据目录](https://github.com/{{REPO}}/blob/{{TAG}}/BUILDING.md) · [项目主页](https://github.com/{{REPO}}/tree/{{TAG}}) · [素材说明](https://github.com/{{REPO}}/blob/{{TAG}}/ASSETS.md) · [原作者项目](https://github.com/jingh12312-rgb/bailong-desktop-pet)

包构建完成不代表五个平台均已完成人工界面验收。下载运行包请使用上方平台链接；页面底部的 Source code 是 GitHub 自动生成的源码快照。
