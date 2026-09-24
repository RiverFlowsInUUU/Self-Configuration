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
