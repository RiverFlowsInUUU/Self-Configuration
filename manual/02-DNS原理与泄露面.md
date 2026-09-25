# 02 · DNS 原理与泄露面

把两个内核共享的那套骨架一次讲透，再分内核讲各自的模型。读完应能自己推导出：为什么模板里那些"看起来多此一举"的键，一个都不能少。

素材来自原两侧 `docs/01` / `docs/02` / `docs/05`（已冻结），逐键语义以两侧 `DetailsReadme` 为准。

---

## 2.1 为什么 DNS 泄露值得单独一套配置

访问一个域名时有两件事：问路（DNS 解析）和走路（TCP/UDP 连接）。代理客户端接管的是"走路"，而"问路"很容易从旁边漏出去。

泄露的严重性排序，本项目的口径是：泄露到运营商（不可撤销的隐私暴露）重于答案被污染（解析错）。

实测（国内解析器解境外域名 `www.google.com`）：`dns.alidns.com`、`doh.pub` 等会返回 Facebook 网段之类的污染 IP。但这条结论有边界：

- 它只约束"本地解析"这条路径。走代理的域名由节点远程解析，根本不经过本地 DNS 段；
- 所以对"要访问的境外网站"，兜底组指向国内解析器不会拿到污染答案；
- 反而对国内 / Apple 域名，本地解析更快更准。

由此推出兜底组的唯一判据是「直连可达」，不是「指向境外」（完整推导见 2.6）。

---

## 2.2 传输方式：明文与加密

| 方式 | 端口 / 协议 | 明文？ | 备注 |
|:-----|:------------|:------:|:-----|
| 传统 DNS | UDP（TCP）`:53` | 明文 | 运营商可重定向、可污染 |
| DoH | HTTPS `:443`，`/dns-query` | 加密 | RFC 8484 线格式为准（见 2.7 的坑） |
| DoT | TLS `:853` | 加密 | `tls://` 前缀 |
| DoQ | QUIC `:853`（UDP） | 加密 | 支持面窄 |

---

## 2.3 bootstrap：两个用途，一次都不能被触发

引导解析（bootstrap）解决"鸡生蛋"问题：加密 DNS 端点若写成主机名（`https://dns.google/dns-query`），客户端得先明文解析出这个主机名的 IP，才能开始加密查询。

它有两个用途：

1. 解析 `upstreams` / `encrypted-dns-server` 里端点的主机名；
2. forward / 上游全部失败后的回退出口。

由此得到模板的两条设计：

- 端点一律写 IP 字面量 —— 写一个主机名就欠一次明文查询，写 IP 一次都不产生；
- bootstrap 只放国内可直达的 IP —— 它一旦被触发就是明文，必须保证"触发了也不出境"；且绝不含 `system`（`system` 等于把运营商 DHCP 下发的解析器主动接进回退链）。

代价也要说清：端点换成 IP 字面量，会失去「按域名走 CDN 就近解析」与 ECS 合规两项收益。模板对保留下来的 2 个主机名端点（`dns.google` / `dns.alidns.com`）与境外兜底端点，用 `# audit-waive:` 注释显式豁免并记录理由。

> **注意**　`# audit-waive:` 是有语义的注释，不是说明文字 —— 删了它，审计读数会变红。

---

## 2.4 泄露面全景

所有"明文 `:53` 可能产生"的通路归类如下，两内核通用，各自标注收口方式：

| 出口 | 场景 | Surge 侧收口 | Egern 侧收口 |
|:----:|:-----|:-------------|:-------------|
| ① 引导解析 | 端点写主机名 / `dns-server` 含 `system` / 冷启动期 | 端点 IP 字面量 + 显式 `dns-server`（不放 `system`） | `bootstrap` 全国内 IP；`upstreams` / `proxy_nameservers` 全 IP 字面量 |
| ② 旁路设备 | 家里 HomePod / 电视 / 游戏机不跑客户端，直连路由器做明文查询 | `hijack-dns` 把它们的重定向收进本地 | 无等价物（靠网络侧处置，见 [07](07-故障排查.md)） |
| ③ 规则触发解析 | IP 类规则（GEOIP / IP-CIDR / rule_set 里的 IP 条目）为判归属而对域名强制解析，查询的是你要访问的站点 | 所有 IP 类规则加 `no-resolve`（含远程规则集条目级） | 同左，`no_resolve`（注意拼写差异） |
| ④ 上游失败回退 | 任何一次上游失败，回退 bootstrap 或系统 DNS | 保证上游"直连可达"（2.6） | 官方明文："未配置或解析失败时自动使用系统 DNS"，判据是"有没有任何一条路径会失败" |
| ⑤ 系统级配置绕过 | 描述文件 / MDM / 1.1.1.1 App 下发的 DoH、DoT，不走 `:53`，劫持也拦不住 | 排查项，见 [07](07-故障排查.md) | 同左（`hijack_dns` 只劫持 UDP:53） |

