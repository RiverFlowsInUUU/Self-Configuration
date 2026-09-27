# 操作：Surge · Egern · 日常维护

> 由原手册 03、04、06 三章合并。装完之后怎么改、怎么维护，都在这一篇。

## Surge 操作


对象：`../surge/profiles/` 下 `lazy` / `routing` 两版（各含带注释完整版与 `.min` 版）。
加固清单逐项与验收标准见 [`shared/hardening-checklist.md`](hardening-checklist.md)（清单本体在那份文件，本章讲怎么用它）；逐键权威是 [`surge/reference/profile-anatomy.md`](../surge/profile-anatomy.md)。


### 3.1 文件结构速览

Surge 的 `.conf` 按节组织，模板里与防泄露相关的节：

| 节 | 作用 | 防泄露相关 |
|:---|:-----|:-----------|
| `[General]` | 全局开关 | DNS 段全部键都在这里：`dns-server`、`encrypted-dns-server`、`hijack-dns`、`always-real-ip`、测试端点等 |
| `[Proxy]` | 静态节点 | 仅 `lazy` 有（占位节点）；`routing` 的节点来自订阅 |
| `[Proxy Group]` | 策略组 | 出口选择逻辑 |
| `[Rule]` | 规则 | 顺序即优先级，见 3.4 |
| `[URL Rewrite]` / `[Header Rewrite]` 等 | 附加功能 | 与防泄露无关，可整节删 |

> **说明**　两份配置的 `[General]` DNS 相关键四份（`lazy` 与 `routing` 及各自 `.min`）保持逐字一致 —— 这是维护纪律，没有自动判据，改 DNS 段时四份一起改（流程见下文「日常维护」）。


### 3.2 `[General]` DNS 段：每行堵哪个出口

对照 [DNS 基础的泄露面全景](dns-basics.md)，这些键各自堵一条通路：

| 键 | 堵哪 | 注意 |
|:---|:-----|:-----|
| `dns-server` | 引导与连通性测试用的本地上游 | 全 IP 字面量，不放 `system`。不要删它来"减少解析面"：删了 Surge 会用系统 DNS（运营商下发），正是出口 ① |
| `encrypted-dns-server` | 日常解析走加密通道 | 端点尽量 IP 字面量；保留的 2 个主机名端点已用 `# audit-waive:` 记录豁免与理由 |
| `hijack-dns` | 旁路设备（出口 ②） | 模板列出最常见的境外解析器地址把它们收进本地；想一网打尽可写 `hijack-dns = *`（有取舍，见 `profile-anatomy` §10.3） |
| `encrypted-dns-follow-outbound-mode` | 防止"出站走代理、解析也跟着出境"的意外 | 模板显式设 `false`，理由在 `profile-anatomy` |
| `use-local-host-item-for-proxy` | 防止本地 hosts 条目污染代理侧解析 | 理由在 `profile-anatomy` |
| `always-real-ip` | Fake-IP 模式下游戏机 / NTP / STUN 拿到假 IP | 是功能清单，不是可选装饰。里面的主机名应能被 `[Rule]` 域名规则接住，`check_surge_dns.py` 第 11 项专查这条 |
| `internet-test-url` / `proxy-test-url` | — | 性能探针，不是泄露通道：前者国内 204（测"能不能上网"），后者保持境外 `gstatic.com`（`smart` 打分要含国际段才是真实路径）。把后者"为防泄露"改成国内是典型的原则误套用，见 `profile-anatomy` §16 |

> **注意**　`# audit-waive: <编号> <理由>` 是有语义的注释，审计器真的会读它。删掉那行，读数立刻从「已豁免」变「HIGH/MEDIUM」；同文件内编号不重复。


### 3.3 广告拦截：pre-matching 与 AD 组的分层

模板里广告拦截有两条清单：白名单 guard 在前、拦截在后。关键约束：

> **注意**　`pre-matching` 的规则，策略必须是字面量 `REJECT` 家族，不能是策略组。预匹配发生在"还来不及决定出口"的阶段；策略组运行时可能解析成 `DIRECT`，Surge 会直接拒绝加载整份配置。

