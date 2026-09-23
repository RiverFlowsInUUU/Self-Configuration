# 📝 更新日志

> 本仓库的**装配史**在这里；**模板内容**的迭代史在两个内核各自的 CHANGELOG 里：
> [`surge/CHANGELOG.md`](surge/CHANGELOG.md) · [`egern/CHANGELOG.md`](egern/CHANGELOG.md)。
> 格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

---

## 2026-09-23 · 规则集刷新统一为一周 · 分流版升 v3.1

同一天的第二轮：这次**动了 profile 与脚本**（上一轮只落在文档层）。

- 🔁 **全部远程规则集的刷新参数统一为 604800（一周）**：新建 `surge/profiles/routing_v3.1{,.min}.conf`
  与 `egern/profiles/routing_v3.1{,.min}.yaml`，`lazy` 按用户要求**保持默认命名、原地覆盖**。
  合计改写 110 行（新补 32 条 + 86400→604800 共 78 处），四份 v3.1 与两份 lazy 现共 100% 显式钉住。
  订阅型组的 `policy-path` 刷新参数**刻意不动**（节点列表刷新 ≠ 规则集刷新，是两件事）。
- 🐛 **修掉一处因果错误**：原文档写「不显式写 `update-interval`，规则集就会停在首次下载的版本」——
  Surge 手册实为 `Default: 86400 (24 hours)`、**负值才关闭自动更新**；真正缺省未文档化的是 Egern 侧。
  据此改写 7 处，并把这条登记为 §8 的**第 5 类刻意修订**（本仓第一次改动 substantive 论述）。
- 🧪 **新增两份同名审计脚本** `audit_ruleset_refresh.py`（Surge / Egern 各一份），
  并接进两套回归的既有阶段：非正值 = HIGH，缺字段或偏离约定值 = 「约定」档（历史存档版不误伤），
  当前推荐版与懒人版由回归加 `--strict` 守住。脚本数 **4→5 / 9→10**，断言数 **15→23 / 24→46**。
- 🩹 **中文 Windows 上「假绿」修复（本轮最实质的一条）**：控制台与管道默认 GBK(cp936)，
  脚本一 `print` emoji 就 `UnicodeEncodeError`、进程以**退出码 1** 结束 —— 而回归里 `bad_*` fixture
  期望的恰恰也是 1，于是**解释器坏了会被计成「判负通过」**，整轮看着绿、一条判据都没执行。
  现在共享模块 import 时把 stdout/stderr 钉成 UTF-8（`force_utf8_stdout`），两个 `.sh` 入口另设
  `PYTHONIOENCODING=utf-8`；不 import 共享模块的 6 个 Egern 脚本与 `check_links.py` 逐个接上。
- 🔢 **两份 `docs/08-审计读数.md` 换成真跑出来的读数**：Surge 全 6 阶段 **23 passed / 0 failed**、
  Egern **10 + 36 = 46** 全绿；分流覆盖 `33/33` → 实测 **39/39**（国内 17 · 境外 8 · 误杀 8 · Apple 6）、
  地区正则 `9/9` → 实测 **3 项全过**、`architecture.sh` `11/11` → **17 项**、
  Egern 规则集数 21 → 推荐版 **25**；`check_surge_dns` 的 `ok` 两份是 **12 / 11**，
  差的只是 `lazy` 多出的「`[Proxy]` 静态节点成员可解析」一项，已如实改写「读数完全一致」那句。
- 🔗 `v3` 保留为存档，仓内指向 `routing_v3` 的**订阅地址 / 命令示例 / 测试入口 / 文档正文**逐处升到 `v3.1`。
  > ⚠️ 这是**第二次因改名让旧地址失效**（第一次是 `routing.conf` → `routing_v3.conf`）。
  > 订阅端必须改到 `routing_v3.1.min.conf` / `routing_v3.1.min.yaml`，说明写在两侧 `docs/07`。
- 🧷 `architecture.sh` 的 ④ 组序承诺：唯一真值从「仓库外的 Egern v3」改为**本仓**
  `egern/profiles/routing_v3.1.yaml` 的 26 组（实测与写死的承诺值逐位相同）；仍写死、不运行时推导，
  理由不变 —— 顺序是对外承诺，改它必须显式面对。
