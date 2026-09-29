---
name: profile-dns-hardening
description: 审计并加固 Surge / Egern 配置（.conf 与 Profile.yaml）的 DNS 泄露面与分流覆盖。触发词：Surge 配置、Egern 配置、防 DNS 泄露、DNS 裸奔、leak test 显示 china telecom、upstream 显示 bootstrap、dns-server = system、encrypted-dns-server 是域名、proxy_nameservers、hijack-dns / hijack_dns、bootstrap 泄露、明文 :53 旁路、HomePod / Apple TV DNS 泄露、no-resolve / no_resolve、GEOIP CN 缺 no-resolve、IP 规则触发 DNS 解析、加了 no-resolve 之后分流坏了、国内域名全落 FINAL、国内网站不是直连、direct.txt、ChinaMax 只有 IP、规则集 IP 条目缺 no-resolve、Apple_All.list 强制解析、pre-matching、pre-matching 指向策略组、underlying-proxy 无法解析、smart 组评分、policy-regex-filter、flatten 的等价写法、always-real-ip、fake-ip、延迟测试域名泄露、cp.cloudflare.com 泄露、图标域名泄露、dns.forward 兜底、白名单排在 REJECT 之后、profile 模板、Egern dns 段、Egern dnsleak、Egern YAML 配置优化、DNS 泄露到运营商（电信/联通/移动）、日志里规则判定正常但 upstream 是 bootstrap、节点域名明文解析、系统 DNS 回退泄露、rule_set 触发 DNS 解析、blackmatrix7 No_Resolve 变体、ChinaMax.list 没有域名规则、ChinaMax_All_No_Resolve、国内域名走代理、分流覆盖审计、dns.google 泄露、引导解析泄露、extended-matching、Surge 拒绝加载配置、proxy-test-url 泄露、gstatic generate_204、归档配置、升版本号、config_old、Release 发布、release_publish、check_releases、Release 资产命名、补发历史版本。命中本技能时优先加载本文件并按内核进入对应分支，不要凭记忆答语法。
agent_created: true
---

# 配置防 DNS 泄露 · Surge / Egern 双内核

本仓库是 **AI 驱动的配置模板仓**：全部操作文档、逐键语义与审计判据都整合在本 skill 里，
没有面向人类的 docs / DetailsReadme。AI 按用户需求 + 内核官方语法修改配置，闸门守底线。

**阅读协议（按序执行）**：
1. §0 定内核 → §1 五类泄露面 → §2 四条铁律 → §3 六条底线与归档/动线 → **只读对应分支文件**
   （Surge → [`reference/surge/branch.md`](reference/surge/branch.md)，Egern → [`reference/egern/branch.md`](reference/egern/branch.md)），不读另一支。
2. 细节按 §4 索引表的「何时读」列跳转 `reference/`；任务没命中索引就不要读。
3. **权威归属**（本文件与专项文件重复时，以专项文件为准）：逐键语义 = `profile-anatomy` ·
   分支主干（模型 / 审计清单 / 验收判据）= `reference/{surge,egern}/branch.md` ·
   加固模板逐行理由 = `hardening-template` · 坑全文 = `pitfalls` · 加固清单判据 = `hardening-checklist` ·
   审计命令与环境 = `checker`。
4. 本文件行文原则：**表格优先、判据先行**；每处「实测」都是经验值教训，改判据前先读对应坑全文。

**先定内核，再进对应分支**——两者的模型不通用，
把一侧的结论套到另一侧是本项目记录在案的头号误用来源。

## 0 · 内核判定

| 线索 | 内核 | 进入 |
|:-----|:-----|:-----|
| 文件是 `.conf` / 段名 `[General]` `[Proxy Group]` `[Rule]` / 键 `dns-server`、`hijack-dns`、`policy-regex-filter` | **Surge** | [分支 A](reference/surge/branch.md) |
| 文件是 `.yaml` / 顶层键 `policy_groups`、`dns.forward`、`hijack_dns`、`proxy_nameservers`、`rule_set` | **Egern** | [分支 B](reference/egern/branch.md) |
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
- **发布层（GitHub Release）**：一个更新日 = 一个 Release（tag = `vYYYY-MM-DD`），
  懒人版与分流版同日更新合并进同一张，正文按产品线分小节逐版本列要点，
  资产 = 当日各产品线最终版本的固定名文件（最多 8 件，**一律不带版本号**）。
  是 config_old 归档层之上的对外发布层，不替代归档。规矩与模板见
  [`reference/shared/ops.md`](reference/shared/ops.md) §6.9，断言在 `skill/tests/check_releases.py`。

### 改配置标准动线

```
① 只读诊断：先跑 python skill/scripts/repo_state.py 拿现状（四份版本号 / 归档进度 /
   最新 Release / CI 结论，一屏 JSON），再跑相关审计脚本，列出可优化项，等用户确认再动手
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
   ↑ 以上收尾闸门可一键替代：python skill/tests/verify_all.py（并行跑全部，出汇总表）
⑥ 本地 commit → **停在推送前**。`git push` 永远是独立确认项：用户说「换掉 / 改吧 /
   找个新的」只授权改动本身，讨论与调研阶段的产物一律停在本地 + 汇报表格；
   拿到用户单独的「推」指令（如「推吧 / 没问题就推」）才 push（CI 在 push / PR 自动重跑同一组检查）
⑦ 发布 Release（push 之后）：先在 `release_publish.py` 补 `DAY_THEMES` 当日主题与
   `PUBLIC_NOTES` 对应条目，再跑 `python skill/scripts/release_publish.py --apply`
   —— 一个更新日一张 Release（tag = vYYYY-MM-DD），两产品线同日合并，资产为当日
   最终版本；缺的日期自动补齐。发完跑 `python skill/tests/check_releases.py` 验收。
   规矩与说明模板见 `reference/shared/ops.md` §6.9。
```

