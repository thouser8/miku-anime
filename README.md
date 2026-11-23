# Miku 动画

个人定制版的安卓 TV 追番客户端，基于 [Izuko TV](https://github.com/GrahamZen/izuko-tv)（[Animeko](https://github.com/open-ani/animeko) 的第三方修改版）构建。

## 开源说明

- **上游项目**：[GrahamZen/izuko-tv](https://github.com/GrahamZen/izuko-tv)，再上游为 [open-ani/animeko](https://github.com/open-ani/animeko)，作者 OpenAni and contributors。
- **许可证**：[GNU Affero General Public License v3.0](LICENSE.txt)。本仓库与其构建产物同样按 AGPLv3 发布。
- **与上游关系**：本仓库是个人修改版，**与 OpenAni 团队、Izuko TV 作者均无隶属关系，也未获其认可**。使用中遇到的问题请在本仓库反馈，不要打扰上游。
- **修改内容**：应用名、启动器图标与 TV 横幅、内置字体（苹方 PingFang SC）、移除工单反馈功能、更新下载镜像。除此之外的代码与功能均来自上游。

## 构建方式

本仓库**不保存上游源码**，只保存定制资产（`miku-assets/`）、定制脚本（`tools/`）和 CI 工作流。

每次构建由 [`.github/workflows/miku-auto.yml`](.github/workflows/miku-auto.yml) 完成：

1. 查询上游版本号最大的 release tag（`alpha` / `beta` / 正式版均纳入）；
2. 浅克隆该 tag 的上游源码；
3. 运行 `tools/miku-customize.py`，覆盖图标、字体实现、镜像清单，并完成改名与功能裁剪；
4. 下载苹方字体注入资源目录，签名构建；
5. 发布 Release，并附上本次构建对应的完整源码包。

想复现某次构建，取该 Release 附带的 `miku-<版本>-source.tar.gz`，即为对应源码（AGPLv3 意义上的对应源码）。

## 安装

在 [Releases](../../releases) 下载 `miku-<版本>-<abi>.apk`，不确定架构就下 `universal`。

- 需要 Android 8.1 及以上；Android 7.1 请用文件名含 `legacy` 的兼容包。
- 本构建使用**自签名证书**，与上游 Izuko TV 签名不同。从上游版本切换过来必须先卸载（会丢失本地数据）。
- 应用内更新默认走 alpha 渠道，构建好后会自动提示。

## 免责声明

仅供个人学习与自用。所有番剧内容来自第三方数据源，本仓库不提供、不托管任何视频内容。请遵守所在地法律法规。
