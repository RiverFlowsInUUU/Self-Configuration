# 04 · Egern 操作

> 对象：`../egern/profiles/` 下 `routing.yaml`（推荐，完整分流）与 `lazy.yaml`（懒人配置），各含带注释完整版与 `.min.yaml` 形态；历代旧版在 `config_old/` 归档、不参与任何检查。
> 加固清单在 [`../egern/docs/03-加固清单-18项.md`](../egern/docs/03-加固清单-18项.md)；逐段细讲在 [`../egern/docs/04-模板逐段讲解.md`](../egern/docs/04-模板逐段讲解.md)（已冻结仍可读，逐行分析全仓最细；与手册冲突时以手册与本侧 `DetailsReadme` 为准）；逐键权威是 [`../egern/DetailsReadme/DetailsReadme.md`](../egern/DetailsReadme/DetailsReadme.md)。

---

## 4.1 顶层字段：值等于默认的不写

Egern 的 YAML 顶层：`ipv6`、`vif_only`、`hijack_dns`、`geoip_db_url` / `asn_db_url`、两个延迟测试 URL、
`real_ip_domains`、`default_proxy_group` 等。两条维护经验：

1. **值恰好等于官方默认值的行是冗余**（`routing_v2.1` 一次性删掉了五十多行这种），读旧版看到它们别当"定制"；
2. **非默认值必须显式写** —— 尤其 `vif_only: true`（官方只有一句"虚拟网接口模式，默认 false"，细节无法确认）。遇到"某些 App 不走代理"，它是第一个 A/B 候选，**但别凭猜测替用户改**。
3. `hijack_dns: ['*']` 接管 `:53` 并返回 Fake IP；`real_ip_domains`（`*.lan` / `*.local` / `*.push.apple.com`）让推送与内网发现拿真实 IP —— Fake IP 反而会让 APNs 异常。

## 4.2 `dns:` 段：五小节，一个原则

原则一句话：**`bootstrap` 唯一安全的形态是"永远不被触发"。** 逐节要点（逐行讲解见 egern/docs/04 §2）：

| 小节 | 要点 |
|:-----|:-----|
| `bootstrap` | 全国内明文 IP；**绝不写 `system`**（等于把运营商接进回退链）；也别指望"换更好的 bootstrap IP"——实测换 IP 后泄露仍来自透明重定向/回退，机制见 2.1/2.4 出口 |
| `upstreams` | `Domestic-DNS` 端点**全部 IP 字面量**（消灭 bootstrap 用途①）；「两家机构 × 两种协议」的冗余结构，同组并发竞速、全组失败才触发回退；`Foreign-DNS` 整组**已注释保留**——它必须经代理才可达，不能当兜底（启动期解析会掉进明文）。Quad9 教训：`https://9.9.9.9/dns-query` 静默失效（只有 HTTP/3），`tls://9.9.9.9` 可用 |
| `forward` | f10 起塌缩为**纯兜底**（指向 `Domestic-DNS`）——换订阅、换节点域名，本段**一个字都不用改**。为什么两条兜底等价一条：value 单值 + 顺序求值 ⇒ 删任何一条行为不变（`audit_dns_forward.py` 可证） |
| `proxy_nameservers` | **硬覆盖**：一设就绕过 `forward`、强制直连、成为代理侧解析唯一出口。"不设"本身也留了一条"未命中回退 Bootstrap"的明文分支 —— 模板最终选择显式设置 + 国内端点（它是强制直连的，境外解析器在国内线路不可达）。⚠️ 排障口诀：**节点连不上，第一件事注释掉这个列表** |
| `hosts` / `block_ips` | `hosts` 是"端点写主机名"时代的补救，端点全 IP 后无引用点已删；`block_ips` 丢弃空路由式污染应答，刻意**不含私网段**免误伤内网 |

已知代价（`DetailsReadme` 的取舍节有完整版）：设置了 `proxy_nameservers` + 兜底国内组 ⇒ 需要本地解析的境外域名会拿到国内答案，实际影响面仅限 `DIRECT` 域名。审计里的 2 条 LOW 就是它，**是取舍不是缺陷**。

## 4.3 `proxies:` 与节点形态

- 模板 `proxies: []` **为空**，不附带示例节点（避免误导）；
- 你自己填节点时：**`server` 能写 IP 就写 IP** —— 写域名必然产生一次"本机 + 直连 + 明文"解析（代理还没通）。这是从根上消除节点域名解析面的唯一办法；中转 `prev_hop` 同理，且无需为节点域名改 `forward`。

## 4.4 `policy_groups:`：四类组与三个易踩的坑

组分四类：入口（`Proxy` / `Final`）、智能与回退（`Smart` / 各应用 `fallback`）、订阅槽位（`external` 组，`hidden: true`，**当前版只有一个 `Airport`**；旧版 `Airport-A`/`Airport-B` 两槽、更早四槽）、地区组（`filter` 正则筛名 + `flatten: true`）。

必须知道的三条：