> **注意**　mutating 步骤（②③④⑥⑦）必须等用户明确确认后再执行；①是只读的，随时可跑。
> **注意**　改 DNS 段 = 一次改全套：`lazy` / `routing` × 完整版 / `.min` 四份（跨 lazy/routing 的
> 16 键逐字一致由 `check_min_pair.py` 的 ②-c 断言守）。想只给某一版加防泄露键，先问它为什么不是四条都要。

### 指令 → 动线映射（用户口令很短，按这张表对号，不要猜）

| 用户说 | 对应动作 | 边界 |
|:-------|:---------|:-----|
| 「看一下 / 排查 / 你觉得呢 / 先讨论」 | **动线①只读**：`repo_state.py` + 相关审计脚本 → 汇报表格 | **禁一切 mutating**；发现的待办只列不做、不"顺带提一句" |
| 「干 / 改了吧 / 按这个来」 | **动线②–⑤**：归档 → 改完整版 → make_min → 闸门 | 授权只覆盖**本地改动**；跑完闸门停下汇报 |
| 「推 / 推完我看看」 | **动线⑥**：git push（必要时 ⑦ --apply 回写 Release） | push 是**独立确认项**，永远不含在上一档授权里 |
| 「没问题就推 / 你认为可以就推」 | 同上（预授权式 push） | 仅限当轮已验证的改动，不扩大到新发现的问题 |

> 🚨 **执行授权铁律（2026-09-29 用户明令入册，违反即事故）**
> 1. **没有用户的命令，不准改任何文件。** 用户对方案的**澄清、补充、范围确认**——
>    「我说的是这两项」「可以改 false」「没说后头的」「我的建议取消」这类话——
>    **一概不是执行授权**，只说明讨论还在继续。当场执行过诊断之后的下一个动作
>    依然是等，不是动手。
> 2. **没有用户的命令，不准 push。** 改和推是两道独立的门，各要一次明确指令；
>    「干」只开门一（本地改），「推」才开门二。
> 3. 只有**命令词**（「干 / 改了吧 / 动手 / 按这个来」）才开启动线②。
>    语义有歧义时，**退回只读讨论并问一句**，永远不猜「这算不算授权」——
>    猜错方向的代价（用户怒斥 + 信任损失）远大于多问一句的代价。

### 其他共享纪律

- 📖 **读配置文件的成本策略**（完整版注释占比约 2/3，通读最贵）：
  **看结构用 `.min`**（零注释、内容与完整版逐字对应，DNS 段除外——见 6.3）；
  **定位目标段落用锚点 grep**（键名 / 组名 / 段名）；
  **只有动手改的那一段才从完整版里精读**。禁止为了改 3 行把整份 500+ 行文件读进上下文。

- ⚠️ **审计通过 ≠ 配置可用。** 脚本只覆盖**静态可判定**的部分；拦截效果、误杀、节点可用性必须实测。
  这条来自 Egern 侧连续 5 次"脚本全绿、实测仍有问题"的代价。
- 📍 **命令的路径基准**：本文与 `reference/` 里凡可照抄执行的命令，路径一律以**仓根**为基准书写（要 `cd` 的会显式写 `cd`）；
  行文里为省字出现的简写（如 `scripts/probe_doh.py`）不是可执行路径，取真身请以仓根全路径为准。
- 🧷 **Egern 改配置的安全姿势**：profile 含数千字符的超长单行，**不要用 YAML dump 重写整个文件**；
  按行读入 + 内容定位 + 断言"全文恰好命中 1 行"，改完逐字段比对未触碰部分。详见 [`reference/egern/branch.md`](reference/egern/branch.md)。
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
| [`reference/surge/branch.md`](reference/surge/branch.md) | **分支 A 主干**——凡涉及 Surge 配置的任务（改动 / 审计 / 加固 / 排查）先读它：DNS 模型、12 项清单、坑速查、验收判据 |
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
| [`reference/egern/branch.md`](reference/egern/branch.md) | **分支 B 主干**——凡涉及 Egern 配置的任务（改动 / 审计 / 加固 / 排查）先读它：双轨 DNS 模型、18 项清单、验收标准 |
| [`reference/egern/profile-anatomy.md`](reference/egern/profile-anatomy.md) | 改 Egern 配置需要确认某个顶层字段 / 组 / 规则的语义与边界时（逐键权威） |
| [`reference/egern/hardening-template.md`](reference/egern/hardening-template.md) | 要产出一份加固后的 `dns` 段 + `rules` 时——完整 YAML，含逐行理由 |
| [`reference/egern/pitfalls.md`](reference/egern/pitfalls.md) | 排查实际泄露、或改动判据 / 规则集之前——18 个坑的事故复盘 |
| [`reference/egern/leak-localization.md`](reference/egern/leak-localization.md) | 用户报「leak test 显示某运营商」时——网络侧实测流程 |
| [`reference/egern/checker.md`](reference/egern/checker.md) | 跑审计脚本前（命令与环境要求）、或要改判据时（审计演进史） |
| [`reference/egern/ruleset-weight.md`](reference/egern/ruleset-weight.md) | 用户问「规则集是不是太重」时——内存 / 耗时实测 |
| [`reference/egern/public-repo.md`](reference/egern/public-repo.md) | 要更新模板 / 了解仓库结构与脱敏清单时 |
