---
name: profile-dns-hardening
description: 审计并加固 Surge / Egern 配置（.conf 与 Profile.yaml）的 DNS 泄露面与分流覆盖。触发词：Surge 配置、Egern 配置、防 DNS 泄露、DNS 裸奔、leak test 显示 china telecom、upstream 显示 bootstrap、dns-server = system、encrypted-dns-server 是域名、proxy_nameservers、hijack-dns / hijack_dns、bootstrap 泄露、明文 :53 旁路、HomePod / Apple TV DNS 泄露、no-resolve / no_resolve、GEOIP CN 缺 no-resolve、IP 规则触发 DNS 解析、加了 no-resolve 之后分流坏了、国内域名全落 FINAL、国内网站不是直连、direct.txt、ChinaMax 只有 IP、规则集 IP 条目缺 no-resolve、Apple_All.list 强制解析、pre-matching、pre-matching 指向策略组、underlying-proxy 无法解析、smart 组评分、policy-regex-filter、flatten 的等价写法、always-real-ip、fake-ip、延迟测试域名泄露、cp.cloudflare.com 泄露、图标域名泄露、dns.forward 兜底、白名单排在 REJECT 之后、profile 模板、Egern dns 段、Egern dnsleak、Egern YAML 配置优化、DNS 泄露到运营商（电信/联通/移动）、日志里规则判定正常但 upstream 是 bootstrap、节点域名明文解析、系统 DNS 回退泄露、rule_set 触发 DNS 解析、blackmatrix7 No_Resolve 变体、ChinaMax.list 没有域名规则、ChinaMax_All_No_Resolve、国内域名走代理、分流覆盖审计、dns.google 泄露、引导解析泄露、extended-matching、Surge 拒绝加载配置、proxy-test-url 泄露、gstatic generate_204、归档配置、升版本号、config_old、Release 发布、release_publish、check_releases、Release 资产命名、补发历史版本。命中本技能时优先加载本文件并按内核进入对应分支，不要凭记忆答语法。
agent_created: true
---

# 配置防 DNS 泄露 · Surge / Egern 双内核

本仓库是 **AI 驱动的配置模板仓**：全部操作文档、逐键语义与审计判据都整合在本 skill 里，
没有面向人类的 docs / DetailsReadme。AI 按用户需求 + 内核官方语法修改配置，闸门守底线。

**阅读协议（按序执行）**：
1. §0 定内核 → §1 五类泄露面 → §2 四条铁律 → §3 六条底线与归档/动线 → **只读对应分支**（A 或 B），不读另一支。
2. 细节按 §4 索引表的「何时读」列跳转 `reference/`；任务没命中索引就不要读。
3. **权威归属**（本文件与专项文件重复时，以专项文件为准）：逐键语义 = `profile-anatomy` ·
   加固模板逐行理由 = `hardening-template` · 坑全文 = `pitfalls` · 加固清单判据 = `hardening-checklist` ·
   审计命令与环境 = `checker`。
4. 本文件行文原则：**表格优先、判据先行**；每处「实测」都是经验值教训，改判据前先读对应坑全文。

**先定内核，再进对应分支**——两者的模型不通用，
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
| Surge | `surge/profiles/*.conf` | `[Proxy Group]` | `[Rule]` | `skill/scripts/surge/` | `skill/scripts/surge/check_surge_dns.py` |
| Egern | `egern/profiles/*.yaml` | `policy_groups:` | `rules:` | `skill/scripts/egern/` | `skill/scripts/egern/check_egern_dns.py` |

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
   判据是**下载规则集数域名条目**，不是看名字（`ChinaMax.list` 名字像域名集，实测 IP 类 12472 条、域名类只有 64 条）。
3. **厂商专属规则排在通用 `AI.list` 之前**（`OpenAI` / `Gemini` / `Anthropic` / `Claude`），否则专属组形同虚设。
4. ⭐ **兜底/默认出口的判据是「直连可达」，不是「指向境外」。**
   两内核同理：兜底承担的是"代理还没起来时的那次解析"。挂在必须经代理才可达的组上，
   等于留下一条通往明文的分支——而**泄露不可撤销，答案被污染可接受**。
   （Egern 侧这条曾以"兜底指国内 = HIGH"的形式被写成错判并撤回，见坑 13。）

**内核专属、不可互相套用的一条**：Surge 的 `pre-matching` 规则策略**必须是字面量 REJECT 族**，写成策略组会导致
Surge **拒绝加载整份配置**；Egern 侧没有对应机制，它的等价约束是 `proxy_nameservers` 一设就**跳过 `forward`**。

