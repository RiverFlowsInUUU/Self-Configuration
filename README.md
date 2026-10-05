<div align="center">

<img src="https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/icons/Surge.png" height="64" alt="Surge">&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/icons/Brand-Cross.png" height="64" alt="">&nbsp;&nbsp;&nbsp;<img src="https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/icons/Egern.png" height="64" alt="Egern">

# Surge · Egern 配置模板

殊途同归 · 久用如一

[![Surge](https://img.shields.io/badge/Surge-iOS%20%7C%20macOS-1f6feb?style=flat-square)](#-两全其美--皆合心意)
[![Egern](https://img.shields.io/badge/Egern-iOS%20%7C%20macOS-0969da?style=flat-square)](#-两全其美--皆合心意)
[![Groups](https://img.shields.io/badge/Groups-22%20%7C%2022-8250df?style=flat-square)](#-井然有序)
[![Rules](https://img.shields.io/badge/Rules-25%20%7C%2025%20%E5%B7%B2%E5%AF%B9%E9%BD%90-dc3545?style=flat-square)](skill/reference/shared/cross-kernel-diff.md)
[![DNS](https://img.shields.io/badge/DNS-Zero%20Leak-2ea043?style=flat-square)](#-隐私至上--无-dns-泄露)
[![License](https://img.shields.io/badge/License-MIT-dfb317?style=flat-square)](LICENSE)
[![CI](https://github.com/RiverFlowsInUUU/Self-Configuration/actions/workflows/ci.yml/badge.svg)](https://github.com/RiverFlowsInUUU/Self-Configuration/actions/workflows/ci.yml)

</div>

> 🤖 **AI agent 请从这里开始** → [`skill/SKILL.md`](skill/SKILL.md)：改完必跑的那一条命令，和六条不要越的线。

## 📥 两全其美 · 皆合心意

| <div align="center">内核</div> | 🪶 懒人版 · 至简 · 省心 | 🧭 分流版 · 可控 · 随心 |
|:--|:--|:--|
| <img src="https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/icons/Surge-Icon.png" height="20" alt=""> **Surge** | [`surge-lazy.min.conf`](https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/surge/profiles/lazy.min.conf) | [`surge-routing.min.conf`](https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/surge/profiles/routing.min.conf) |
| <img src="https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/icons/Egern-Icon.png" height="20" alt=""> **Egern** | [`egern-lazy.min.yaml`](https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/egern/profiles/lazy.min.yaml) | [`egern-routing.min.yaml`](https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/egern/profiles/routing.min.yaml) |

---

## 🧭 井然有序

🗂️ 各司其职，各安其序，无隙可乘。

| <div align="center">组</div> | 🪶 懒人版 | 🧭 分流版 |
|:---|:---:|:---:|
| 🚀 `Proxy` | ✅ | ✅ |
| ⚡ `Smart` | - | ✅ |
| 🤖 `ChatGPT` · `Gemini` · `Claude` · `AI` | 仅 `AI` | ✅ |
| ▶️ `YouTube` · 🎬 `Emby` · ✈️ `Telegram` · 🎶 `YouTube Music`<br>🔎 `Google` · 🎵 `Spotify` · 🐦 `Twitter` · 🪟 `Microsoft` | - | ✅ |
| 🛰️ `Airport`（订阅槽位）| ✅ | ✅ |
| 🛑 `AD` | ✅ | ✅ |
| 🇭🇰 `Hong Kong` · 🇨🇳 `Taiwan` · 🇯🇵 `Japan` · 🇸🇬 `Singapore`<br>🇺🇸 `United States` · 🇦🇶 `Other Regions` | - | ✅ |

---

## 🌐 隐私至上 · 无 DNS 泄露

| | <div align="center"><img src="https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/icons/Surge-Icon.png" height="22" alt=""> Surge</div> | <div align="center"><img src="https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/icons/Egern-Icon.png" height="22" alt=""> Egern</div> |
|:--|:------|:------|
| 🚫 盲⁠区⁠设⁠备 | `hijack-dns` 接管明文 `:53`（六个知名解析器） | `hijack_dns` 接管明文 `:53`（全量） |
| 🔐 加⁠密⁠通⁠道 | 主解析走 DoH，主机名端点经裸 IP 受控引导 | 主解析走 DoH/DoT，四条端点全是 IP 字面量 |
| 🛡️ 明⁠文⁠回⁠退 | `dns-server` 全裸 IP，绝不写 `system` | `forward` 兜底只指加密组，绝不落明文 |
| 🧭 规⁠则⁠克⁠制 | IP 类规则一律 `no-resolve`；零 IP 的规则集不写（实测判定） | IP 类规则一律 `no_resolve`；该键对 `rule_set` 不生效，原则写进规则集文件 |
| ✂️ 远⁠端⁠解⁠析 | 代理域名交节点解析，本地不留答案 | 代理域名交节点解析，本地不留答案（`proxy_nameservers` 专用通道、强制直连） |
| 📋 自⁠检⁠读⁠数 | 5 个审计脚本 + 6 阶段 · 19 断言 | 10 个审计脚本 + 2 阶段 · 24 断言 |

---

## 📖 按需查阅

操作文档、逐键语义与审计判据已全部整合进 [`skill/`](skill/SKILL.md)（AI 驱动仓库的唯一知识库）。

---

<div align="center">

🐈 让 DNS 无处可漏 · MIT License

</div>