- 🧷 **「当前推荐版」收成一行常量 `CURRENT`**：Surge 的 `run.sh` / `architecture.sh` 与 Egern 的
  `run.sh` 各持有一行 `CURRENT="${CURRENT:-routing_v3.1}"`，阶段 2 的 `--strict` 名单、阶段 4 的
  联网审计、阶段 5 的地区正则对账、`architecture.sh` 的 ②-b / ④ 段全部由它派生 ——
  升版从「改十几处」变成「改这一行」（docs 里的命令示例仍写实际文件名，那是给人照抄的）。
  配套补了前置检查：`$CURRENT` 指向的 profile 不存在 ⇒ **退出码 2**。此前阶段 4 / 5 对不存在的
  文件是 `continue`，升版忘了改常量会**静默少跑一整个阶段**、输出照样全绿 —— 与「解释器坏掉
  会假绿」是同一类故障。
- 🔢 **Egern 回归的断言口径统一到「按脚本对账」**：阶段 1 的 5 行 fixture 每行校两个脚本
  （`check_egern_dns` 与 `audit_dns_forward` 是两条独立判据），因此计 **10** 条而非 5 条，
  与文档口径一致；末尾新增两阶段合计的 `TOTAL: 46 passed` 行。
  此前 runner 自己报 41、文档写 46 —— 两边对不上号，属于「数字没跑出来」的残留。
- 🧪 **本地检查有了仓内入口**：新增 `skill/tests/all.sh`（两内核回归 + 全仓链接与锚点 + 两版形态
  对拍，合计一行、退出码 0/1/2）与 `skill/tests/check_min_pair.py`。后者补的是此前无人守的空档：
  `architecture.sh` 只比 `.conf` 与 `.min.conf` 的 **DNS 键与组顺序**、且只管 Surge 侧，
  Egern 侧两版形态**从没对拍过整份配置**（实测 12 对全部逐字相同）。
- 📦 **升版脚本进仓**：`skill/tests/bump_version.py`（默认只出计划，`--apply` 才写盘，`--gate` 跑 `all.sh`）。
  它把四份形态、刷新秒数、全仓活指向、三处 `CURRENT` 这些机械活做完，CHANGELOG 与「版本沿革」
  只列清单不改写。默认仓库根由脚本自身位置推导 ⇒ 换设备 `git clone` 后直接可用，不含任何维护者本地路径。
- 🔧 **顺手两处**：`CURRENT=routing_v3.2` 的示例行统一改指**存档版** `routing_v3`（示例若写"下一个版本号"，
  真升版后会变成过期事实）；`run.sh` 前置检查里列现存分流版的那句用 `grep -o 'routing_v[^.]*'`，
  会把 `routing_v3.1` 打回 `routing_v3` —— 正是升版时最需要看清的一行。
- 🗂 **与源仓的差异清单 49 → 52 项**：上面三个文件在两个前身仓里**没有对应路径**，故计入人工确认清单；
  反解后逐字节相同的仍是 **39 个**。逐字节对账与「旧仓是否被改动」两项合并验收**刻意留在维护者本地**，
  `all.sh` 不含它们 —— 详见 [`docs/跨内核差异对照.md`](docs/跨内核差异对照.md) §8 第 7 条。

## 2026-09-23 · 合并后修订（文档准确性 · 失效外链 · 自包含）

合并成仓当天做的一次全仓复核，改动只落在文档层，**profile 与脚本零改动**。

- 🔢 **数字按 HEAD 树实测校正**：图标引用 **618 → 616 处**（三处同步，= 源仓 Surge 75 + Egern 541）；
  SKILL 行数与分段口径（原三个分支数相加与总数自相矛盾）；`profiles/` 引用核验 **19 个 / 14 存在 / 5 历史名**
  并逐个列出那 5 个已删除的版本名；命令计数写明「去重 14 条 · 共 66 处提及」口径；
  「15 个 Python 脚本」限定为 `skill/scripts/` 下的 15 个。硬编码的「两处刻意修订」改为指向 §8。
- 🔗 **失效外链全部修好**：Surge 手册改版把旧的 `/policy/*.html` 一层拆成了
  `/dns/`、`/rules/`、`/policy-groups/`、`/policies/` 四个章节，`skill/SKILL.md` 里那四条链接因此全 404。
  现按分支正文实际讲到的键重新指向对应新章节，并补上加密 DNS 与策略组参数两页
  （`encrypted-dns-server` / `hijack-dns` / `always-real-ip` / `include-all-proxies` 都有专页了）——
  八条链接逐条实测 200。社区参考实现 `repcz.github.io/Egern` 是**搬家不是下线**，
  新址 `doc.repcz.link/egern/` 实测 200，`skill/SKILL.md` 与 `egern/docs/01` 两处一并改指并留旧地址说明。
  > ⚠️ 这两处都在 `skill/SKILL.md` 的内核分支正文里，因此登记为**对「两侧正文逐字保留」的第 2 类刻意修订**，
  > 见 [`docs/跨内核差异对照.md`](docs/跨内核差异对照.md) §8。代码块未受影响，仍与源文件字节一致。