## 3 · 底线与纪律（AI 改配置前必读）

### 六条底线

1. 🚫 **不得删除项目文件。** `profiles/` 顶层固定名四件（`lazy` / `routing` × 完整版 / `.min`，两内核）
   与 `profiles/config_old/` 归档永远保留；配置文件的位置与组织形式不得移动或调整。
2. 🎯 **修改必须按用户意愿在原有配置上改。** 固定名 `lazy` / `routing` 不得擅自改名；不擅自重构结构。
3. 🛡️ **防 DNS 泄露是不可触碰的红线。** 本仓立身于此：**任何文件**（配置、文档、脚本、CI）的改动
   都不得削弱既有防泄露面——删防泄露键、放松解析顺序约束、引入新回退路径、破坏 `no-resolve`
   成对交付、放松审计判据，都算削弱；**只许加固，不许放松**。改前读本文件对应分支与
   `profile-anatomy`；改后跑闸门（下方动线第 ⑤ 步）。官方文档入口在分支 A / B 末尾。
4. 🔐 **占位符凭据纪律。** 节点 IP 用 RFC 5737（`192.0.2.x` 等）、凭据用 `REPLACE_WITH_*`、
   订阅 token 用 `REPLACE_WITH_YOUR_TOKEN`。`check_secrets.py` 全仓扫描，push 前必过。
5. 🧬 **`.min` 对拍与可移植性。** `.min` 永远由 `make_min.py` 生成、不手工编辑；
   完整版与 `.min` 的 DNS 段逐字一致（`check_min_pair.py` 守）；行尾 / BOM / 命名由 `check_portability.py` 守。
6. ⚖️ **Surge / Egern 基本对齐不可破。** 两内核的防泄露结构、键集、版本号、审计判据必须保持
   基本对齐——此原则先于本 skill 存在，**任何文件改动都不得触碰它**。四份现役头注**两内核同号**；
   一侧动了防泄露相关结构，另一侧必须同步评估。对齐 = **防泄露能力等效**，不是逐字照抄——
   一侧写法不得机械套到另一侧，允许偏差仅限 `reference/shared/cross-kernel-diff.md` 记录的内核本质差异。

### 归档机制（配置变动时执行）

- `profiles/` 顶层永远只有固定名四件——它们是永久订阅地址的落点，**升版不改名**；
- 「当前是哪一版」只写在文件头注 `#! version=` 里；
- **配置发生变动时**：变动前的现役内容归档进 `profiles/config_old/`，
  **归档版本号 = 该目录内此分工最新号 + 0.1**（v3.3 → v3.4；v3.9 → 进位 v4.0），
  **完整版与 `.min` 成对归档**（`.min` 不带头注行），**现役头注同步升为归档号 + 0.1**；
  ⚠️ 两侧目录深浅有**历史缺口**时（如 egern lazy 缺 v1.3），归档号取**变动前现役头注号**
  （即 V6「升版前打的快照，与线上逐字节相同」的语义），缺口保留不补号；
  **内容未变的分工也要随四份同号升版并同样入档快照** —— 跨侧「两侧版本一致」断言要求四份头注永远同号。
- 任何文档、脚本、README 里出现"带版本号的订阅 URL"都是错的。
- **发布层（GitHub Release）**：一个分工版本 = 一个 Release（tag = `lazy-vX.Y` / `routing-vX.Y`），
  是 config_old 归档层之上的对外发布层，不替代归档；tag 允许带版本号，
  **Release 资产文件名一律不带版本号**（固定名四件脸）；说明中明确版本号。规矩与模板见
  [`reference/shared/ops.md`](reference/shared/ops.md) §6.9，断言在 `skill/tests/check_releases.py`。

### 改配置标准动线