所以链路是刻意的分层：拦截规则写字面量 `REJECT`，换取 DNS / SYN 阶段即拒、不建连不解析（全模板最大的一笔省电优化）；旁边 `AD = select, REJECT, DIRECT` 组作为独立手动开关，不被任何规则引用，职责是给人工干预留入口。

想让面板开关接管拦截？可以，但要一并去掉 `pre-matching`，接受"先解析再拒"的代价。


### 3.4 `[Rule]` 顺序铁律

两版共享同一条顺序铁律，自上而下、首个命中生效：

```
① 白名单 guard（防误杀，DIRECT）
② 广告拦截（REJECT 字面量，pre-matching）
③ 内网 / LAN
④ …（routing 版：应用规则插在中间，见 3.5）
⑤ 域名类国内直连（direct.txt 等）
⑥ IP 类（GEOIP,CN,DIRECT,no-resolve）
⑦ FINAL 兜底（dns-failed 一并标注）
```

三条不能错位的细节：

1. 白名单必须在 REJECT 之前。"DIRECT 永远在 REJECT 前"这种一刀切不变量本身是错的 —— 白名单就是 DIRECT，且必须排在 REJECT 前。
2. 应用类规则必须排在 `direct.txt` 之前。否则域名恰好被国内清单收录的 AI / GitHub 会被直连接走：`github.com` 同时被 `direct.txt` 收录，`GitHub.list` 排后面分流就失效。
3. `GEOIP` 必须带 `no-resolve`，且必须与 ⑤ 成对。见 [DNS 基础](dns-basics.md)。

> **说明**　两版 `[Rule]` 都没有游戏机域名规则（`nintendo.net` 等只在 `always-real-ip` 里）—— 这些主机名照旧拿真实 IP，去向由常规规则链决定。别把"缺这三条"当 bug 来"修"。


### 3.5 分流版（`routing.conf`）要点

完整的分组层次与逐条规则表直接读 [`routing.conf`](../../../surge/profiles/routing.conf) 本体（注释齐全）。这里只讲动手最容易撞的四条墙。

#### ① smart 组不能拿组名当子策略

官方限制：Smart 组不可使用其他组作为子策略，也不可用作 `url-test` / `load-balance` 组的子策略。等价做法是 `include-other-group`：

```ini
Proxy = smart, include-other-group="Airport"    # ✅ 拿到的是解析后的具体节点
Proxy = smart, Airport                           # ❌ 成员是"Airport"这一个组名，测不到组内节点
```

#### ② flatten 的对应物

Egern 的 `flatten: true` 在 Surge 没有同名字段，语义对应 `include-other-group`（官方："includes the resolved member policies from other policy groups"）。应用组因此写成：

```ini
ChatGPT = select, include-other-group="Proxy"
```

差异要说白：Egern 应用组自 `routing_v3` 起同为手动 `select`（旧版是 `fallback`），与 Surge 的 `select` 现版同形。想要应用组自动选优：Egern 换 `fallback` / `smart`、Surge 把某组换成 `smart, include-other-group="Proxy"`，代价是面板不能再手动挑节点。旧版这处确是能力差异，现已拉平 —— 史实写明，不假装一直没差过。

#### ③ 地区组靠正则筛名字，且有两个开关要一起开

```ini
Hong Kong = smart, include-all-proxies=true, include-other-group="Airport", policy-regex-filter=(?i)🇭🇰|香港|…
```

- `policy-regex-filter` 对显式列出的成员无效 —— 手写在 `[Proxy]` 里的节点，必须靠 `include-all-proxies=true` 才会被筛到；
- 正则别写太宽：`(?i)us` 会同时命中 `Russia` / `Belarus` / `AUStralia`，保守用 `\b` 锁词边界；
- `Other Regions` 是负向断言，把其余地区组的关键词逐字抄了一遍 —— 任何组加关键词必须同步改它，漏改不报错、面板也看不出（节点会同时出现在两个组）。这条拷贝在配置层面消灭不掉，靠 `audit_region_filters.py` 守（用法见 [验证与自检](troubleshoot-faq.md)）。