1. **`flatten: true` = 把组名展开成组内全部具体节点**，让 `fallback` / `smart` 做节点级尝试。`fallback` 不给 `flatten` 时，`policies: [Proxy]` 只有**一个候选单位** —— 等于没有故障转移。官方明确 `flatten` 在 `select` / `auto_test` / `smart` / `fallback` / `load_balance` 五种类型通用。
2. **`fallback` 不做延迟择优** —— 按顺序取第一个可用。想固定地区把目标写首位；想自动挑最快改 `smart`。`ChatGPT` / `Gemini` 在旧版曾是空组 `[]` 而规则直指它们 ⇒ **导入即静默断流**；当前版已填 `[Proxy] + flatten`。
3. **`MAX` 组 = 带"低倍率节点"筛选的 `Smart`**，它是 `Proxy` 首项 ⇒ 默认出口优先落低倍率节点。它的 filter 曾写错（只认字面 `0.01`/`0.1`，误收 `10.1`、漏收 `0.5`）—— 现版用带左边界的负向后行断言。改任何地区组 filter 关键词，**必须同步 `Other Regions` 的负向断言**（`audit_region_filters.py` 守）。

`lazy` 特有：只有 `Proxy` / `AI` / `AD` 三组；`Proxy` 组 policies 为空、**必须自己填节点名**；
`AD` 子策略只有 `REJECT`（无 DIRECT 兜底）——临时放行单个域名，在 `rules` 更前面加一条 `DIRECT` 规则，**别整组切走**。

## 4.5 `rules:`：分四段理解顺序

| 段 | 内容 | 要点 |
|:--:|:-----|:-----|
| A | DNS 端点固定路由 | **已整体移除**。端点全是 IP 字面量 ⇒ 解析器直接以 IP 访问，不需要在 rules 里钉。只有**你自己**把 DNS 端点写成主机名时，才需要补一条 DIRECT 路由，否则它落 `default → Proxy` |
| B | 白名单 guard → 广告 → 内网 → 各应用规则集 | 顺序即优先级；`Proxy.list` 类"默认 `disabled: true`"的规则由 `Final` 兜底；AI 规则集 URL **钉 commit** 防上游漂移；每条 `rule_set` 各自带 `update_interval`（现值两侧统一钉 `604800`，别只写第一条） |
| C | Apple（No_Resolve 版）→ `direct.txt` → `.cn` 后缀 → `geoip: CN` + `no_resolve` | 这就是 [02 章判据 A+B](02-DNS原理与泄露面.md) 的本内核落点：`geoip` 带 `no_resolve` 后不匹配域名，国内域名直连**完全依赖 `direct.txt`** 那条纯域名规则集；动一条必须看另一条。Apple 必须用 `Apple_All_No_Resolve.list`（原版藏 13 条裸 IP 会强制解析） |
| D | `default: {name: Final, policy: Final}` | 未命中走代理，由节点远程解析、**不经过 `dns` 段** —— 日志里的 `default → Final → Proxy` 是正常决策不是泄露。`lazy` 没有 `Final` 这层组，`policy` 直写 `Proxy`；`name: Final` 只是日志标签 |

**`no_resolve` 的三层**（写之前先确认自己在哪一层）：规则级（`geoip` / `ip_cidr` 的 `no_resolve`）· `rule_set` 级（**在这里写不生效** —— 坑）· 条目级（`.list` 每条自带的 `,no-resolve`）。

`default_proxy_group: Proxy` **不是兜底**：官方定义是"添加代理时自动加入的策略组"。改它不换出口，删它则手动新加的节点不进组。Egern 只有一条兜底通路，就是 `rules` 末尾的 `default`。

## 4.6 分流顺序与应用组默认出口

逐位匹配顺序表在 [`../egern/docs/12-分流顺序.md`](../egern/docs/12-分流顺序.md)（已冻结，内容准确，仍可读）。
两条与 Surge 侧共同的铁律同样成立：应用规则必须排在 `direct.txt` 之前；具体的在前、兜底在后。
应用组的 `policies` 里**只有 `Proxy` 一项**（+ `flatten`）—— 这是设计，不是"忘了加地区"；想固定地区改首位即可。

## 4.7 必须替换 / 环境

- **必填**：`Airport`（旧版 `Airport-A` / `Airport-B`）订阅组的 `url(s)` 占位 —— 换成你的订阅地址。当前版所有分流组已填好、`proxies` 可留空 ⇒ **填完这一个占位就能直接导入**。
- **可选**：自建节点写进 `proxies`（`server` 尽量 IP）。
- 运行审计脚本需要 Python 3 + **PyYAML**（本仓唯一第三依赖）。
- 官方文档入口：DNS `https://egernapp.com/docs/configuration/dns` · rules 字段 `https://egernapp.com/docs/configuration/rules` · 顶层字段全表 `https://egernapp.com/docs/configuration/example`（两处页键名不一致，以 example 页为准）。
  ⚠️ `https://egernapp.com/zh-CN/docs` 与 `/docs/configuration/general` 是 **404**，别按其他客户端文档站的直觉找路径。

## 4.8 改完之后的验证

```bash
python skill/scripts/egern/check_egern_dns.py         egern/profiles/routing.yaml
python skill/scripts/egern/audit_ruleset_noresolve.py egern/profiles/routing.yaml   # 联网：下载规则集数条目
python skill/scripts/egern/audit_routing_coverage.py  egern/profiles/routing.yaml   # 联网：真实域名走规则链
python skill/scripts/egern/audit_dns_forward.py       egern/profiles/routing.yaml
bash skill/tests/egern/run.sh
```

期望读数与逐版口径见 [`../egern/docs/08-审计读数.md`](../egern/docs/08-审计读数.md)。
最后在**目标链路**（尤其蜂窝）跑一次 leak test，并先写下"哪台设备、哪条链路、谁的 DNS" —— 混链路会让整轮结论作废。
