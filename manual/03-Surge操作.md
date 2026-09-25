# 03 · Surge 操作

> 对象：`../surge/profiles/` 下 `lazy` / `routing` 两版（各含带注释完整版与 `.min` 版）。
> 加固清单逐项与验收标准见 [`../surge/docs/03-加固清单-14项.md`](../surge/docs/03-加固清单-14项.md)（清单本体仍在那份文件，本章讲怎么用它）；
> 逐键权威是 [`../surge/DetailsReadme/DetailsReadme.md`](../surge/DetailsReadme/DetailsReadme.md)。

---

## 3.1 文件结构速览

Surge 的 `.conf` 按节组织，模板里与防泄露相关的节：

| 节 | 作用 | 防泄露相关 |
|:---|:-----|:-----------|
| `[General]` | 全局开关 | **DNS 段全部键都在这里**：`dns-server`、`encrypted-dns-server`、`hijack-dns`、`always-real-ip`、测试端点等 |
| `[Proxy]` | 静态节点 | 仅 `lazy` 有（占位节点）；`routing` 的节点来自订阅 |
| `[Proxy Group]` | 策略组 | 出口选择逻辑 |
| `[Rule]` | 规则 | 顺序即优先级，见 3.4 |
| `[URL Rewrite]` / `[Header Rewrite]` 等 | 附加功能 | 与防泄露无关，可整节删 |

> 📌 **两份配置的 `[General]` DNS 相关键被测试断言为逐字相同**（含 `lazy` 与 `routing`、及各自 `.min` 共四份）。
> 想只改一份的 DNS 段？`skill/tests/surge/architecture.sh` 会拦下来。改 DNS 段 = 四份一起改（流程见 [06](06-日常维护.md)）。

---

## 3.2 `[General]` DNS 段：每行在白堵哪个出口

对照 [02 章的泄露面全景](02-DNS原理与泄露面.md)，模板里这些键各自堵一条通路：

| 键 | 堵哪 | 注意 |
|:---|:-----|:-----|
| `dns-server` | 引导与连通性测试用的本地上游 | 全 IP 字面量；**不放 `system`**；不要删它来"减少解析面"——删了 Surge 会用系统 DNS（运营商下发），正是出口 ① |
| `encrypted-dns-server` | 日常解析走加密通道 | 端点尽量 IP 字面量；保留的 2 个主机名端点已用 `# audit-waive:` 记录豁免与理由 |
| `hijack-dns` | 旁路设备（出口 ②） | 模板列出最常见的境外解析器地址把它们收进本地；想一网打尽可写 `hijack-dns = *`（有取舍，见 `DetailsReadme` §10.3） |
| `encrypted-dns-follow-outbound-mode` | 防止"出站走代理、解析也跟着出境"的意外 | 模板显式设 `false`，理由在 `DetailsReadme` |
| `use-local-host-item-for-proxy` | 防止本地 hosts 条目污染代理侧解析 | 同上 |
| `always-real-ip` | Fake-IP 模式下游戏机 / NTP / STUN 拿到假 IP | **是功能清单不是可选装饰**；里面的主机名应能被 `[Rule]` 域名规则接住，`check_surge_dns.py` 第 11 项专查这条 |
| `internet-test-url` / `proxy-test-url` | —— | **性能探针，不是泄露通道**：前者国内 204（测"能不能上网"），后者保持境外 `gstatic.com`（`smart` 打分要含国际段才是真实路径）。把后者"为防泄露"改成国内是典型的**原则误套用**，见 `DetailsReadme` §16 |

> ⚠️ `# audit-waive: <编号> <理由>` 是**有语义的注释**，审计器真的会读它。删掉那行，读数立刻从「waived」变「HIGH/MEDIUM」。形状必须与消费方正则同形（`check_doc_readings.py` 的 D10 专守这条）。

---

## 3.3 广告拦截：`pre-matching` 与 `AD` 组的分层

模板里广告拦截有两条清单（白名单 guard 在前、拦截在后），关键约束：

> **`pre-matching` 的规则，策略必须是字面量 `REJECT` 家族，不能是策略组。**
> 预匹配发生在"还来不及决定出口"的阶段；策略组运行时可能解析成 `DIRECT`，Surge 会**直接拒绝加载整份配置**。

所以链路是刻意的分层：拦截规则写字面量 `REJECT`（换取 DNS/SYN 阶段即拒、不建连不解析 —— 全模板最大的一笔省电优化），旁边 `AD = select, REJECT, DIRECT` 组作为**独立手动开关**（不被任何规则引用，职责是给人工干预留入口）。

想让用户开关接管拦截？可以，但要**一并去掉 `pre-matching`**，接受"先解析再拒"的代价。

---

## 3.4 `[Rule]` 顺序铁律

两版共享同一条顺序铁律（自上而下，首个命中生效）：

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

1. **白名单必须在 REJECT 之前** —— "DIRECT 永远在 REJECT 前"这种一刀切不变量本身是错的（白名单就是 DIRECT 且必须在 REJECT 前）；
2. **应用类规则必须排在 `direct.txt` 之前** —— 否则"域名恰好被国内清单收录的 AI / GitHub"会被直连接走（`github.com` 同时被 `direct.txt` 收录，`GitHub.list` 排后面分流就失效）；
3. **`GEOIP` 必须带 `no-resolve` 且必须与 ⑤ 成对** —— 见 [02 章 2.5](02-DNS原理与泄露面.md)。