> **说明**　出口 ③ 还有隐蔽变体：强制解析不写在你的 profile 里，藏在别人仓库的规则集文件里。远程条目缺 `no-resolve`，只能下载内容数一遍才知道 —— 这正是两侧 `audit_ruleset_*` 脚本存在的理由。

---

## 2.5 no-resolve 是双刃刀：分流与防泄露必须成对交付

这是全项目最贵的一条教训。官方语义：`no-resolve`（Surge）/ `no_resolve`（Egern）仅适用于 IP 类规则；设为真时仅匹配已解析的 IP，不触发 DNS 解析。

两面效果同时发生：

```
GEOIP,CN,DIRECT               # 域名 →（解析）→ IP →（查 GeoIP）→ CN → 直连
GEOIP,CN,DIRECT,no-resolve    # ✅ 不再触发解析（治好出口 ③）
                              # ❌ 也不再匹配域名（"解析后判归属"这条直连路径一起消失）
```

于是有真实事故（Egern f7 / Surge 同期）：给所有 IP 规则补上 `no-resolve` 后，两个 DNS 审计脚本双双全绿，国内域名却整片落到 `default/FINAL → Proxy`。修法不是撤回 `no-resolve`（那会把泄露放回来），而是补上另一半。

| 判据 | 内容 | 单独交付的后果 |
|:----:|:-----|:---------------|
| A | 所有 IP 类规则带 `no-resolve` | 消灭"规则触发解析"；只交 A，分流坏 |
| B | 兜底之前有一份域名条目足够多的国内 DIRECT 规则集（本仓用 Loyalsoldier `direct.txt`，约十一万条纯域名） | 国内域名仍判给 DIRECT；只交 B，泄露面还在 |

**A 与 B 必须成对交付；任何一次动 `no_resolve` 或换 `rule_set`，都必须重跑分流覆盖审计。**

### 规则集的名字会骗人，判据是数域名条目

实测教训（f8 时期）：`ChinaMax.list` 听起来最像"中国域名全量"，下载下来数是 —— 一万多条里 IP 类占 99.5%，域名只有几十条。名字、README 标题都不可信，判据只有下载统计：

```bash
python skill/scripts/egern/profile_ruleset.py ChinaMax.list   # 规则集类型分布
```

> **注意**　抓规则集内容时 `curl` 必须带 `-L` —— GitHub 的 `raw` 路径有 301，漏了会数出"空文件"的错误结论。

### 测试探针必须能证伪

分流覆盖审计的国内探针刻意混入不以 `.cn` 结尾的域名（`jd.com` / `zhihu.com` / `163.com` / `miui.com` 等）。如果探针全是 `.cn`，一条 `DOMAIN-SUFFIX,cn` 兜底就能让它们全部假通过。

> **说明**　测试集必须包含能证伪配置的样本，否则它只是在复述配置里的假设。

---

## 2.6 兜底组判据：直连可达（group_reach）

Egern 的 `forward` 未命中时回退 bootstrap。曾有一版（f5）把兜底指向境外组（端点全 IP、且规则里判给 Proxy），审计 `0 high`，用户实测却持续 `upstream: bootstrap`。复盘出两条原因：

1. "命中组的端点全失败会怎样"官方未定义 —— 一旦同样回退 bootstrap，兜底挂境外就是一条明文通道；
2. 兜底组经代理，等于引入隐式依赖「先有代理才敢解析」—— 启动阶段（规则集 / GeoIP DB 下载、首轮测速）代理尚未就绪，此刻的解析必然掉进 bootstrap 明文。

判据由此收紧为「端点全为 IP 字面量，且至少一条直连可达」。后续演化（f10 删掉 DNS 端点的显式路由规则后）成双向二选一：

