# GPT白龙娘动态桌宠 v0.5.1

当前反哺分支：`joseph/optimization`，版本 `0.5.1-opt.6`，保留作者 `0.5.1` 基线。变更见 [CHANGELOG](CHANGELOG.md)。按 Windows／macOS／Linux 共用 Qt 实现维护，当前仅构建 Apple Silicon 本机测试包。

两套构建入口均随本分支维护：[macOS 应用构建](work/build_macos.py)、[Windows 应用构建](work/build_windows.py)。分别在对应系统运行；Windows 完整包整理入口为 [build_release.py](work/build_release.py)。

Windows轻量版：自移动、吸边探头、大小调节、Codex公开任务进展提醒，35段透明WebM动画。

普通使用者请到[发布页](https://github.com/jingh12312-rgb/bailong-desktop-pet/releases/tag/v0.5.1)下载 `bailong-desktop-pet-v0.5.1-windows-x64-webm.zip`，全部解压后双击 `BailongPet.exe`。

## 开发者运行

此仓库提供v0.5.1轻量版源码；动画素材和Windows解码器随上述完整发布包提供，没有纳入Git历史。

1. 安装64位Python（当前构建使用Python 3.13）。
2. 在源码目录执行 `python -m pip install -r requirements.txt`。
3. 从完整Windows发布包复制整个 `outputs` 和 `tools` 文件夹到源码根目录，与 `app` 并列。保留全部35段WebM及素材清单。
4. 执行 `python app/pet.py`；自检执行 `python app/pet.py --self-test`。

程序通过 FFmpeg 的 libvpx-vp9 解码透明通道。启动仅读取默认待机首帧，后台默认预读当前动作的 24 帧，不再把全部动作常驻运行内存 (RAM)。右键／托盘菜单的“性能设置…”可选择解码分辨率和预加载帧数；“性能统计…”分别显示主程序与 FFmpeg 的用量。

## 构建Windows包

在Windows上安装PyInstaller 6.22.3至 `.build-tools`：`python -m pip install --target .build-tools pyinstaller==6.22.3`。

运行 `python work/build_windows.py` 生成EXE。重新整理完整ZIP使用 `python work/build_release.py`，需要先将FFmpeg放在 `work/video-deps/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe`（可从完整包的tools/ffmpeg.exe复制），并保留outputs素材。脚本会生成带运行库、解码器及素材的发布包。

## 说明

没有Codex也能使用普通桌宠功能。额度、对话与任务同步需要使用者自己的Codex安装和登录。仓库不包含账号、密钥、个人聊天记录。

macOS 本机测试包使用 `requirements-macos.txt` 和 `python work/build_macos.py` 构建，WebM 解码器随应用打包。当前完整交互与长时间运行仍待实机验收；本分支尚未构建或验收 Windows／Linux。

源码尚未指定开源许可证；公开源码不代表授予任意使用或再分发许可。美术素材说明见ASSETS.md，运行库遵循各自许可证。本项目非OpenAI官方产品。