> 📌 两版 `[Rule]` 都**没有**游戏机域名规则（`nintendo.net` 等只在 `always-real-ip` 里）—— 这些主机名照旧拿真实 IP，去向由常规规则链决定。别把"缺这三条"当 bug 来"修"。

---

## 3.5 分流版（`routing.conf`）要点

完整的分组层次、首项=默认取向表、逐条规则表在 [`../surge/docs/11-分流版设计.md`](../surge/docs/11-分流版设计.md)（该文件因被读数判据引用而保持活文档）。这里只讲**动手最容易撞的四条墙**：

### ① smart 组不能拿组名当子策略

官方限制：Smart 组**不可使用其他组作为子策略**，也不可用作假如 `url-test` / `load-balance` 组的子策略。等价做法是 `include-other-group`：

```ini
Proxy = smart, include-other-group="Airport"    # ✅ 拿到的是解析后的具体节点
Proxy = smart, Airport                           # ❌ 成员是"Airport"这一个组名，测不到组内节点
```

### ② `flatten` 的对应物

Egern 的 `flatten: true` 在 Surge 没有同名字段，语义对应 `include-other-group`（官方："includes the **resolved member policies** from other policy groups"）。应用组因此写成：

```ini
ChatGPT = select, include-other-group="Proxy"
```

差异要说白：Egern 应用组是 `fallback`/`smart`（**自动**故障转移），Surge 的 `select` 是纯手动。想要自动选优就把某组换成 `smart, include-other-group="Proxy"`，代价是面板不能再手动挑节点。这是**能力差异，不是配置疏漏**。

### ③ 地区组靠正则筛名字，且有两个开关要一起开

```ini
Hong Kong = smart, include-all-proxies=true, include-other-group="Airport", policy-regex-filter=(?i)🇭🇰|香港|…
```

- `policy-regex-filter` **对显式列出的成员无效** —— 你手写在 `[Proxy]` 里的节点必须靠 `include-all-proxies=true` 才会被筛到；
- 正则别写太宽：`(?i)us` 会同时命中 `Russia` / `Belarus` / `AUStralia`，保守用 `\b` 锁词边界；
- **`Other Regions` 是负向断言，把其余地区组的关键词逐字抄了一遍** —— 任何组加关键词必须同步改它，漏改不报错、面板也看不出（节点会同时出现在两个组）。这条拷贝在配置层面消灭不掉，靠 `audit_region_filters.py` 守（用法见 [08](08-验证与自检.md)）。

### ④ 已知边界（都是设计，不是 bug）

| 边界 | 说明 |
|:-----|:-----|
| 空地区组 | 节点名不含关键词则该组为空，指向它的规则会断流。导入后到面板确认 |
| `MAX` 在 `Proxy` 首项 | 默认出口优先落低倍率节点（省钱但可能慢），与 Egern 对齐；不想要就把 `MAX` 挪走 |
| `https` 类型节点不支持 UDP 中继 | 别让承担 UDP 的组落到它们 |
| Apple 无独立策略组 | 走 `Apple` 规则 → DIRECT；要"给 Apple 挑地区"得自己复制 select 组 |
| 段内顺序 | 与 Egern 逐位对齐、由 `architecture.sh` 钉死；"先写引用别人的，后写被引用的"，Surge 允许前向引用 |

---

## 3.6 你必须替换 / 可以删除的

**必须替换**（本手册为准；旧版逐行讲解见 [`../surge/docs/04-模板逐段讲解.md`](../surge/docs/04-模板逐段讲解.md)，已冻结）：`lazy` 的 `[Proxy]` 占位节点、`routing` 的 `Airport` 组 `policy-path` 占位订阅地址。

**可以删**（按收益排序，删完必须重跑分流覆盖审计）：

- `[URL Rewrite]` / `[Header Rewrite]` 等附加节；
- AI 分流（`AI` 组 + 对应规则）；
- `AD` 组（反正不被规则引用）。

**不能删**：`direct.txt` 规则、`GEOIP,CN`（连同 `no-resolve` 是一对）、白名单 guard。删任何一个都会立刻构成 [02 章](02-DNS原理与泄露面.md) 说的"只交一半"。

**改 `routing.conf` 想加新应用组**：照 §3.5 的写法复制一个 `select, include-other-group="Proxy"` 组，
把它的规则插在**国内直连集之前**，并给 `audit_routing_coverage.py` 加对应探针（期望值精确到组名，不许放宽成"不是 DIRECT 就行"）。

---

## 3.7 官方文档入口

- 策略组 / `include-other-group`：[manual.nssurge.com/policy-groups/policy-including.html](https://manual.nssurge.com/policy-groups/policy-including.html)
- Smart 组限制（中文）：[kb.nssurge.com · smart-group](https://kb.nssurge.com/surge-knowledge-base/zh/guidelines/smart-group)
- 其余逐节引用见 `DetailsReadme` 各节脚注。
