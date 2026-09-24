# 📝 更新日志

> 本仓唯一的改动记录。体例三条：**一天只有一段**，当天后续改动往这一段里增补，不开第二个同名日期段；
> 段内分 `Surge` / `Egern` / `共享层` 三块，**当天没动的内核不写**；每条只答「改了什么 · 哪里没动 · 验收」，
> 推理过程和当时的纠结不进日志。
>
> 合并前的内核迭代史：[`surge/docs/07`](surge/docs/07-文件版本沿革.md) ·
> [`egern/docs/07`](egern/docs/07-文件版本沿革.md) 末节。
> 本文件 2026-09-24 文风统一前的原文：[`docs/日志旧版原文.md`](docs/日志旧版原文.md)。

---

## 2026-09-24

### Surge

- 🧬 **分流版升版 `routing_v3.2`**（新建四份形态，`routing_v3.1` 转为存档，`profiles/` 现 8 份 `.conf`）。
  相对 `v3.1` 只动一处实质内容：**规则级 `no-resolve` 按「实测零 IP 就不写」重排** —— 9 条零 IP 的规则集
  （`private.txt` / `Gemini` / `Anthropic` / `Claude` / `AI.list` / `YouTubeMusic` / `GitHub` / `Microsoft` / `direct.txt`）
  去掉开关，9 条真含 IP 的保留（内置 `LAN` · `OpenAI` · `Spotify` · `YouTube` · `Google` · `Telegram` · `Twitter` · `WeChat` · `GEOIP`）。
  分组、规则条数（24）、顺序、DNS 段**逐字未动**。
- ✂️ **`lazy.conf` 两处**：删掉远程 Apple 全量集（只留内置 `SYSTEM`，规则 11 → 10 条）；
  段序统一为 白名单 → 广告 ×2 → 内网 ×2 → `SYSTEM` → `AI.list` → `direct.txt` → `GEOIP,CN` → `FINAL`，
  与 Egern 懒人版同位；同样去掉 3 条零 IP 规则的 `no-resolve`。`.min` 形态按新 `[Rule]` 段重建。
- 🚫 **未动**：`[General]` 的 16 个 DNS 键、`[Proxy Group]` 组序、图标、占位凭据 —— 防泄露面与分流能力都没碰。
- 🔢 读数：`check_surge_dns` `lazy` 0 high / 3 low / 12 ok / 2 waived、`routing_v3.2` 同判据面 11 ok；
  `audit_ruleset_refresh --strict` 20 条 + 6 条全部钉在 604800；`audit_routing_coverage`
  `lazy` **37/37** · `routing_v3.2` **39/39**。回归 23 → **27 断言**（阶段 2 的 profile 数 6 → 8）。
- 🏷️ **订阅地址固定化**（同日第二轮）：`profiles/` 顶层只剩 `routing.conf` · `routing.min.conf` · `lazy.conf` · `lazy.min.conf`
  四件，被替代的 `routing_v3` / `v3.1` 连同各自 `.min` 逐字节进 `profiles/config_old/`（4 份）；当前版 `v3.2`
  不再占版本号文件名，就住在 `routing.conf` 里，只在第一行留一句 `#! version=routing_v3.2`（懒人版同形）。
  懒人版从此也有了归档：`lazy_v1.0` 是当前 `lazy.conf` 的逐字节快照。**配置正文零改动** ——
  分组、规则、DNS 段、图标都没碰，动的只有文件名与那一行头注。
- ✂️ **`routing.min.conf` 一次性空白规范化**（同日第四轮，由新的 `make_min.py --apply` 落盘）：
  144 → **145 行**、10594 → 10595 字节，**非空行序列逐字未变**，动的全是空行位置（`[Proxy]` 与注释之间那条
  挪了位、末段前补了一条分隔空行）。⚠️ **订阅端字节会变**（行数差 1），内容语义不变。
  `lazy.min.conf` 这半边**故意没跑**：它在 `config_old/` 里有同号快照 `lazy_v1.0`，规范化会点亮对拍 `V6`
  的「改了没升版」⇒ 留到下次真改 lazy 时随升号一起落地。

### Egern

- 🩹 订正 2026-09-23 查出未改的那处文档错误：`default_proxy_group` 按官方定义写作「添加代理时自动加入的策略组名称」
  （顶层字段全表 `egernapp.com/docs/configuration/example`），不再叫"默认出口组 / 默认策略组"，并写明它与兜底无关 ——
  兜底只有 `rules` 末尾那条 `default`。改的是 `DetailsReadme` §1.1（这条同时从「C. DNS 与默认出口」挪进「A. 全局开关 /
  辅助项」）与 `docs/04` §6。配置零改动，`Proxy` 这个取值保留（懒人版 `Proxy` 组为空，正靠它接住手动添加的节点）。
- 📦 新增本仓第一份自托管规则集 [`egern/apple_system.list`](egern/apple_system.list)：Surge 官方内置 `SYSTEM` 的
  2026-09-24 快照，18 条域名（快照原件里的 2 条 `PROCESS-NAME` 删掉，Egern 没有进程名匹配）。
  存在的理由是 `docs/规则集与来源.md` §2 那条「`SYSTEM` 仅 Surge 有、Egern 无对应内置集」—— 懒人版用它补上 `SYSTEM` 位。
  本文件先落仓，**profile 还没引用**（raw URL 得先存在，否则联网审计只是静默跳过）；引用与读数同步在懒人版那一批里做。
  配置零改动。
- 🧬 **分流版升版 `routing_v3.2`**（新建两份形态，`routing_v1`~`v3.1` **八版全部保留**，`profiles/` 现 20 份 `.yaml`）。
  相对 `v3.1` 两处：① 位 ⑲ 补 `apple_system.list → DIRECT`，与 Surge 内置 `SYSTEM` 同位同策略；
  ② `Proxy.list` 由 `disabled: true` 改成**纯注释块** —— Surge 侧没有禁用开关、只有注释，`disabled` 仍占一个
  `rules` 数组位，注释化才是两侧同写法。规则 24 条、分组 26 个、`dns` 段**逐字未动**。
- ✂️ **`lazy.yaml` 两处**：删掉内联 `domain_suffix: cn`（`direct.txt` 第 23,829 行本来就是 `DOMAIN-SUFFIX,cn`，
  属重复）；补上 `apple_system.list → DIRECT`。规则一增一减仍 10 条，编号 ①–⑦ 重排，
  文件末尾关于 `push.apple.com` / `real_ip_domains` 的两处说明按现状改正。`.min` 重新生成。
- 🚫 **未动**：`dns` 段四层 `forward`、26 个分组、`AD` 只留 `REJECT` 的懒人版特例、兜底 `default → Proxy`。
  规则级 `no-resolve` 那条原则**在 Egern 侧不落成规则行开关** —— `no_resolve` 只适用 `geoip`/`ip_cidr`/`ip_cidr6`/`asn`，
  写在 `rule_set` 上不生效，同层防线仍在规则集文件里（条目级 `,no-resolve`）。
- 🔢 读数：`check_egern_dns routing_v3.2` / `lazy` 均 0 high / 2 low / 24 ok；
  `audit_ruleset_noresolve` `lazy` 10 → **11 个**规则集（`rules` 8 + `dns.forward` 3）、`routing_v3.2` **25 个**
  （与 `v3.1` 同数不同组成：进 `apple_system.list`、出 `Proxy.list`）；
  `audit_ruleset_refresh --strict` 22 条 + 8 条全部钉在 604800。回归 46 → **50 断言**（阶段 2 覆盖 20 份 profile）。
- 🏷️ **订阅地址固定化**（同日第二轮）：顶层只剩 `routing.yaml` · `routing.min.yaml` · `lazy.yaml` · `lazy.min.yaml` 四件，
  `routing_v1` → `v3.1` **八版全部**连同 `.min` 逐字节进 `profiles/config_old/`（16 份），再加懒人版快照
  `lazy_v1.0` ×2 ⇒ 该目录 18 份。当前版 `v3.2` 住在 `routing.yaml`，头注 `#! version=routing_v3.2`；
  `lazy.yaml` 头注 `lazy_v1.0`。**配置正文零改动**，20 份 `.yaml` 收成 4 份只是"当前版换固定名 + 其余进归档"。

### 共享层

