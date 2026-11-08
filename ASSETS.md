# 原作者素材来源

- 原项目作者：**jingh12312-rgb**。
- 原仓库：https://github.com/jingh12312-rgb/bailong-desktop-pet
- 原始素材版本：**v0.5.1**，共 35 段动画及对应素材清单。
- 原始发布：https://github.com/jingh12312-rgb/bailong-desktop-pet/releases/tag/v0.5.1
- 本分支仅整理独立素材包，方便构建时自动获取；动画与透明边缘未重新绘制，素材创作不归本分支所有。
- 独立素材包：https://github.com/Joseph-Blue/bailong-desktop-pet-optimization/releases/tag/v0.5.1-opt.assets.1
- 修复备选包：https://github.com/Joseph-Blue/bailong-desktop-pet-optimization/releases/tag/v0.5.1-opt.assets.repaired.1

原始包保留全部原始动画；修复备选包仅替换 idle、idle2、drag、landing 四段，其余 31 段保持原样。修复使用本项目 2026-11-07 的 Alpha 清理结果，以无损 APNG 分发；来源、范围和使用方法见 [修复素材备选包](docs/修复素材备选包.md)。默认自动下载仍选择原始包。

Windows EXE 与 macOS App 图标使用同批修复 idle 的第一帧。`app/icons/repaired-idle.png` 为该帧原样副本，构建时导出 ICO／ICNS，不重绘角色、不增加底色或阴影。

原作者说明：素材随 Releases 发布，不纳入 Git 历史。35 段动画来自项目作者提供的角色素材及透明处理版本。未额外授予美术素材商用或再分发许可。

缺少素材时构建脚本自动获取；已有素材文件不会覆盖。有 GitHub 登录时使用本仓库素材包，没有登录时使用原作者公开完整包中的 `outputs`。本仓库为私有仓库，素材包访问权限沿用仓库设置。
