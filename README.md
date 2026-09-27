<div align="center">

# 🛡️ Surge · Egern 配置模板

面向 Apple 平台两款代理客户端（Surge / Egern）的防 DNS 泄露开箱即用配置模板。
懒人版与分流版两份分工 × 带注释完整版与纯配置 `.min` 版两种形态 × 两个内核，
分组与规则跨内核逐位对齐。不绑定节点与订阅。

</div>

## 📥 订阅地址（四选一）

🪶 **懒人版** · 至简省心

**Surge**

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/surge/profiles/lazy.min.conf
```

**Egern**

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/egern/profiles/lazy.min.yaml
```

🧭 **分流版** · 可控随心

**Surge**

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/surge/profiles/routing.min.conf
```

**Egern**

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/egern/profiles/routing.min.yaml
```

> 订阅地址是永久固定文件名，升版不改名；带注释完整版在同目录下去掉 `.min` 即是。
> 装好后怎么填自己的订阅、怎么五分钟自检：[`docs/quick-start.md`](docs/quick-start.md)。

## 🧭 分流版分组

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
| 🇭🇰 `Hong Kong` · 🇺🇸 `USA` · 🇯🇵 `Japan` · 🇨🇳 `Taiwan`<br>🇸🇬 `Singapore` · 🇰🇷 `Korea` · 🌍 `Other Regions` | - | ✅ |
| 💧 `MAX` | - | ✅ |
| 🌐 `Final` | - | ✅ |

## 🌐 DNS 防泄露

| | Surge | Egern |
|:--|:------|:------|
| 🚫 盲区设备 | `hijack-dns` 接管明文 `:53` | `hijack_dns: '*'` 全量接管 |
| 🔐 加密通道 | 端点尽量写 IP 字面量，主机名端点显式豁免 | 四条端点全是 IP 字面量 |
| 🛡️ 明文回退 | `dns-server` 裸 IP、绝不写 `system` | `forward` 兜底指向加密组 |
| 🧭 规则克制 | IP 类规则一律 `no-resolve`，零 IP 的规则集不写（实测判定） | 同一原则写在规则集文件里（`no_resolve` 对 `rule_set` 不生效） |
| ✂️ 远端解析 | 代理域名交节点解析，本地不留答案 | `proxy_nameservers` 专用通道、强制直连 |

## 📖 文档

| 想查 | 去哪 |
|:-----|:-----|
| 👉 装改验修（快速开始） | [`docs/quick-start.md`](docs/quick-start.md) |
| ⚙️ 怎么改、怎么维护 | [`docs/ops.md`](docs/ops.md) |
| 🔧 出问题了（排查 · 自检 · 注意事项 · FAQ） | [`docs/troubleshoot-faq.md`](docs/troubleshoot-faq.md) |
| 📚 DNS 原理与泄露面 | [`docs/dns-basics.md`](docs/dns-basics.md) |
| ✅ 加固清单（Surge 14 项 · Egern 18 项） | [`docs/hardening-checklist.md`](docs/hardening-checklist.md) |
| 🔀 分流与 no-resolve 成对交付 | [`docs/no-resolve-pairing.md`](docs/no-resolve-pairing.md) |
| 🔁 两内核语法映射与差异 | [`docs/cross-kernel-diff.md`](docs/cross-kernel-diff.md) |
| 📜 规则集指向与来源 | [`docs/rulesets.md`](docs/rulesets.md) |
| ⌨️ 逐键语义 | [`Surge`](surge/DetailsReadme/DetailsReadme.md) · [`Egern`](egern/DetailsReadme/DetailsReadme.md) |
| 🎨 图标与许可 | [`docs/icon-license.md`](docs/icon-license.md) · [`icons/`](icons/) |
| 🤖 agent 技能包与审计脚本 | [`skill/`](skill/) |
| 🕘 改动记录 | [`CHANGELOG.md`](CHANGELOG.md) |

## 🧪 检查

每次 push / PR 由最小 CI（[`.github/workflows/ci.yml`](.github/workflows/ci.yml)）自动跑五项检查：
占位符/凭据扫描 · 可移植性 · `.min` 对拍 · 链接与锚点 · 双内核 DNS 审计。
本地复现同组命令见 [`skill/README.md`](skill/README.md)。

---

<div align="center">

MIT License · 图标归属见 [`docs/icon-license.md`](docs/icon-license.md)

</div>