- 🗑 删除 `surge/CHANGELOG.md` 与 `egern/CHANGELOG.md`，正文整段并入各自 `docs/07` 末节；本文件是唯一日志。
- 📜 历史条目原文未改，只降一级标题、按新位置改写相对链接。
- 🔗 活链接 8 处改道；`check_links.py` 扫不到的目录树与表格提法 6 处手工同步（两份 `public-repo.md`、`surge/DetailsReadme`、`AGENTS.md`）。
- 🚪 `skill/tests/bump_version.py`（冻结文件，本轮授权）改两处文案：手工清单「三处 CHANGELOG」→ 本文件一份；
  排除口径注明并入后的历史条目靠 `沿革` 一条排除。判定逻辑未动。
- 🚫 未动：`docs/体检报告.md` P5 与 `docs/跨内核差异对照.md` 的历史记述，只在 P5 下补一句去处。
- ✂️ 本文件文风重写：一天一段、段内按内核分块（见头部体例三条），推理与纠结从条目里去掉。
  重写前的原文归档在 [`docs/日志旧版原文.md`](docs/日志旧版原文.md)（只读存档，超链接已摊平以免断链）；
  体例同步写进两份 `skill/reference/*/public-repo.md`。配置、脚本、判据零改动。
- 🛠 新增批量编辑执行器 [`skill/tests/apply_edits.py`](skill/tests/apply_edits.py)：一份 JSON 说清「哪些文件、把哪句改成哪句」，
  每条替换要求锚点在**当前内容**里恰好命中 `count` 次（默认 1，可 `"all"`）；**任何一条不达标 ⇒ 整批一个字节都不写**，
  治的是批量改文档时「锚点撞车静默改错处」与「改到一半得回滚」两类返工。四条守门：锚点计数、内存里算完再写盘（`newline='\n'`）、
  含 CR 的文件拒改、**冻结闸门文件默认拒绝**（要 `--allow-gate`，拒绝消息里写着请示要附哪两条；写它时名单 9 个，本轮起 10 个，见本段最后一条）。
  闸门名单与 `all.sh` 里的 `GATE` 由自带回归 A9 逐字对拍，防两处漂移。自带回归 12 条全绿；
  **它不参与 `all.sh`**（接进去要改冻结文件，另说）。
- ✅ 三轮各自跑过 `all.sh`，四项全绿（第 5 项是本轮后面那两条才加上的）。
- 📐 新增文档读数对拍 [`skill/tests/check_doc_readings.py`](skill/tests/check_doc_readings.py)，并接成 `all.sh` **第 5 项**：
  它不判配置内容对错，只拿解析器实测出的组数 / 规则条数 / 规则集条数 / 订阅文件份数 / 图标数 / 检查项数，
  去对拍 13 篇文档里写死的这些数字。固定 10 条判据：D0 两内核三对读数逐位对齐 · D1–D6 六类读数 ·
  D7 本仓自托管 raw URL 的落点存在 · D8 profile 文件名不悬空 · D9 三处 `CURRENT=` 一致且当前版四件齐。
  一句里同时讲懒人版和分流版、或内核与形态都判不出的表述**跳过不误报**，宁可少判。当前读数：
  对拍 **130 处声明**、跳过 47 处、10 条全过。反例实测：把 Surge `lazy` 的一条 `RULE-SET` 注释掉，
  D0 立即按「两侧实测已分叉」判负；改回后与 HEAD 逐字节相同。按 §3 的规矩，读数同步进两份
  `docs/08-审计读数`。
- 🩹 `skill/tests/bump_version.py`（冻结文件，本轮授权）不再改写历史表述：排除名单补
  `docs/体检报告.md` 与 `docs/日志旧版原文.md`，计划输出里把这两份并入「排除路径里仍有旧名 ·
  确认是历史表述而非活指向」逐条人工确认。**替换逻辑与 `CURRENT=` 豁免未动。**
  改前改后对拍（同一参数 `routing_v3.2 → routing_v3.9` 干跑）：改前 **26 个文件 / 117 处**、
  其中含那两份共 2 处当时的读数；改后 **24 个文件 / 115 处**，那 2 处不再被改。
- 🚪 **上面两条触碰闸门 2 个文件**：`all.sh`（加第 5 项命令与抬头注释「五项」）· `bump_version.py`（上一条的排除名单与文案）。
  不改会漏掉的东西，两条各有实测反例：① 只动一侧 profile 或改了 profile 忘了同步文档数字 —— 此前只能人肉全仓搜数字，
  本轮实测这类声明有 130 处、散在 13 篇文档；② 下次升版会把体检报告与日志旧版原文里「当时的读数」按新版本号改掉，
  那两份是证据、不是活指向。
  实测保护生效：不带 `--allow-gate` 让 `apply_edits.py` 改 `check_doc_readings.py` ⇒ 拒改、退出码 1、一个字节没写。
- ✏️ README 章节标题「两全其美，皆合心意」→「两全其美 · 皆合心意」。GitHub 的锚点由标题现算：逗号被吃掉、
  `·` 两侧的空格各留一个连字符 ⇒ 锚点从 `#-两全其美皆合心意` 变成 `#-两全其美--皆合心意`，三条活链接跟着改道
  （README 两枚徽章 · `surge/DetailsReadme` · `surge/docs/11`）；`surge/docs/07` 里那条历史记录提到的旧锚点
  按惯例不回溯，它是当时的事实。反证：把任一锚点退回旧写法，`check_links.py` 立即判「目标锚点不存在」。
  同一轮把「井然有序」那句 tagline 的斜体标记去掉（`*各司其职，各安其序，无隙可乘。*` → 纯文本），字未改。
- 🏷️ README 副标题「让 DNS 无处可漏」退役，换成「殊途同归 · 久用如一」（维护者从 20 条候选里点的，要的取向是：不提 DNS、不提具体内核名，将来加第三个内核也不用改口径）。斜体标记一并去掉。
  **没动**：页脚那句 `🐈 让 DNS 无处可漏 · MIT License`、`DNS / Zero Leak` 徽章、正文各节的 DNS 表述 —— 都等他点头。
  验收：`check_links` 与文档读数对拍全过（副标题不含读数，无连带）。
- 🔒 冻结名单 **9 → 10 个**：`skill/tests/check_doc_readings.py` 加进去（本轮授权）。
  理由就是 §2 第 5 条那条判据本身：文档读数对不上时，最省事的作弊不是改文档，是把它的 `RULES` 正则放宽、
  或把那一类归进"跳过"—— 它上线时跳过 47 处，这个数涨上去输出照样 10 条全绿，属于"看着全绿而其实失效"。
  `apply_edits.py` **不加**：它是动手改文件的，不判对错；越界与否由 `all.sh` 从 `git status` 算出来，
  跟它有没有被改无关 —— 冻它换不到检测力，只会让每次加特性都变成一次请示。
  名单同步 4 处（`all.sh` 的 `GATE` · `apply_edits.py` 的副本，两者由 A9 逐字对拍 · `AGENTS.md` §2 的文件清单 ·
  `docs/注意事项.md` 那句"改那 10 个"）；`all.sh` 末尾那句提示打印 `len(GATE)`，自动跟着变 —— 也就是**这一条又动了一次闸门文件 `all.sh`**（只加名单一行）。
  实测保护生效：不带 `--allow-gate` 让 `apply_edits.py` 改 `check_doc_readings.py` ⇒ 拒改、退出码 1、一个字节没写。
- 🧪 `skill/scripts/surge/audit_routing_coverage.py`（非冻结）补上内置集合的判定面：`SYSTEM` 过去没有内容快照，
  模拟匹配时**永远不命中**，懒人版删掉远程 Apple 全量集后就有探针必然判负。现在它按本仓
  `egern/apple_system.list` 近似内置 `SYSTEM`（联网取不到时静默退回旧行为，并打一行 `ℹ️` 说明是快照近似）；
  Apple 探针同时**分两套**：分流版 6 条、懒人版 4 条 —— 懒人版按设计不再接住 `developer.apple.com` /
  `gateway.icloud.com`，让它们走节点，不是把它们从断言里删掉。
- 📚 文档读数与活指向同步：两份 `docs/07-文件版本沿革`（升版段 + 历代版本表 + 懒人版段）、
  两份 `docs/08-审计读数`、`docs/规则集与来源` / `跨内核差异对照` / `注意事项`、`README` / `skill/README`、
  两份 `skill/reference/*/checker.md` 与 `public-repo.md`、两份 `DetailsReadme`、`surge/docs/04`·`06`·`11`、
  `egern/docs/04`·`05`。顺带修掉三处早已陈旧的读数（Egern 懒人版"4 组 / 9 条"、两处"23 个断言"、
  `audit_ruleset_refresh` 读数的 21/22 之差）。