#### ④ 已知边界（都是设计，不是 bug）

| 边界 | 说明 |
|:-----|:-----|
| 空地区组 | 节点名不含关键词则该组为空，指向它的规则会断流。导入后到面板确认 |
| `MAX` 在 `Proxy` 首项 | 默认出口优先落低倍率节点（省钱但可能慢），与 Egern 对齐；不想要就把 `MAX` 挪走 |
| `https` 类型节点不支持 UDP 中继 | 别让承担 UDP 的组落到它们 |
| Apple 无独立策略组 | 走 `Apple` 规则 → DIRECT；要"给 Apple 挑地区"得自己复制 select 组 |
| 段内顺序 | 与 Egern 逐位对齐（维护纪律）；"先写引用别人的，后写被引用的"，Surge 允许前向引用 |


### 3.6 你必须替换 / 可以删除的

必须替换（逐键语义见 [`surge/reference/profile-anatomy.md`](../surge/profile-anatomy.md)）：

- `lazy` 的 `[Proxy]` 占位节点；
- `routing` 的 `Airport` 组 `policy-path` 占位订阅地址；
- 两份 `[SSID Setting]` 段里的 `SSID:MyHome` —— `MyHome` 是照官方示例留的占位网络名，不替换就匹配不到任何 Wi-Fi，「回家自动暂停」静默不生效。该段只有 Surge 侧有，Egern 无对等件（见 [`cross-kernel-diff.md`](cross-kernel-diff.md) §1「网络级暂停」）。

可以删（按收益排序，删完必须重跑分流覆盖审计）：

- `[URL Rewrite]` / `[Header Rewrite]` 等附加节；
- AI 分流（`AI` 组 + 对应规则）；
- `AD` 组（反正不被规则引用）。

不能删：`direct.txt` 规则、`GEOIP,CN`（连同 `no-resolve` 是一对）、白名单 guard。删任何一个都会立刻构成 [DNS 基础](dns-basics.md) 说的"只交一半"。

改 `routing.conf` 想加新应用组：照 §3.5 的写法复制一个 `select, include-other-group="Proxy"` 组，把它的规则插在国内直连集之前，并给 `audit_routing_coverage.py` 加对应探针（期望值精确到组名，不许放宽成"不是 DIRECT 就行"）。


### 3.7 官方文档入口