- 🧱 **内容自包含（切断对前身两仓的一切指向）**：全树扫过，指向 `RiverFlowsInUUU/Surge` 与
  `/Egern` 的只有 **6 处超链接 + 3 处沿革文字**，且全在文档正文 —— profile / 图标 / 脚本 / fixture
  从一开始就零依赖（624 处自引用全部指向本仓）。逐处处理：4 处姊妹仓超链接改指同侧目录
  （`egern/docs/07` 两处、`surge/docs/07`、`surge/docs/11` 各一处），合并条目的两处超链接改为纯文本来源说明，
  三处「旧仓地址继续可用」的表述改为「前身仓可能转私有，**新写地址一律用本仓**」。
  改完全树**零条指向两仓的链接**。社区规则集与图标来源（blackmatrix7 / Loyalsoldier / ACL4SSR /
  AWAvenue / Jinx / Qure 等）属公共资源，**保持引用不动**。这条同时立为约定，写进
  [`docs/注意事项.md`](docs/注意事项.md) 的通用表。
- 🧩 **`skill/reference/*/public-repo.md` 的 4 处 `_base/verify_readme_tone.py`** —— 那是装配用的
  本地闸门脚本、按仓库惯例不进公开仓，读者照路径找不到东西。改为写明它是维护者本地闸门，
  并把该项到底查什么就地写清（正文本来就已经写了检查内容，只差一个找不到的路径）。
- 🧹 **`skill/SKILL.md` 只留一份 YAML 头**：两个内核分支的开头各残留着**源技能包的整段头部**
  （`name` / `description` / `agent_created` 加两条分隔线，各 6 行共 12 行），渲染时是两条压在正文里的假头。
  删掉它们，但把其中的检索线索全部并进文件头那一条 `description`：两侧原文 705 + 546 = **1251 字符**，
  逐条拼接会太长，因此按「同名异形合并、共享线索去重」处理 —— `hijack-dns / hijack_dns`、
  `no-resolve / no_resolve`、`国内域名全落 FINAL` 各一条覆盖两内核，Surge 侧的「`dns.google` 泄露」
  「引导解析泄露」「`extended-matching`」「Surge 拒绝加载配置」「`proxy-test-url` 泄露」「`gstatic generate_204`」
  与 Egern 侧的「`Egern dnsleak`」「日志里规则判定正常但 upstream 是 bootstrap」「`ChinaMax_All_No_Resolve`」
  「`blackmatrix7` No_Resolve 变体」「分流覆盖审计」等同步补入。合并后 **1000 字符 / 56 条**，
  ⚠️ 语义零丢失、字面写法有合并（例：源仓的「旁路设备明文 53」在本仓写作「明文 :53 旁路」）。
  ⚠️ **根因不在源仓**：两份源文件各只有一处头部、位置正确 —— 是装配脚本剥头部的正则按 LF 写，
  而 Windows 的 `core.autocrlf=true` 把工作区 checkout 成 CRLF，正则匹配不上。装配脚本已改为
  **先归一化换行**，并重跑确认「从干净克隆重跑 == 本仓当前树」逐字节一致。
- 🔒 **`.gitignore` 补私钥兜底**：`*.p12` / `*.pfx` / `*.pkcs12` / `*.key` / `*.pem` / `.env*`。
  文档反复警告 Egern 的 `ca_p12` 是私钥容器，此前却没有任何拦截；**刻意不含 `*.crt`**，
  导出的公钥证书有时需要留档。现有跟踪文件零命中，不影响任何既有内容。
- 🧪 **环境要求写明**：回归要 Python 3，Egern 侧还需 `PyYAML`，Windows 的 Git Bash 两者都不自带 ——
  此前只在 `skill/README.md` 里提过一次，现补进通用注意事项与本节，避免「没跑成」被当成「跑绿」。
- ✅ **改后复跑**（本轮全部改完之后重跑，不是沿用合并时的读数）：
  相对链接 **42 篇全通过**、锚点 **44 个全存在**、slug 自检 6/6；
  `SKILL.md` 两分支的**代码块 4 段与源文件逐字一致**；**10 对 `.min`** 去注释后 0 不一致；
  反解回源形态后逐字节相同的文件 **54 个**（20 profile · 15 Python 脚本 · 9 fixture · `check_links.py` 等）、
  **26 个图标**与两个源仓同时相同。