- 🚪 **本轮触碰闸门 4 个文件**（`all.sh` · `surge/run.sh` · `surge/architecture.sh` · `egern/run.sh`）：
  其中 `CURRENT=` 那一行属 `bump_version.py` 的既定豁免；**超出豁免的还有三处纯注释 / 提示文案**
  —— `all.sh` 打印默认版本号、`architecture.sh` 里 3 条注释与断言消息里的版本号、`egern/run.sh:140` 的
  版本清单注释。**判定逻辑与断言条数未改**，但按 §2 第 5 条这属于要报备的部分，故在此写明。
- ⚠️ **订阅端要改地址**：`.../surge/profiles/routing_v3.2.min.conf` 与 `.../egern/profiles/routing_v3.2.min.yaml`。
  `v3.1` / `v3` 的文件仍在仓内可达，但已不是推荐版 —— 这是本项目**第三次**因升版让旧订阅地址指向旧内容。
- ✅ `bash skill/tests/all.sh` 复测：Surge **27** · Egern **50** · `.min` 对拍 **14** · 可移植性 **18** ·
  文档读数对拍 **10**，五项全绿。
- 📌 **订阅地址固定化**（同日第三轮，本轮的主改动；两内核各跟着一条，见上面两段）。`profiles/` 顶层从此**恒为固定名四件**，
  被替代的版本进 `profiles/config_old/`。「哪一版」这个承诺也从三处收成一处：从前 `surge/run.sh` ·
  `surge/architecture.sh` · `egern/run.sh` 各写一行 `CURRENT=routing_vX.Y`（改一漏二），现在只剩 profile
  第一行的 `#! version=routing_vX.Y`；`all.sh` 抬头那句「当前版」直接读 `routing.conf` 的头注，不再打印常量。
- 🗂 **归档不参与任何检查**：检查路径上的 glob 全是非递归 ⇒ `config_old/` 天然在场外，断言数**不再随版本累积**。
  读数随之变化：Surge 27 → **19**、Egern 50 → **18**、形态对拍 14 → **18**（4 对逐字相同 + 固定 14 条归档判据：
  V1–V6 ×2 + 跨侧 2 条，条数与归档份数无关）。可移植性 18 · 文档读数 10 不变。**判据含义一条没改**，少的只是存档版。
- 🔧 `skill/tests/bump_version.py` 重写为「归档 + 原地升号」：`--family routing|lazy` 先读两内核头注（缺一条或
  两边不一致就直接停），当前版四件**逐字节**复制进 `config_old/<家族>_v<旧号>.*`，两份完整版原地自增版本号
  （3.2 → 3.3，到 `x.9` 进位成 `(x+1).0`，只保留一位小数）并钉刷新秒数，再改全仓活指向。**订阅端从此不用换地址。**
  归档里已有同名文件时只承认一种情形：与当前版**逐字节相同**的升版前快照 ⇒ 复用不重复复制（本轮 lazy 的起点就是这样）；
  内容不同即「同号不同内容」，拒写并要求显式 `--to`。
- 🧷 `check_doc_readings.py` 两条判据跟着换口径：D8 允许 raw URL 落在 `profiles/`（必须是固定名四件之一）或
  `config_old/`；D9 从「三处 `CURRENT=` 一致」改成「头注即当前版 · 同族跨内核一致 · 固定名四件齐」。
- ⚠️ **一次性的代价**：带版本号的旧订阅地址（`.../profiles/routing_v3.2.min.conf` 那一批）从这次提交起 **404**，
  维护者已确认接受 —— 断这一次，换此后每升一版都不再断链。本段上一条「订阅端要改地址」从此作废。
- 🚪 **本轮触碰闸门 7 个文件**：`all.sh`（抬头改成读头注、删 `CURRENT=` 用法行）· `bump_version.py`（上一条的重写）·
  `check_min_pair.py`（接管固定名与归档的 14 条判据）· `check_doc_readings.py`（D8/D9 换口径）·
  `surge/run.sh` · `surge/architecture.sh` · `egern/run.sh`（`CURRENT=` 那三行退役）。
  不改会漏掉什么，逐条带实测反例：三个 runner 继续按 `routing_v3.2.conf` 找文件 ⇒ 固定名一落地就有整个阶段
  对不存在的文件 `continue`、静默少跑还报绿（正是这套检查自己防的那类假绿）。改后实测：把 `routing.conf` 挪走
  ⇒ `surge/run.sh` **退出码 2**；头注写成 `routing_v3.2.1` ⇒ V2 与跨侧一致两条同时判负；两内核头注一个 `v3.2`
  一个 `v3.9` ⇒ 跨侧那条判负；归档里删掉一份 `.min` ⇒ V5 判负；塞进一份高于当前版的归档 ⇒ V6 判负。
  `check_doc_readings.py` 若沿用旧版：拿它对拍本轮改后的树，**前置就退出码 2**（那句"三处 `CURRENT=` 找不到"），
  连读数都不再产出 —— 它必须跟着换口径，不是可选的同步。
- ✅ 验收：在临时副本里跑过**两轮真实升版**（`routing_v3.2 → v3.3`、`lazy_v1.0 → v1.1`），副本内 `all.sh` 五项全绿，
  顶层仍是四件固定名、`config_old/` 各多一版、头注自增到位、`.min` 对拍未被误伤；本仓 `bash skill/tests/all.sh`
  （含联网项）Surge **19** · Egern **18** · 形态对拍 **18** · 可移植性 **18** · 文档读数 **10**，五项全绿。
- 🧷 **`.min` 生成器进仓**：`skill/tests/make_min.py`（非冻结，同 `apply_edits.py` 的口径 —— 它动手改文件、不判对错）。
  补的是本仓最后一处手工同步：`.min` 从此不手抄。它 **import `check_min_pair.py` 的判据函数**
  （`normalize` / `TRAIL` / `WHOLE` / `head_version`），不复制规则 ⇒ **生成器与对拍器不可能各说一套**。
  Egern 侧是纯函数（去注释 + 规范空白，生成即过拍）；Surge 侧正文重算，另外**按锚点继承三类有语义的注释**
  （`# audit-waive:` 行、两条 `[Proxy Group]` 的「怎么加节点」），所以那行豁免注释不再需要手工补回。
  默认只出计划，`--apply` 才写盘；写盘**全成全不做**（先校验完所有继承注释，任一不成立就整个不写）；
  落盘前还有一次自证：把要写的内容再 `normalize` 一遍与完整版比对，不一致就退出。
  **不碰完整版、不碰 `config_old/`**（归档只读），`--selftest` **7 条**回归全绿。
- 🔧 `bump_version.py`（**冻结文件**，本轮授权）改三处。① **同号归档的语义按维护者拍的口径改成「保留已发布快照、照常升号」**：
  归档里已有同号且字节相同 ⇒ 复用；不同 ⇒ 打一句 ⚠️ 保留快照、**不覆盖**，线上那份改动随新版本出厂。
  ② 修一个**真 bug**：归档目标路径存的是仓内相对名，写盘时按**当前工作目录**解析 ⇒ 从仓外调用时
  「快照已存在」守卫**静默失效**，`--apply` 还会把归档写到仓外的野路径。现在统一按 `--root` 拼接，三条分支
  （无同号 / 同号相同 / 同号已漂）各实测一遍，退出码与打印逐条对上。③ 新增 `--changelog-stub`：
  输出一段贴得进根日志的骨架（日期段 + 升版行 + `make_min --apply` 行 + 留空的五处验收读数），
  **只出文本、不写文件**；不加 flag 一行不出，加了也不碰 `CHANGELOG.md` 一个字节。
- ✅ `V6` 从此是**设计出来的告警**而不是死路：改了已发布版 → `make_min --apply` 写线上、提示归档在场 →
  `V6` 判负一句「改了没升版」→ 跑 `bump_version.py` 升号，`V6` 自动转绿。此前它是死路（改后 `exit 1`，
  连 `--to` 也绕不过，因为目标名从旧号推导），维护者据此选了「保留快照」这一支。