- (a) 旧判据：至少一个端点在 `rules` 里判给 `DIRECT`；
- (b) 新判据：至少一个是已知国内解析器 IP —— 国内到公共解析器 IP 的可达性是公共事实，不需要 profile 里的路由来证明。

这条判据固化在 `check_egern_dns.py` 里，演进史见 [`../skill/reference/egern/pitfalls.md`](../skill/reference/egern/pitfalls.md)。

---

## 2.7 端点实测的两条铁律

模板里的每个 DNS 端点都逐个实测过（`skill/scripts/egern/probe_dns_endpoints.py`，吃 profile 文件）。两条结论值得永远记住：

1. 判死活只能用 RFC 8484 线格式：`GET /dns-query?dns=<base64url>` 加 `application/dns-message`。Google 风格的 JSON API（`?name=x&type=A`）是可选扩展 —— `dns.google` / `8.8.8.8` / `dns.alidns.com` 用 JSON 全回 400，但它们没坏。拿 JSON 判死活会得出完全错误的"不可用清单"。
2. 协议形式写错等于静默失效，配置校验不会报错。实测案例：Quad9 在 `9.9.9.9` 上只提供 HTTP/3，`https://9.9.9.9/dns-query` 直接 `HTTP Version Not Supported`；改 `tls://9.9.9.9` 正常（证书 `CN=dns.quad9.net`）。对候选端点应连测三轮再下"稳定"的结论。

---

## 2.8 两内核各自的 DNS 模型

骨架（2.1–2.7）之上，两个内核把"哪些名字在本地解析"管法不同。

### Surge

- `[General]` 里一组键：`dns-server`（本地解析上游）+ `encrypted-dns-server`（加密端点，优先）+ `hijack-dns`（收口旁路设备的 `:53`）+ `doh-server` 等；
- 代理侧解析天然在节点上做：官方 KB 明确「使用代理策略时，DNS 解析永远在代理服务器进行」。本地解析只在命中 DIRECT 时发生 —— 所以 Surge 侧不需要 Egern 那样的 `proxy_nameservers`；
- `always-real-ip`：Fake-IP 模式下游戏机 / NTP / STUN 等必须拿真实 IP 的主机名清单，删了它这些设备会拿到假 IP；
- 测试端点不是泄露通道（走代理时远程解析），它是给 `smart` 打分的性能探针：`internet-test-url` 用国内 204，`proxy-test-url` 保持境外 `gstatic.com`（含国际段才反映真实路径）。

### Egern

- `dns:` 段：`servers` / `upstreams` / `forward`（按域名分流到不同上游组）/ `bootstrap` / 可选 `proxy_nameservers`；
- 与 Surge 的根本差异：Egern 的代理侧解析默认也走本地 `dns` 段，靠 `forward` 规则决定用哪组上游 —— 所以节点域名、延迟测试域名、profile 自身依赖（规则集 / 图标的托管域名）都必须被 `forward` 覆盖，漏一个就是一个持续泄露源（f3→f4 的教训）；
- `proxy_nameservers` 不是"多加一层保险"，是"砍掉整条 `forward`"：一旦设置，所有代理侧解析强制走它、完全绕过 `forward`、且强制直连。模板最终选择显式设置它并兜底国内组，作为"唯一出口"的确定性取舍（代价记录在 `DetailsReadme` 的已知取舍一节）；
- `no_resolve` 有三层：规则级、`rule_set` 级（在 `rule_set` 上写不生效，这是坑）、条目级（`.list` 内每条自带的 `,no-resolve`）。写 `no_resolve` 之前必须分清在哪一层。

---

## 2.9 延伸阅读（按内核）

| 主题 | 去处 |
|:-----|:-----|
| 原理全篇（已冻结，读时注意顶部横幅） | [`../surge/docs/01-DNS是怎么工作的.md`](../surge/docs/01-DNS是怎么工作的.md) · [`../egern/docs/01-DNS是怎么工作的.md`](../egern/docs/01-DNS是怎么工作的.md) |
| 泄露案例全篇 | 两侧 `docs/02-DNS为什么会泄露.md` |
| 事故复盘 | 两侧 `docs/05` · [07-故障排查](07-故障排查.md) |
| 逐键语义 | 两侧 `DetailsReadme` |
