<div align="center">

# 🛡️ 双内核 DNS 防泄露配置模板

*Surge · Egern —— 让 DNS 无处可漏*

[![Surge](https://img.shields.io/badge/Surge-iOS%20%7C%20macOS-1f6feb?style=flat-square)](#-先选内核)
[![Egern](https://img.shields.io/badge/Egern-iOS%20%7C%20macOS-0969da?style=flat-square)](#-先选内核)
[![Groups](https://img.shields.io/badge/Groups-26%20%2B%2026%20%E5%B7%B2%E5%AF%B9%E9%BD%90-8250df?style=flat-square)](#-井然有序)
[![DNS](https://img.shields.io/badge/DNS-Zero%20Leak-2ea043?style=flat-square)](#-隐私至上--无-dns-泄露)
[![License](https://img.shields.io/badge/License-MIT-dfb317?style=flat-square)](docs/图标与许可.md)

</div>

同一套分流策略，两款内核的落地版本合在一处。
**26 个分组同名同序，分流版 24 条规则逐位对应**；因内核实现不同，差异集中在少数几处，全部记录在
[`docs/跨内核差异对照.md`](docs/跨内核差异对照.md)。

---

## 🧩 先选内核

| 你用的是 | 配置格式 | 入口 |
|:--|:--|:--|
| **Surge** | `.conf` | [`surge/`](surge/) |
| **Egern** | `.yaml` | [`egern/`](egern/) |

> ⚠️ 两者判据**不通用**。把一侧的结论照搬到另一侧是本项目记录在案的头号误用来源
> ——例如 Egern 的「广告指向 `AD` 组」搬到 Surge 的 `pre-matching` 规则上，会让 **Surge 拒绝加载整份配置**。
> 不确定就读 [`skill/SKILL.md`](skill/SKILL.md) 的第 0 节。

## 📥 两全其美，皆合心意

🪶 **懒人版** · 至简 · 省心  ｜  🧭 **分流版** · 可控 · 随心

**Surge**

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/surge/profiles/lazy.min.conf
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/surge/profiles/routing_v3.min.conf
```

**Egern**

```
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/egern/profiles/lazy.min.yaml
https://raw.githubusercontent.com/RiverFlowsInUUU/Self-Configuration/main/egern/profiles/routing_v3.min.yaml
```

> 每份都有对应的**带注释原始版**（去掉 `.min`）：改配置改带注释那份，再把改动同步到 `.min`。
> 模板**不绑定节点与订阅**：懒人版自己填节点，分流版填 1 处订阅槽位。

---

## 🧭 井然有序

分流版 26 组，两内核**逐项同名同序**。自上而下：第一列分组，第二列懒人版有则 ✅，第三列分流版全覆盖。

| 组 | 🪶 懒人版 | 🧭 分流版 |
|:---|:---:|:---:|
| 🚀 `Proxy` | ✅ | ✅ |
| ⚡ `Smart` | - | ✅ |
| 🤖 `ChatGPT` · `Gemini` · `Claude` · `AI` | ✅ | ✅ |
| 🎵 `Spotify` · 🎶 `YouTubeMusic` · ▶️ `YouTube` | - | ✅ |
| 🐙 `GitHub` · 🔎 `Google` · 🪟 `Microsoft` | - | ✅ |
| ✈️ `Telegram` · 🐦 `Twitter` · 💚 `WeChat` | - | ✅ |
| 🛑 `AD` | ✅ | ✅ |
| 🇭🇰 `Hong Kong` · 🇺🇸 `USA` · 🇯🇵 `Japan` · 🇨🇳 `Taiwan`<br>🇸🇬 `Singapore` · 🇰🇷 `Korea` · 🇦🇶 `Other Regions` | - | ✅ |
| 💧 `MAX` | - | ✅ |
| 🌐 `Final` | ✅ | ✅ |

---

## 🌐 隐私至上 · 无 DNS 泄露

五类明文查询出口，**两侧全部收口**。漏一类，剩下的那类就仍是必然通路。

| 泄露面 | Surge 的收口 | Egern 的收口 |
|:--|:--|:--|
| 引导解析（端点写成域名） | 加密端点全部 IP 字面量 | 同 + `hosts` 钉住 |
| 回退落到明文 | `dns-server` 绝不写 `system` | `bootstrap` 列 ≥2 国内解析器、不含 `system`，多端点压低「全失败」概率 |
| 不识 DNS 的旁路设备 | `hijack-dns` 接管明文 `:53` | `hijack_dns: '*'` 全量接管 |
| IP 规则为判定而解析 | 一律 `no-resolve` | 一律 `no_resolve` |
| 远程规则集里嵌的裸 IP | 逐个下载数条目，只引 `No_Resolve` 变体 | 同（`audit_ruleset_noresolve.py`） |

另加两条两侧共用的设计原则：

- 🧭 **规则克制** —— IP 类规则只为匹配，不额外发问；`no-resolve` 与「域名条目足够多的国内直连规则集」**成对交付**，否则国内域名整片落默认出口。
- 🔒 **闭环连接** —— DoH 直连、不跟代理链，启动不成环；代理域名交节点远端解析，本地不留答案。

---

## 🗂 目录结构

```
icons/          26 个分组图标（两内核共用，原本各存一份且逐字节相同）
docs/           共享文档：跨内核差异对照 · 规则集与来源 · 注意事项 · 图标与许可
surge/          profiles/  ·  docs/(9 篇)  ·  DetailsReadme/  ·  CHANGELOG.md
egern/          profiles/  ·  docs/(9 篇)  ·  DetailsReadme/  ·  CHANGELOG.md
skill/          SKILL.md（单一入口，按内核分支）
  ├─ reference/surge/ · reference/egern/     六个深度主题各一侧
  ├─ scripts/surge/   · scripts/egern/       审计脚本（Surge 4 + 公共模块 / Egern 9）
  └─ tests/surge/     · tests/egern/         回归套件 + fixture
```

改完在仓库根目录本地跑（**本仓库刻意不挂 CI**）：

```bash
bash skill/tests/surge/run.sh     # 6 阶段 · 15 断言（联网阶段可 SKIP_NET=1 跳过）
bash skill/tests/egern/run.sh     # 阶段 1 · 5 fixture；阶段 2 · 全部 profile 通配扫描
```

---

## ⚠️ 已知边界

- 🔬 **审计全绿 ≠ 配置可用**：脚本只覆盖静态可判定部分，拦截效果、误杀、节点可用性必须实测。
- 📦 **Egern 侧本机验证缺口**：合并后两侧的 Python 回归需真实解释器（Egern 脚本另需 `PyYAML`），本次装配未在具备环境处执行，详见 [`CHANGELOG.md`](CHANGELOG.md)。
- 🧪 **两款都是闭源商业软件**：文档中凡标注「实测」的结论都是特定版本下的经验值，升级后需重新验证。

---

## 📜 许可与出处

MIT，见 [`LICENSE`](LICENSE) 与 [`docs/图标与许可.md`](docs/图标与许可.md)。
本仓库由 [`RiverFlowsInUUU/Surge`](https://github.com/RiverFlowsInUUU/Surge) 与
[`RiverFlowsInUUU/Egern`](https://github.com/RiverFlowsInUUU/Egern) 合并而成，两个源仓库保持原样未改动，
其中的订阅地址仍然可用。合并记录见 [`CHANGELOG.md`](CHANGELOG.md)。