- 📉 `docs/体检报告.md` 瘦身 **622 → 496 行**（去掉与根 `CHANGELOG.md` 重复的过程叙述 126 行：P1 落地表、
  收尾状态、提速 1–4、检查进仓、完全独立、换设备演练）。结论一条没丢：新增「过程记录的去处」一节，
  结论 → 现在写在哪个文件逐条列表；只在本篇出现过的三条事实（`__pycache__` 会污染逐字节比对、
  Egern 41 vs 46 的计数口径、短路径 junction 不是前置条件）留在原地；P10 / P11 两节整段保留。
- 📚 文档同步 `make_min.py` 与新的归档语义：`AGENTS.md`（§3 目录表的连带栏 + §5 升版流程）、
  `skill/README.md`（`tests/` 清单）、两份 `skill/reference/*/checker.md`、`skill/reference/surge/public-repo.md`
  那句「这行要手工补回」、`docs/注意事项.md` 那句「再把改动同步到 `.min`」、`surge/docs/04` 两处、
  `docs/跨内核差异对照.md` §8 第 7 条。
- 🚪 **本轮触碰闸门 1 个文件**：`skill/tests/bump_version.py`（上一条）。不改会漏掉什么，带实测反例：
  ① 路径 bug —— 在仓库外的临时副本里跑 `--apply`，改前会把归档写到**当前目录**下的野路径，
  且同号快照守卫一条都不触发（本轮三条分支的对拍就是修完才跑得出正确结论的）；
  ② 归档语义 —— 改前遇同号不同内容直接 `exit 1` 拒升，**已发布版改了就没法按正常流程升版**，
  只能手工挪归档；改后维护者的口径落地为「保留 + 升号」，`V6` 从误报变成有出口的告警。
- ✅ 验收（本轮改完后重跑，不是沿用上面的读数）：`bash skill/tests/all.sh` → Surge **19** · Egern **18** ·
  形态对拍 **18** · 可移植性 **18** · 文档读数 **10**，`ALL GREEN · 5 项检查通过`；
  `make_min.py --selftest` 7 条全绿。**没动**：任何 profile 的规则与分组、全部判据逻辑与断言条数、
  冻结名单（仍 10 个，`make_min.py` 刻意不冻）、`config_old/` 里的每一份归档字节。
- 🧭 `AGENTS.md` §4 加「换到一个新会话也只做三件事」（同日第五轮，维护者授权上线）：工作目录选在仓根 ·
  先读 §1–§2 与本日志最近一段 · 一个批次一件事做完就换会话。写的是**动作形状**，
  不含任何本机克隆路径 —— 路径与凭据一样属单机事实，不进仓。
  依据是这两天的实测账：机器时间 380.8 分钟里模型生成占 **88%**（1424 轮 × 平均 14.1 秒），
  工具执行只占 **6.9%**，上下文压缩 12 次 ≈ 19.5 分钟；按会话进度分档，薄档约 **10 秒/轮**、
  肥档约 **20.7 秒/轮** ⇒ 省时间的杠杆在轮次与上下文重量，不在"命令跑得更快"。
  **没动**：§1–§3 的判定纪律、§4 原有的换机器三件事、`skill/SKILL.md` 门面。
- ✂️ **「判据过了」与「这批落地了」拆成两档**（同日第六轮，维护者授权）：默认档末行不再一概说
  `ALL GREEN` —— 那三个字在 §1 里同时背着"五项判据过"和"三数全 0"两个意思，而 §1 的顺序是
  跑闸 → commit → push，**跑闸那一刻三数必然非 0**。实测反例：往 `skill/tests/` 扔一个未跟踪文件再跑，
  旧版输出 `未提交 1 个文件 … ALL GREEN · 5 项检查通过` 且退出码 0，与干净树的一模一样。
  现在默认档说「判据全过 · 但状态未落地（未提交 N · 落后 N · 未推送 N）」、退出码照旧 0；
  新增 `--landed` 跑在 push 之后，三数非 0 ⇒ **退出码 1**（复用 §1 已有的三档，不新增码 3）。
  `--landed` 重跑五项（只查 git 状态会造出"三数全 0 但这棵树从没跑过闸"的窗口），与 `--offline`
  在参数解析处即死判 2（离线时 Surge 侧实测少跑 4 条联网断言），无 `.git` / 无上游判 2。
  **它是按批开关、不是新默认**：「先改本地不提交不推送」那批按设计就该不跑它。两档都**不判**
  "有没有把垃圾文件扫进提交" —— 那由提交前点名 stage 挡，本脚本够不着。未知参数从此不静默吞。
- 🔎 判负输出：子项失败时先 `grep -nE '❌|Traceback|FAIL|[1-9] failed'` 点名失败行、无命中才兜底 `tail -14`。
  反例实测：把 Surge 阶段 1 一条 fixture 的期望码改错（临时副本，不碰仓内文件），
  旧版 `all.sh` 摘要里那条失败出现 **0** 次（末 14 行只剩阶段 6 汇总，要多跑一次 runner 才看见），
  新版出现 **1** 次并带行号 —— `4:ok_minimal.conf exit=0 ❌ 期望 1`。
- 🧷 `apply_edits.py --selftest` 的闸门名单对拍从「两处」扩成**真相 1 + 对拍 5**（新增 A13，12 → 13 条）：
  拿 `all.sh` 里现读出来的 `GATE` 当真相，去对 `AGENTS.md` §2 的名单块 + 三处写死个数
  （`AGENTS.md:50`「下面 10 个文件」· `docs/注意事项.md:46`「改那 10 个」· 本模块头注「现 10 个」）。
  文档侧**按集合比、不比顺序**：那个块是 5 行 × 每行 2 列的排版产物，实测块内行主序与 `GATE`
  在第 6/7 位天然互换，拿有序 `==` 裸比会让 A13 上线第一天就红给自己、还误报成"AGENTS.md 漂移"。
  槽位数与唯一性两条都要立（只比集合会放过"在册项原样 + 多抄一行"：11 槽 / 10 唯一 ⇒ 集合仍相等），
  这两条由 A13 自带的判别自证钉住。A9（代码 ↔ 代码）保持逐字有序不变。
  三条故障各自实测过：删掉块里一个名字 → 旧版 12 条全绿（漏）、新版 A13 红；
  `注意事项` 的「10 个」写成「9 个」→ 旧版全绿、新版 A13 红；只往 `all.sh` 加第 11 个 → A9 与 A13 各红一次。
- ✏️ 文档连带 4 处（同一口径写四处不如写一处，但这些都是**活指向**）：`AGENTS.md` §1 命令块 +
  "三数全 0"那句 + 退出码那句补「`0` 只代表五项判据过了，不含落地状态」；`docs/注意事项.md:46` 的
  「三数全 0」浓缩句；`:48` 那句「`all.sh` 全绿 → `git add -A && commit && push`」—— 它是同一个误读在
  文档里的孪生写法（它把"全绿"当成推送前件）；`docs/跨内核差异对照.md:232` 的「三个数全 0 才算同步」补
  「由 `--landed` 判」。`skill/README.md:54` 的自带回归数 12 → 13。**没动**：`git add -A` 那两处措辞
  （对外口径维持 `-A` + `.gitignore` 兜底）。
- 🚫 **`docs/体检报告.md:397` 那句「三个数全 0 才算同步」刻意不改**：本仓两个工具已把体检报告划成历史类 ——
  `check_doc_readings.py` 的 `HISTORY` 元组含它（整篇不扫，"旧数字在那儿是对的"），`bump_version.py:36`
  写着「每节写的都是**那一轮**的观测值，不是活指向」并用正则把它排除出自动替换。内证也对：它下一句的
  读数（Egern 46 / 形态对拍 12）只在 09-23 那轮成立，紧跟着就是带日期的第四轮小节。改它等于给证据打补丁，
  而 D 规则与升版脚本都不扫它 —— 那会变成一处"只有人记得"的隐形不一致。
- 🚪 **本轮触碰闸门 1 个文件**：`skill/tests/all.sh`（上面前三条都在它里面）。不改它会漏掉的具体文件与面：
  ① 未提交 / 未推送非 0 时它仍说 `ALL GREEN` 且退出码 0（已给实测反例）；② 判负时末 14 行看不见靠前的
  失败行（已给行号级反例）。`apply_edits.py` 不在冻结名单内（`CHANGELOG:117` 的理由照旧：它动手不判对错），
  所以 A13 那一条不构成越界。**没动**：五项判据本身、`GATE` 的 10 个成员、任何 profile 与规则集、
  `config_old/` 归档字节、`AGENTS.md` §2 的名单块。