- ✅ **指向前身两仓的超链接 = 0 条**。全树只剩 **5 处纯文字提及**，逐处核过：本 `CHANGELOG` 的
  合并条目与更正块 3 处（来源说明）、`egern/CHANGELOG.md` 改名条目 1 处（历史原文）、
  `egern/docs/07` 的 301 跳转说明 1 处（紧跟着已写明「已停止更新、不保证长期可达」）。
  旧仓地址在本仓**不参与任何内容加载**，两仓转私有后本仓照常可用。

---

## 2026-09-23 · 合并成仓

本仓库由 `RiverFlowsInUUU/Surge` 与 `RiverFlowsInUUU/Egern` **合并**而成（两个前身仓仅作来源说明，
合并时对它们**未作任何改动**）。⚠️ **本仓自包含**：profile、图标、审计脚本与全部详解都部署在本仓，
配置里不引用那两个仓的任何地址；它们后续可能转为私有，**新写地址一律用 `RiverFlowsInUUU/Self-Configuration`**。
唯一的外部依赖是社区规则集与官方文档，与它们无关。

### 新增

- 🏗️ **共享层 + 双内核目录**的结构：`icons/`、`docs/`、`skill/SKILL.md` 为共享层；
  `surge/`、`egern/` 各持自己的 `profiles/`、`docs/`、`DetailsReadme/`、`CHANGELOG.md`。
- 📄 [`docs/跨内核差异对照.md`](docs/跨内核差异对照.md) —— 本仓库的**主文档**：
  语法映射表、26 个分组的逐项对齐、24 条规则的位位对应与三处引擎差异、
  两侧脚本对照，以及「哪些结论不能跨内核照搬」。
- 📄 [`docs/规则集与来源.md`](docs/规则集与来源.md) —— 两侧规则集合并清单：
  **21 条两侧逐字相同**，另有各自独有的一条（Surge 内置 `SYSTEM` / 内置 `LAN`，Egern `domain_suffix: cn`）。
- 📄 [`docs/注意事项.md`](docs/注意事项.md) · [`docs/图标与许可.md`](docs/图标与许可.md) —— 由两侧同主题文档合并。
- 🧭 **单一技能入口** [`skill/SKILL.md`](skill/SKILL.md)：第 0 节先判内核，再进 A/B 两个内核分支。
  当前 **581 行**（frontmatter 5 + 共享头部 73 + Surge 分支 183 + Egern 分支 320；
  合并时 591 行 —— 上方「合并后修订」里外链修复 +2、去掉两份内嵌假头 −12）；
  ⚠️ **两侧正文逐字保留**，只做标题降级、路径改写、以及上方登记并在
  [`docs/跨内核差异对照.md`](docs/跨内核差异对照.md) §8 留痕的外链修订 ——
  用代码块抽取比对验证过，两个分支里的**全部代码块与源文件字节一致**。

### 变更

- 🔗 **URL 全量改写**：仓库自身的 raw URL 由两个旧仓名改为本仓名，
  **616 处**图标引用改指共享根 `icons/`；改写后旧自引用**零残留**（32 个文件、40 类替换规则）。
- 📁 **测试与脚本改道**：`skill/scripts/{surge,egern}/`、`skill/tests/{surge,egern}/`，
  三个 runner（`surge/run.sh`、`surge/architecture.sh`、`egern/run.sh`）里的
  `SCRIPTS` / `ROOT` / `PROFILES` 已重算并**逐个求值确认**可解析。
- 📚 **文档层收敛**：每侧各 3 篇同主题文档提升到 `docs/`，内核目录内保留 9 篇各自的编号系列。

### 验证与已知缺口（如实记录）

- ✅ **相对链接检查**：先用两个源仓库做**对照测试**（二者断链数 = 0），检查器因此可信；
  目录改造造成的断链 **52 处**，已全部修复至 **0**（当前树 42 篇 `.md` 全通过）。
- ✅ **锚点检查**：同一套对照测试跑在两个源仓库上 —— Surge 28 个锚点**全通过**，
  Egern 抓出 **3 处**指向已撤下 README 章节的失效锚点。合并版把这 3 处一并修好，
  当前树 **44 个锚点全通过**（修掉的 3 处见 [`docs/跨内核差异对照.md`](docs/跨内核差异对照.md) §8）。
  slug 算法不靠猜：逐条移植自仓内 `skill/tests/surge/check_links.py` 的 `gh_slug()`，
  并用它自带的 6 条对拍样例自检通过。
