# 🤖 AGENTS.md · 给 AI agent 的开工说明

> 本仓是一个**公开的配置模板仓**。本文件面向 agent，不是给人读的，所以只列约束和动作。
> 人读的详解在 [`docs/`](docs/)，配置领域知识在 [`skill/SKILL.md`](skill/SKILL.md)。

## 0 · 先分清你在做哪类任务

| 任务 | 入口 | 有没有闸 |
|:-----|:-----|:---------|
| **A. 改这个仓**（profile / 脚本 / 文档 / 规则集指向） | 本文件 + [`docs/注意事项.md`](docs/注意事项.md) | **有**，见 §1，改完必须跑 |
| **B. 帮用户排查真实设备的 DNS / 分流问题** | [`skill/SKILL.md`](skill/SKILL.md)（按内核分支，别凭记忆答语法） | 无，但**先定内核**：Surge 与 Egern 模型不通用 |

## 1 · 改完的固定动作（这是本仓唯一的验收）

```bash
bash skill/tests/all.sh            # 七项检查；离线用 --offline（第 7 项出声跳过，见下）
bash skill/tests/all.sh --landed   # 提交并推送之后再跑一次：三数在这档计入判负
```

末行的三个数就是「线上线下是否一致」。**默认档只报这三个数、不据它判负** ——
跑闸的那一刻改动通常还没提交，三数非 0 说明不了问题；判它的是 `--landed`（非 0 ⇒ 退出码 1）：

```
未提交 0 个文件 · HEAD=<sha> · 上游 origin/main：落后 0 · 未推送 0
```

然后 `git add -A && git commit && git push`。跑不绿就别推。
`--landed` 是**按批开关、不是新默认**：维护者说「先改本地、不提交不推送」的那批按设计就不该跑它
（跑了必红，那是设计而不是故障）。它也不判「有没有把垃圾文件扫进提交」—— 那由提交前点名 stage 挡。
退出码口径：`0` 判据全过 / `1` 判据失败 / `2` 环境或前置不达标（**没跑成不等于跑绿**）。
`0` 只代表七项判据过了，**不含落地状态** —— 这批提交推送了没有，跑 `--landed` 才算数。

七项分别守：Surge 六阶段回归 · Egern 两阶段回归 · `.min` 与完整版去注释对拍 ·
换设备可移植性（行尾 / BOM / 命名 / 单机残留，**固定 18 条规则**）·
文档读数与实测对拍（组数 / 规则条数 / 份数 / 图标数 / 检查项数 / 悬空指向、豁免行可被读到，**固定 18 条规则**，
见 `skill/tests/check_doc_readings.py`）· 工具自检 + 覆盖矩阵（三套自带回归 + 全部被跟踪 `.py` 可编译 + 顶层死绑定 + 用了没绑 +
覆盖矩阵，**固定 8 条判据**，见 `skill/tests/check_tools.py`）·
回归断言数对拍（文档写死的「19 断言 / 24 断言」↔ 本轮六个 TOTAL，**固定 6 条判据**，
见 `skill/tests/check_assert_counts.py`；`--offline` 档它**不出声判过**，因为离线时 Surge 侧少跑 4 条联网断言）。

## 2 · 五条硬约束（agent 最常在这里犯错）

1. **不要加 CI / GitHub Actions / workflow。** 这是维护者的决定，记录在
   [`docs/跨内核差异对照.md`](docs/跨内核差异对照.md) 与 [`docs/注意事项.md`](docs/注意事项.md)：
   检查只以「本地一条命令」的形态存在仓里。
2. **不要去引用、依赖或克隆 `RiverFlowsInUUU/Surge`、`RiverFlowsInUUU/Egern` 这两个前身仓。**
   本仓完全独立，把它们当已弃用。内容需要就自己写在本仓里。
   （**规则集引用第三方社区仓库是允许的**，那是公共资源，不在此列。）
3. **不要为了「行尾对不上」去改任何人的 git 配置。** 字节层由仓根
   [`.gitattributes`](.gitattributes) 的 `* text=auto eol=lf` 钉死，优先级高于 `core.autocrlf`。
   若在 Windows 上 `git status` 干净但磁盘仍是 CRLF ⇒ 那是**老克隆**的一次性问题，解法见 §4。
   **用脚本写文件时**（agent 最常干这事）：Windows 上 `open(p, 'w')` 默认文本模式会把 `\n` 写成 `\r\n`，
   落盘即被第 4 项 `E2` 判负。写时给 `newline='\n'`（或写二进制），`git add` 时的归一化不覆盖工作树 ——
   它救得了提交，救不了工作树。