- ✅ 验收（本轮改完后重跑）：`bash skill/tests/all.sh` → Surge **19** · Egern **18** · 形态对拍 **18** ·
  可移植性 **18** · 文档读数 **10**，末行走新措辞「判据全过 · 但状态未落地」；
  `apply_edits.py --selftest` **13** 条全绿。
- 🧰 **`all.sh` 加第 6 项「工具自检」**：新增 [`skill/tests/check_tools.py`](skill/tests/check_tools.py)（非冻结，
  与 `apply_edits.py` 同理 —— 它只报对错、不动手，但不在名单里也判不了别人）。4 条断言 = 三套自带回归
  （`make_min.py` / `apply_edits.py` / `surge/check_links.py` 各自的 `--selftest`）+ "全部被 git 跟踪的 `.py`
  都能编译"。治的是"检查器自己坏了没人知道"：改前编译面零判据、三套自测散在三个文件里要记三条命令。
  反例是现成的 —— 本批实施过程中就往 `audit_ruleset_content.py` 里掉进过一个语法错误（替换用的 JSON 漏 escaping
  的 `%%`），编译那条当场点名，人还没跑到闸就先红了；那条 SyntaxError 后来成为 T1 有牙的证据。
- 🧊 **规则集缓存从此会过期**：取远端规则集的三处（`skill/scripts/surge/audit_ruleset_content.py` ·
  `skill/scripts/egern/audit_routing_coverage.py` · `skill/scripts/egern/audit_ruleset_noresolve.py`，**都非冻结**）
  从前只看"文件在不在"（改前全仓 grep `mtime` / `max_age` / `TTL` 零命中）⇒ 联网阶段可能拿半年前落下的一份判"通过"，
  而输出里那个（缓存）看不出新陈。现统一 7 天窗口：窗口内直用 · 过窗先重下 · **重下失败才退回旧那份并逐条出声**，
  末尾各打一行「缓存读数：N 个规则集 —— 新下载 a · 窗口内直用 b · 过期退回 c」。
  过期退回**只报不判**（与闸门触碰同口径：那不是配置错了，是这台机器此刻下不动）。
  实测：把缓存里一份的 mtime 推到 30 天前 —— `--offline` 下两份 Egern 脚本各出「缓存已过 7 天窗口」、
  联网重跑变「新下载 1 · 过期退回 0」；Surge 侧用打桩 `urlopen` 逐分支验过 `fresh / cache / stale`，
  其中 `stale` 那次网络调用数为 1、正文仍是旧那份。`--max-age-days` 只在 Surge 侧加（负数 = 不过期、0 = 全部重下），
  Egern 两脚本要重下就直接删缓存或联网跑。
- 🩹 `skill/tests/check_min_pair.py:115`（**冻结**，本轮授权）的 V3 是一条**恒真断言**：消息写着"存在"，
  判据位上是一个字面量 `True`，而缺目录由上面的 `isdir` 分支单独兜 ⇒ 归档被挪空时它照样绿。现按 `bool(names)` 判。
  改前改后各实测一次：把 `surge/profiles/config_old/` 清空 ⇒ 改前 `✅ surge V3 归档目录存在（0 个文件）` ·
  18/0 · 退出码 0；改后同条件 `❌ …（0 个文件）· 空归档：…` · 17/1 · 退出码 1；恢复后回到 18/0。
- 🖥 三个没有编码兜底的脚本（`apply_edits.py` · `check_portability.py` · `check_doc_readings.py`）补上
  `bump_version.py` / `make_min.py` 同款 `reconfigure(encoding="utf-8", errors="replace")`。
  为什么值得单独一条：中文 Windows 的管道默认 GBK，脚本 print emoji 就 `UnicodeEncodeError` ⇒ 退出码 1，
  与"期望判负"的用例**撞码** ⇒ 假绿；而 `all.sh:44` 那个 `PYTHONIOENCODING` 只护得住从 `all.sh` 进来的调用，
  文档里教的"单跑某一条命令"没有那层护。
- 🧷 文档读数对拍 **10 → 11 条**：新增 `D10` 管当前版 profile（含 `.min`，`config_old/` 天然在场外）里的
  `# audit-waive:` 行，口径**逐字抄自消费方** `skill/scripts/surge/check_surge_dns.py:load_waivers()` 的正则。
  三种坏法逐个拿打桩文件实测（每条同时打印审计器真正读到了什么）：
  ① 用 `//` 起头、或编号与理由之间没空格 ⇒ 审计器一条都读不到 ⇒ 判负；
  ② `# audit-waive: 2` 光有编号 —— 消费方的 `\s+` 会吃掉换行，所以它**确实生效了**，只是报告里
  「已豁免（profile 内声明）：」后面空无一物，"留痕"那半没了 ⇒ 判负；
  ③ 同文件两条同编号 —— `_waivers[cid] = 理由` 后写覆盖先写，审计输出与只有一条时逐字相同，
  **不跑这条判据永远不会有人发现** ⇒ 判负。当前真实读数：4 行 / 4 个文件 · 零判负。
  刻意不判两条：编号是否连续（删一条豁免不该逼后面重编号）· 是否落在审计器现有检查号区间内（那要把判据钉在
  审计器源码上，检查号一加一删就误伤）。文档连带 4 处：`AGENTS.md` §1 那行 · `skill/README.md` 的命令行注释 ·
  两份 `docs/08-审计读数` 的「固定 10 条（D0–D9）」。
- 🚪 **本轮触碰闸门 5 个文件**：`all.sh`（第 6 项命令 + 抬头「六条命令」）· `check_min_pair.py`（V3 那条）·
  `check_doc_readings.py`（D10）· `check_portability.py`（编码兜底 6 行）· `bump_version.py`（升版桩里
  「五项 TOTAL」→ 六项）。同样加了编码兜底的 `apply_edits.py` **不在名单内**，不构成越界。
  每条"不改会漏掉什么"都带实测反例，列在上面四条里。**没动**：`GATE` 的 10 个成员、五项判据本身的口径、
  任何 profile 与规则集、`config_old/` 归档字节。
- 🚫 `check_tools.py` **没有**加进冻结名单：加进去是 10 → 11 的连锁（`all.sh` 的 `GATE`、`apply_edits.py` 的 A9/A13
  与 5 处文档锚点都跟着动），而它自己不判配置内容 —— 这条留给维护者拍，本批不自作主张。
- ✅ 验收（本批改完后重跑，不沿用上面的读数）：`bash skill/tests/all.sh` → Surge **19** · Egern **18** ·
  形态对拍 **18** · 可移植性 **18** · 文档读数 **11** · 工具自检 **4**，六项全绿 · 11s。
- 🔢 **检查项 6 → 7：新增 `skill/tests/check_assert_counts.py`** —— 把文档里写死的「19 断言 / 18 断言」
  跟**本轮**六个 TOTAL 对拍。为什么单独立一项而不并进 D 规则：`check_doc_readings.py` 头注写着
  「判据 / 回归的断言数不判 —— 那要真跑测试才有值，递归且不划算」，这一项不推翻它，而是把那个输入
  从外面喂进来：`all.sh` 跑完前 6 项手里就有六个 TOTAL，按 `surge=19 egern=18 …` 传进第 7 项，
  **它自己不跑任何测试**（不递归）。四条判据固定：C1 Surge 侧 · C2 Egern 侧 ·
  C3 认不出归属的并排声明 · C4 判别自证。C1/C2 在「命中 0 处」时判负 —— 文档一处都不许诺 ⇒ 不是没漂移，是判据空转。
- 📏 覆盖面实测：**13 处声明 / 12 行**（README 门面表与 `docs/跨内核差异对照.md` 各占两格），
  扫 39 篇 `.md`、历史类整篇不扫（`CHANGELOG` / `体检报告` / `日志旧版原文` / `docs/07`）。
  只判**总数**：`surge/docs/08` 那张逐阶段表、`run.sh` 注释里的「3 个断言」不钉死数（加一条断言就要改一整张表，
  且一行只覆盖一个阶段）；这类"没判到"照 D 规则的口径在末尾报「跳过 3 处」，不静默。
  总数式怎么认出来：数字出现在「阶段」**前面**（`6 阶段` / `六个阶段` / `两阶段`）才算，
  于是 `阶段 1（… = 10 断言）+ 阶段 2（…）` 与 `共 3 条断言` 都进不来；
  `DNS 段已被阶段 3 断言为逐字相同` 那句里的「断言」是**动词** ⇒ 再看「阶段」前面有没有数词才能分开。
  为把 `skill/README.md:51` 那句（`阶段 1 · …；阶段 2 · … = 18 断言`，总数式认不出）纳进来，
  把它改写成 `两阶段 · 18 断言（阶段 1 · 5 fixture ×2；阶段 2 · 顶层固定名四件 ×2）` —— 信息一字未丢。