- ✅ **正文里的路径提及**同步改道（链接之外，读者会直接照抄命令）：
  23 个文件、**157 处** `skill/scripts/` · `skill/tests/` · `skill/reference/` · `profiles/` 补上内核段
  （现势可复核：带内核段的 `skill/{scripts,tests,reference}/{surge,egern}/` 提及 126 处、分布在 30 个文件）；
  改后**逐条求值**：文档中出现的 `python` / `bash` 命令（去重 14 条、共 66 处提及）全部指向真实脚本，
  19 个被引用的 `profiles/` 路径中 **14 个真实存在**，另 5 个指向已删除的历史版本名
  （`routing.conf`、`routing_v2.5.yaml`、`routing_v2.5.min.yaml`、`v0.yaml`、`v2.5.min.yaml`）
  —— 那五处本身就是"此地址已 404"的通知，**故意保留**。
  ⚠️ 两份内核 `CHANGELOG.md` **不参与改写** —— 历史条目按发生时的事实保留。
- ✅ **内容零漂移**（合并最容易出事的地方）：把新仓 URL 反解回源形态后与源文件 `cmp` 比对 ——
  **20 份 profile**、**26 个图标**（与两个源仓同时相同）、`skill/scripts/` 下 **15 个 Python 脚本**
  （另有 `skill/tests/surge/check_links.py`，同样与源仓逐字节相同）、**9 个测试 fixture**
  全部**逐字节相同**；其余 24 篇文档的差异**逐行归类**，除
  [`docs/跨内核差异对照.md`](docs/跨内核差异对照.md) §8 记录的修订外全部属于既定改写类别
  （URL / 技能包路径 / `profiles/` 前缀 / 相对链接深度）。
  三个 shell runner 的差异逐行核过，只有 `SCRIPTS` / `ROOT` / `PROFILES` 与用法注释。
- ✅ **脱敏复核**：全树 `token=` 命中项**只有一种** —— 占位符 `REPLACE_WITH_YOUR_TOKEN`；
  订阅 URL 只有 `sub.example.com`；无 `ca_p12` / 私钥 / 真实凭据。
- ✅ **改动纪律**：所有装配步骤写成可重放脚本（脚手架 / 改写表 / 修链器 / 改道器 / 两个检查器 /
  字节还原核对），从干净克隆重跑一遍即得同一棵树。
- ⚠️ **未跑的部分**：两侧 `*.py` 回归套件**本次未执行** —— 装配环境无可用 Python 解释器，
  且 Egern 侧脚本另需 `PyYAML`。因此本仓库只声明「静态检查通过」，**不声明回归通过**。
  环境要求已写进 [`docs/注意事项.md`](docs/注意事项.md)：**Python 3 + PyYAML**，
  Windows 的 Git Bash 两者都不自带（`python` / `python3` 可能是商店占位符，需自行安装）。
  联网阶段（Surge 侧阶段 4）可用 `SKIP_NET=1` 跳过。
  在具备环境处请按 [`README.md`](README.md) 的命令跑一遍再用于生产。
- 🚫 **刻意不挂 CI**：两个源仓库都记录了这一决定，合并后沿用。

### 未继承的源文档缺陷（合并版已修，源仓保持原样）

合并时发现源仓库文档中有 **4 处**与现状不符的表述，本仓库逐一改掉；
源仓库按用户要求**未作任何改动**，仍带着这几处。明细与修法见
[`docs/跨内核差异对照.md`](docs/跨内核差异对照.md) 第 8 节。
该节同时记录了一处**刻意保持原样**的差异：加固清单两侧条数不同（Surge 12 项 / Egern 18 项）——
这是内核差异，不是缺陷。

---

## 历史

合并前的完整迭代史按内核分别保存在
[`surge/CHANGELOG.md`](surge/CHANGELOG.md)（Surge `v1`→`routing_v3`）与
[`egern/CHANGELOG.md`](egern/CHANGELOG.md)（Egern `v0`→`routing_v3`、DNS 加固 `f1`→`f10`），
**内容逐字未改**，包括其中的旧文件名与旧仓库名表述。

> ⚠️ 按发生时事实保留的代价：内核 `CHANGELOG` 里「新写地址请用 `.../RiverFlowsInUUU/Egern/...`」
> 这类提示（`egern/CHANGELOG.md` 改名条目）**已经过期** —— 回溯改写历史条目会破坏它的证据价值，
> 所以只在这里更正一次：**新写地址一律用 `RiverFlowsInUUU/Self-Configuration`**，
> 前身两仓仅作来源说明、后续可能转为私有。
