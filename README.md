<div align="center">

# 🛡️ Surge · Egern 配置模板

殊途同归 · 久用如一

[![Surge](https://img.shields.io/badge/Surge-iOS%20%7C%20macOS-1f6feb?style=flat-square)](#-两全其美--皆合心意)
[![Egern](https://img.shields.io/badge/Egern-iOS%20%7C%20macOS-0969da?style=flat-square)](#-两全其美--皆合心意)
[![Groups](https://img.shields.io/badge/Groups-26%20%7C%2026-8250df?style=flat-square)](#-井然有序)
[![Rules](https://img.shields.io/badge/Rules-24%20%7C%2024%20%E5%B7%B2%E5%AF%B9%E9%BD%90-dc3545?style=flat-square)](skill/reference/shared/cross-kernel-diff.md)
[![DNS](https://img.shields.io/badge/DNS-Zero%20Leak-2ea043?style=flat-square)](#-隐私至上--无-dns-泄露)
[![License](https://img.shields.io/badge/License-MIT-dfb317?style=flat-square)](LICENSE)

</div>

> 🤖 **AI agent 请从这里开始** → [`skill/SKILL.md`](skill/SKILL.md)：改完必跑的那一条命令，和六条不要越的线。

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
| 🤖 `ChatGPT` · `Gemini` · `Claude` · `AI` | 仅 `AI` | ✅ |
| 🎵 `Spotify` · 🎶 `YouTubeMusic` · ▶️ `YouTube` | - | ✅ |
| 🐙 `GitHub` · 🔎 `Google` · 🪟 `Microsoft` | - | ✅ |
| ✈️ `Telegram` · 🐦 `Twitter` · 💚 `WeChat` | - | ✅ |
| 🛰️ `Airport`（订阅槽位）| ✅ | ✅ |
| 🛑 `AD` | ✅ | ✅ |
| 🇭🇰 `Hong Kong` · 🇺🇸 `USA` · 🇯🇵 `Japan` · 🇨🇳 `Taiwan`<br>🇸🇬 `Singapore` · 🇰🇷 `Korea` · 🇦🇶 `Other Regions` | - | ✅ |
| 💧 `MAX` | - | ✅ |
| 🌐 `Final` | - | ✅ |

---

## 🌐 隐私至上 · 无 DNS 泄露

| | Surge | Egern |
|:--|:------|:------|
| 🚫 盲⁠区⁠设⁠备 | `hijack-dns` 接管明文 `:53` | `hijack_dns: '*'` 全量接管 |
| 🔐 加⁠密⁠通⁠道 | 端点尽量写 IP 字面量，主机名端点显式豁免 | 四条端点全是 IP 字面量 |
| 🛡️ 明⁠文⁠回⁠退 | `dns-server` 裸 IP、绝不写 `system` | `forward` 兜底指向加密组 |
| 🧭 规⁠则⁠克⁠制 | IP 类规则一律 `no-resolve`，零 IP 的规则集不写（实测判定） | 同一原则写在规则集文件里（`no_resolve` 对 `rule_set` 不生效） |
| ✂️ 远⁠端⁠解⁠析 | 代理域名交节点解析，本地不留答案 | `proxy_nameservers` 专用通道、强制直连 |
| 📋 自⁠检⁠读⁠数 | 5 个审计脚本 + 6 阶段 · 19 断言 | 10 个审计脚本 + 2 阶段 · 24 断言 |

---

## 📖 按需查阅

操作文档、逐键语义与审计判据已全部整合进 [`skill/`](skill/SKILL.md)（AI 驱动仓库的唯一知识库）。

---

<div align="center">

🐈 让 DNS 无处可漏 · MIT License

</div>