- 🧭 归属先问**表格列**（往上找表头，认「哪一列在说哪一侧」），再退到格子文本 / 整行 / 文件路径。
  这一层是实测逼出来的：不认列时把 README:79 两格的 19/18 整整齐齐互换，判据**照样绿**（两个数都还在本轮实测里）；
  认了列之后互换必红 —— README:79 与对照表:110 两处各自实测过一遍，红在 C1 + C2 两条上。
- 🔌 `--offline` 档**不调**第 7 项：离线时 Surge 侧实测 **15**（少跑 4 条联网断言），与文档的联网口径是两个数
  ⇒ 比了必假红；而"跳过"也不能算成一条通过（那是本仓忌的假绿），所以只印一行 `↷ … 跳过：离线档 Surge 侧实测 15`、
  **不进项数**（末行仍是「6 项」）、退出码仍是 0。`--offline --landed` 早在参数解析处就 exit 2 ⇒ 这一档不需要第三态。
  前 6 项里任何一项没印出 TOTAL ⇒ 第 7 项拿空值当**前置不达标**（exit 2），不拿缺失值当 0 去对拍。
- 🚪 **本轮触碰闸门 2 个文件**：`skill/tests/all.sh`（第 7 项 + `item()` 记 `LAST_NUM` + 抬头「六条命令」→ 七条）·
  `skill/tests/bump_version.py`（升版桩「六项 TOTAL ＿＿×6」→ 七项 ×7）。不改它们会漏掉的具体面，各带实测反例：
  ① 只把 `README.md:79` 的 19 改成 20 ⇒ **旧六项全绿、退出码 0**（一条判据都没碰过这个数），加第 7 项后 C3 红；
  ② 只改 `egern/docs/08:48` 的 18→17 ⇒ 旧六项全绿，新 C2 红（红在 Egern 侧，不牵连 Surge）；
  ③ 把 Surge 侧 6 处声明全改成「六阶段回归」这种没数的写法 ⇒ C1 报「命中 0 处 ⇒ 判据空转」而不是绿；
  ④ 桩里那个「六项 TOTAL ＿＿×6」是**下一次升版的交底模板**，不改它 = 每轮升版照抄一个少一项的验收行。
  **没动**：`GATE` 的 10 个成员、前六项判据本身的口径、任何 profile 与规则集、`config_old/` 归档字节。
  新脚本 `check_assert_counts.py` 与上一批的 `check_tools.py` 同理**不加进 `GATE`**（加进去是 10 → 11 的连锁，
  要动 `AGENTS.md` §2 的名单块与三处写死个数），这条留给维护者拍。
- ✅ 验收（本批改完后重跑）：`bash skill/tests/all.sh` → **19 · 18 · 18 · 18 · 11 · 4 · 4**，七项全绿 · 12s；
  `bash skill/tests/all.sh --offline` → 前六项 **15 · 18 · 18 · 18 · 11 · 4** + 第 7 项出声跳过 · 末行 6 项 · 退出码 0。
- 🔧 **工具自检判据 4 → 6：`check_tools.py` 加 T5①②（顶层死绑定扫描）** —— 补 T1 的那半边：
  可编译只保证"语法还读得动"，判不到"顶层绑了却再没人用的名字"。首跑实测 **26 个被跟踪 `.py` 里 9 处判死**
  （3 处未用 import + 6 处死常量），同批人工修掉：删 8 处、留 1 处记名（`APPLE_PROBES` 是「兼容旧提法」的别名，
  **删否点名的动作归维护者**，本批只给它加 `# t5-keep: …`）。删除的 8 处逐条：
  `skill/tests/make_min.py`（未用的 `import re` 与 `ALL_SH`）· `surge/check_surge_dns.py:28`（未用 import
  `DOMESTIC_RESOLVER_IPS`，同块的 `FOREIGN_RESOLVER_IPS` 在用）· `surge/audit_routing_coverage.py`
  （未用 import `parse_ruleset`、死常量 `IP_RULE_TYPES`）· `egern/audit_ruleset_noresolve.py:54`（`IP_TYPES`）·
  `surge/_surge_common.py:158-159`（`_IP4_CIDR_RE` / `_IP6_CIDR_RE`，两个共享 helper 从没被任何一侧 import 过）。
  定义家不塌：`DOMESTIC_RESOLVER_IPS` 在 `_surge_common.py` 自己文件内 :203/:226 仍在用 ⇒ 删 importer 不会
  第二轮红给自己（这条是上一轮"级联红"担心的那个点，实测过才动手）。
- 🧭 T5 的口径写死在 `check_tools.py` 头注里，四条活路各有实测救回数：本文件内有 `Load`（主判据，走 AST 不走文本）·
  `# t5-keep: 理由`（理由为空**不算记名**，实测仍红）· import 的名字在源模块顶层被裸调用（编码垫片，实测救回
  **7 处** `force_utf8_stdout`）· 常量全文件字面出现 ≥2 次放过（误差方向固定在漏报；代价照实记：
  `_egern_common.py:98 ep_ip` 字面 4 次而全仓无人 import ⇒ 它点不亮，那是**口径选择**不是漏了）。
  为什么必须按"文件内"算而不是全仓 grep 词频：`IP_RULE_TYPES` 在 `egern/check_egern_dns.py:46` 定义并在 :377 在用，
  `surge/audit_routing_coverage.py:174` 那份同名同形却无人用 —— 按词频判会把它读成活的。
  判别力用 12 个内存样本验（不碰仓库文件，真仓里造红它的 fixture 就得改在仓代码，那是闸门最不该干的事）：
  **该红的 5 处一处不落、该放过的 7 个样本一个不误报**；def/class 与 `try:` 块里的绑得不进面。
- ↷ `apply_edits.py --selftest` 的 A9 / A13 改成**第三档**：读不到真仓文件时从前是 `ck(…, True)`，
  环境不对也能拿一张"闸门名单一致"的合格证。现在印 `↷ …（没跑成 ≠ 跑绿，也不算判负）`，
  **不进 passed、不进 failed**，末行追加 `· 跳过 N 条`。跳过数写在 TOTAL **后面**而不是并进那两个数，
  因为 `all.sh` 的 `item()` 与第 7 项按 `TOTAL: N passed, M failed` 逐字取数，并进去会读成"少跑了一条"。
  实测反例：把 `apply_edits.py` 单独复制到没有 `all.sh` / `AGENTS.md` 的目录跑 ⇒ 现在
  `TOTAL: 11 passed, 0 failed · 跳过 2 条`，**改前同一棵树印的是 `13 passed, 0 failed`**、退出码一样是 0。
- 📄 连带活文档三处：`AGENTS.md` §1 七项里"工具自检"那句补上死绑定与「固定 6 条判据」·
  `docs/注意事项.md` 同一句 · `skill/README.md:54` 那句「apply_edits 自带回归…**不参与 all.sh**」
  是上一批（`check_tools.py` 进闸）之后就已经假掉的读数，按现状改成「由 all.sh 第 6 项串跑」。
- 🚪 **本轮触碰闸门 0 个文件**（全非冻结，`GATE` 的 10 个成员一个没动）。留下一条已知偏窄的读数不改：
  `all.sh` 第 6 项那行标签还写着「工具自检（自测+可编译）」，它现在多做一件"顶层死绑定"——
  改那行要动冻结文件 ⇒ 留给下一次本来就要动 `all.sh` 的批次顺带，不为一句标签单独开一次请示。
- 🐛 顺手实测到一处**没修**的运行时崩（记名等点名）：`skill/scripts/egern/probe_dns_endpoints.py:30` 行尾的
  `# noqa: E402` 把下一行的 `import sys` 一起吃进了注释 ⇒ 第 29 行 `sys.path.insert` 当场
  `NameError: name 'sys' is not defined`（实跑 `python … probe_dns_endpoints.py --help` 复现，一处没修成 4 处用到：:29/:124/:144/:184）。
  T5 判不到它（那是"绑了没人用"，方向相反），T1 也判不到（语法完好），而闸永远不执行这个脚本 ⇒
  要判这一类得再加一条"用了没绑"。粗扫 26 个 `.py`：剔掉 `__file__` 这类隐式名之后**只有这一个文件**中招。