4. **看到某个配置「好像不对」，先在文件里 grep `audit-waive`。** 明知故犯的地方都在 profile 头部
   留了豁免条目和理由，审计脚本的注释里也写了取舍。例：Surge 的 `encrypted-dns-server` 保留
   `dns.google` / `dns.alidns.com` 两条主机名端点是有意的（CDN 就近与 ECS 合规），不是泄露。
5. **下面 12 个文件是「闸」，动它们之前必须先请示维护者。** 它们是判定对错的东西 ——
   改坏它们，全套检查会**看着全绿而其实失效**，比 profile 里写错一条规则严重得多。

   ```
   .gitattributes                             skill/tests/all.sh
   skill/tests/check_portability.py           skill/tests/check_min_pair.py
   skill/tests/bump_version.py                skill/tests/surge/run.sh
   skill/tests/check_doc_readings.py          skill/tests/surge/architecture.sh
   skill/tests/surge/check_links.py           skill/tests/egern/run.sh
   skill/tests/check_tools.py                 skill/tests/check_assert_counts.py
   ```

   **请示时要带什么**：① 不改它会漏掉或误判**哪一个具体文件**（能给个反例最好）；
   ② 改完能抓住什么（跑一遍 `all.sh`，必要时造个 fixture 证明改前会漏）。
   这两条把"顺手加固一下"变成有成本的事 —— 这是刻意的。

   **一条豁免**：升版脚本 `bump_version.py` 改写的 profile 头注与文档活指向属机械动作，不算越界
   （它不碰冻结名单里的任何一个文件 —— runner 里的版本常量已于 2026-09-24 随固定订阅地址退役）；
   `docs/`、`README`、profile 与审计脚本（`skill/scripts/`）**不在冻结名单内**，按 §3 的常规连带范围改。

   `all.sh` 每次跑完会在末尾回一句实出的陈述，句式逐字照代码出声：「本批待落地改动未触碰闸门文件」
   （查：未提交与未推送的提交两面，该仓没有上游时退一步只看「最近一次提交（该仓无上游）」；只报不判负，无需翻 diff）。
   **闸门一律没有放行例外**：`all.sh` 里曾有过一次性的 `once_released()`，只认
   `skill/tests/surge/check_links.py` 这一件，判据是「该件带着授权标记、且标记尚未进入 HEAD」；
   授权那一批一落地（2026-09-26 q11）它就再也不成立，q15 起整段删除，任何场景都不会再出 ℹ️ 那一行放行出声。
   该件里 4 行 `q11-user-approved` 标记自此不再被任何判据读取，只作**授权留痕**保留，不许删。
   **后来者不许照学这个模式给任何文件开后门**：加名单项、放宽判据、
   给自己放行，一律按本条先请示维护者。

## 3 · 目录速查

| 路径 | 是什么 | 改了它要顺手改什么 |
|:-----|:-------|:-------------------|
| `surge/profiles/` · `egern/profiles/` | 订阅文件：顶层固定名四件 + `config_old/` 归档 | 改了完整版跑 `make_min.py` 生成 `.min`（见 §5），对拍是第 3 项；升版走 §5 |
| `skill/` | 配置领域技能包：`skill/SKILL.md` + `skill/reference/` + `skill/scripts/` | 触发词表与 `agent_created` 头**别乱动**，是靠它被检索的 |
| `skill/scripts/` · `skill/tests/` | 审计脚本与回归判据（批量改文档走 `skill/tests/apply_edits.py`：锚点不唯一就整批拒写） | 新增判据要把读数写进 `surge/docs/08-审计读数.md` 与 `egern/docs/08-审计读数.md` |
| `docs/` | 人读的**活专题四篇**（注意事项、规则集与来源、跨内核差异对照、图标与许可）+ **归档快照三篇**（体检报告、技能包合并与自包含、日志旧版原文，首行各自标快照/存档、不随现状更新）+ `_archive/` 旧文档目录。没有叫「跨设备一致性」的篇目 —— 那个话题在注意事项里 | 相对链接由 Surge 侧阶段 6 全仓校验 |
| `manual/` | 人读手册：`MANUAL.md` 索引 + 编号章节 01–11、99 | 手册允许指向审计项**序号**与**取舍结论**；会漂的统计读数一律落两侧 `docs/08-审计读数.md`，别抄进手册 |
| `CHANGELOG.md` | **唯一一份**改动记录：装配层 + 两个内核的迭代都按日期写在这里 | 体例三条：**一天一段**（当天后续改动往那段增补，不开第二个同名日期段）· 段内分 `### Surge` / `### Egern` / `### 共享层`，没动的不写 · 一条只答「改了什么 · 哪里没动 · 验收」。别在 `surge/` `egern/` 里另起日志；合并前的内核迭代史在各自 `docs/07` 末节 · **一条边界**：本文件整篇在判据② 的排除表内（沿革层不扫，机制见 `skill/tests/surge/check_links.py` 的 `_CMD_HIST`）⇒ 往日志里写的可照抄命令路径没有机器兜底，落笔前先自己跑一遍 |
| `icons/` | 26 个策略组图标（两内核共用） | 路径**必须纯 ASCII**（`skill/tests/check_portability.py` 的 `N6`），别新加中文名 |

