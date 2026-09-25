---
name: profile-dns-hardening
description: 审计并加固 Surge / Egern 配置（.conf 与 Profile.yaml）的 DNS 泄露面与分流覆盖。触发词：Surge 配置、Egern 配置、防 DNS 泄露、DNS 裸奔、leak test 显示 china telecom、upstream 显示 bootstrap、dns-server = system、encrypted-dns-server 是域名、proxy_nameservers、hijack-dns / hijack_dns、bootstrap 泄露、明文 :53 旁路、HomePod / Apple TV DNS 泄露、no-resolve / no_resolve、GEOIP CN 缺 no-resolve、IP 规则触发 DNS 解析、加了 no-resolve 之后分流坏了、国内域名全落 FINAL、国内网站不是直连、direct.txt、ChinaMax 只有 IP、规则集 IP 条目缺 no-resolve、Apple_All.list 强制解析、pre-matching、pre-matching 指向策略组、underlying-proxy 无法解析、smart 组评分、policy-regex-filter、flatten 的等价写法、always-real-ip、fake-ip、延迟测试域名泄露、cp.cloudflare.com 泄露、图标域名泄露、dns.forward 兜底、白名单排在 REJECT 之后、profile 模板、Egern dns 段、Egern dnsleak、Egern YAML 配置优化、DNS 泄露到运营商（电信/联通/移动）、日志里规则判定正常但 upstream 是 bootstrap、节点域名明文解析、系统 DNS 回退泄露、rule_set 触发 DNS 解析、blackmatrix7 No_Resolve 变体、ChinaMax.list 没有域名规则、ChinaMax_All_No_Resolve、国内域名走代理、分流覆盖审计、dns.google 泄露、引导解析泄露、extended-matching、Surge 拒绝加载配置、proxy-test-url 泄露、gstatic generate_204。命中本技能时优先加载本文件并按内核进入对应分支，不要凭记忆答语法。
agent_created: true
---

# 配置防 DNS 泄露 · Surge / Egern 双内核

本技能覆盖两款客户端。**先定内核，再进对应分支**——两者的模型不通用，
把一侧的结论套到另一侧是本项目记录在案的头号误用来源。

## 0 · 内核判定

