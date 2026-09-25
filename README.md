<div align="center">

# 🛡️ Surge · Egern 配置模板

殊途同归 · 久用如一

[![Surge](https://img.shields.io/badge/Surge-iOS%20%7C%20macOS-1f6feb?style=flat-square)](#-两全其美--皆合心意)
[![Egern](https://img.shields.io/badge/Egern-iOS%20%7C%20macOS-0969da?style=flat-square)](#-两全其美--皆合心意)
[![Groups](https://img.shields.io/badge/Groups-26%20%7C%2026-8250df?style=flat-square)](#-井然有序)
[![Rules](https://img.shields.io/badge/Rules-24%20%7C%2024%20%E5%B7%B2%E5%AF%B9%E9%BD%90-dc3545?style=flat-square)](docs/跨内核差异对照.md)
[![DNS](https://img.shields.io/badge/DNS-Zero%20Leak-2ea043?style=flat-square)](#-隐私至上--无-dns-泄露)
[![License](https://img.shields.io/badge/License-MIT-dfb317?style=flat-square)](docs/图标与许可.md)

</div>

> 🤖 **AI agent 请从这里开始** → [`AGENTS.md`](AGENTS.md)：改完必跑的那一条命令，和四条不要越的线。

## 📥 两全其美 · 皆合心意

🪶 **懒人版** · 至简 · 省心

**Surge**

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/surge/profiles/lazy.min.conf
```

**Egern**

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/egern/profiles/lazy.min.yaml
```

🧭 **分流版** · 可控 · 随心

**Surge**

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/surge/profiles/routing.min.conf
```

**Egern**

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/egern/profiles/routing.min.yaml
```

---

## 🧭 井然有序

🗂️ 各司其职，各安其序，无隙可乘。

| 组 | 🪶 懒人版 | 🧭 分流版 |
|:---|:---:|:---:|
| 🚀 `Proxy` | ✅ | ✅ |
| ⚡ `Smart` | - | ✅ |
| 🤖 `ChatGPT` · `Gemini` · `Claude` · `AI` | 只 `AI` | ✅ |
| 🎵 `Spotify` · 🎶 `YouTubeMusic` · ▶️ `YouTube` | - | ✅ |
| 🐙 `GitHub` · 🔎 `Google` · 🪟 `Microsoft` | - | ✅ |
| ✈️ `Telegram` · 🐦 `Twitter` · 💚 `WeChat` | - | ✅ |
| 🛰️ `Airport`（订阅槽位）| - | ✅ |
| 🛑 `AD` | ✅ | ✅ |
| 🇭🇰 `Hong Kong` · 🇺🇸 `USA` · 🇯🇵 `Japan` · 🇨🇳 `Taiwan`<br>🇸🇬 `Singapore` · 🇰🇷 `Korea` · 🇦🇶 `Other Regions` | - | ✅ |
| 💧 `MAX` | - | ✅ |
| 🌐 `Final` | - | ✅ |

---

## 🌐 隐私至上 · 无 DNS 泄露

| | Surge | Egern |
|:--|:------|:------|
| 🚫 盲区设备 | `hijack-dns` 接管明文 `:53` | `hijack_dns: '*'` 全量接管 |
| 🔐 加密通道 | 端点尽量写 IP 字面量，主机名端点显式豁免 | 四条端点全是 IP 字面量 |
| 🛡️ 明文回退 | `dns-server` 裸 IP、绝不写 `system` | `forward` 兜底指向加密组 |
| 🧭 规则克制 | IP 类规则一律 `no-resolve`，零 IP 的规则集不写（实测判定） | 同一原则写在规则集文件里（`no_resolve` 对 `rule_set` 不生效） |
| ✂️ 远端解析 | 代理域名交节点解析，本地不留答案 | `proxy_nameservers` 专用通道、强制直连 |
| 📋 自检读数 | 5 个审计脚本 + 6 阶段 · 19 断言 | 10 个审计脚本 + 2 阶段 · 24 断言 |

---

## 📁 文件结构

| 角色 | 位置 · 一句话 |
|:-----|:-------------|
| 📖 入口 | [`manual/`](manual/MANUAL.md) —— 《操作手册》，唯一权威操作层 |
| 📥 配置 | 两内核 `profiles/` 各固定名四件：`routing` 分流版 · `lazy` 懒人版，各含注释版 + `.min` 版；退役件在 `config_old/` 按版本号留档 · `egern/apple_system.list` 为本仓自托管规则集（Surge 内置 `SYSTEM` 的时点快照，只给 Egern 引用） |
| 🖼️ 素材 | [`icons/`](icons/) —— 26 个策略组图标，两内核共用一份 |
| 📚 附录 | `docs/` 跨内核清单与 `_archive/` 归档决策 · 各内核 `docs/` 与 `DetailsReadme/`（哪些活、哪些冻结，见下） |
| 🧪 工具 | [`skill/`](skill/) —— 审计脚本与回归闸门：`bash skill/tests/all.sh` 一条命令跑完七项检查 |
| 🗂️ 仓务 | [`AGENTS.md`](AGENTS.md) agent 开工说明 · [`CHANGELOG.md`](CHANGELOG.md) 唯一一份改动记录 · `.gitattributes` 行尾钉成 LF |

---

## 📖 按需查阅

| 想查什么 | 去哪 |
|:---------|:-----|
| 装、改、验、修 —— 一切操作与排查 | 👉 [`manual/MANUAL.md`](manual/MANUAL.md) 读起 |
| 哪篇旧文档的内容去了手册哪一章 | [`manual/99-版本历史`](manual/99-版本历史.md) 映射表 |
| 跨内核语法映射 · 对齐程度 · 哪些结论不能照搬 | [`docs/跨内核差异对照`](docs/跨内核差异对照.md) |
| 21 份共用规则集的指向 / 作用 / 来源 | [`docs/规则集与来源`](docs/规则集与来源.md) |
| 使用前必看的坑 | [`docs/注意事项`](docs/注意事项.md) |
| 图标来源 · MIT 许可 · 第三方版权 | [`docs/图标与许可`](docs/图标与许可.md) |
| 每个配置项的完整语义 · FAQ | 两侧 `DetailsReadme/`（[Surge](surge/DetailsReadme/DetailsReadme.md) · [Egern](egern/DetailsReadme/DetailsReadme.md)） |
| 当前审计读数（唯一落点，文档不抄数） | 两侧 `docs/08`（[Surge](surge/docs/08-审计读数.md) · [Egern](egern/docs/08-审计读数.md)） |
| 全部改动记录（合并前内核史见两侧 `docs/07` 末节） | [`CHANGELOG.md`](CHANGELOG.md) |
| 本仓为何不依赖其他仓库 · 当时的快照（不反映现状） | [`技能包合并与自包含`](docs/技能包合并与自包含.md) · [`体检报告`](docs/体检报告.md) · `日志旧版原文` |

> **说明**　两侧 `docs/` 的 01 / 02 / 04 / 05 / 06（另 `egern/docs/12`）共 11 篇**已就地冻结** ——
> 顶部有横幅，原文保留可读、不再更新，操作以手册为准。编号沿旧：`surge/docs/11` 与 `egern/docs/12`
> 讲的是**同一主题**，09 / 10 / 11 是历史缺口，不是漏了文件。

---

<div align="center">

🐈 让 DNS 无处可漏 · MIT License · [图标与许可](docs/图标与许可.md)

</div>