```
① 只读诊断：跑相关审计脚本，列出可优化项，等用户确认再动手
② 归档：变动前的现役四份（若该分工要动）按上行规则复制进 config_old/，现役头注升号
③ 改带注释完整版（lazy.conf / routing.conf / *.yaml）—— .min 不手工碰
④ 生成 .min：python skill/tests/make_min.py --family lazy|routing|all   # 默认只出计划
             python skill/tests/make_min.py --family all --apply        # 确认后写盘
⑤ 收尾闸门（全过才算完）：
   python skill/tests/check_secrets.py && python skill/tests/check_portability.py
   python skill/tests/check_min_pair.py && python skill/tests/check_badges.py && python skill/tests/check_links.py .
   python skill/scripts/surge/check_surge_dns.py surge/profiles/lazy.conf
   python skill/scripts/surge/check_surge_dns.py surge/profiles/routing.conf
   python skill/scripts/egern/check_egern_dns.py egern/profiles/lazy.yaml egern/profiles/routing.yaml
   python skill/tests/make_min.py                 # 漂移检查：四份 .min 应全部「已同步」
⑥ 本地 commit → **停在推送前**。`git push` 永远是独立确认项：用户说「换掉 / 改吧 /
   找个新的」只授权改动本身，讨论与调研阶段的产物一律停在本地 + 汇报表格；
   拿到用户单独的「推」指令（如「推吧 / 没问题就推」）才 push（CI 在 push / PR 自动重跑同一组检查）
⑦ 发布 Release（push 之后）：`python skill/scripts/release_publish.py --family <lazy|routing> --apply`
   —— 只发本次升到的那个分工版本（tag 允许带版本号，资产文件名不带，说明写明版本号；
   缺 --family 则补齐全部缺失的 Release）。发完跑 `python skill/tests/check_releases.py` 验收。
   规矩与说明模板见 `reference/shared/ops.md` §6.9。
```

> **注意**　mutating 步骤（②③④⑥⑦）必须等用户明确确认后再执行；①是只读的，随时可跑。
> **注意**　改 DNS 段 = 一次改全套：`lazy` / `routing` × 完整版 / `.min` 四份（跨 lazy/routing 的
> 16 键逐字一致由 `check_min_pair.py` 的 ②-c 断言守）。想只给某一版加防泄露键，先问它为什么不是四条都要。

### 其他共享纪律

- ⚠️ **审计通过 ≠ 配置可用。** 脚本只覆盖**静态可判定**的部分；拦截效果、误杀、节点可用性必须实测。
  这条来自 Egern 侧连续 5 次"脚本全绿、实测仍有问题"的代价。
- 📍 **命令的路径基准**：本文与 `reference/` 里凡可照抄执行的命令，路径一律以**仓根**为基准书写（要 `cd` 的会显式写 `cd`）；
  行文里为省字出现的简写（如 `scripts/probe_doh.py`）不是可执行路径，取真身请以仓根全路径为准。
- 🧷 **Egern 改配置的安全姿势**：profile 含数千字符的超长单行，**不要用 YAML dump 重写整个文件**；
  按行读入 + 内容定位 + 断言"全文恰好命中 1 行"，改完逐字段比对未触碰部分。详见分支 B。
- 🚨 **凡写「实测」处皆为经验值**，两款都是闭源商业软件，很多行为无文档可依，版本更新后需重新验证。
- 📊 **任何条数一律现抓，不要照抄文档里的数。** 远程规则集里除 `AI.list`（两内核都钉在 40 位 commit）外都没锁、随上游每周漂；
  文档为可读性写的条数只是**写作时点的约数**。要精确值就跑 `skill/scripts/surge/audit_ruleset_content.py <profile>`（Surge）/
  `skill/scripts/egern/profile_ruleset.py <规则集 URL>`（Egern），两侧脚本都逐个数条目类型。
- 🚷 **没有用户明确指令，不连接、不操作任何网络设备**（旁路由等）。验证配置用本地脚本，不动用户的路由器。

## 4 · 按需读取

### reference/shared/（跨内核主题）

| 文件 | 何时读 |
|:-----|:-------|
| [`reference/shared/cross-kernel-diff.md`](reference/shared/cross-kernel-diff.md) | 要在两内核间移植一份改动时——**必读**，含逐项语法映射与实测差异清单 |
| [`reference/shared/rulesets.md`](reference/shared/rulesets.md) | 换 / 加 / 删任何规则集之前——清单、来源、匹配顺序、排序与选材约束 |
| [`reference/shared/hardening-checklist.md`](reference/shared/hardening-checklist.md) | 人工逐条对照加固清单时（Surge 14 项 / Egern 18 项完整判据） |
| [`reference/shared/no-resolve-pairing.md`](reference/shared/no-resolve-pairing.md) | 动 `no-resolve` / 换国内直连规则集之前——成对交付的完整事故复盘 |
| [`reference/shared/dns-basics.md`](reference/shared/dns-basics.md) | 需要向用户解释泄露机制时——五个真实泄露案例（现象 → 机制 → 修法） |
| [`reference/shared/ops.md`](reference/shared/ops.md) | 按内核的逐段操作要点 + 日常维护动线 |
| [`reference/shared/troubleshoot-faq.md`](reference/shared/troubleshoot-faq.md) | 出了问题——排查序列、两内核症状速查、全量闸门用法、FAQ 与术语表 |