| 线索 | 内核 | 进入 |
|:-----|:-----|:-----|
| 文件是 `.conf` / 段名 `[General]` `[Proxy Group]` `[Rule]` / 键 `dns-server`、`hijack-dns`、`policy-regex-filter` | **Surge** | [分支 A](#分支-a--surge-配置防-dns-泄露) |
| 文件是 `.yaml` / 顶层键 `policy_groups`、`dns.forward`、`hijack_dns`、`proxy_nameservers`、`rule_set` | **Egern** | [分支 B](#分支-b--egern-配置防-dns-泄露) |
| Clash / mihomo / Shadowrocket / Sing-box | **都不适用** | 本技能两侧判据均不可套用（`no-resolve` 语义、`fake-ip-filter` 各成一套） |

同一份流量策略在两个内核里的落地位置：

| | 配置载体 | 分组段 | 规则段 | 脚本 | 测试 |
|:--|:--|:--|:--|:--|:--|
| Surge | `surge/profiles/*.conf` | `[Proxy Group]` | `[Rule]` | `scripts/surge/` | `tests/surge/run.sh` |
| Egern | `egern/profiles/*.yaml` | `policy_groups:` | `rules:` | `scripts/egern/` | `tests/egern/run.sh` |

## 1 · 两内核共享的骨架：泄露面只有五类

Surge 侧把它归纳为「一条路径、三个明文出口」，Egern 侧归纳为「两条互不相通的路径、六个泄露位置」。
**它们是同一批物理事实的两种切分**——按"谁触发了一次明文查询"归并，五类在两内核上一一对应：

| # | 泄露面 | Surge 的表现 | Egern 的表现 | 收口手段 |
|:-:|:-------|:-------------|:-------------|:---------|
| ① | **引导解析**：加密端点写成了主机名 | `encrypted-dns-server` / `dns-server` 含域名 → 冷启动必被明文解析一次 | `upstreams` / `proxy_nameservers` 含域名 → `bootstrap` 用途① | **端点一律写 IP 字面量** |
| ② | **回退链落到明文** | `dns-server = system` | 上游全失败 → `bootstrap`(UDP:53) → `system` | 显式列 ≥2 个国内解析器；`bootstrap` 绝不写 `system`；多列端点使"全失败"几不可能 |
| ③ | **旁路设备**：不识 DNS 设置的设备直接发 `:53` | 靠 `hijack-dns` 接管 | 靠 `hijack_dns: ['*']` 接管 | 全量接管；判据是「已知的知名硬编码解析器还漏几个」而非条数 |
| ④ | **规则判定触发的解析**：IP 类规则要为判定而解析 | `GEOIP` / `IP-CIDR` / `IP-ASN` 缺 `no-resolve` | 同四类缺 `no_resolve` | 全部补上——**并成对交付⑤，见下方铁律** |
| ⑤ | **远程规则集内嵌裸 IP 条目**：缺陷在别人仓库的 `.list` 里 | 同 | 同（`audit_ruleset_noresolve.py` 实测 `Apple_All.list` 13 条） | 逐个下载数条目，用 `scripts/*/audit_*` |

⭐ **五类必须全堵。** 堵四类剩一类，剩下的那类仍然是**必然通路**——这是两个内核共同的第一教训。
①只在冷启动发生一次但 100% 发生；④每个新域名都发生但只在命中时发生。严重度与必然性方向相反，不能只挑严重的做。

## 2 · 两内核共同的四条铁律

1. **白名单 → 黑名单 → 常规分流**，顺序不可反。REJECT 排到国内直连规则之后就等于白加。
2. ⭐ **`no-resolve` 与「域名条目足够多的国内直连规则集」必须成对交付。**
   补 `no-resolve` 会**同时**关掉"靠解析判 IP 归属"这条直连路径；只交一半 → 国内域名整片落 `FINAL / default → 代理`。
   判据是**下载规则集数域名条目**，不是看名字（`ChinaMax.list` 名字像域名集，实测 12472 条里只有 64 条域名）。
3. **厂商专属规则排在通用 `AI.list` 之前**（`OpenAI` / `Gemini` / `Anthropic` / `Claude`），否则专属组形同虚设。
4. ⭐ **兜底/默认出口的判据是「直连可达」，不是「指向境外」。**
   两内核同理：兜底承担的是"代理还没起来时的那次解析"。挂在必须经代理才可达的组上，
   等于留下一条通往明文的分支——而**泄露不可撤销，答案被污染可接受**。
   （Egern 侧这条曾以"兜底指国内 = HIGH"的形式被写成错判并撤回，见坑 13。）

**内核专属、不可互相套用的一条**：Surge 的 `pre-matching` 规则策略**必须是字面量 REJECT 族**，写成策略组会导致
Surge **拒绝加载整份配置**；Egern 侧没有对应机制，它的等价约束是 `proxy_nameservers` 一设就**跳过 `forward`**。

## 3 · 共享纪律

- ⚠️ **审计通过 ≠ 配置可用。** 两侧脚本只覆盖**静态可判定**的部分；拦截效果、误杀、节点可用性必须实测。
  这条来自 Egern 侧连续 5 次"脚本全绿、实测仍有问题"的代价。
- 🔒 **本仓库刻意不挂 CI / 任何自动化。** 改动后在仓库根目录本地跑：
  `bash skill/tests/surge/run.sh` 与 `bash skill/tests/egern/run.sh`（联网审计阶段可用 `SKIP_NET=1` 跳过）。
- 📍 **命令的路径基准**：本文与 `skill/reference/` 里凡可照抄执行的命令，路径一律以**仓根**为基准书写（要 `cd` 的会显式写 `cd`）；
  行文里为省字出现的简写（如 `scripts/probe_doh.py`）不是可执行路径，取真身请以仓根全路径为准。
- 🧷 **改配置的安全姿势**：Egern profile 含数千字符的超长单行，**不要用 YAML dump 重写整个文件**；
  按行读入 + 内容定位 + 断言"全文恰好命中 1 行"，改完逐字段比对未触碰部分。详见分支 B。
- 🚨 **凡写「实测」处皆为经验值**，两款都是闭源商业软件，很多行为无文档可依，版本更新后需重新验证。
- 📊 **任何条数一律现抓，不要照抄本仓文档里的数。** 所有远程规则集都没锁 commit、随上游每周漂；文档为可读性写的条数只是**写作时点的约数**。要精确值就跑 `skill/scripts/surge/audit_ruleset_content.py <profile>`（Surge）/ `skill/scripts/egern/profile_ruleset.py <规则集 URL>`（Egern），两侧脚本都逐个数条目类型。

## 4 · 按需读取

| 文件 | 何时读 |
|:-----|:-------|
| `reference/surge/*.md` · `reference/egern/*.md` | 六个主题各一侧：`hardening-template`（产出加固配置）· `pitfalls`（事故复盘）· `leak-localization`（用户报了具体运营商）· `checker`（跑脚本前 / 改判据前）· `ruleset-weight`（嫌规则集重）· `public-repo`（改模板 / 仓库结构） |
| [`docs/跨内核差异对照.md`](../docs/跨内核差异对照.md) | 要在两内核间移植一份改动时——**必读**，含逐项语法映射与实测差异清单 |
| [`docs/规则集与来源.md`](../docs/规则集与来源.md) | 想知道用了哪些规则集、来源、排序约束 |
| [`surge/docs/`](../surge/docs/) · [`egern/docs/`](../egern/docs/) | 单内核的逐段讲解、加固清单、审计读数、版本沿革 |

---

## 分支 A · Surge 配置防 DNS 泄露

### 适用

用户给一份 Surge `.conf`（或要生成一份 Surge profile），要求「防 DNS 泄露 / 别让 DNS 裸奔 /
检查 DNS 配置」，或反馈「实测有 DNS 泄露」「国内网站不是直连」。也可用于交付前自检。

**不适用**：Clash / mihomo（`no-resolve` 语义不同，`fake-ip-filter` 是另一套）、
Egern（见 `egern-profile-dns-hardening` 技能）、Shadowrocket（`dns-server` 语义不同）。

### 引用文件（按需读取）

本文件是**主干**：三条出口模型、12 项审计清单、加固模板、坑索引、验收判据。
下列细节按需读取 —— 每个文件开头都写了「何时读」：

| 文件 | 何时读 |
|---|---|
| `reference/surge/hardening-template.md` | 要产出一份加固后的 Surge profile 时 —— 逐段模板 + 逐行理由 |
| `reference/surge/pitfalls.md` | 排查实际泄露、或改动判据 / 规则集之前 —— 坑的事故复盘 |
| `reference/surge/leak-localization.md` | 用户报「leak test 显示某运营商」时 —— 网络侧实测流程 |
| `reference/surge/checker.md` | 跑审计脚本前（命令与环境要求）、或要改判据时（判据演进史） |
| `reference/surge/ruleset-weight.md` | 用户问「规则集是不是太重」时 —— 按类型数条目、识破名字骗人 |
| `reference/surge/public-repo.md` | 要更新模板 / 了解公开仓库结构时 |

---

### Surge 的 DNS 模型（不理解这个就会改错地方）

与 Egern 的两条互不相通路径不同，**Surge 只有一条解析路径**，但有**三个明文出口**。
这是本技能的核心模型：

| 出口 | 触发条件 | 是否必然发生 | 收口手段 |
|---|---|---|---|
| ① **引导解析** | `encrypted-dns-server` / `dns-server` 里写了主机名 | 冷启动时**必然** | 端点写 IP 字面量 |
| ② **旁路设备** | 忽略 Surge DNS 的设备（HomePod / Apple TV / Chromecast / 智能音箱）直接发 `:53` | 设备在线时**必然** | `hijack-dns` |
| ③ **规则触发解析** | IP 类规则（`GEOIP` / `IP-CIDR` / `IP-ASN`）不带 `no-resolve` | 每个走到它的**域名**都触发 | 全部加 `no-resolve` |

⭐ **三个出口的严重度依次递减，但"必然性"依次递增。**
出口 ① 只在冷启动发生一次，但它 100% 会发生；出口 ③ 每次新域名都发生，
但只在规则命中时发生。**三者必须都堵** —— 堵两个剩一个，剩下的仍然是"必然通路"。

⭐ **`dns-server` 绝不能用 `system`。** 它承担引导与连通性测试职责。
写 `system` 等于把引导这一步交给运营商 DHCP 下发的那台解析器 —— 那正是出口 ①。

⭐ **`encrypted-dns-follow-outbound-mode` 必须 `false`。** 设 `true` 时 DoH 连接
自己也要遵循代理规则，形成「解析它 → 需要它 → 解析它」的环，Surge 会回退明文。

⭐ **`use-local-host-item-for-proxy` 必须 `false`。** 本地 DNS 映射只服务 DIRECT 路径；
开启会把本地结果变成**硬性的代理目标**，破坏远端解析（走代理的域名应该由节点侧
按地理就近解析，本地不该有它的答案）。

---

### 12 项审计清单

`scripts/surge/check_surge_dns.py` 自动跑这 12 项。逐条判据与检查号对应：

| # | 审什么 | 判负级别 |
|:-:|:-------|:--------:|
| 1 | `encrypted-dns-server` 端点是否为 IP 字面量 | HIGH（任一非字面量） |
| 2 | `dns-server` 是否显式、无 `system`、无主机名、≥2 个国内解析器 | HIGH / MEDIUM |
| 3 | `hijack-dns` 是否覆盖已知的知名硬编码解析器 | LOW |
| 4 | `encrypted-dns-follow-outbound-mode` 是否为 `false` | HIGH |
| 5 | `always-real-ip` 是否配置、`use-local-host-item-for-proxy` 是否为 `false` | HIGH / LOW |
| 6 | `internet-test-url` / `proxy-test-url` / `proxy-test-udp` 的域名归属（**提示性**） | LOW |
| 7 | 策略组引用的节点 / 组是否存在 | HIGH |
| 8 | 规则引用的策略是否可解析（`policy_index` 定位） | HIGH / MEDIUM |
| 9 | 规则顺序：域名类在 IP 类之前、FINAL 在最后、REJECT 位置 | HIGH / MEDIUM |
| 10 | 带 `pre-matching` 的规则策略是否为**字面量** REJECT 族 | HIGH |
| 11 | `always-real-ip` 主机名是否被前置域名规则接住 | MEDIUM / LOW |
| 12 | 所有 IP 类规则是否带 `no-resolve`；FINAL 是否带 `dns-failed` | MEDIUM / LOW |

另有四个**不在清单里但必须查**的东西（见 `reference/surge/checker.md`）：

| 脚本 | 查什么 | 联网 |
|---|---|---|
| `audit_ruleset_content.py` | ① 远程规则集里有没有**不带 `no-resolve` 的 IP 条目**；② 判给 DIRECT 的规则集**域名条目总量**是否够（判据是数域名条目，**不是**看规则集名字） | ✅ |
| `audit_routing_coverage.py` | 拿真实域名**走一遍** `[Rule]`，看最终命中哪条。期望表按 profile 自动切换；**不得**放宽成"只要不是 DIRECT" | ✅ |
| `audit_region_filters.py` | 分流配置里 7 个地区组的 `policy-regex-filter` 关键词是否同步（负向断言那份拷贝）、是否互斥、类型是否 `smart`。见坑 16 | ❌ |

⚠️ **分流配置（按应用 / 按地区分组）另有三条 Surge 特有的硬约束**，
与 Egern 等客户端的写法**不通用**：

| 约束 | 官方依据 | 正确写法 |
|:-----|:---------|:---------|
| Surge **没有** `flatten` | — | 用 `include-other-group="X"`，它复制的是"resolved member policies"，语义等价 |
| **Smart 组不能拿组名当子策略** | [Smart 智能策略组](https://kb.nssurge.com/surge-knowledge-base/zh/guidelines/smart-group) | 要 `smart` 自动选优 → `include-other-group`；要在面板点进地区 → 用 `select` + 组名作成员 |
| `policy-regex-filter` **对显式列出的成员无效** | [Policy Including](https://manual.nssurge.com/policy-groups/policy-including.html) | 想筛 `[Proxy]` 里的本机节点，必须同时写 `include-all-proxies=true` |

⚠️ 空组是允许的（正则没筛到任何节点）—— Surge **不会**因此拒绝加载，
但指向它的规则会断流。分流配置导入后要确认哪几个组是空的。

---

### 加固模板

完整模板见 `reference/surge/hardening-template.md`。最小可用骨架：

```
[General]
dns-server = 223.5.5.5, 119.29.29.29, 1.1.1.1, 8.8.8.8
encrypted-dns-server = https://1.1.1.1/dns-query, https://dns.google/dns-query, https://dns.alidns.com/dns-query
encrypted-dns-follow-outbound-mode = false
hijack-dns = 8.8.8.8:53, 8.8.4.4:53, 1.1.1.1:53, 1.0.0.1:53, 9.9.9.9:53, 208.67.222.222:53
use-local-host-item-for-proxy = false
test-timeout = 5
internet-test-url = http://connect.rom.miui.com/generate_204
proxy-test-url = http://www.gstatic.com/generate_204
proxy-test-udp = apple.com@1.1.1.1

[Rule]
RULE-SET,<白名单>,DIRECT
RULE-SET,<广告黑名单>,REJECT,pre-matching,extended-matching
RULE-SET,SYSTEM,DIRECT
RULE-SET,LAN,DIRECT,no-resolve
RULE-SET,<private.txt>,DIRECT,no-resolve
RULE-SET,<direct.txt>,DIRECT,no-resolve        ← 主承重墙，见下方铁律
GEOIP,CN,DIRECT,no-resolve
FINAL,Proxy,dns-failed
```

#### 三条铁律

1. **白名单(DIRECT) → 黑名单(REJECT) → 常规分流（`direct.txt` / `GEOIP,CN`）。**
   REJECT 绝不能排在 `direct.txt` / `GEOIP,CN` **之后** —— 那等于白加，
   因为国内广告域名会先被 `direct.txt` 接走。
2. **`no-resolve` 与「域名体量足够的国内直连规则集」必须成对交付。**
   给 IP 规则补 `no-resolve` 会**同时**关掉「解析后判 IP 归属」这条直连路径。
   只交一半 → 国内域名整片落 `FINAL → Proxy`。判据是「数**域名**条目」，
   **不是**看规则集名字（`ChinaMax.list` 名字像国内域名集，实测 12472 条里只有 64 条域名）。
3. **`pre-matching` 的规则策略必须是字面量 REJECT 族**，不能是策略组。
   策略组在运行时可能解析成 DIRECT，Surge 会**拒绝加载整份配置**。

#### 验收判据（7 条，全过才算可用）

- [ ] `check_surge_dns.py` 退出码 0（无 HIGH）—— `surge/profiles/*.conf` **顶层固定名四件**都要过
- [ ] `audit_ruleset_content.py` 通过（远程规则集无缺 `no-resolve` 的 IP 条目；直连集合域名条目 ≥1000）
- [ ] `audit_routing_coverage.py` 通过（国内探针全部 DIRECT、境外探针**命中预期的组**、误杀探针不被 REJECT）
- [ ] `audit_region_filters.py` 通过（仅分流配置：关键词同步 / 互斥 / 类型 smart）
- [ ] `architecture.sh` 通过（占位符纪律 / 订阅 token 纪律 / 两组形态 DNS 段一致性 / 规则顺序）
- [ ] 手工实测：抓包确认冷启动无明文 `:53`
- [ ] 手工实测：游戏机 / NAT 检测 / 时间同步正常（`always-real-ip` 生效）

> ⚠️ **审计通过 ≠ 配置可用。** 本项目审计脚本只覆盖**静态可判定**的部分。
> 拦截效果、误杀、节点可用性必须实测 —— 这是 Egern 项目连续 5 次
> "脚本全绿、实测仍有问题"换来的结论。

---

### 坑索引

完整复盘见 `reference/surge/pitfalls.md`。**高频坑速查**：

| 症状 | 根因 | 修法 |
|---|---|---|
| 国内网站整片走代理 | IP 规则加了 `no-resolve`，但 `FINAL` 前没有域名类国内直连集 | 加 `direct.txt`，见铁律 2 |
| 配置加载失败「策略无法解析」 | `pre-matching` 策略写成了策略组；或 `underlying-proxy` 指向不存在的节点 | 改字面量 / 先建被引用的节点 |
| 报「规则引用了未定义的策略 `CN`」 | 审计器把 `GEOIP` 当成"无匹配值"类型，策略取到了 index 1 | `GEOIP` / `IP-GEOIP` / `ASN` 的策略恒在 index 2（`RULE-SET` 同理，index 1 是规则集标识） |
| 冷启动抓包有明文 `:53` | `encrypted-dns-server` 里有主机名端点；或 `dns-server` 写了 `system` | 端点换 IP 字面量 |
| 每个新域名首访卡一下 | `GEOIP,CN` 或其他 IP 规则缺 `no-resolve` | 全部加 `no-resolve`（注意同时补铁律 2） |
| 端点选境内还是境外 | 是**性能取向**还是泄露问题？ | 它是**性能探针**：官方 KB 明确走代理时解析在代理服务器进行。`internet-test-url` 宜国内，`proxy-test-url` 宜境外（含国际段）。**别把境外端点当缺陷报** |
| 游戏机 NAT 检测坏掉 | `always-real-ip` 缺游戏机主机名，或它们没被前置域名规则接住 | 补 `always-real-ip` + `DOMAIN-SUFFIX` 规则 |
| 审计器把 `miui.com` 当境外域 | 国内域名判据只认 `.cn` 后缀 | 用显式后缀清单，见 `_surge_common.py` 的 `DOMESTIC_TEST_SUFFIXES` |
| 审计器说「hijack-dns 只覆盖 6 个」 | 判据是"条数"，但 `:53` 地址空间无限、永远列不全 | 判据改成「还有多少**已知的**知名境外解析器没覆盖」 |
| 只测 `.cn` 域名时全绿，实际分流是坏的 | 配置靠 `DOMAIN-SUFFIX,cn` 兜底，不是真的接住了国内域名 | 探针里**刻意混入非 `.cn`** 的国内域名（`qq.com`/`taobao.com`/`miui.com`） |

---

### 引用文件与官方文档

- Surge 官方文档：<https://manual.nssurge.com/>
  - DNS 服务器与语法：<https://manual.nssurge.com/dns/dns-server.html>
  - 加密 DNS（`encrypted-dns-server`）：<https://manual.nssurge.com/dns/encrypted-dns.html>
  - `hijack-dns` / `always-real-ip` / DNS 阶段 REJECT：<https://manual.nssurge.com/dns/advanced.html>
  - `[Rule]` 类型与选项：<https://manual.nssurge.com/rules/overview.html>
  - `[Proxy Group]` 类型与参数：<https://manual.nssurge.com/policy-groups/overview.html> · <https://manual.nssurge.com/policy-groups/parameters.html>
  - Proxy 类型与参数：<https://manual.nssurge.com/policies/overview.html> · <https://manual.nssurge.com/policies/parameters.html>

> ⚠️ Surge 是闭源商业软件，**很多行为没有文档，只能实测**。
> 本技能里凡是写「实测」的地方都请当作经验值 —— 版本更新后需重新验证。

---

## 分支 B · Egern 配置防 DNS 泄露

### 适用

用户给一份 Egern `Profile.yaml`（或含 `dns:` 段的 YAML），要求「防 DNS 泄露 / 别让 DNS 裸奔 / 检查 DNS 配置」，或反馈「实测有 DNS 泄露」。也可用于交付前自检。

### 引用文件（按需读取）

本文件是**主干**：Egern 双轨 DNS 模型、18 项审计清单、加固模板、验收标准。
下列细节按需读取 —— 每个文件开头都写了「何时读」：

| 文件 | 何时读 |
|---|---|
| `reference/egern/hardening-template.md` | 要产出一份加固后的 `dns` 段 + `rules` 时 —— 完整 YAML，含逐行理由 |
| `reference/egern/pitfalls.md` | 排查实际泄露、或改动判据 / 规则集之前 —— 18 个坑的事故复盘 |
| `reference/egern/leak-localization.md` | 用户报「leak test 显示某运营商」时 —— 网络侧实测流程 |
| `reference/egern/ruleset-weight.md` | 用户问「规则集是不是太重」时 —— 内存 / 耗时实测 |
| `reference/egern/checker.md` | 跑审计脚本前（命令与环境要求）、或要改判据时（审计演进史） |
| `reference/egern/public-repo.md` | 要更新模板 / 了解公开仓库结构时 |

---

### Egern 的 DNS 模型（不理解这个就会改错地方）

官方 `docs/configuration/dns` 定义**两条互不相通的解析路径**：

| 路径 | 用途 | 连接上游时 | 未命中时 |
|---|---|---|---|
| **默认 DNS** | 解析**用户要访问**的域名 | **遵循代理规则**（可走代理） | 回退 Bootstrap |
| **代理 DNS** | 官方措辞是"供代理服务解析目标域名"；但从"**强制直连**"这个约束反推，它实际承担的是**节点 `server` 的域名** —— 那个名字必须在隧道建立前解析出来 | **强制直连**（避免 DNS→代理→DNS 循环） | 未配 `proxy_nameservers` 时回退 Bootstrap |

⭐ **「强制直连」这条约束是理解一切的关键**：在国内，直连去问境外解析器（8.8.8.8:443 之类）基本不通。所以**代理侧的任何解析，只有两条出路：国内解析器，或者明文 bootstrap（223.5.5.5 → 也可能回落 `system` = 运营商）**。这条路径**无法加密**，只能靠"让它不需要解析"（节点写成 IP）或"给它一个确定的可达解析器"来收口。

⭐ **被忽略的最重要前提：`proxies[].server` 是域名还是 IP。** 本类事故里，**域名形式的节点必然产生一次「本机 + 直连 + 明文」解析**，这是整份配置里唯一**必定发生**的国内解析（不取决于用户访问什么网站，只取决于要连哪个节点）。**动手前先统计节点形式**：
```bash
python -c "import yaml;d=yaml.safe_load(open('Profile.yaml',encoding='utf-8'));print([(list(p.values())[0].get('name'),list(p.values())[0].get('server')) for p in d['proxies']])"
```


**社区事实标准配置（Repcz，被 Toperlock 等多仓库引用）有一句比官方文档更实用的话：**

> 「Egern 的解析规则接近 Surge，即**已经匹配到走节点的规则交由节点 dns 查询，dns 设置仅对需要本地解析的域名进行查询**」

→ **进代理的域名由节点远端解析；本地 `dns:` 段只服务「直连域名」和「代理节点自己的域名」。** 这决定了改哪里才有意义。

**Bootstrap 与回退链（这是"泄露到运营商"的唯一来源）**，官方原文：

> `bootstrap` …… 仅支持传统 UDP 协议（端口 53），且不遵循代理规则——**流量直连**。用途：① 解析 `upstreams` 中加密 DNS 服务器的主机名；② 作为最终的 DNS 回退。
> `bootstrap` …… **未配置或解析失败时，自动使用系统 DNS 服务器。**

**完整回退链：选中的上游解析失败 → bootstrap（明文 UDP:53、直连）→ 若 bootstrap 也失败 → system DNS（= 运营商 DHCP 下发的那台）。**

> 🚨 **国内运营商普遍对第三方明文 :53 做 DNS 重定向/调度。** 所以只要有任何查询落到 bootstrap 或 system 这两条明文路上，最终应答的解析器就可能变成**运营商自己的服务器** —— 用户就会看到「DNS 泄露到中国 ISP」。**这条路无法加密，唯一办法是让它永不触发。**

**推论：泄露只可能出在这几个位置** ——
1. `upstreams` / `proxy_nameservers` 里用了**域名**形式的加密 DNS（必被 bootstrap 明文解析一次）
2. ⭐ **节点 `server` 是域名，且 `forward` 里没有为它写显式规则**（→ 落境外组 → 直连通不了 → 回退明文 bootstrap / `system`）。**这是 CN 环境下最常见、也最容易被漏掉的一条。**
3. **回退被触发**（上游写错、端点失效、或端点路由被绕坏）→ 落到明文 bootstrap / system
4. **IP 类规则没 `no_resolve`**（为判定规则而触发解析）
5. **国内解析器被用在境外域名上**（见下）
6. ⭐ **profile 自身运行所必需的解析**（`proxy_latency_test_url` / `direct_latency_test_url` 的域名、策略组 `icon` 的域名）没有被靠前的 forward 规则接住。这些名字**普遍不在 ChinaDomain.list 里** —— 实测 `cp.cloudflare.com`、`connectivitycheck.platform.hicloud.com`、`jsdelivr.net`、`raw.githubusercontent.com` 全部 **0 命中**（表里唯一两条 cloudflare 还是注释掉的），于是整类落到兜底 = 境外组。而这类解析**每轮节点测速都要做一次**（策略组 `interval` 到点就全量测一遍），所以它的泄露是**持续型**的、与你访问什么网站无关。**这是继节点域名之后第二个必须显式接住的名字类别**（f3 漏的就是它）。

### ⚠️ 实测铁律：国内解析器不能用来解析境外域名

实测（本机出口直连，取 `www.google.com` 的 A 记录）：

| 端点 | RFC8484 线格式 | JSON API | `www.google.com` 返回 |
|---|---|---|---|
| `doh.18bit.cn` | 200 ✓ | 400 | `216.239.38.120` |
| `dns.alidns.com` | 200 ✓ | 400 | **`31.13.92.37`（Facebook 段，典型 GFW 污染签名）** |
| `doh.pub` | 200 ✓ | 200 | `174.132.167.252` |
| `dns.google` / `1.1.1.1` / `8.8.8.8` | 200 ✓ | 400/200 | `142.251.x.x` ✓ 真实地址 |

**结论：让国内解析器解境外域名，不是"泄露"这么轻 —— 是直接解析错（拿到污染 IP）。** 所有分岔设计都要围绕这条。

#### ⚠️ 铁律修正：本条只约束"本地解析"，不适用于兜底组（2026-09-19 二次修正）

上面这条铁律有两个边界，不划清就会把配置改坏：

1. **它只约束"本地解析"这条路径。** 官方 DNS 文档 + 社区共识：**已经匹配到走节点的域名由节点远程解析**，本地 `dns:` 段只为"需要本地解析"的名字服务（DIRECT 域名、节点域名、profile 自身依赖）。所以**兜底指国内组，不会让"要访问的境外网站"拿到污染答案** —— 它只影响那些本来就走直连的域名。
2. **"泄露到运营商"和"答案被污染"是两个不同的问题，致命的是前者。** 一份把兜底挂在境外组、却在代理未就绪时回退明文的配置，比一份兜底用国内加密组的配置**危险得多**：前者泄露给运营商（不可撤销），后者最坏只是本地解析的 DIRECT 域名拿到国内答案（可接受，且对国内/Apple 域名反而更快更准）。

⇒ **兜底组的唯一判据是「直连可达」，不是「指向境外」。** 这条判据的代价是：我上一版审计里"兜底指国内 = HIGH"是**错判**，已撤回（见坑 13）。

### 审计清单

| # | 检查 | 判据 | 严重度 |
|---|---|---|---|
| 1 | `upstreams` / `proxy_nameservers` 的加密 DNS 是否 IP 字面量或已钉 hosts | 域名端点 → 必被 bootstrap 明文解析 | **境外域名=高**；国内域名=低 |
| 2 | ⭐ **`proxies[].server` 是域名的节点，它的解析走哪条路** | 节点域名走的是**代理 DNS**。f7 起 `proxy_nameservers` 已被显式设置 ⇒ 代理 DNS **跳过 `forward`**，只用那组 IP 字面量端点 ⇒ **不需要、也不应该**在 `forward` 里为节点域名写规则（那是死代码，见坑 18 / 清单 18）。判据从"forward 有没有接住"改成「**`proxy_nameservers` 是否显式设置、端点是否全为 IP 字面量**」 | **高** |
| 2b | `proxy_nameservers` 是否存在 | **f7 起必须显式写。** 它是**硬覆盖**：一设就绕过 `forward`、强制直连。**"不写"才是问题** —— 官方语义「未配置时，代理 DNS 与默认 DNS 共用 Forward 规则，**未命中回退 Bootstrap**」，等于留下一条通往明文 UDP:53 的兜底分支。只能用**国内**端点（代理 DNS 强制直连，境外解析器在电信线路上不可达） | **高（缺失时）** |
| 3 | ⭐ **DNS 端点是否有显式路由** | `geoip` 加了 `no_resolve` 就**不再匹配域名**；主机名形式的端点会落到 `default` → 国内端点被绕到境外出口 / 境外端点直连被阻断。**国内端点必须显式 → DIRECT，境外端点必须显式 → Proxy** | **高** |
| 4 | ⭐ **`forward` 里是否存在「捕获一切」的兜底，且该兜底组「直连可达」** | 兜底存在的意义只有一个：让"未命中的域名"不回退 bootstrap 明文。**判据是"这组在代理没起来时能不能工作"，不是"它指国内还是境外"** —— 组内端点必须全是 IP 字面量，**且至少一个端点在 `rules` 里被判给 `DIRECT`**。只判给 Proxy 的组 = 依赖代理 = 启动期（规则集/DB 下载、首轮测速）会掉进 bootstrap 明文。**兜底指国内组才是对的**（见"铁律修正"）。**写法要认全**：`domain_wildcard: '*'` **和** `domain_regex: '.'`（官方 PCRE2 find 式，命中任意子串）都算兜底 —— 别只认前一种（审计器 f2 就误判过）。推荐**两条都写**（互不依赖的双保险），并让 `domain_wildcard` 放最后便于人/工具识别 | **高** |
| 5 | `geoip` / `ip_cidr` / `ip_cidr6` / `asn` 是否带 `no_resolve` | 官方：`no_resolve` **仅适用这四类**；不加则规则会触发解析 | 高 |
| 6 | ⭐ **规则引用的策略能否解析** | `policy` 是嵌在类型字典里的（`{domain: {match, policy}}`），要读 `r[type]['policy']`。抓 `负载均衡` 这类笔误 | 高 |
| 7 | 硬编码 DoH IP（8.8.8.8 / 1.1.1.1 / 9.9.9.9 / OpenDNS…）是否有启用规则 → 代理 | `hijack_dns` 只覆盖 **:53**，App 用 DoH on **:443** 会绕过 | 中 |
| 8 | ⭐ **`rule_set.match` 是否为 URL 或文件路径** | 写成 `AI` / `抓取` / `Apple push` 这种名字 → 无法加载，等同死规则 | 中 |
| 9 | `block_ips` | 未设 → `0.0.0.0` 这类空路由式污染应答照单全收 | 低 |
| 10 | `real_ip_domains` | 为空 → 走不到隧道的流量（APNs / 内网）也拿 Fake IP，推送/内网会异常 | 低 |
| 11 | `ipv6` | `true` → AAAA 可绕过 IPv4 侧封堵 | 中 |
| 12 | `hijack_dns` 是否覆盖全部 | 官方 example 示例值即 `['*']`（= 接管 :53 并返回 Fake IP） | 高（缺失时） |
| 13 | `public_ip_lookup_url` | **不配置**才不发 ECS（不把公网 IP 交给 DNS 服务器） | 配了才是问题 |
| 14 | `skip_tls_verify` | 应为未设置 / `false` | 低 |
| 15 | ⭐ **profile 自身必需解析的名字**（两个 latency test URL 的域名 + 策略组 `icon` 的域名）是否被"兜底之前"的 forward 规则接住 | 没接住 → 落兜底=境外组 → 一旦这次解析发生在直连侧（代理 DNS 强制直连 / 无代理可用），境外组不可达 → 回退 bootstrap 明文 → 再落 `system` = 运营商。**延迟测试端点 = 高**（每轮测速都触发，持续泄露）；**图标 = 低**（失败只是图标不显示；硬钉到国内解析器反而可能拿到污染/`0.0.0.0` 应答，收益<风险，可故意不动） | **高**（前提：兜底组不安全；f6 起兜底已换成直连可达的国内组 ⇒ 落到兜底不再构成泄露，实际降级为 LOW，且 f10 起**连"单列规则"都不再需要** —— 见清单 18） |
| 16 | ⭐⭐ **远程规则集里有没有"不带 `no-resolve` 的 IP 类条目"** | 这是**最隐蔽的一类**：缺陷不在 profile 里，而在别人仓库的 `.list` 文件里。官方 rules 文档：`no_resolve` 为 true 才"不触发 DNS 解析" ⇒ **不带就触发**。一条启用的 `rule_set` 规则里只要有**一条**这种条目，**每个走到该规则的域名都会被强制本地解析一次**。实测 `blackmatrix7/Surge/Apple/Apple_All.list` 有 13 条（139.178.128.0/18 等 Apple CDN 段）—— 这就是"规则判定 `default → Final → Proxy`、upstream 却是 `bootstrap`"的成因（坑 16）。**必须逐个下载 + 数**，用 `scripts/egern/audit_ruleset_noresolve.py` | **高** |
| 17 | ⭐⭐ **国内域名有没有"域名类"规则兜底**（不是"有没有一条叫 China 的规则"） | 给 IP 规则补 `no_resolve` 会**同时**关掉"靠解析判 IP 归属"这条直连路径。此时若没有一个**真正的域名规则集**接住国内域名，它们会整片落到 `default → Final → 代理`。判据：把规则集**下载下来数域名条目**（`DIRECT` 规则集域名条目 ≈ 0 就是这个坑），再用 `scripts/egern/audit_routing_coverage.py` 拿真实域名走一遍。实测 `ChinaMax.list` 只有 64 条域名 / 12472 条 IP（仓库 README：它与 `ChinaMax_Domain.list` 需"共同使用"） | **高** |
| 18 | ⭐ **`dns.forward` 的 `value` 是不是单值？有没有把节点域名写死？** | 若**除 `reject` 外**所有规则的 `value` 相同（`reject` 是终止动作、不产生解析，`routing_v3` 起允许与其并存） ⇒ **顺序与域名清单都不影响结果** ⇒ 本节对"换订阅/换机场"天然免疫；反之新域名会落到兜底组，必须先确认兜底组安全。另：节点域名的解析走**代理 DNS**，配了 `proxy_nameservers` 后官方明确"**跳过 Forward**" ⇒ **写在 `forward` 里的节点域名规则是死代码**（坑 18）。用 `scripts/egern/audit_dns_forward.py` 跑，含"换订阅演练"（合成未来节点域名） | **中**（可维护性/耦合面） |

**关于 `no_resolve` 的三个层级，别混**：
1. **规则级**（`rules:` 里 `- geoip: {match: CN, policy: DIRECT, no_resolve: true}`）—— 官方明说**只适用 `geoip`/`ip_cidr`/`ip_cidr6`/`asn` 四类**，写在 `rule_set` 规则上**不生效**。
2. **规则集文件内的顶层字段**（Egern 原生 YAML 格式才有的 `no_resolve: true`）—— "影响所有 IP 相关规则"。
3. **规则集条目级**（Surge `.list` 里的 `IP-CIDR,x/y,no-resolve`）—— **第三方 `.list` 走的就是这一层**，也是坑 16 的战场。profile 写得再干净也管不到它。

**键名以 DNS 专页为准**：`domain` / `domain_suffix` / `domain_keyword` / `domain_wildcard` / `domain_regex` / `proxy_rule_set`。
`configuration/example` 页里出现的是 `wildcard` / `regex` 这类短名（且与同页的 `domain_suffix` 混用）—— 那是**陈旧/不一致**的写法，别照抄。`real_ip_domains`、`vif_only`、`include_all_networks`、`include_apns`、`compat_route`、`block_quic` 等顶层字段确实存在（以 example 页为准，没有 `general` 页）。

### 加固模板

```yaml
dns:
  bootstrap:                      # 只能明文 UDP:53 —— 本文件唯一无法加密、无法走代理的出口。
  - 223.5.5.5                     # 列 2 个以上国内公共 DNS：官方「解析失败时自动使用系统 DNS」，
  - 223.6.6.6                     # 而 system 在蜂窝下就是运营商。多列几个只为压低这一最坏分支。
  - 119.29.29.29                  # ⚠️ 绝不写 system —— 那是主动把运营商解析器接进回退链。
  upstreams:
    Domestic-DNS:                 # 国内域名 → 国内加密 DNS。★ 全部写 IP 字面量：
    - https://223.5.5.5/dns-query  #   端点上每写一个主机名，官方就会用明文 bootstrap 解析它一次
    - https://223.6.6.6/dns-query  #   （bootstrap 用途①）。写 IP 则一次都不产生，且零依赖。
    - https://1.12.12.12/dns-query #   下面 6 个已实测通过（含证书覆盖 IP），两家机构 × 两种协议。
    - https://120.53.53.53/dns-query
    - tls://223.5.5.5
    - tls://1.12.12.12
    Foreign-DNS:                  # ★ 一律 IP 字面量，杜绝 bootstrap 解析
    - https://8.8.8.8/dns-query    # 需在 rules 里把这些 IP 显式判给 Proxy，链路才是
    - https://8.8.4.4/dns-query    # 「设备 → 代理 → 8.8.8.8」，从国内蜂窝也能建起来。
    - https://1.1.1.1/dns-query    # 多列端点：官方「组内并发竞速、最快者胜」，
    - https://1.0.0.1/dns-query    # 触发回退的唯一条件是「本组全失败」，端点越多越不可能。
    - tls://8.8.8.8
    - tls://9.9.9.9                # ⚠️ Quad9 只能走 DoT：其 9.9.9.9 的 DoH 实测
                                  #    返回 HTTP Version Not Supported（只提供 HTTP/3）
                                  #    写 https://9.9.9.9/dns-query 会静默失效。
    # ⚠️⚠️ 本组**不要**用作 forward 的兜底 —— 它必须经代理才可达，把兜底挂在它身上等于
    #      「先有代理，才敢解析」，代理未就绪时那次解析会掉进 bootstrap 明文（见坑 13）。
  forward:                        # ★★ f10 起只留兜底 —— **不要在这里写任何具体域名**（坑 18）
  - domain_regex:                 # ★★ 双保险之一：官方 PCRE2 find 式，'.' 必然命中任何域名
      match: '.'
      value: Domestic-DNS         # ★★ 兜底指向「直连可达」的国内加密组 —— 不是境外组。
  - domain_wildcard:              #    境外组必须经代理，代理没就绪时兜底就会掉进 bootstrap
      match: '*'                  #    明文（见坑 13）。按官方语义走代理的域名由节点远程解析，
      value: Domestic-DNS         #    本地 dns 段只服务 DIRECT 域名，所以国内组没有副作用。
  # ★ 为什么不需要 `.cn` / 国内域名表 / 节点域名 / 延迟测试域名 / 图标域名这些规则：
  #   ① 它们的 value 与兜底**完全相同** ⇒ 单值集合里"命中顺序"不产生任何影响，删掉也不变（清单 18）。
  #      官方那句"第一条命中的决定上游"只在 value 有差异时才有意义。
  #   ② 节点域名的解析走**代理 DNS**，配了 proxy_nameservers 后官方明确"**跳过 Forward**"
  #      ⇒ 写在 forward 里的节点域名规则是**死代码**（f7 之前它有用，f7 之后退役）。
  #   ③ 延迟测试域名与图标域名同理：f4 加它们是因为当时兜底是境外组（不安全）；
  #      f6 把兜底换成国内组之后，它们就已被兜底覆盖。
  #   ⚠️ 千万别为了"看起来严谨"再往这里堆域名 —— 每堆一条就把"换订阅"变成一次复查配置的义务。
  # ★★ f7 起必须显式写 proxy_nameservers —— 不写就等于留下一条通往明文 UDP:53 的兜底分支：
  #   官方原文：「未配置时，代理 DNS 与默认 DNS 共用 Forward 规则，**未命中回退到 Bootstrap**」；
  #   配置后语义：「所有代理 DNS 查询强制走该列表，**Forward 规则会被跳过**」。
  #   只能用国内端点 —— 代理 DNS **强制直连**，境外解析器在电信线路上不可达。
  proxy_nameservers:
  - https://223.5.5.5/dns-query
  - https://223.6.6.6/dns-query
  - https://1.12.12.12/dns-query
  - https://120.53.53.53/dns-query
  - tls://223.5.5.5
  - tls://1.12.12.12
  # ⚠️ 如果你发现"节点连不上"，第一件事是注释掉这 6 行（等价于回到 f6 的行为）。
  hosts:                          # ★ 把上面 DoH 域名钉到 IP（仅当 IP 固定）
    dns.alidns.com: [223.5.5.5, 223.6.6.6]
    doh.pub: [1.12.12.12, 120.53.53.53]
    dot.pub: [1.12.12.12, 120.53.53.53]
  block_ips:                      # 丢弃空路由式污染应答；别放私网段免得误伤内网
  - 0.0.0.0
  - 127.0.0.1

rules:
# ★★ DNS 端点固定路由必须放在 rules 最前 —— geoip 带 no_resolve 后不再匹配域名，
#    主机名形式的端点会落到 default。国内端点不钉住就会被绕到境外出口。
- domain_suffix:
    match: alidns.com
    policy: DIRECT
- domain:
    match: doh.pub
    policy: DIRECT
- ip_cidr:
    match: 223.5.5.5/32
    policy: DIRECT
    no_resolve: true
# ... 223.6.6.6 / 1.12.12.12 / 120.53.53.53 同样处理
- domain:
    match: dns.google
    policy: Proxy
- domain_suffix:
    match: cloudflare-dns.com
    policy: Proxy
- ip_cidr:                        # ★ 兜住「App 硬编码 DoH IP + :443 绕过 hijack」
    match: 8.8.8.8/32
    policy: Proxy
    no_resolve: true
# ... 8.8.4.4 / 1.1.1.1 / 1.0.0.1 / 9.9.9.9 / 208.67.222.222 / 208.67.220.220
# ---- 以下是原有规则 ----
# ... 最后（顺序很关键：国内域名兜底必须在 default 之前）：
- rule_set:                      # ★★ 国内域名直连兜底（坑 17）—— 必须用域名条目足够多的那份：
    match: https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/ChinaMax/ChinaMax_All_No_Resolve.list
    policy: DIRECT               #   111332 条域名 + 12473 条 IP（IP 全带 no-resolve）
                                 #   ❌ 别用 ChinaMax.list：它只是 IP 规则集，域名只有 64 条
- domain_suffix:                  # ★ 补 .cn 直连兜底：不依赖上面那份规则集是否加载成功
    match: cn
    policy: DIRECT
- geoip:                          # ★ 不加 no_resolve 会为每次判定触发解析
    match: CN
    policy: DIRECT
    no_resolve: true
- default:
    policy: <代理组>
```

顶层另加：`ipv6: false`、`hijack_dns: ['*']`、`real_ip_domains: ['*.lan','*.local','*.push.apple.com']`。

> 📌 上面这段（含下面那条 f10 修正）与 [`reference/egern/hardening-template.md`](reference/egern/hardening-template.md)
> 里的**逐字相同**。**权威版本在那一份** —— 要改请改它，本处跟着同步（同一段写两处，只改一处是这仓最忌的事）。

⭐ **f10 起不要做这一步（它的反面才是对的）**：早期版本（f3）要求"把域名形式的节点逐个写成 `domain_suffix → Domestic-DNS`"，因为那时代理 DNS 会共用 `forward`。**f7 显式写出 `proxy_nameservers` 之后，代理 DNS 会跳过 `forward`** ⇒ 那些规则再也没被查询过（死代码，坑 18）。现在只需保证两件事：

1. `proxy_nameservers` **显式设置**，端点全部是**国内可达的 IP 字面量** —— 它是节点域名解析的唯一出口；
2. `forward` **只留兜底**，且兜底组「直连可达」。

⚠️ 顺序仍不能反：**先把解析路径收口（这两条），再去调 `upstreams` 里的解析器**。理由没变 —— 这些名字在隧道建立前必须被解析，而代理侧强制直连，国内根本问不到境外解析器。**但收口的手段是"把代理 DNS 钉死"，不是"在 forward 里列举域名"。**

⭐ **同理，profile 自身运行必需的域名**（`proxy_latency_test_url` / `direct_latency_test_url` / 策略组 `icon`）**也不需要单列规则**：f6 起兜底已是国内加密组，它们天然被覆盖。它们只在**兜底是境外组的配置里**才会造成持续泄露 —— 那正是 f4 加它们的场景。用 `audit_dns_forward.py --drill` 可验证任何域名（含这两类）都落到安全的兜底。

### 判断 hosts 能不能钉

**先实测解析**，IP 固定才钉；CDN 池不能钉（钉了反而破坏轮换）：

```bash
python -c "
import socket
for h in ['dns.alidns.com','doh.pub','doh.18bit.cn']:
    print(h, sorted({a[4][0] for a in socket.getaddrinfo(h,443)}))"
```

实测参考：`dns.alidns.com`→223.5.5.5/223.6.6.6（固定 ✅）、`doh.pub`→1.12.12.12/120.53.53.53（固定 ✅）、`doh.18bit.cn`→**11 个 IP 的 CDN 池（不可钉 ❌）**，且它落在 **42.51.x.x（中国联通）** 上的自建服务 —— 能用作国内上游，但别让它承担"所有国内域名"。

### ⚠️ 已知缺陷索引

**18 条，每条都是真实事故复盘。全文（含完整机制链与修法）见 `reference/egern/pitfalls.md`。**
排查实际泄露、或改动判据 / 规则集之前，先扫一眼这张表。

| # | 一句话 |
|:--:|---|
| 1 | 用 JSON API 判 DoH 端点死活 → 误判（RFC 8484 只强制线格式） |
| 2 | 给 `geoip` 加 `no_resolve` 会悄悄改掉 DNS 端点的路由 |
| 3 | 自己的审计脚本只能验证自己编码进去的假设 |
| 4 | 别假定 `.list` 是域名表（`ChinaMax.list` 98.6% 是 IP） |
| 5 | `policy` 嵌在类型字典里 —— 要读 `r[type]['policy']` |
| 6 | `proxy_nameservers` 不是"多加一层保险"，是"砍掉整条 `forward`" |
| 7 | 兜底判定不要只认 `'*'` —— `domain_regex: '.'` 等效，也要认 |
| 8 | `forward` 里的 `proxy_rule_set` 含裸 IP 条目 ⇒ 为判定而强制预解析 |
| 9 | 审计器"看不见"的那一类名字，就是最终泄露的那一类 |
| 10 | 「解析失败自动用系统 DNS」= 运营商泄露的入口 |
| 11 | **流程坑，代价最大**：先确认设备与链路，再谈机制 |
| 12 | 端点写成 IP 字面量之前，必须逐个实测（Quad9 的 DoH 静默失效） |
| 13 | 兜底组挂在"必须经代理才可达"的组上 ⇒ 审计 OK、实测 `upstream: bootstrap` |
| 14 | 看到 `bootstrap` / `system`，一步锁定"明文回退面" |
| 15 | 漏写 `no_resolve` 的 `geoip` ⇒ 每个走到它的域名被强制预解析一次 |
| 16 | 强制解析藏在**别人仓库的 `.list` 里**（`Apple_All.list` 13 条裸 IP） |
| 17 | 治好 DNS 泄露的那一手，会顺手把国内域名分流一起干掉 |
| 18 | 不要把节点域名写进 DNS 分流规则 —— 死代码 + 制造维护耦合 |

---

### 改配置的安全姿势

Egern profile 常含**超长单行**（`mitm.ca_p12` 的 base64 CA 证书，可达数千字符）。**不要用 YAML dump 重写整个文件**（会丢注释、改格式）。正确做法：

1. 按行读入（`raw.split('\n')`）
2. 用「内容定位 + 断言唯一性」的方式插行/替换行
3. 额外写回，逐字节对比关键字段（如 `ca_p12` 完全一致）
4. 用 `yaml.safe_load` 验证新旧两份都能解析

⭐ **替换锚点必须换行锚定**：`src.index('dns:\n')` 会命中 `hijack_dns:\n` 里的子串，静默吃掉中间十几行（实测）。用 `src.index('\ndns:\n') + 1`，并且改完**逐字段比对未触碰的部分**（本项目用它抓到了那次误删）。

定位改动点的核心是 `find_one(pred, what)` —— 对每处改动断言「全文恰好命中 1 行」，命中 0 或 >1 行就中止。

#### 删除顶层键（实测：f9 删 `mitm` 段）

用户说「HTTPS 解密暂时不用了 / 把 mitm 删掉」时，**先查依赖再删**：

1. ⭐ **有没有规则依赖解密？** 只有 **`url_regex` / `header` / `user_agent` / `process_name`** 这四类需要 MITM 解密才能匹配；`domain*` / `ip_cidr` / `rule_set` / `geoip` 在 TLS 握手前就能判定。查法：
   `sed -n '<rules 起始行>,$p' profile.yaml | grep -c 'url_regex\|header\|user_agent\|process_name'`
   —— 零命中才可安全删（本项目实测零命中，零能力损失）。
2. **删除范围不能按行数猜**：先定位 `^mitm:$`，再断言紧随的缩进行**恰好**是 `  ca_p12:` + `  ca_passphrase:` 两行，再断言第 4 行不是缩进（否则段内还有别的子键，按行数删会吃错）。`ca_p12` 是**单行 3674 字符**的超长行，只有一行，别当成多行 base64。
3. **断言清单（七项）**：被删字段名与 base64 主体零残留 → 其余行逐条未变 → 顶层键数 = 原数 −1 且**差集恰好是 `{mitm}`** → 其余顶层键的值逐个相同 → `dns` / `rules` / `proxies` / `policy_groups` 解析后逐项相等 → YAML 可解析 → UTF-8 无 BOM / LF。
4. **原位留一行中性注释**（**不含** `mitm` / `ca_p12` 等字样，如「此处原为 HTTPS 解密（个人证书）配置段，2026-09-19 按需删除；需要时从 vN 取回」）—— 便于日后恢复，又不会干扰敏感串扫描。
5. **告知用户**：设备上已装的 CA 证书**不必删**（配置里不再解密，它不会被使用；真要清理去「设置 → 通用 → VPN与设备管理 → 配置描述文件」，但这与 DNS 泄露/分流无关）；**回滚 = 用上一版覆盖**，所以上一版必须保留。
6. 删 `mitm` 后三项审计应**与上一版逐字相同**（DNS 面 / 规则集 / 分流）—— 不同就是误删，回去查第 2 步的断言。

### 加固结束的验收标准（七条同时满足才算完）

1. `upstreams` 与 `proxy_nameservers` 里**没有任何主机名端点**（全部 IP 字面量，或已钉 `hosts`）—— 消灭 bootstrap 用途①。
2. `forward` 有兜底，**且兜底组直连可达**（端点全为 IP 字面量 + **至少一个在 `rules` 里判给 `DIRECT`，或至少一个是已知国内解析器 IP** —— 两条二选一，见坑 13 末尾）—— 消灭 bootstrap 用途②，且不依赖"代理已就绪"。
3. 所有 IP 类规则（`geoip` / `ip_cidr` / `ip_cidr6` / `asn`）**都带 `no_resolve`** —— 否则每个走到它的域名都会被强制本地预解析一次（坑 15）。
4. ⭐ **所有被启用的 `rule_set` / `proxy_rule_set`，其规则集文件里的 IP 类条目都带 `no-resolve`** —— 用 `audit_ruleset_noresolve.py` 跑，必须 OK（坑 16）。
5. `bootstrap` 显式列 2 个以上国内公共 DNS 的 IP，**且不含 `system`** —— 把"全失败 → 系统 DNS"压到最低。
   ⚠️ 前 4 条是"让它不被用到"；第 5 条只是把最坏分支的概率压小。**bootstrap 是明文 UDP:53，在运营商线路上无论指向哪个 IP 都可能被接管 —— 它唯一安全的形态是"永远不被触发"。**
6. ⭐⭐ **分流仍然正确：国内域名仍判给 DIRECT。** 用 `audit_routing_coverage.py` 跑，15 个国内探针必须全 `DIRECT`。
   **这一条是第 3 条的代价，必须成对交付** —— 给 IP 规则补 `no_resolve` 会同时关掉"靠解析判 IP 归属"那条直连路径（坑 17）。所以补 `no_resolve` 的同一时刻，必须确认 `default` 之前有一份**含大量域名条目**的国内规则集（如 `ChinaMax_All_No_Resolve.list`）。**"DNS 审计全绿"不等于"配置可用"**：f7 时两个审计脚本双双通过，分流却整片是坏的。
7. ⭐ **`dns.forward` 与订阅零耦合：`value` 单值（`routing_v3` 起 = 非 `reject` 去向单值且等于兜底组），且没有任何一条规则把节点域名写死。** 用 `audit_dns_forward.py profile.yaml --drill` 跑，必须「零耦合 + 通过」。
   **防泄露必须由"兜底组的安全性"承担，而不是由"记得去列举域名"承担** —— 后者会让换订阅变成一件需要复查配置的事，而它连功能都没有（坑 18）。

### 官方文档入口

- DNS 机制：`https://egernapp.com/docs/configuration/dns`（**核心页**，两条路径 + bootstrap + proxy_nameservers + block_ips + hosts 全在此）
- 规则字段：`https://egernapp.com/docs/configuration/rules`（`no_resolve` 适用范围、逻辑规则 `and`/`or`/`not`、rule_set 内部字段）
- 顶层字段全表：`https://egernapp.com/docs/configuration/example`（**注意键名与 DNS 页不一致**）
- 社区参考实现（中国网络环境的最佳实践，DNS 段写法值得对照）：`https://doc.repcz.link/egern/`（原 `repcz.github.io/Egern` 已迁至此，旧地址现 404）
- sitemap（找页面用）：`https://doc.egernapp.com/sitemap.xml`

⚠️ `https://egernapp.com/zh-CN/docs` 和 `/docs/configuration/general` 是 **404**；顶层字段只能从 `configuration/example` 页获取。DNS 页有中文版 `/zh-CN/docs/configuration/dns`。