- ✅ 验收（本批改完后重跑）：`bash skill/tests/all.sh` → **19 · 18 · 18 · 18 · 11 · 6 · 4**，七项全绿 · 11s。
- 📥 **三份手抄的取件逻辑收编成一处**：`skill/scripts/egern/_egern_common.py` 新增 `fetch_cached()`
  （窗口判据本体 **35 行一处**），三个消费方各留一层薄适配器（13 / 7 / 23 行，只负责自己那套出声措辞
  和行内标签），UA 与超时按原样传进去（`egern-routing-audit/1.0` · 90s / `egern-dns-audit/1.0` · 60s ×2）。
  改前三份分别长 34 / 26 / 21 行、各抄各的：`audit_routing_coverage.py:78` · `audit_ruleset_noresolve.py:61` ·
  `profile_ruleset.py:56`。行数几乎没省（81 → 78），省的是**口径**：三份共用同一个缓存目录
  （`egern-ruleset-cache`）却两套判法——前两份判 7 天窗口，第三份只判"文件在不在"。
- 🎯 这个混读的具体面，拿同一份陈旧缓存跑过对照（把 `%TEMP%\egern-ruleset-cache\x.list` 的 mtime 改成
  10 天前，再用 `git show HEAD:` 取改前的脚本原样跑一遍）：
  改前 `profile_ruleset.py` 印 `取法: 缓存 …`（判成命中、不出任何声）⇒ 改后印
  `取法: ⚠️ 缓存已过 7 天窗口（重下失败：…）⇒ 以上按陈旧那份判 …`。
  ⇒ 从前"条目类型分布 / 有没有裸 IP"这类结论可以整个落在一份没人知道多久的清单上。
  三条实现约束按原样搬，没借收编偷偷改行为：**存在且非空**才算命中、过窗**先试重下**失败才退回、写盘固定 LF。
- 🔀 顺手修一处**说错成因**的措辞：`audit_ruleset_noresolve.py` 的过期那行从前一律写"且重下失败"，
  而 `--offline` 档根本没尝试重下 ⇒ 现在按 `a.offline` 分开印，实测
  `⚠️ 缓存已过 7 天窗口，--offline 不重下 ⇒ 以上按陈旧那份判`（同一条 `stale` 有两种成因，只报一种就是假信号）。
- 🧪 六条来源分支逐条实跑：`fresh`（联网重下）· `cache`（窗口内直用）· `stale`（离线不重下）·
  `stale`（重下失败退回）· `miss`（离线无缓存 ⇒ `缓存未命中（--offline）`）· `error`（连不上 ⇒
  noresolve 侧仍译成 `FAIL <原因>`、行内印「取失败」）；`profile_ruleset.py` 的本地路径分支照旧（`本地文件`）。
  整份 profile 的联网读数回归：`audit_routing_coverage.py egern/profiles/routing.yaml --offline` ⇒
  22 个规则集 —— 窗口内直用 21 · 过期退回 1 · 取不到 0。
- 🚪 **本轮触碰闸门 0 个文件**（全非冻结）。**没动**：surge 侧 `audit_ruleset_content.py` 那份 fetch
  （它多三个开关 —— `--max-age-days` 可调窗口 / `force` 强重下 / `cache_dir` 入参，把 Egern 写死 7 天的
  口径套上去是削能力，跨内核共用一份是另一件事）· 任何 profile 与规则集内容 · `config_old/` 归档 ·
  `GATE` 名单。`_egern_common.py` 122 → 186 行。
- ✅ 验收（本批改完后重跑）：`bash skill/tests/all.sh` → **19 · 18 · 18 · 18 · 11 · 6 · 4**，七项全绿 · 13s。
- 📌 **断言数对拍判据 4 → 5（C5）**：`check_assert_counts.py` 钉住「文档写给 `check_tools.py` 的
  「固定 N 条判据」== 本轮 tools 实测」。治的洞是复测量出来的：`all.sh` 第 7 项一直收着 `tools=` 这个数却
  无人比 —— 喂 `tools=7` 而 `AGENTS.md:37` 写 6，第 7 项照绿（`KERNEL_KEYS` 只有两侧内核，工具自检的条数
  不在归属面）。锚点**按行取**（数字与脚本名须同一行；文档重排时以「命中 0 处 ⇒ 判据空转」出声，不拿 ±1 行
  窗口猜归属）；缺 `tools` 值按前置 exit 2，不拿缺失值空转。判别样本四条走内存 fixture（C4 先例）：
  同数换措辞不红 · 改一个数必被抓 · 写着 `check_assert_counts.py` 的行不归给 tools · 无脚本名的
  「固定 9 条判据」不归进来。**它不钉自己的 5**（判据判自己是递归）—— `AGENTS.md:38`「固定 4 条判据」
  本批手工同步成 5；`portability=18`（活文档 3 处）与 `doc_readings=11`（1 处）是同类未钉，留维护者拍。
  **没动**：C1–C4 口径与命中面（改前改后 C1 命中 8 · C2 命中 6 逐字一致）。
  验收：漂移注入实测 `❌ C5 … AGENTS.md:37 文档写 6，实测 tools=7` 退出码 1；缺值档 `❌ 前置` 退出码 2。
- 🔍 **工具自检判据 6 → 7（T6「用了没绑」）**：`check_tools.py` 补 T5 的反方向 —— **整文件任何位置**
  都没绑过的 `Load` 名判死。上线由头是那条记名的运行时崩：`probe_dns_endpoints.py:30` 的 `# noqa: E402`
  把注释尾巴上的 `import sys` 一起吃掉，:29 `sys.path.insert` 实跑即 `NameError`（改前复现）——
  T1 判不到（语法完好）、T5 判不到（方向相反），而闸从不执行这个脚本。口径：绑的采集走全文件
  `ast.walk`（不像 T5 只看第一层）、内建名与 `__` 围裹的隐式名不进面、含 `import *` 的文件整份跳过**并出声**、
  `exec`/`globals()` 注入判不到 ⇒ 只漏报不误报（与 T5 同向）。26 个被跟踪 `.py` 对账：改前命中 **1** 处
  （正是 probe:29 的 `sys`）、其余 25 个零误报、无 `import *`、无读不懂文件；`import sys` 拆回 :22-26
  import 组单行（`# noqa: E402` 留在 from-import 行）后复扫 **0** 命中，不留哑弹；probe 改后实跑表头正常
  打出（`--help` 被当查询目标解出 DNS FAIL 属脚本自身设计，不是崩溃类）。文档连带 1 处：`AGENTS.md` §1
  「固定 6 条判据」→ 7 —— 这行正被上一条的 C5 钉着，本批实测咬合。**没动**：T1–T5 口径、任何 profile 与
  规则集、闸门名单（`check_tools.py` 此刻仍未冻，冻它走下一批）。
  验收：`bash skill/tests/all.sh` → **19 · 18 · 18 · 18 · 11 · 7 · 5**，七项全绿。

---

## 2026-09-23

### Egern

- 🧬 `lazy.yaml` 补上分流版 v3 的三项：`dns.forward` 扩为四层（白名单 → 两条广告清单 `reject` → 兜底）、
  `rules` 补 `Private`（`private.txt` → `DIRECT`）、`AI` 组 `flatten: true`。头注"dns 段与 `routing_v2.4` 逐字相同"
  按现状改写。实际后果：广告域名改在**解析阶段**拒答，与 Surge 懒人版的 `pre-matching` 一致。`.min` 重新生成。
- 🗑 同日第二轮：`lazy.yaml` 移除 `Final` 组，兜底 `default.policy` 直写 `Proxy` —— 分组 4 → 3，规则仍 10 条，
  `name: Final` 保留（官方定义它是日志与调试用的标签）。依据官方文档：`policy` 可填内置策略 / 服务器名 / 组名，
  内置策略只有 `DIRECT` 与 `REJECT`，`Final` 不是关键字。**分流版仍保留 `Final` 组**（面板要能换兜底去向）。