### reference/surge/（单侧主题）

| 文件 | 何时读 |
|:-----|:-------|
| [`reference/surge/profile-anatomy.md`](reference/surge/profile-anatomy.md) | 改 Surge 配置需要确认某个键 / 组 / 规则的语义与边界时（逐键权威） |
| [`reference/surge/hardening-template.md`](reference/surge/hardening-template.md) | 要产出一份加固后的 Surge profile 时——逐段模板 + 逐行理由 |
| [`reference/surge/pitfalls.md`](reference/surge/pitfalls.md) | 排查实际泄露、或改动判据 / 规则集之前——坑的事故复盘 |
| [`reference/surge/leak-localization.md`](reference/surge/leak-localization.md) | 用户报「leak test 显示某运营商」时——网络侧实测流程 |
| [`reference/surge/checker.md`](reference/surge/checker.md) | 跑审计脚本前（命令与环境要求）、或要改判据时（判据演进史） |
| [`reference/surge/ruleset-weight.md`](reference/surge/ruleset-weight.md) | 用户问「规则集是不是太重」时——按类型数条目、识破名字骗人 |
| [`reference/surge/public-repo.md`](reference/surge/public-repo.md) | 要更新模板 / 了解仓库结构与门面纪律时 |

### reference/egern/（单侧主题）

| 文件 | 何时读 |
|:-----|:-------|
| [`reference/egern/profile-anatomy.md`](reference/egern/profile-anatomy.md) | 改 Egern 配置需要确认某个顶层字段 / 组 / 规则的语义与边界时（逐键权威） |
| [`reference/egern/hardening-template.md`](reference/egern/hardening-template.md) | 要产出一份加固后的 `dns` 段 + `rules` 时——完整 YAML，含逐行理由 |
| [`reference/egern/pitfalls.md`](reference/egern/pitfalls.md) | 排查实际泄露、或改动判据 / 规则集之前——18 个坑的事故复盘 |
| [`reference/egern/leak-localization.md`](reference/egern/leak-localization.md) | 用户报「leak test 显示某运营商」时——网络侧实测流程 |
| [`reference/egern/checker.md`](reference/egern/checker.md) | 跑审计脚本前（命令与环境要求）、或要改判据时（审计演进史） |
| [`reference/egern/ruleset-weight.md`](reference/egern/ruleset-weight.md) | 用户问「规则集是不是太重」时——内存 / 耗时实测 |
| [`reference/egern/public-repo.md`](reference/egern/public-repo.md) | 要更新模板 / 了解仓库结构与脱敏清单时 |

## 分支 A · Surge 配置防 DNS 泄露

### 适用

用户给一份 Surge `.conf`（或要生成一份 Surge profile），要求「防 DNS 泄露 / 别让 DNS 裸奔 /
检查 DNS 配置」，或反馈「实测有 DNS 泄露」「国内网站不是直连」。也可用于交付前自检。

**不适用**：Clash / mihomo（`no-resolve` 语义不同，`fake-ip-filter` 是另一套）、
Egern（见分支 B）、Shadowrocket（`dns-server` 语义不同）。

### 引用文件（按需读取）

本文件是**主干**：三条出口模型、12 项审计清单、加固模板、坑索引、验收判据。
`reference/surge/` 七篇的「何时读」索引见 §4，不在此重复。**移植到 Egern 侧前必读
[`reference/shared/cross-kernel-diff.md`](reference/shared/cross-kernel-diff.md)**。

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

另有三个**不在清单里但必须查**的审计脚本（+ 规则集刷新参数 `audit_ruleset_refresh.py`，见 `reference/surge/checker.md`）：

| 脚本 | 查什么 | 联网 |
|---|---|---|
| [`audit_ruleset_content.py`](scripts/surge/audit_ruleset_content.py) | ① 远程规则集里有没有**不带 `no-resolve` 的 IP 条目**；② 判给 DIRECT 的规则集**域名条目总量**是否够（判据是数域名条目，**不是**看规则集名字） | ✅ |
| [`audit_routing_coverage.py`](scripts/surge/audit_routing_coverage.py) | 拿真实域名**走一遍** `[Rule]`，看最终命中哪条。期望表按 profile 自动切换；**不得**放宽成"只要不是 DIRECT" | ✅ |
| [`audit_region_filters.py`](scripts/surge/audit_region_filters.py) | 分流配置里 7 个地区组的 `policy-regex-filter` 关键词是否同步（负向断言那份拷贝）、是否互斥、类型是否 `smart`。见坑 16 | ❌ |