## 4 · 换到一台新机器只做四件事

```bash
git clone https://github.com/RiverFlowsInUUU/Self-Configuration.git
git config --global user.name  "你的名字"
git config --global user.email "你的邮箱"
pip install pyyaml   # Egern 侧脚本读 .yaml 靠它；缺它 `all.sh` 前置就 rc=2（没跑成不等于跑绿）
```

推送凭据用 `gh auth login` 或 Git 凭据管理器。**token 不进仓内任何文件，也不写进 remote URL。**

`.gitattributes` 不回头改写已在磁盘上的文件 ⇒ **今天之前 clone 的旧目录** pull 之后磁盘可能仍是 CRLF
（而 `git status` 干净，属隐形差异）。一次修好：`git rm -r --cached . && git reset --hard`，
或直接删掉重 clone。详见 [`docs/注意事项.md`](docs/注意事项.md) 的「换设备 / 双端一致」。

**换到一个新会话也只做三件事**（配 AI 助手干活时用；仓只有这一份，会话不另开副本）：

1. 📍 **工作目录选在仓根**，别在临时目录里开工后再 clone 一份 —— 本仓的验收、归档、链接校验都按仓根算。
2. 📖 **先读 §1–§2 与 [`CHANGELOG.md`](CHANGELOG.md) 最近一段**再动手 —— 该知道的都在仓里，
   不必把上一个会话的历史一直背在上下文里。
3. 🔪 **一个批次一件事，做完就换一个新会话** —— 别把同一个会话拖到反复压缩：
   上下文越肥，每一轮越慢，实测薄与肥两档的单轮平均耗时差近一倍。

## 5 · 升版：订阅地址不动，旧版进归档

订阅地址是**永久**的：当前版恒为 `routing.conf` / `routing.min.conf` / `lazy.*`，升版**不改文件名**。
「哪一版」只写在 profile 头注 `#! version=routing_vX.Y` 里（从前是三处 runner 各一行 `CURRENT=`，改一漏二）。
**改完完整版先跑生成器，再谈别的**：`python skill/tests/make_min.py --family routing|lazy|all`
（默认只出计划，`--apply` 才写盘，`--selftest` 跑它自己的 7 条回归）。`.min` 不是手工同步的：
它按 `check_min_pair.py` 的同一套规则重算，注释按锚点继承（`# audit-waive:` 与两条「怎么加节点」）——
**判据与生成器共用一份代码，不存在"生成器自己跑歪 yet 对拍放行"**。它不碰完整版、不碰 `config_old/`。
机械升版交给 `python skill/tests/bump_version.py`（默认只出计划，`--apply` 才写盘，`--gate` 跑 §1，
`--changelog-stub` 出一条贴得进根日志的骨架）：
它把当前版**逐字节复制**进 `profiles/config_old/`（按头注版本号命名），再按「小数点后一位、`x.9` 进位到 `(x+1).0`」
把头注自增，最后改全仓活指向。归档不参与检查 —— 指回归与读数类；唯一例外是 `architecture.sh` ①
的占位符 / 凭据扫描，归档不享豁免。要复核旧版就带着路径直接调脚本。
散文（根 `CHANGELOG.md` 的升版说明、各篇「版本沿革」里的历史表述、写死的断言数）由它列成清单交给人，**脚本不猜**。
⚠️ **同号归档只读**：改了已发布版、`config_old/` 里已有同号快照 ⇒ 脚本**保留快照不覆盖**、警告一句、照常升号
   （线上那份改动随新版本出厂，下次退休才归档）。这时对拍器的 `V6` 会判负一句"改了没升版"，
   **那是设计出来的告警**，处置就是升版 —— 别手改归档。

## 6 · 设计依据与背景

- [`docs/跨内核差异对照.md`](docs/跨内核差异对照.md) §8 —— 本仓相对两个前身仓的全部刻意差异与理由
- [`docs/体检报告.md`](docs/体检报告.md) —— P1–P11 的问题记录，含**被实测推翻的原结论**
- [`docs/技能包合并与自包含.md`](docs/技能包合并与自包含.md) —— `skill/SKILL.md` 为什么长这样
- [`docs/注意事项.md`](docs/注意事项.md) —— 动手前读，含改配置 / 改判据 / 换设备的边界
