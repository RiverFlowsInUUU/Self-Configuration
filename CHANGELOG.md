# 📝 更新日志

> 本仓库的**装配史**在这里；**模板内容**的迭代史在两个内核各自的 CHANGELOG 里：
> [`surge/CHANGELOG.md`](surge/CHANGELOG.md) · [`egern/CHANGELOG.md`](egern/CHANGELOG.md)。
> 格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

---

## 2026-09-23 · 合并成仓

本仓库由 [`RiverFlowsInUUU/Surge`](https://github.com/RiverFlowsInUUU/Surge) 与
[`RiverFlowsInUUU/Egern`](https://github.com/RiverFlowsInUUU/Egern) **合并**而成。
两个源仓库**未作任何改动**，其订阅地址与图标 URL 继续可用。

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
  合并后 **592 行**（共享头部 79 + Surge 分支 179 + Egern 分支 321）；
  ⚠️ **两侧正文逐字保留**，只做标题降级与路径改写 —— 用代码块抽取比对验证过，
  两个分支里的**全部代码块与源文件字节一致**。

### 变更

- 🔗 **URL 全量改写**：仓库自身的 raw URL 由两个旧仓名改为本仓名，
  **618 处**图标引用改指共享根 `icons/`；改写后旧自引用**零残留**（32 个文件、40 类替换规则）。
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
  23 个文件、**157 处** `skill/scripts/` · `skill/tests/` · `skill/reference/` · `profiles/` 补上内核段；
  改后**逐条求值**：文档中出现的 14 条 `python` / `bash` 命令全部指向真实脚本，
  18 个被引用的 `profiles/` 路径中 **15 个真实存在**，另 3 个指向已删除的历史版本名
  （`routing.conf`、`routing_v2.5(.min).yaml`）—— 那三处本身就是"此地址已 404"的通知，**故意保留**。
  ⚠️ 两份内核 `CHANGELOG.md` **不参与改写** —— 历史条目按发生时的事实保留。
- ✅ **内容零漂移**（合并最容易出事的地方）：把新仓 URL 反解回源形态后与源文件 `cmp` 比对 ——
  **20 份 profile**、**26 个图标**（与两个源仓同时相同）、**15 个 Python 脚本**、**9 个测试 fixture**
  全部**逐字节相同**；其余 24 篇文档的差异**逐行归类**，除两处刻意修订外全部属于既定改写类别
  （URL / 技能包路径 / `profiles/` 前缀 / 相对链接深度）。
  三个 shell runner 的差异逐行核过，只有 `SCRIPTS` / `ROOT` / `PROFILES` 与用法注释。
- ✅ **脱敏复核**：全树 `token=` 命中项**只有一种** —— 占位符 `REPLACE_WITH_YOUR_TOKEN`；
  订阅 URL 只有 `sub.example.com`；无 `ca_p12` / 私钥 / 真实凭据。
- ✅ **改动纪律**：所有装配步骤写成可重放脚本（脚手架 / 改写表 / 修链器 / 改道器 / 两个检查器 /
  字节还原核对），从干净克隆重跑一遍即得同一棵树。
- ⚠️ **未跑的部分**：两侧 `*.py` 回归套件**本次未执行** —— 装配环境无可用 Python 解释器，
  且 Egern 侧脚本另需 `PyYAML`。因此本仓库只声明「静态检查通过」，**不声明回归通过**。
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
