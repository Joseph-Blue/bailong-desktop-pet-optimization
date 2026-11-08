# 白龙桌宠 {{TAG}}

五个平台独立构建的完整运行包，包含 Python/Qt、FFmpeg、原始动画和音效。解压整个目录后运行，保留附带的依赖和素材文件。

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
- 桌宠角色窗口关闭系统阴影，原始素材不变。
- 所有应用构建入口自动补齐缺失素材；已有文件不覆盖。素材来自原作者 **jingh12312-rgb**，本仓库仅整理[独立素材包](https://github.com/{{REPO}}/releases/tag/v0.5.1-opt.assets.1)，没有 GitHub 登录时使用作者公开发布包。

[更新记录](https://github.com/{{REPO}}/blob/{{TAG}}/CHANGELOG.md) · [构建说明、运行依赖与数据目录](https://github.com/{{REPO}}/blob/{{TAG}}/BUILDING.md) · [项目主页](https://github.com/{{REPO}}/tree/{{TAG}}) · [素材说明](https://github.com/{{REPO}}/blob/{{TAG}}/ASSETS.md) · [原作者项目](https://github.com/jingh12312-rgb/bailong-desktop-pet)

包构建完成不代表五个平台均已完成人工界面验收。下载运行包请使用上方平台链接；页面底部的 Source code 是 GitHub 自动生成的源码快照。