- 策略组 / `include-other-group`：[manual.nssurge.com/policy-groups/policy-including.html](https://manual.nssurge.com/policy-groups/policy-including.html)
- Smart 组限制（中文）：[kb.nssurge.com · smart-group](https://kb.nssurge.com/surge-knowledge-base/zh/guidelines/smart-group)
- 其余逐节引用见 `profile-anatomy` 各节脚注。


### 相关页面

| 下一步 | 去处 |
|:-------|:-----|
| 对侧内核的操作章 | 本篇「Egern 操作」章（已并入本篇） |
| 换、加、删任何规则集之前 | [规则集与素材](rulesets.md) |
| 出问题了 | [故障排查 · FAQ](troubleshoot-faq.md) |
| 把本篇改动搬到 Egern 侧 | [跨内核移植](cross-kernel-diff.md) |
| 名词不认识、常见疑问没解决 | [FAQ 与术语表](troubleshoot-faq.md) |


---

## Egern 操作


对象：`egern/profiles/` 下 `routing.yaml`（推荐，完整分流）与 `lazy.yaml`（懒人配置），各含带注释完整版与 `.min.yaml` 形态，共四件，历史版本看 git。
加固清单在 [`hardening-checklist.md`](hardening-checklist.md)；逐键权威是 [`egern/reference/profile-anatomy.md`](../egern/profile-anatomy.md)。


### 4.1 顶层字段：值等于默认的不写

Egern 的 YAML 顶层：`ipv6`、`vif_only`、`hijack_dns`、`geoip_db_url` / `asn_db_url`、两个延迟测试 URL、`real_ip_domains`、`default_proxy_group` 等。三条维护经验：

1. 值恰好等于官方默认值的行是冗余（`routing_v2.1` 一次性删掉了五十多行这种）。读旧版看到它们，别当"定制"。
2. 非默认值必须显式写，尤其 `vif_only: true`（官方只有一句"虚拟网接口模式，默认 false"，细节无法确认）。遇到"某些 App 不走代理"，它是第一个 A/B 候选，但别凭猜测替用户改。
3. `hijack_dns: ['*']` 接管 `:53` 并返回 Fake IP；`real_ip_domains`（`*.lan` / `*.local` / `*.push.apple.com`）让推送与内网发现拿真实 IP —— Fake IP 反而会让 APNs 异常。


### 4.2 `dns:` 段：五小节，一个原则

原则一句话：`bootstrap` 唯一安全的形态是"永远不被触发"。逐节要点：

| 小节 | 要点 |
|:-----|:-----|
| `bootstrap` | 全国内明文 IP，绝不写 `system`（等于把运营商接进回退链）。也别指望"换更好的 bootstrap IP"：实测换 IP 后泄露仍来自透明重定向 / 回退，机制见 [DNS 基础](dns-basics.md) 的泄露面各出口 |
| `upstreams` | `Domestic-DNS` 端点全部 IP 字面量（消灭 bootstrap 用途①）；「两家机构 × 两种协议」的冗余结构，同组并发竞速、全组失败才触发回退。`Foreign-DNS` 整组已注释保留：它必须经代理才可达，不能当兜底（启动期解析会掉进明文）。Quad9 教训：`https://9.9.9.9/dns-query` 静默失效（只提供 HTTP/3），`tls://9.9.9.9` 可用 |
| `forward` | f10 起塌缩为纯兜底（指向 `Domestic-DNS`）—— 换订阅、换节点域名，本段一个字都不用改。两条兜底与一条等价的原因：value 单值 + 顺序求值，删任何一条行为不变（`audit_dns_forward.py` 可证） |
| `proxy_nameservers` | 硬覆盖：一设就绕过 `forward`、强制直连、成为代理侧解析的唯一出口。"不设"本身也留了一条"未命中回退 Bootstrap"的明文分支 —— 模板最终选择显式设置 + 国内端点（它是强制直连的，境外解析器在国内线路不可达）。排障口诀：节点连不上，第一件事注释掉这个列表 |
| `hosts` / `block_ips` | `hosts` 是"端点写主机名"时代的补救，端点全 IP 后无引用点、已删；`block_ips` 丢弃空路由式污染应答，刻意不含私网段，免误伤内网 |

已知代价（完整版见 `profile-anatomy` 的取舍节）：设置了 `proxy_nameservers` + 兜底国内组，需要本地解析的境外域名会拿到国内答案，实际影响面仅限 `DIRECT` 域名。审计里那两条 `LOW`（一条是 `proxy_nameservers` 成为代理侧解析唯一出口，一条是 `forward` 兜底指向国内组）就是它 —— 是取舍，不是缺陷。


### 4.3 `proxies:` 与节点形态

- 模板 `proxies` 带 2 条占位节点（`Node-A` / `Node-B`），`server` 都写成 IP 字面量。
- 自己填节点时，`server` 能写 IP 就写 IP：写域名必然产生一次"本机 + 直连 + 明文"解析（代理还没通）。这是从根上消除节点域名解析面的唯一办法；中转 `prev_hop` 同理，且无需为节点域名改 `forward`。


### 4.4 `policy_groups:`：四类组与三个易踩的坑

组分四类：入口（`Proxy` / `Final`）、应用组（`ChatGPT` / `Gemini` 等，现行版皆为 `select`，旧版才是 `fallback`）、智能组（`Smart` / `MAX` 与各地区组，皆 `smart`；地区组用 `filter` 正则筛名 + `flatten: true`）、订阅槽位（`external` 组，`hidden: true`，当前版只有一个 `Airport`；旧版为 `Airport-A` / `Airport-B` 两槽、更早四槽）。

必须知道的三条：

1. `flatten: true` 把组名展开成组内全部具体节点，让 `fallback` / `smart` 做节点级尝试。`fallback` 不给 `flatten` 时，`policies: [Proxy]` 只有一个候选单位，等于没有故障转移。官方明确 `flatten` 在 `select` / `auto_test` / `smart` / `fallback` / `load_balance` 五种类型通用。
2. `fallback` 不做延迟择优，按顺序取第一个可用。想固定地区，把目标写首位；想自动挑最快，改 `smart`。`ChatGPT` / `Gemini` 在旧版曾是空组 `[]` 而规则直指它们，导入即静默断流；当前版已填 `[Proxy]` + `flatten`，且这两组自 `routing_v3` 起已由 `fallback` 改为 `select`。
3. `MAX` 组 = 带"低倍率节点"筛选的 `Smart`，它是 `Proxy` 首项，默认出口因此优先落低倍率节点。它的 filter 曾写错（只认字面 `0.01` / `0.1`，误收 `10.1`、漏收 `0.5`），现版用带左边界的负向后行断言。改任何地区组 filter 关键词，必须同步 `Other Regions` 的负向断言（`audit_region_filters.py` 守）。

`lazy` 特有：只有 `Proxy` / `AI` / `AD` 三组；`Proxy` 组 `policies` 为空，必须自己填节点名；`AD` 子策略只有 `REJECT`（无 `DIRECT` 兜底）。临时放行单个域名，在 `rules` 更前面加一条 `DIRECT` 规则，别整组切走。


### 4.5 `rules:`：分四段理解顺序

| 段 | 内容 | 要点 |
|:--:|:-----|:-----|
| A | DNS 端点固定路由 | 已整体移除。端点全是 IP 字面量，解析器直接以 IP 访问，不需要在 `rules` 里钉。只有你自己把 DNS 端点写成主机名时，才需要补一条 `DIRECT` 路由，否则它落 `default → Proxy` |
| B | 白名单 guard → 广告 → 内网 → 各应用规则集 | 顺序即优先级；`Proxy.list` 类"默认 `disabled: true`"的规则由 `Final` 兜底；AI 规则集 URL 钉 commit 防上游漂移；每条 `rule_set` 各自带 `update_interval`（现值两侧统一钉 `604800`，别只写第一条） |
| C | Apple（No_Resolve 版）→ `direct.txt` → `.cn` 后缀 → `geoip: CN` + `no_resolve` | 这就是 [成对交付篇的判据 A+B](no-resolve-pairing.md) 在本内核的落点：`geoip` 带 `no_resolve` 后不匹配域名，国内域名直连完全依赖 `direct.txt` 那条纯域名规则集，动一条必须看另一条。Apple 必须用 `Apple_All_No_Resolve.list`（原版藏 13 条裸 IP，会强制解析） |
| D | `default: {name: Final, policy: Final}` | 未命中走代理，由节点远程解析、不经过 `dns` 段 —— 日志里的 `default → Final → Proxy` 是正常决策，不是泄露。`lazy` 没有 `Final` 这层组，`policy` 直写 `Proxy`；`name: Final` 只是日志标签 |

> **注意**　`no_resolve` 有三层，写之前先确认自己在哪一层：规则级（`geoip` / `ip_cidr` 的 `no_resolve`）、`rule_set` 级（在这里写不生效，这是坑）、条目级（`.list` 每条自带的 `,no-resolve`）。

`default_proxy_group: Proxy` 不是兜底：官方定义是"添加代理时自动加入的策略组"。改它不换出口，删它则手动新加的节点不进组。Egern 只有一条兜底通路，就是 `rules` 末尾的 `default`。


### 4.6 分流顺序与应用组默认出口

逐位匹配顺序表直接读 [`routing.yaml`](../../../egern/profiles/routing.yaml) 的 `rules:` 段注释。
两条与 Surge 侧共同的铁律同样成立：应用规则必须排在 `direct.txt` 之前；具体的在前、兜底在后。
应用组的 `policies` 里只有 `Proxy` 一项（+ `flatten`）—— 这是设计，不是"忘了加地区"；想固定地区，改首位即可。


### 4.7 必须替换与环境

- 必填：`Airport`（旧版 `Airport-A` / `Airport-B`）订阅组的 `url(s)` 占位，换成你的订阅地址。当前版所有分流组已填好 —— 填完这一个占位就能直接导入（分流版 `AI` 首项是 `Node-B`，不填节点就在面板里把它切到订阅节点）。
- 可选：`proxies` 里那 2 条占位节点换成你的自建节点（`server` 尽量 IP），或整条删掉并把组里的名字一并摘掉。
- 运行审计脚本需要 Python 3 + PyYAML（本仓唯一第三方依赖）。
- 官方文档入口：DNS `https://egernapp.com/docs/configuration/dns` · rules 字段 `https://egernapp.com/docs/configuration/rules` · 顶层字段全表 `https://egernapp.com/docs/configuration/example`（两处页键名不一致，以 example 页为准）。

> **注意**　`https://egernapp.com/zh-CN/docs` 与 `https://egernapp.com/docs/configuration/general` 是 404，别按其他客户端文档站的直觉找路径。


### 4.8 改完之后的验证

```bash
python skill/scripts/egern/check_egern_dns.py         egern/profiles/routing.yaml
python skill/scripts/egern/audit_ruleset_noresolve.py egern/profiles/routing.yaml   # 联网：下载规则集数条目
python skill/scripts/egern/audit_routing_coverage.py  egern/profiles/routing.yaml   # 联网：真实域名走规则链
python skill/scripts/egern/audit_dns_forward.py       egern/profiles/routing.yaml
python skill/scripts/egern/check_egern_dns.py egern/profiles/lazy.yaml egern/profiles/routing.yaml
```

判据逐项见 `skill/scripts/egern/check_egern_dns.py` 头注。
最后在目标链路（尤其蜂窝）跑一次 leak test，并先写下"哪台设备、哪条链路、谁的 DNS" —— 混链路会让整轮结论作废。


### 相关页面

| 下一步 | 去处 |
|:-------|:-----|
| 对侧内核的操作章 | 本篇「Surge 操作」章（已并入本篇） |
| 换、加、删任何规则集之前 | [规则集与素材](rulesets.md) |
| 出问题了 | [故障排查 · FAQ](troubleshoot-faq.md) |
| 把本篇改动搬到 Surge 侧 | [跨内核移植](cross-kernel-diff.md) |
| 名词不认识、常见疑问没解决 | [FAQ 与术语表](troubleshoot-faq.md) |


---

## 日常维护


面向"改这份配置的人"：改哪里、怎么升版、怎么同步、怎么记录。
仓库级红线（节点不提交真实值等）见根 [`SECURITY.md`](../../../SECURITY.md)，本章不重复其条文，只讲操作动线。


### 6.1 固定名规矩：先记住这个，再碰任何文件

- 顶层永远只有四个固定名 × 两内核（`.conf` / `.yaml` 各一对）：`routing` / `lazy` 的完整版与 `.min` 版。它们是永久订阅地址的落点，不随版本改名；
- "当前是哪一版"只写在文件头注 `#! version=…` 里；
- 配置变动时，变动前的旧配置归档进 `profiles/config_old/`：归档版本号 = 该目录内此分工最新号 + 0.1（v3.3 → v3.4，v3.9 → 进位 v4.0），完整版与 `.min` 成对，现役头注同步升为归档号 + 0.1；更早历史看 git（备份 tag：`pre-cleanup-20260927`）；
- 因此：任何文档、脚本、README 里出现的"带版本号的订阅 URL"都是错的。


### 6.2 改配置的标准动线

```
① 改带注释完整版（lazy.conf / routing.conf / 对应 .yaml）
② 生成 .min：      python skill/tests/make_min.py --family routing|lazy|all        # 默认只出差异计划
                   python skill/tests/make_min.py --family all --apply              # 确认后写盘
③ 核豁免行：       .min 由生成器重算正文、按锚点继承注释 —— 仍要肉眼确认 `# audit-waive:` 那几行在 min 版里读得到
④ 升版（要对外发布时）：直接改四份 profile 头注里的 `#! version=`（`.min` 由生成器重算继承）
⑤ 收尾：`python skill/tests/check_secrets.py && python skill/tests/check_portability.py && python skill/tests/check_min_pair.py && python skill/tests/check_links.py .`（push 后 CI 会再跑一遍同组检查）
```

> **注意**　`.min` 不手工编辑。手工同步迟早漂 —— `check_min_pair.py` 会拿完整版对拍 `.min`，漂了就红。

> **注意**　`audit-waive` 是有语义的注释，同文件内编号不重复。

> **建议**　`make_min.py` 默认只出计划不写盘，`--apply` 才动文件 —— 先读计划再落盘是刻意设计。


### 6.3 DNS 段是"一份内容、四张脸"

`lazy` / `routing` × 完整版 / `.min` 共四份，DNS 相关键保持逐字一致（维护纪律，无自动判据）。

操作含义只有一条：改 DNS 段 = 一次改全套，闸门负责抓漏。想只给某一版加一条防泄露键，先问它为什么不是四条都要 —— 答案是"是"的才动手。


### 6.4 换设备与双端一致

本机与另一台设备（或新克隆）之间核对配置一致性，跑：

```bash
python skill/tests/check_portability.py
```

`check_portability.py` 逐条比对"两份拷贝是否等价"（规则清单现算，直接看脚本输出）。

换机常见坑：行尾（本仓 `.gitattributes` 统一 `text=auto eol=lf`，不要动任何人的 git config）、编码（脚本内部已钉 UTF-8 输出）、路径分隔符（拼接一律用 `/`）。


### 6.6 精简配置（给自己瘦身）

不要另开第三份配置 —— 历史教训是"同一件事写在两个地方，早晚会只改一处"（`v0` / `v1` 分叉就是这么砍掉的）。在你要用的那份上直接删，按收益排序：

| 可删 | 备注 |
|:-----|:-----|
| `[URL Rewrite]` 等附加节（Surge）/ 用不到的应用组 | 删组时连同指向它的规则一起删 |
| AI 分流（`AI` 组 + 规则） | 出口退回兜底 |
| `AD` 开关组（Surge） | 它不被规则引用，删了不影响拦截链路本体 |

| 不能删 | 原因 |
|:-------|:-----|
| `direct.txt` 域名直连集 | 判据 B 的一半 |
| `GEOIP,CN` / `geoip: CN`（连同 `no-resolve` 语义） | 判据 A 的一半；两条拆开即"只交一半" |
| 白名单 guard | 它必须排在 REJECT 之前，删了广告清单会开始误杀 |

删完必做：重跑分流覆盖审计与单侧回归（见 [验证与自检](troubleshoot-faq.md)）。


### 6.7 想加第三份配置

先问：这是新分工，还是老配置的另一种写法？后者一律否掉（那是版本分叉）。
确认是新分工后，走 [`surge/reference/profile-anatomy.md`](../surge/profile-anatomy.md) 维护者一节 —— 一句话判据：能过全部检查的才算一份新配置（固定名、`.min` 对拍、DNS 段一致）。


### 6.8 判据脚本的纪律

日常维护的正确姿势是：改配置与文档去适配判据，而不是改判据去适配配置。确实证明判据本身错了才动它，改动时写清"哪个反例会漏判、改后能抓住什么"。


### 相关页面

| 下一步 | 去处 |
|:-------|:-----|
| 改 DNS 段之前先读泄露面 | [DNS 基础](dns-basics.md) |
| Surge 侧的操作动线 | 本篇「Surge 操作」章 |
| Egern 侧的操作动线 | 本篇「Egern 操作」章 |
| 换、加、删任何规则集之前 | [规则集与素材](rulesets.md) |
| 出问题了 | [故障排查 · FAQ](troubleshoot-faq.md) |
| 把本篇改动同步到对侧内核 | [跨内核移植](cross-kernel-diff.md) |
