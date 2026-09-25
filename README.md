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

| | 路径 | 内容 |
|:--:|:-----|:-----|
| 📁 | [`surge/profiles/`](surge/profiles/) | 固定名四件 `.conf`：`routing` 分流版 · `lazy` 懒人版，各含带注释 / 纯配置 |
| 📂 | [`surge/profiles/config_old/`](surge/profiles/config_old/) | 被替代的旧版按版本号留档，不参与检查 |
| 📁 | [`egern/profiles/`](egern/profiles/) | 固定名四件 `.yaml`：与 Surge 侧同名同序 |
| 📂 | [`egern/profiles/config_old/`](egern/profiles/config_old/) | 同上，`routing_v1` 起到 `v3.1` 的完整沿革 |
| 📄 | [`egern/apple_system.list`](egern/apple_system.list) | 本仓**自托管**的第一份规则集：Surge 内置 `SYSTEM` 的时点快照，只给 Egern 引用 |
| 🖼️ | [`icons/`](icons/) | 26 个策略组图标（两内核共用一份） |
| 📚 | [`docs/`](docs/) | 共享文档 6 篇：跨内核差异对照 / 规则集与来源 / 注意事项 / 图标与许可 / 技能包合并与自包含 / 体检报告 |
| 📂 | [`surge/docs/`](surge/docs/) · [`egern/docs/`](egern/docs/) | 各内核 9 篇专题（01–08 编号系列 + 分流设计 / 分流顺序） |
| 📘 | [`surge/DetailsReadme/`](surge/DetailsReadme/) · [`egern/DetailsReadme/`](egern/DetailsReadme/) | 完整技术文档 |
| 🧪 | [`skill/`](skill/) | 单一入口 `SKILL.md`（按内核分支）+ 审计脚本 + 回归测试：`bash skill/tests/all.sh` 一条命令跑完七项检查 |
| 🤖 | [`AGENTS.md`](AGENTS.md) | 给 AI agent 的开工说明：改完的固定动作 · 五条硬约束 · 换设备三件事 · 升版不改订阅地址 |
| 🔁 | [`.gitattributes`](.gitattributes) | 行尾钉成 LF —— 同一个 commit 在任何设备上落盘字节相同，clone 下来直接改、改完直接推 |
| 🗓️ | [`CHANGELOG.md`](CHANGELOG.md) | **唯一一份**改动记录：装配层与两个内核的迭代都按日期写在这里；合并前的内核迭代史见 [`surge/docs/07`](surge/docs/07-文件版本沿革.md) · [`egern/docs/07`](egern/docs/07-文件版本沿革.md) 末节 |

---

## 📖 更多文档

- 🔀 [`docs/跨内核差异对照`](docs/跨内核差异对照.md) —— 语法映射 · 分组与规则的对齐程度 · 哪些结论不能照搬
- 📚 [`docs/规则集与来源`](docs/规则集与来源.md) —— 21 份共用规则集的指向 / 作用 / 去向 / 来源
- ⚠️ [`docs/注意事项`](docs/注意事项.md) —— 使用前必看
- 🎨 [`docs/图标与许可`](docs/图标与许可.md) —— 图标来源 · MIT 许可 · 第三方版权
- 🧩 [`docs/技能包合并与自包含`](docs/技能包合并与自包含.md) —— 两份单内核技能包怎么合成一份双分支入口 · 本仓为何完全不依赖其他仓库
- 🩺 [`docs/体检报告`](docs/体检报告.md) —— 全仓排查快照：每条硬判据是拿什么换的（含三处被实测推翻的原结论）
- 🧪 [`skill/SKILL.md`](skill/SKILL.md) —— 方法论主干（先判内核，再进 Surge / Egern 分支）
- 📘 [`surge/DetailsReadme/`](surge/DetailsReadme/) · [`egern/DetailsReadme/`](egern/DetailsReadme/) —— 逐段详解 · 原理推导 · 已知取舍 · FAQ
- 🗓️ [`CHANGELOG.md`](CHANGELOG.md) —— 本仓唯一的改动记录，两个内核都写在这一份里

**读上面这份清单前，有两点容易踩**：

- **两侧 `docs/` 的编号不对应**：`surge/docs/11-分流版设计` 与 `egern/docs/12-分流顺序` 讲的是**同一主题**，
  只是编号沿用了合并前的历史。编号 **09 / 10 / 11 是历史缺口**，不是漏了文件。
- **清单里混着历史存档**：`体检报告`（当时的读数快照）· `技能包合并与自包含`（当时的合并决策）
  · `日志旧版原文`（只读存档）—— 三者记录的都是**当时**的观测与决策，**不反映当前状态**；
  要看现状请以各专项文档与 `CHANGELOG` 为准。

---

<div align="center">

🐈 让 DNS 无处可漏 · MIT License · [图标与许可](docs/图标与许可.md)

</div>
