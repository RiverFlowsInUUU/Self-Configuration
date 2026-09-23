<div align="center">

# 🛡️ Surge · Egern 配置模板

*让 DNS 无处可漏*

[![Surge](https://img.shields.io/badge/Surge-iOS%20%7C%20macOS-1f6feb?style=flat-square)](#-两全其美皆合心意)
[![Egern](https://img.shields.io/badge/Egern-iOS%20%7C%20macOS-0969da?style=flat-square)](#-两全其美皆合心意)
[![Groups](https://img.shields.io/badge/Groups-26%20%7C%2026-8250df?style=flat-square)](#-井然有序)
[![Rules](https://img.shields.io/badge/Rules-24%20%7C%2024%20%E5%B7%B2%E5%AF%B9%E9%BD%90-dc3545?style=flat-square)](docs/跨内核差异对照.md)
[![DNS](https://img.shields.io/badge/DNS-Zero%20Leak-2ea043?style=flat-square)](#-隐私至上--无-dns-泄露)
[![License](https://img.shields.io/badge/License-MIT-dfb317?style=flat-square)](docs/图标与许可.md)

</div>

## 📥 两全其美，皆合心意

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
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/surge/profiles/routing_v3.min.conf
```

**Egern**

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/egern/profiles/routing_v3.min.yaml
```

> 📖 用哪一份、导入前要填什么，见 [`docs/注意事项`](docs/注意事项.md)。

---

## 🧭 井然有序

🗂️ *各司其职，各安其序，无隙可乘。*

**分流版按应用与地区分组，两款内核同名同序；懒人版只留必要的几组。**

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
| 🌐 `Final` | 只 Egern | ✅ |

> 🪶 分流版两内核逐位对齐；懒人版两侧不同构，差别见
> [`docs/跨内核差异对照`](docs/跨内核差异对照.md) 第 3、4 节。
> 🔍 选路、地区筛法与规则顺序见 [`surge/docs/11`](surge/docs/11-分流版设计.md) · [`egern/docs/12`](egern/docs/12-分流顺序.md)。

---

## 🌐 隐私至上 · 无 DNS 泄露

| | Surge | Egern |
|:--|:------|:------|
| 🚫 盲区设备 | `hijack-dns` 接管明文 `:53` | `hijack_dns: '*'` 全量接管 |
| 🔐 加密通道 | 端点尽量写 IP 字面量，主机名端点显式豁免 | 四条端点全是 IP 字面量 |
| 🛡️ 明文回退 | `dns-server` 裸 IP、绝不写 `system` | `forward` 兜底指向加密组 |
| 🧭 规则克制 | IP 类规则一律 `no-resolve` | 一律 `no_resolve`，与域名直连集成对交付 |
| ✂️ 远端解析 | 代理域名交节点解析，本地不留答案 | `proxy_nameservers` 专用通道、强制直连 |
| 📋 自检读数 | 4 个审计脚本 + 6 阶段回归 | 9 个审计脚本 + 2 阶段回归 |

> 🔍 五类出口的完整推导见 [`surge/docs/02`](surge/docs/02-DNS为什么会泄露.md) ·
> [`egern/docs/02`](egern/docs/02-DNS为什么会泄露.md)；审计读数与各条含义见
> [`surge/docs/08`](surge/docs/08-审计读数.md) · [`egern/docs/08`](egern/docs/08-审计读数.md)。
> 同一判据在两侧未必同一取舍 —— 例如端点要不要一律写成 IP 字面量，见
> [`docs/跨内核差异对照`](docs/跨内核差异对照.md) 第 8 节。

---

## 📁 文件结构

| | 路径 | 内容 |
|:--:|:-----|:-----|
| 📁 | [`surge/profiles/`](surge/profiles/) | 4 份 `.conf`：懒人版 / 分流版 × 带注释 / 纯配置 |
| 📁 | [`egern/profiles/`](egern/profiles/) | 16 份 `.yaml`：lazy + `routing_v1~v3`，各含带注释 / 纯配置 |
| 🖼️ | [`icons/`](icons/) | 26 个策略组图标（两内核共用一份） |
| 📚 | [`docs/`](docs/) | 共享文档 4 篇：跨内核差异对照 / 规则集与来源 / 注意事项 / 图标与许可 |
| 📂 | [`surge/docs/`](surge/docs/) · [`egern/docs/`](egern/docs/) | 各内核 9 篇专题（01–08 编号系列 + 分流设计 / 分流顺序） |
| 📘 | [`surge/DetailsReadme/`](surge/DetailsReadme/) · [`egern/DetailsReadme/`](egern/DetailsReadme/) | 完整技术文档 |
| 🧪 | [`skill/`](skill/) | 单一入口 `SKILL.md`（按内核分支）+ 审计脚本 + 回归测试 |
| 🗓️ | [`CHANGELOG.md`](CHANGELOG.md) | 合并成仓记录；各内核迭代史见 [`surge/`](surge/CHANGELOG.md) · [`egern/`](egern/CHANGELOG.md) |

---

## 📖 更多文档

- 🔀 [`docs/跨内核差异对照`](docs/跨内核差异对照.md) —— 语法映射 · 分组与规则的对齐程度 · 哪些结论不能照搬
- 📚 [`docs/规则集与来源`](docs/规则集与来源.md) —— 21 份共用规则集的指向 / 作用 / 去向 / 来源
- ⚠️ [`docs/注意事项`](docs/注意事项.md) —— 使用前必看
- 🎨 [`docs/图标与许可`](docs/图标与许可.md) —— 图标来源 · MIT 许可 · 第三方版权
- 🧪 [`skill/SKILL.md`](skill/SKILL.md) —— 方法论主干（先判内核，再进 Surge / Egern 分支）
- 📘 [`surge/DetailsReadme/`](surge/DetailsReadme/) · [`egern/DetailsReadme/`](egern/DetailsReadme/) —— 逐段详解 · 原理推导 · 已知取舍 · FAQ
- 🗓️ [`CHANGELOG.md`](CHANGELOG.md)

---

<div align="center">

🐈 让 DNS 无处可漏 · MIT License · [图标与许可](docs/图标与许可.md)

</div>
