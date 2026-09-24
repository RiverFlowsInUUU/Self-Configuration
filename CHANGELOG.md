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

### Egern

- 🩹 订正 2026-09-23 查出未改的那处文档错误：`default_proxy_group` 按官方定义写作「添加代理时自动加入的策略组名称」
  （顶层字段全表 `egernapp.com/docs/configuration/example`），不再叫"默认出口组 / 默认策略组"，并写明它与兜底无关 ——
  兜底只有 `rules` 末尾那条 `default`。改的是 `DetailsReadme` §1.1（这条同时从「C. DNS 与默认出口」挪进「A. 全局开关 /
  辅助项」）与 `docs/04` §6。配置零改动，`Proxy` 这个取值保留（懒人版 `Proxy` 组为空，正靠它接住手动添加的节点）。

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
- ✅ 两轮各自跑过 `all.sh`，四项全绿。

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