⚠️ **分流配置（按应用 / 按地区分组）另有三条 Surge 特有的硬约束**，
与 Egern 等客户端的写法**不通用**：

| 约束 | 官方依据 | 正确写法 |
|:-----|:---------|:---------|
| Surge **没有** `flatten` | — | 用 `include-other-group="X"`，它复制的是"resolved member policies"，语义等价 |
| **Smart 组不能拿组名当子策略** | [Smart 智能策略组](https://kb.nssurge.com/surge-knowledge-base/zh/guidelines/smart-group) | 要 `smart` 自动选优 → `include-other-group`；要在面板点进地区 → 用 `select` + 组名作成员 |
| `policy-regex-filter` **对显式列出的成员无效** | [Policy Including](https://manual.nssurge.com/policy-groups/policy-including.html) | 想筛 `[Proxy]` 里的本机节点，必须同时写 `include-all-proxies=true` |

⚠️ 空组是允许的（正则没筛到任何节点）—— Surge **不会**因此拒绝加载，
但指向它的规则会断流。分流配置导入后要确认哪几个组是空的。

### 加固模板

完整模板见 [`reference/surge/hardening-template.md`](reference/surge/hardening-template.md)。最小可用骨架：

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
RULE-SET,<private.txt>,DIRECT       ← 实测零 IP ⇒ 不写规则级开关
RULE-SET,<direct.txt>,DIRECT        ← 主承重墙，见下方铁律（实测零 IP ⇒ 不写开关）
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
   **不是**看规则集名字（`ChinaMax.list` 名字像国内域名集，实测 IP 类 12472 条、域名类只有 64 条）。
3. **`pre-matching` 的规则策略必须是字面量 REJECT 族**，不能是策略组。
   策略组在运行时可能解析成 DIRECT，Surge 会**拒绝加载整份配置**。

#### 验收判据（7 条，全过才算可用）

- [ ] `check_surge_dns.py` 退出码 0（无 HIGH）—— `surge/profiles/*.conf` **顶层固定名四件**都要过
- [ ] `audit_ruleset_content.py` 通过（远程规则集无缺 `no-resolve` 的 IP 条目；直连集合域名条目 ≥1000）
- [ ] `audit_routing_coverage.py` 通过（国内探针全部 DIRECT、境外探针**命中预期的组**、误杀探针不被 REJECT）
- [ ] `audit_region_filters.py` 通过（仅分流配置：关键词同步 / 互斥 / 类型 smart）
- [ ] `check_secrets.py` 通过（占位符纪律 / 订阅 token 纪律）
- [ ] 手工实测：抓包确认冷启动无明文 `:53`
- [ ] 手工实测：游戏机 / NAT 检测 / 时间同步正常（`always-real-ip` 生效）

### 坑索引

完整复盘见 [`reference/surge/pitfalls.md`](reference/surge/pitfalls.md)。**高频坑速查**：

| 症状 | 根因 | 修法 |
|---|---|---|
| 国内网站整片走代理 | IP 规则加了 `no-resolve`，但 `FINAL` 前没有域名类国内直连集 | 加 `direct.txt`，见铁律 2 |
| 配置加载失败「策略无法解析」 | `pre-matching` 策略写成了策略组；或 `underlying-proxy` 指向不存在的节点 | 改字面量 / 先建被引用的节点 |
| 报「规则引用了未定义的策略 `CN`」 | 审计器把 `GEOIP` 当成"无匹配值"类型，策略取到了 index 1 | `GEOIP` / `IP-GEOIP` / `ASN` 的策略恒在 index 2（`RULE-SET` 同理，index 1 是规则集标识） |
| 冷启动抓包有明文 `:53` | `encrypted-dns-server` 里有主机名端点；或 `dns-server` 写了 `system` | 端点换 IP 字面量 |
| 每个新域名首访卡一下 | `GEOIP,CN` 或其他 IP 规则缺 `no-resolve` | 全部加 `no-resolve`（注意同时补铁律 2） |
| 端点选境内还是境外 | 是**性能取向**还是泄露问题？ | 它是**性能探针**：官方 KB 明确走代理时解析在代理服务器进行。`internet-test-url` 宜国内，`proxy-test-url` 宜境外（含国际段）。**别把境外端点当缺陷报** |
| 游戏机 NAT 检测坏掉 | `always-real-ip` 缺游戏机主机名，或它们没被前置域名规则接住 | 补 `always-real-ip` + `DOMAIN-SUFFIX` 规则 |
| 审计器把 `miui.com` 当境外域 | 国内域名判据只认 `.cn` 后缀 | 用显式后缀清单，见 `check_surge_dns.py` 里的 `DOMESTIC_TEST_SUFFIXES` |
| 审计器说「hijack-dns 只覆盖 6 个」 | 判据是"条数"，但 `:53` 地址空间无限、永远列不全 | 判据改成「还有多少**已知的**知名境外解析器没覆盖」 |
| 只测 `.cn` 域名时全绿，实际分流是坏的 | 配置靠 `DOMAIN-SUFFIX,cn` 兜底，不是真的接住了国内域名 | 探针里**刻意混入非 `.cn`** 的国内域名（`qq.com`/`taobao.com`/`miui.com`） |

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

## 分支 B · Egern 配置防 DNS 泄露

### 适用

用户给一份 Egern `Profile.yaml`（或含 `dns:` 段的 YAML），要求「防 DNS 泄露 / 别让 DNS 裸奔 / 检查 DNS 配置」，或反馈「实测有 DNS 泄露」。也可用于交付前自检。

### 引用文件（按需读取）

本文件是**主干**：Egern 双轨 DNS 模型、18 项审计清单、模板骨架速览、验收标准。
`reference/egern/` 七篇的「何时读」索引见 §4，不在此重复。**移植到 Surge 侧前必读
[`reference/shared/cross-kernel-diff.md`](reference/shared/cross-kernel-diff.md)**。

### Egern 的 DNS 模型（不理解这个就会改错地方）

官方 `docs/configuration/dns` 定义**两条互不相通的解析路径**：

| 路径 | 用途 | 连接上游时 | 未命中时 |
|---|---|---|---|
| **默认 DNS** | 解析**用户要访问**的域名 | **遵循代理规则**（可走代理） | 回退 Bootstrap |
| **代理 DNS** | 实际承担**节点 `server` 的域名**——那个名字必须在隧道建立前解析出来（官方措辞是"供代理服务解析目标域名"；从"强制直连"约束反推出这个实际角色） | **强制直连**（避免 DNS→代理→DNS 循环） | 未配 `proxy_nameservers` 时回退 Bootstrap |

**四个决定一切的要点**（改配置前逐一核对）：

| # | 事实 | 对改配置的直接推论 |
|:-:|:-----|:-------------------|
| 1 | **代理 DNS 强制直连**；国内直连去问境外解析器（`8.8.8.8:443` 之类）基本不通 | 代理侧的任何解析只有两条出路：**国内解析器**，或**明文 `bootstrap`**（还可能回落 `system` = 运营商）。这条路径**无法加密**，只能靠「让它不需要解析」（节点写 IP）或「给它确定的可达解析器」收口 |
| 2 | **`proxies[].server` 是域名的节点必然产生一次「本机 + 直连 + 明文」解析**——整份配置里唯一**必定发生**的国内解析，不取决于访问什么网站，只取决于连哪个节点 | 动手前先统计节点形式：`python -c "import yaml;d=yaml.safe_load(open('Profile.yaml',encoding='utf-8'));print([(list(p.values())[0].get('name'),list(p.values())[0].get('server')) for p in d['proxies']])"` |
| 3 | **进代理的域名由节点远端解析**（官方语义 + 社区事实标准 Repcz 原话：「已经匹配到走节点的规则交由节点 dns 查询，dns 设置仅对需要本地解析的域名进行查询」） | 本地 `dns:` 段只服务三类名字：**直连域名 · 节点自己的域名（走 `proxy_nameservers`）· profile 自身依赖**。改哪里才有意义由此决定 |
| 4 | **回退链**（"泄露到运营商"的唯一来源）：选中上游解析失败 → `bootstrap` → 再失败 → `system`。官方原文：bootstrap「仅支持传统 UDP 协议（端口 53），且不遵循代理规则——**流量直连**」，用途「① 解析 `upstreams` 中加密 DNS 服务器的主机名；② 作为最终的 DNS 回退」，且「未配置或解析失败时，自动使用系统 DNS 服务器」 | 🚨 国内运营商普遍对第三方明文 :53 做 DNS 重定向/调度 ⇒ 任何查询落到 bootstrap / system，最终应答者就可能变成**运营商自己的服务器**（用户看到「DNS 泄露到中国 ISP」）。**这条路无法加密，唯一办法是让它永不触发** |

### 泄露只可能出在这六个位置

| # | 位置 | 机制与备注 |
|:-:|:-----|:-----------|
| 1 | `upstreams` / `proxy_nameservers` 里用了**域名**形式的加密 DNS | 必被 bootstrap 明文解析一次（用途①） |
| 2 | ⭐ **节点 `server` 是域名，且解析没有显式出口** | 未配 `proxy_nameservers` 时：落 `forward` 境外组 → 直连通不了 → 回退明文 bootstrap / `system`。**CN 环境下最常见、也最容易被漏掉的一条**。f7 起由 `proxy_nameservers` 收口（见清单 2 / 2b） |
| 3 | **回退被触发** | 上游写错、端点失效、或端点路由被绕坏 → 落到明文 bootstrap / system |
| 4 | **IP 类规则没 `no_resolve`** | 为判定规则而触发解析 |
| 5 | **国内解析器被用在境外域名上** | 见下方实测铁律——不是泄露这么轻，是直接解析错 |
| 6 | ⭐ **profile 自身运行所必需的解析**（`proxy_latency_test_url` / `direct_latency_test_url` 的域名、策略组 `icon` 的域名）没有被靠前的 forward 规则接住 | 这些名字**普遍不在 ChinaDomain.list 里**——实测 `cp.cloudflare.com`、`connectivitycheck.platform.hicloud.com`、`jsdelivr.net`、`raw.githubusercontent.com` 全部 **0 命中**（表里唯一两条 cloudflare 还是注释掉的），于是整类落到兜底 = 境外组。而这类解析**每轮节点测速都要做一次**（策略组 `interval` 到点就全量测一遍）⇒ 泄露是**持续型**的、与访问什么网站无关。**继节点域名之后第二个必须显式接住的名字类别**（f3 漏的就是它；f6 起兜底换国内组后天然覆盖，f10 起连单列规则都不再需要——见清单 15 / 18） |

### ⚠️ 实测铁律：国内解析器不能用来解析境外域名（只约束"本地解析"路径）

实测（本机出口直连，取 `www.google.com` 的 A 记录）：

| 端点 | RFC8484 线格式 | JSON API | `www.google.com` 返回 |
|---|---|---|---|
| `doh.18bit.cn` | 200 ✓ | 400 | `216.239.38.120` |
| `dns.alidns.com` | 200 ✓ | 400 | **`31.13.92.37`（Facebook 段，典型 GFW 污染签名）** |
| `doh.pub` | 200 ✓ | 200 | `174.132.167.252` |
| `dns.google` / `1.1.1.1` / `8.8.8.8` | 200 ✓ | 400/200 | `142.251.x.x` ✓ 真实地址 |

**结论：让国内解析器解境外域名，不是"泄露"这么轻 —— 是直接解析错（拿到污染 IP）。** 所有分岔设计都要围绕这条。

**边界（2026-09-19 二次修正，不划清就会把配置改坏）**：

1. **只约束"本地解析"这条路径。** 已经匹配到走节点的域名由节点远程解析，本地 `dns:` 段只为"需要本地解析"的名字服务（DIRECT 域名、节点域名、profile 自身依赖）⇒ **兜底指国内组，不会让"要访问的境外网站"拿到污染答案**——它只影响本来就走直连的域名。
2. **"泄露到运营商"和"答案被污染"是两个问题，致命的是前者。** 兜底挂境外组、代理未就绪时回退明文的配置，比兜底用国内加密组的配置**危险得多**：前者泄露给运营商（不可撤销），后者最坏只是本地解析的 DIRECT 域名拿到国内答案（可接受，且对国内/Apple 域名反而更快更准）。

⇒ **兜底组的唯一判据是「直连可达」，不是「指向境外」。**（早期审计里"兜底指国内 = HIGH"是**错判**，已撤回，见坑 13。）

### 审计清单

| # | 检查 | 判据 | 严重度 |
|---|---|---|---|
| 1 | `upstreams` / `proxy_nameservers` 的加密 DNS 是否 IP 字面量或已钉 hosts | 域名端点 → 必被 bootstrap 明文解析 | **境外域名=高**；国内域名=低 |
| 2 | ⭐ **`proxies[].server` 是域名的节点，它的解析走哪条路** | 节点域名走的是**代理 DNS**。f7 起 `proxy_nameservers` 已被显式设置 ⇒ 代理 DNS **跳过 `forward`**，只用那组 IP 字面量端点 ⇒ **不需要、也不应该**在 `forward` 里为节点域名写规则（那是死代码，见坑 18 / 清单 18）。判据从"forward 有没有接住"改成「**`proxy_nameservers` 是否显式设置、端点是否全为 IP 字面量**」 | **高** |
| 2b | `proxy_nameservers` 是否存在 | **f7 起必须显式写。** 它是**硬覆盖**：一设就绕过 `forward`、强制直连。**"不写"才是问题** —— 官方语义「未配置时，代理 DNS 与默认 DNS 共用 Forward 规则，**未命中回退 Bootstrap**」，等于留下一条通往明文 UDP:53 的兜底分支。只能用**国内**端点（代理 DNS 强制直连，境外解析器在电信线路上不可达） | **高（缺失时）** |
| 3 | ⭐ **DNS 端点是否有显式路由** | `geoip` 加了 `no_resolve` 就**不再匹配域名**；主机名形式的端点会落到 `default` → 国内端点被绕到境外出口 / 境外端点直连被阻断。**国内端点必须显式 → DIRECT，境外端点必须显式 → Proxy** | **高** |
| 4 | ⭐ **`forward` 里是否存在「捕获一切」的兜底，且该兜底组「直连可达」** | 兜底存在的意义只有一个：让"未命中的域名"不回退 bootstrap 明文。**判据是"这组在代理没起来时能不能工作"，不是"它指国内还是境外"** —— 组内端点必须全是 IP 字面量，**且至少一个端点在 `rules` 里被判给 `DIRECT`（判据 A），或至少一个是已知国内公共解析器 IP（判据 B，f10 引入）**。只判给 Proxy 的组 = 依赖代理 = 启动期（规则集/DB 下载、首轮测速）会掉进 bootstrap 明文。**兜底指国内组才是对的**（依据 = 上方实测铁律的边界两条）。**写法要认全**：`domain_wildcard: '*'` **和** `domain_regex: '.'`（官方 PCRE2 find 式，命中任意子串）都算兜底 —— 别只认前一种（审计器 f2 就误判过）。推荐**两条都写**（互不依赖的双保险），并让 `domain_wildcard` 放最后便于人/工具识别 | **高** |
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

完整模板（`dns:` 段逐键注释 + `rules` 骨架 + 顶层字段，**权威版本**）：
[`reference/egern/hardening-template.md`](reference/egern/hardening-template.md)。要改模板只改那一份。骨架速览：

1. `bootstrap`：≥2 个国内公共 DNS 的 **IP 字面量**，绝不写 `system`（回退链终点 = 运营商）；
2. `upstreams`：国内组 + 境外组端点**全部 IP 字面量**；境外组必须在 `rules` 里显式判给 Proxy，否则只能 bootstrap 明文去连；
3. `forward`：**只留兜底**——`domain_regex: '.'` + `domain_wildcard: '*'` 双保险都指向**直连可达**的国内加密组；不写任何具体域名（写了就是死代码 / 维护耦合，见清单 18）；
4. `proxy_nameservers`：**显式设置**，端点全是国内 IP 字面量（代理 DNS 的唯一出口，一设就跳过 `forward`）；
5. `rules`：最前钉 DNS 端点路由（国内端点 → DIRECT、境外端点 → Proxy，IP 类带 `no_resolve`），最后按序 `ChinaMax_All_No_Resolve` 域名兜底 → `.cn` → `geoip CN + no_resolve` → `default`。

顶层另加：`ipv6: false`、`hijack_dns: ['*']`、`real_ip_domains: ['*.lan','*.local','*.push.apple.com']`。

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

> 🪟 **Windows Git Bash 用户**：此命令含多行，粘入双引号会被 MSYS 参数转换**静默扭曲**（实测 `\n` → `/n`）——改存 .py 文件执行（任何平台通用）。

实测参考：`dns.alidns.com`→223.5.5.5/223.6.6.6（固定 ✅）、`doh.pub`→1.12.12.12/120.53.53.53（固定 ✅）、`doh.18bit.cn`→**11 个 IP 的 CDN 池（不可钉 ❌）**，且它落在 **42.51.x.x（中国联通）** 上的自建服务 —— 能用作国内上游，但别让它承担"所有国内域名"。

### ⚠️ 已知缺陷索引

**18 条，每条都是真实事故复盘**，全文（含完整机制链与修法）见
[`reference/egern/pitfalls.md`](reference/egern/pitfalls.md)——排查实际泄露、或改动判据 / 规则集之前先读它。

改动判据时最高频的三条：**13**（兜底挂在"必须经代理才可达"的组上 → 审计 OK、实测 `upstream: bootstrap`）·
**16**（强制解析藏在别人仓库的 `.list` 里——`Apple_All.list` 实测 13 条裸 IP）·
**17**（治好 DNS 泄露的那一手会顺手砍掉国内域名分流——`no_resolve` 与域名兜底必须成对交付）。

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
