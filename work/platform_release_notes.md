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

- Linux 统一直接运行与 run.sh 的 XCB 启动路径，补齐 fcitx5 输入法和 Codex Desktop CLI 查找。
- 修复 Linux 音效与连续点击时气泡文字裁切；应用图标与待机/托盘图标一致。
- Linux 排除 PDF、虚拟键盘、AVIF 和 QtMultimedia 依赖；原始动画保持不变，GTK 主题插件保留。
- 构建脚本统一使用方式：Windows 为 PowerShell，macOS/Linux 为 Bash；可运行产物放在可见的 dist 目录。

[更新记录](https://github.com/{{REPO}}/blob/{{TAG}}/CHANGELOG.md) · [构建说明、运行依赖与数据目录](https://github.com/{{REPO}}/blob/{{TAG}}/BUILDING.md) · [项目主页](https://github.com/{{REPO}}/tree/{{TAG}}) · [素材说明](https://github.com/{{REPO}}/blob/{{TAG}}/ASSETS.md) · [原作者项目](https://github.com/jingh12312-rgb/bailong-desktop-pet)

包构建完成不代表五个平台均已完成人工界面验收。下载运行包请使用上方平台链接；页面底部的 Source code 是 GitHub 自动生成的源码快照。