- 🔁 新建 `routing_v3.1{,.min}.yaml`：22 条 `rule_set` 全部显式 `update_interval: 604800`（一周），
  分组 / 规则 / `dns` 段逐字未动。⚠️ 订阅端改用 `routing_v3.1.min.yaml`；`routing_v3` 留作存档可订阅。
- 🧪 新增 `audit_ruleset_refresh.py`（第 10 个脚本）；`audit_dns_forward.py` 判据由"`value` 全体单值"放宽为
  「非 `reject` 去向单值且等于兜底组」（`reject` 是终止动作，可与兜底并存），5 个 fixture 回归守住。
- 🔢 读数：`check_egern_dns lazy` 0 high / 2 low / 24 ok；`audit_ruleset_noresolve` 对 lazy 6 → 10 个规则集；
  `routing_v3` / `v3.1` 实测 **25** 个规则集（`v1`~`v2.4` 为 21）；白名单实测 43 条（原写"42 条 DOMAIN"两处都不对）。
- 🩹 两处文档错误**查出未改**（待拍板）：`DetailsReadme` §1.1 与 `docs/04` §6 把 `default_proxy_group`
  讲成"默认出口组"，官方定义是「添加代理时自动加入的策略组」，与兜底无关。配置本身该留。

### Surge

- ✏️ `lazy.conf` 一处注释与值矛盾：`proxy-test-url` 上方写"用国内 204"、值是 `www.gstatic.com`。
  逐字采用 v3.1 那段口径；配置本体零改动（注释不进 `.min`）。
- 🩹 四处陈旧表述校正：`docs/04`（两处）· `docs/06` · `docs/11` 称 `[Rule]` 段有 3 条游戏机
  `DOMAIN-SUFFIX` 规则 —— 四份 profile 实测都没有，这些主机名只在 `always-real-ip` 里。
  `docs/07` 那句"当时删了 3 条"是事实记录，不改。
- 🔁 新建 `routing_v3.1{,.min}.conf`：20 条远程规则集显式 `"update-interval=604800"`，组 / 规则 / DNS 段逐字未动；
  `lazy` 原地覆盖（7 条钉住）。⚠️ 订阅端改用 `routing_v3.1.min.conf` —— 这是**第二次因改名让旧地址失效**。
- 🧪 新增 `audit_ruleset_refresh.py`（第 5 个审计脚本）：非正值 = HIGH，缺字段或偏离约定值归「约定」档，
  `--strict` 才判负。

### 共享层

- 🏗️ 本仓由 `RiverFlowsInUUU/Surge` 与 `/Egern` 合并而成：`icons/` · `docs/` · `skill/SKILL.md` 为共享层，
  `surge/` `egern/` 各持 profile / docs / DetailsReadme。**前身仓未作任何改动**、本仓不引用它们。
  ⚠️ 新写地址一律用 `RiverFlowsInUUU/Self-Configuration`。
- 📄 新增共享四篇：跨内核差异对照（主文档）· 规则集与来源 · 注意事项 · 图标与许可；
  单一技能入口 `skill/SKILL.md` 先判内核再进 A/B 分支，两侧正文逐字保留（只降级标题、改写路径、
  以及登记在案的外链修订），代码块与源文件字节一致。
- 🔄 装配改写：raw URL 换本仓名、616 处图标引用改指共享 `icons/`、脚本与测试分道
  `skill/{scripts,tests}/{surge,egern}/`、正文路径提及 157 处补内核段。
- ✅ 合并验收：内容零漂移 —— 20 份 profile / 26 个图标 / 15 个脚本 / 9 个 fixture 与源仓逐字节相同；
  断链 52 处修至 0、失效锚点 3 处修好（现 42 篇 / 44 锚点全通过）；脱敏复核只剩占位符 `REPLACE_WITH_YOUR_TOKEN`。
- ⚠️ 合并当轮**未跑** Python 回归（装配环境无解释器），当时只声明静态检查通过。环境要求 Python 3 + PyYAML
  写进 `docs/注意事项.md`，联网阶段可 `SKIP_NET=1` 跳过。
- 🩹 合并后复核（只落文档层）：5 组读数按 HEAD 实测校正（图标引用 618 → 616 处等）；`skill/SKILL.md` 四条
  404 外链改指 Surge 手册改版后的新章节、社区参考实现搬家到 `doc.repcz.link/egern/`（八条链接实测 200）；
  去掉两份内嵌假头、检索线索并入一条 `description`（1000 字符 / 56 条）；`.gitignore` 补私钥兜底（刻意不含 `*.crt`）。
- 🐛 上面假头的根因不在源仓：装配脚本剥头部的正则按 LF 写，Windows `core.autocrlf=true` 检出 CRLF ⇒ 正则失效。
  脚本改为先归一化换行，重跑与当前树逐字节一致。
- 🧱 与两个前身仓彻底脱钩：逐字节对账、"旧仓是否被改动"的红线检查、仓外闸门、`SKILL.md` 装配脚本全部退役。
  立场：只要一项默认检查需要别的仓库在场，它就不该存在。规则转录进
  [`docs/技能包合并与自包含.md`](docs/技能包合并与自包含.md)，体检记录进 [`docs/体检报告.md`](docs/体检报告.md)
  （含三处被实测推翻的原结论）。
- 🧮 新增根 `.gitattributes`：`* text=auto eol=lf`。病根是安装器把 `core.autocrlf=true` 写进系统级配置 ⇒
  同一 commit 在 Windows 落盘 CRLF。⚠️ 老克隆 `git pull` 后磁盘仍是 CRLF 而 `git status` 干净（隐形差异），
  一次性修复：`git rm -r --cached . && git reset --hard`。
- 🧪 新增 `skill/tests/check_portability.py`（`all.sh` 第 4 项，固定 18 条：行尾 / BOM / shebang / NFC /
  非法字符 / 保留设备名 / 大小写折叠冲突 / 机器消费路径纯 ASCII / 单机残留 …），刻意不随文件数增长；
  反例实测能判负。同时修掉 `E2` 一个真盲区：`LICENSE` 这类无扩展名文本从没进过字节判据。
- 🔁 `all.sh` 从 3 项变 4 项，末尾报 `未提交 N · 落后 N · 未推送 N` 与「闸门有没有被触碰」。
  新增 `check_min_pair.py`（Egern 侧两版形态此前从没对拍过整份配置）与 `bump_version.py`；
  「当前推荐版」收成三处 runner 各一行 `CURRENT`，升版从改十几处变成改一行 ——
  配套：`$CURRENT` 指向不存在的 profile 就**退出码 2**（此前静默少跑整阶段、输出照样全绿）。
- 🩹 中文 Windows 的「假绿」：控制台默认 GBK，脚本一 `print` emoji 就崩成退出码 1，而 `bad_*` fixture
  期望的正是 1 ⇒ 解释器坏了被计成"判负通过"。共享模块 import 时钉 UTF-8，两个 runner 另设
  `PYTHONIOENCODING=utf-8`，不 import 共享模块的 6 个脚本逐个接上垫片。
- 🧷 `architecture.sh` ④ 组序承诺的唯一真值，从"仓库外的 Egern v3"改为本仓
  `egern/profiles/routing_v3.1.yaml` 的 26 组；仍是写死的承诺值，不运行时推导。
- 🤖 新增 [`AGENTS.md`](AGENTS.md)：给 agent 的开工说明 —— 唯一验收一条命令、五条硬约束、
  冻结 9 个闸文件与请示门槛、换设备三件事。按真·新设备链路走过一遍：全新克隆 → 跑 `all.sh` →
  试改不推 → 内联凭据推回 → 线上文件实测不含 CR。
- 🚫 依旧不挂 CI / workflow：进仓的只有本地可执行的检查入口。

---

## 历史

合并前的完整迭代史保存在 `surge/CHANGELOG.md` 与 `egern/CHANGELOG.md`，2026-09-24 两文件删除、
正文逐字并入各自内核的 [`surge/docs/07`](surge/docs/07-文件版本沿革.md) ·
[`egern/docs/07`](egern/docs/07-文件版本沿革.md) 末节，包括其中的旧文件名与旧仓库名表述。

> ⚠️ 这类历史条目里的「新写地址请用 `.../RiverFlowsInUUU/Egern/...`」**已经过期** ——
> 回溯改写会破坏它的证据价值，所以只更正一次：**新写地址一律用 `RiverFlowsInUUU/Self-Configuration`**，
> 前身两仓仅作来源说明、后续可能转为私有。
