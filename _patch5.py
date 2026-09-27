# -*- coding: utf-8 -*-
"""Pass 5: skill/README rewrite + SKILL.md + reference docs + script comments."""
import io, os

ROOT = os.path.dirname(os.path.abspath(__file__))

def patch(path, pairs):
    p = os.path.join(ROOT, path)
    t = io.open(p, encoding="utf-8").read()
    for old, new in pairs:
        if old not in t:
            print(f"MISS [{path}]: {old[:70]!r}")
            continue
        t = t.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("patched", path)

# ================= skill/README.md — full rewrite =================
readme = """# skill/ · 审计脚本与 agent 技能包

本目录是仓库的**工具层**：给 AI agent 的内核知识包（`SKILL.md` + `reference/`），
和一套对两内核 profile 做静态审计的脚本（`scripts/`）。人读的操作文档在 [`docs/`](../docs/)。

```
skill/
├── SKILL.md                  # agent 技能包门面：§0 判内核 → 分支 A(Surge) / 分支 B(Egern)
├── README.md                 # 本文件
├── reference/{surge,egern}/  # 深度主题各一侧：checker · pitfalls · hardening-template · public-repo · leak-localization · ruleset-weight
├── scripts/{surge,egern}/    # 审计脚本（Surge 6 / Egern 11，各含一个共享模块）
└── tests/                    # 四项共享检查：check_secrets · check_portability · check_min_pair · check_links；make_min 为 `.min` 生成器
```

## 检查怎么跑

CI（根 `.github/workflows/ci.yml`）在每次 push / PR 自动跑；本地复现同组命令：

```bash
python skill/tests/check_secrets.py                    # 占位符 / 凭据扫描（全仓 .conf + .yaml）
python skill/tests/check_portability.py                # 行尾 / BOM / 命名 / 单机残留
python skill/tests/check_min_pair.py                   # 固定名四件 + 两侧版本一致
python skill/tests/check_links.py .                    # 全仓 markdown 链接与锚点
python skill/scripts/surge/check_surge_dns.py surge/profiles/lazy.conf surge/profiles/routing.conf
python skill/scripts/egern/check_egern_dns.py egern/profiles/lazy.yaml egern/profiles/routing.yaml
python skill/tests/make_min.py                         # 计划模式：四份 .min 应全部「已同步」
```

环境：Python 3（Egern 侧脚本需 PyYAML）。退出码 `0` 全过 · `1` 有判负 · `2` 前置不达标。

## 改动动线

改 profile → `make_min.py` 重建 `.min` → 跑上面一组 → 提交推送（CI 再跑一遍）。
流程细节见 [`docs/ops.md`](../docs/ops.md)「日常维护」。

相关：[`SKILL.md`](SKILL.md) · [`../docs/troubleshoot-faq.md`](../docs/troubleshoot-faq.md)
"""
io.open(os.path.join(ROOT, "skill/README.md"), "w", encoding="utf-8", newline="\n").write(readme)
print("rewrote skill/README.md")

# ================= skill/SKILL.md =================
patch("skill/SKILL.md", [
    ("| Surge | `surge/profiles/*.conf` | `[Proxy Group]` | `[Rule]` | `skill/scripts/surge/` | `skill/tests/surge/run.sh` |\n| Egern | `egern/profiles/*.yaml` | `policy_groups:` | `rules:` | `skill/scripts/egern/` | `skill/tests/egern/run.sh` |",
     "| Surge | `surge/profiles/*.conf` | `[Proxy Group]` | `[Rule]` | `skill/scripts/surge/` | `skill/scripts/surge/check_surge_dns.py` |\n| Egern | `egern/profiles/*.yaml` | `policy_groups:` | `rules:` | `skill/scripts/egern/` | `skill/scripts/egern/check_egern_dns.py` |"),
    ("  `bash skill/tests/all.sh`（七项一条跑完）；只查单内核时分别跑 `bash skill/tests/surge/run.sh` 与 `bash skill/tests/egern/run.sh`（联网审计阶段可用 `SKIP_NET=1` 跳过）。",
     "  检查命令清单见 [`skill/README.md`](README.md)：CI（push / PR 自动）与本地同组命令。"),
    ("| [`surge/docs/`](../surge/docs/) · [`egern/docs/`](../egern/docs/) | 单内核的逐段讲解、加固清单、审计读数、版本沿革 |",
     "| [`docs/hardening-checklist.md`](../docs/hardening-checklist.md) · [`docs/no-resolve-pairing.md`](../docs/no-resolve-pairing.md) | 单内核加固清单与 no-resolve 成对交付 |"),
    ("- [ ] `architecture.sh` 通过（占位符纪律 / 订阅 token 纪律 / 两组形态 DNS 段一致性 / 规则顺序）",
     "- [ ] `check_secrets.py` 通过（占位符纪律 / 订阅 token 纪律）"),
])

# ================= skill/reference/egern/checker.md =================
patch("skill/reference/egern/checker.md", [
    ("bash skill/tests/egern/run.sh                                        # ★★ 回归测试两阶段（fixture 在 `skill/tests/egern/`、脚本在 `skill/scripts/egern/`；10 + 12 + 2 = 24 断言；联网那 2 条 SKIP_NET=1 时跳过），退出码非 0 即失败",
     "python skill/scripts/egern/check_egern_dns.py egern/profiles/lazy.yaml egern/profiles/routing.yaml   # ★★ DNS 面回归，退出码非 0 即失败"),
    ("   四个文件名，阶段 2 的 `--strict` 名单由 `run.sh` 里那一行 `CURRENT=\"routing\"` 派生。",
     "   四个文件名（固定名四件）。"),
    ("   要复核归档版：带着路径直接调对应脚本（归档在 `profiles/config_old/`，不进检查路径）。",
     "   要复核历史版本：从 git 历史取出对应文件，带着路径直接调对应脚本。"),
    ("2. ⭐⭐ **fixture 必须喂给\"所有\"脚本，而不是常跑的那一个。** 新增 `skill/tests/egern/run.sh`",
     "2. ⭐⭐ **构造的反例必须喂给\"所有\"脚本，而不是常跑的那一个。**（原 fixture 套件已随精简删除，反例直接构造临时 yaml 喂脚本）"),
    ("   **看着绿，其实一个断言都没执行**。所以 `run.sh` 的阶段 2 单独对**顶层固定名四件真实 profile** 跑它（归档版在 `config_old/`，不在通配里）。",
     "   **看着绿，其实一个断言都没执行**。所以对**顶层固定名四件真实 profile** 逐份跑它。"),
])

# ================= skill/reference/egern/pitfalls.md =================
patch("skill/reference/egern/pitfalls.md", [
    ("（或直接 `bash skill/tests/egern/run.sh`，**阶段 1** 把五份同时喂给两个脚本、共 10 个断言）：",
     "（或把构造的几份 yaml 同时喂给两个脚本逐份验证）："),
    ("| `skill/tests/egern/ipv6_only.yaml` | 端点仅 IPv6 国内解析器（`[2400:3200::1]`） | **通过 + 退出码 0，且两脚本结论必须一致** | `bash skill/tests/egern/run.sh` |\n| `skill/tests/egern/scheme_case.yaml` | 端点 scheme 写成大写（`HTTPS://` / `TLS://`），其余与 `ok_route.yaml` **逐字相同** | **通过 + 退出码 0，结论必须与 `ok_route.yaml` 完全相同** | `bash skill/tests/egern/run.sh` |",
     "| 临时构造：`ipv6_only.yaml` | 端点仅 IPv6 国内解析器（`[2400:3200::1]`） | **通过 + 退出码 0，且两脚本结论必须一致** | 喂 `check_egern_dns.py` + `audit_dns_forward.py` |\n| 临时构造：`scheme_case.yaml` | 端点 scheme 写成大写（`HTTPS://` / `TLS://`），其余与正确版**逐字相同** | **通过 + 退出码 0，结论必须与正确版完全相同** | 喂 `check_egern_dns.py` + `audit_dns_forward.py` |"),
])

# ================= skill/reference/egern/public-repo.md =================
egern_tree_old = """```
README.md                                   # 门面：内核选择 + 四份订阅地址 + 五类泄露面 + 隐私对照 + 按需查阅
CHANGELOG.md                                # **唯一一份**改动记录：只记两内核配置文件的修改（文档与脚本改动看 git log）
LICENSE · .gitignore · AGENTS.md            # AGENTS.md = 维护者任务书：冻结名单 · 连带范围 · 推送规矩
icons/                                      # 26 个 PNG —— 两内核共用（原各存一份且逐字节相同）
manual/                                     # ★ 手册层：唯一权威操作层（MANUAL.md 入口 + 11 章 + 99 版本历史）
docs/                                       # ★ 共享文档层（不再各内核一份）
  活专题四篇：跨内核差异对照.md · 规则集与来源.md · 注意事项.md · 图标与许可.md
  归档快照三篇 + _archive/：体检报告.md · 技能包合并与自包含.md · 日志旧版原文.md（首行各自标快照/存档、不随现状更新）
skill/                                      # 本 skill：SKILL.md（§0 判内核 → 分支 A/B）
  reference/{surge,egern}/ · scripts/{surge,egern}/ · tests/{surge,egern}/
egern/profiles/lazy.yaml / lazy.min.yaml          # 懒人版 · 可选（4 组 / 10 条规则：Proxy · AI · AD + 隐藏订阅槽位 Airport；AD 只留 REJECT、无 Final 兜底组（policy 直写 Proxy））
egern/profiles/routing.yaml / .min.yaml           # 分流版 · 推荐（脱敏模板：2 条占位节点 + 1 个机场槽位，凭据与订阅均为占位符、无真实证书）
egern/profiles/config_old/                        # 历代版本按号留档、各含 `.min`，不参与检查（例外：`architecture.sh` ① 连归档一起扫）：
                                                  #   v2.4（v3 前一版）· v2.3（与 v2.4 只差 rule_set 的 update_interval）
                                                  #   v2.2（4 处修正）· v2.1（机场槽位 4 vs 2）· v2（多 52 行「值等于默认值」的冗余行）
                                                  #   v1（分流线起点，dns 段较冗长、功能等价）· lazy_v1.0（懒人版快照）
egern/docs/01-DNS是怎么工作的.md                  # 递归解析 / 加密 DNS / Fake IP / Egern 双轨模型
egern/docs/02-DNS为什么会泄露.md                  # 5 个真实案例（每个：现象→机制→修法）
docs/hardening-checklist.md                    # 清单 + no_resolve 三层级 + 验收 6 条
egern/docs/04-模板逐段讲解.md                     # 逐段讲模板，含「必须替换的清单」（routing_v2.3 起只需 1 处）
docs/no-resolve-pairing.md     # f7→f8 事故复盘
egern/docs/06-实测数据与版本谱系.md               # 端点实测表 / 污染实测表 / f1→f8 谱系
egern/docs/07-文件版本沿革.md                     # 两条线 + 分流版 routing_v1→v2.4 逐个说明（含四次改名记录）；末节 = 本内核合并前的迭代史（原 egern/CHANGELOG.md 全文并入）
egern/docs/08-审计读数.md                         # 6 个审计脚本的读数 / 2 条 LOW 的含义 / 回归测试
egern/docs/12-分流顺序.md                         # 分流版 24 条规则的顺序与理由
egern/DetailsReadme/DetailsReadme.md              # 完整技术文档
```"""
egern_tree_new = """```
README.md                                   # 门面：四份订阅地址 + 分组表 + DNS 防泄露对照 + 文档导航
CHANGELOG.md                                # **唯一一份**改动记录：只记两内核配置文件的修改（文档与脚本改动看 git log）
LICENSE · .gitattributes · .gitignore
icons/                                      # 26 个 PNG —— 两内核共用
docs/                                       # ★ 共享文档（九篇，2026-09-27 精简后）：quick-start · dns-basics · hardening-checklist ·
                                            #   no-resolve-pairing · cross-kernel-diff · rulesets · icon-license · ops · troubleshoot-faq
skill/                                      # 本 skill：SKILL.md（§0 判内核 → 分支 A/B）
  reference/{surge,egern}/ · scripts/{surge,egern}/ · tests/（check_secrets · check_portability · check_min_pair · check_links · make_min）
egern/profiles/lazy.yaml / lazy.min.yaml          # 懒人版 · 可选（4 组 / 10 条规则；隐藏订阅槽位 Airport）
egern/profiles/routing.yaml / .min.yaml           # 分流版 · 推荐（脱敏模板：2 条占位节点 + 1 个机场槽位，凭据与订阅均为占位符）
egern/apple_system.list                           # 本仓自托管的 Apple 系统域名规则集
egern/DetailsReadme/DetailsReadme.md              # 完整技术文档（逐键语义）
.github/workflows/ci.yml                          # 最小 CI：五项检查（push / PR 自动）
```"""
patch("skill/reference/egern/public-repo.md", [
    (egern_tree_old, egern_tree_new),
    ("> ④ **改动记录只有根 `CHANGELOG.md` 一份**（2026-09-24 起，内核目录里不再各留一份日志）——\n> 本内核合并前的迭代史存档在 [`docs/07-文件版本沿革.md`](../../../egern/docs/07-文件版本沿革.md) 末节。",
     "> ④ **改动记录只有根 `CHANGELOG.md` 一份** —— 更早的历史看 git（备份 tag：`pre-cleanup-20260927`）。"),
    ("> 当前是第哪一版写在头注 `#! version=routing_v3.4` 里。历代旧版在 `profiles/config_old/` 备对照。",
     "> 当前是第哪一版写在头注 `#! version=` 里；历史版本看 git（备份 tag：`pre-cleanup-20260927`）。"),
    ("`bash skill/tests/egern/run.sh`（两阶段 24 断言；SKIP_NET=1 时 22）+ 下面那批审计脚本，再提交推送。",
     "检查命令清单见 [`skill/README.md`](../../README.md)（CI 与本地同组命令），再提交推送。"),
    ("📌 **全部验证都在本地完成 —— 本仓库刻意不挂 CI / 任何自动化（2026-09-21 决定）。**\n这是个人模板仓库，不会有外部贡献者，\"自动验 PR\"没有服务对象；而本地跑一次\n`bash skill/tests/egern/run.sh` 只要几十秒。少一个对外暴露的面就少一份事。\n\n⇒ 全部验证用这**一条**本地命令复现：`bash skill/tests/egern/run.sh` —— 阶段 1 跑 fixture，\n阶段 2 逐份 profile 跑 DNS 面 / 地区组面 / 刷新面，联网档再跑分流覆盖面。具体脚本名\n**不抄在这里**，以该 runner 的头部注释为准：名单会随\"某个面接进闸\"而漂移，抄一份进文档\n就是下一个过期读数。\n\n闸外那几个不在验证链上：是手工探针 / 量测工具，另有一个需联网、尚未接闸的规则集条目级\n审计（`audit_ruleset_noresolve.py`）—— 名单与\"刻意不进闸\"的理由以\n`python skill/tests/check_tools.py` 的 T7 **现算**为准（同源就是它自己的 `MATRIX_WAIVED` 豁免表）。\n功能上没有任何损失。",
     "📌 **验证 = CI（`.github/workflows/ci.yml`，push / PR 自动）+ 本地同组命令复现。**\n命令清单见 [`skill/README.md`](../../README.md)；探针 / 量测类脚本（`probe_*` / `weigh_*` / `profile_ruleset`）不在验证链上，是手工工具。"),
    ("- 🚫 **内部判据与断言名** —— 「由 `architecture.sh` ④ 断言守着」。",
     "- 🚫 **内部判据与断言名** —— 「由某脚本某断言守着」。"),
    ("该放哪：**改动记录 → 根 [`CHANGELOG.md`](../../../CHANGELOG.md)（唯一一份）；判据与原理 → [`DetailsReadme/`](../../../egern/DetailsReadme/DetailsReadme.md) 或 [`docs/`](../../../egern/docs/)。**",
     "该放哪：**改动记录 → 根 [`CHANGELOG.md`](../../../CHANGELOG.md)（唯一一份）；判据与原理 → [`DetailsReadme/`](../../../egern/DetailsReadme/DetailsReadme.md) 或 [`docs/`](../../../docs/)。**"),
    ("[`docs/rulesets.md`](../../../docs/rulesets.md) 承接全部规则集信息，",
     "[`docs/rulesets.md`](../../../docs/rulesets.md) 承接全部规则集信息，"),
])

# ================= skill/reference/surge/checker.md =================
patch("skill/reference/surge/checker.md", [
    ("| 输出编码 | 无需设置 —— `_surge_common` 在 import 时把 stdout 钉成 UTF-8（中文 Windows 默认 GBK，emoji 会崩成**退出码 1** ⇒ 判负 fixture 假绿）；`run.sh` / `architecture.sh` 另设 `PYTHONIOENCODING=utf-8` |",
     "| 输出编码 | 无需设置 —— `_surge_common` 在 import 时把 stdout 钉成 UTF-8（中文 Windows 默认 GBK，emoji 会崩成**退出码 1**）；CI 另设 `PYTHONIOENCODING=utf-8` |"),
    ("bash   ./skill/tests/surge/architecture.sh                           # 期望 exit 0",
     "python ./skill/tests/check_secrets.py                                # 期望 exit 0"),
    ("bash ./skill/tests/surge/run.sh\nSKIP_NET=1 bash ./skill/tests/surge/run.sh\nPY=/path/to/python bash ./skill/tests/surge/run.sh",
     "python ./skill/scripts/surge/check_surge_dns.py surge/profiles/lazy.conf surge/profiles/routing.conf"),
    ("   `architecture.sh` 的 ②-b / ④ 段都由 `run.sh` 里那一行 `CURRENT=\"routing\"` 派生。",
     "   当前版本由 profile 头注 `#! version=` 标识。"),
    ("   要复核归档版：带着路径直接调对应脚本（归档在 `profiles/config_old/`，不进检查路径）。",
     "   要复核历史版本：从 git 历史取出对应文件，带着路径直接调对应脚本。"),
    ("   （阶段 2 自动遍历 `profiles/*.conf`，`config_old/` 不在其中）。",
     "   （对 `profiles/*.conf` 逐份跑）。"),
    ("`run.sh` 的 `bad_*` fixture **期望退出码 1**。如果解释器坏掉，脚本也返回 1",
     "构造的反例**期望退出码 1**。如果解释器坏掉，脚本也返回 1"),
    ("## 7 · 架构不变量（`architecture.sh`）",
     "## 7 · 架构不变量（`check_secrets.py`）"),
    ("| 扫描面 | **全仓** walk 到的 `*.conf` / `*.yaml` / `*.yml`（不是只有 `surge/profiles/`）。三档同一套判据：`LIVE` 当前版 / `ARCHIVE` 两侧 `config_old/` / `FIXTURE` `skill/tests/`，档位只决定报错怎么点名 ⇒ **归档不享豁免**。跳过 `.` 开头目录 / `node_modules` / `__pycache__`；刻意不用 `git ls-files`（未提交的本地工作副本正是这道纪律要拦的东西） |",
     "| 扫描面 | **全仓** walk 到的 `*.conf` / `*.yaml` / `*.yml`（不是只有 `surge/profiles/`）。`LIVE` 当前版 / `FIXTURE` `skill/tests/`，档位只决定报错怎么点名。跳过 `.` 开头目录 / `node_modules` / `__pycache__`；刻意不用 `git ls-files`（未提交的本地工作副本正是这道纪律要拦的东西） |"),
    ("| v3 | 取消豁免 —— 配置已收敛为单一版本 | 见 [`docs/07`](../../../surge/docs/07-文件版本沿革.md) §3 |",
     "| v3 | 取消豁免 —— 配置已收敛为单一版本 | 见 git 历史 |"),
    ("| v1 | `run.sh` 只有\"退出码非 0 即失败\" | 初版 |",
     "| v1 | 只判\"退出码非 0 即失败\" | 初版 |"),
])

# ================= skill/reference/surge/hardening-template.md =================
patch("skill/reference/surge/hardening-template.md", [
    ("> 见 [`docs/11`](../../../surge/docs/11-分流版设计.md)。",
     ""),
    ("一周刷新。`no-resolve` **不是**这条的固定尾巴 —— 取舍是「实测零 IP 条目的规则集不写、真含 IP 条目的必须写」，纯域名集写上是空转（Surge 四份 profile 共用这一条，见 [`docs/rulesets.md`](../../../docs/rulesets.md) 原则 4b）。",
     "一周刷新。`no-resolve` **不是**这条的固定尾巴 —— 取舍是「实测零 IP 条目的规则集不写、真含 IP 条目的必须写」，纯域名集写上是空转（Surge 四份 profile 共用这一条，见 [`docs/rulesets.md`](../../../docs/rulesets.md) 原则 4b）。"),
    ("[ ] bash skill/tests/surge/architecture.sh                               → exit 0",
     "[ ] python skill/tests/check_secrets.py                                  → exit 0"),
])

# ================= skill/reference/surge/pitfalls.md =================
patch("skill/reference/surge/pitfalls.md", [
    ("**已固化为测试**：`skill/tests/surge/architecture.sh` 把这条写成断言。",
     "**已固化为测试**：`skill/tests/check_secrets.py` 把这条写成判据。"),
    ("> 见 [`docs/07`](../../../surge/docs/07-文件版本沿革.md) §3）。**但教训仍然成立** ——",
     "> 见 git 历史）。**但教训仍然成立** ——"),
    ("**根因**：`run.sh` 的 `bad_*` fixture **期望退出码 1**。",
     "**根因**：构造的反例 **期望退出码 1**。"),
])

# ================= skill/reference/surge/public-repo.md =================
patch("skill/reference/surge/public-repo.md", [
    ("├── AGENTS.md                    # 维护者任务书：冻结名单 · 连带范围 · 推送规矩\n├── CHANGELOG.md                 # **唯一一份**改动记录：只记两内核配置文件的修改（文档与脚本改动看 git log）",
     "├── CHANGELOG.md                 # **唯一一份**改动记录：只记两内核配置文件的修改（文档与脚本改动看 git log）"),
    ("├── manual/                      # ★ 手册层：唯一权威操作层（MANUAL.md 入口 + 11 章 + 99 版本历史）\n├── icons/                       # 26 个 PNG —— 两内核各存一份且逐字节相同，合并后只留一份\n├── docs/                        # 共享文档：活专题四篇（差异对照 · 规则集与来源 · 注意事项 · 图标与许可）+ 归档快照三篇（体检报告 · 技能包合并与自包含 · 日志旧版原文）+ _archive/",
     "├── icons/                       # 26 个 PNG —— 两内核共用\n├── docs/                        # 共享文档（九篇，2026-09-27 精简后）：quick-start · dns-basics · hardening-checklist · no-resolve-pairing · cross-kernel-diff · rulesets · icon-license · ops · troubleshoot-faq"),
    ("│   └── tests/{surge,egern}/     # 回归套件 + fixture",
     "│   └── tests/                   # check_secrets · check_portability · check_min_pair · check_links · make_min"),
    ("    │   └── config_old/           # 被替代的旧版按版本号留档，不参与检查（例外：`architecture.sh` ① 连归档一起扫）\n    ├── docs/                     # 01–08 编号系列 + 11-分流版设计（07 末节 = 本内核合并前的迭代史）\n    └── DetailsReadme/",
     "    └── DetailsReadme/"),
    ("> ④ **改动记录只有根 `CHANGELOG.md` 一份**（2026-09-24 起，内核目录里不再各留一份日志）——\n>    本内核合并前的迭代史存档在 [`docs/07-文件版本沿革.md`](../../../surge/docs/07-文件版本沿革.md) 末节。",
     "> ④ **改动记录只有根 `CHANGELOG.md` 一份** —— 更早的历史看 git（备份 tag：`pre-cleanup-20260927`）。"),
    ("| `manual/` | **唯一权威操作层**：装 · 改 · 验 · 修的日常与排障 | 实测读数（两侧 `docs/08`）、逐键语义（`DetailsReadme`） |\n| `docs/`（共享层） | **跨内核**的综合：差异对照 · 规则集 · 注意事项 · 许可 | 单内核的专题推导 |\n| `surge/docs/` | 每个专题一篇，**单一主题** | 跨主题的综合 |",
     "| `docs/`（共享层） | 操作（`ops.md`）与跨内核综合：差异对照 · 规则集 · DNS 基础 · 加固清单 · 排障 FAQ · 许可 | 单内核的逐键语义 |"),
    ("   括号套括号的辩护 —— 都不进日志（要留证据就写进 `docs/体检报告.md` 那类专题）。\n   自查：删掉这句，事实会少吗？不会就删。",
     "   括号套括号的辩护 —— 都不进日志。自查：删掉这句，事实会少吗？不会就删。"),
    ("| 内部判据与断言名 | 「由 `architecture.sh` ④ 断言守着」 | `DetailsReadme` / `skill/` |",
     "| 内部判据与断言名 | 「由某脚本某断言守着」 | `DetailsReadme` / `skill/` |"),
    ("  （这就是 `v0` 被删的原因，见 [`docs/07`](../../../surge/docs/07-文件版本沿革.md) §3）",
     "  （`v0` 已删，见 git 历史）"),
    ("**内容必须一致，只差注释** —— 由 `architecture.sh` 的 16 键一致性断言兜底",
     "**内容必须一致，只差注释** —— 由 `check_min_pair.py` 的对拍判据兜底"),
    ("这 6 条基本就是 `architecture.sh` 的全部断言。",
     "以上基本就是 `check_secrets.py` 的全部判据。"),
    ("检验由 `architecture.sh` 第 ① 组断言自动完成。",
     "检验由 `check_secrets.py` 自动完成。"),
    ("bash skill/tests/surge/architecture.sh     # 占位符纪律 + DNS 段一致性 + 规则顺序",
     "python skill/tests/check_secrets.py        # 占位符纪律（全仓 .conf + .yaml）"),
    ("`architecture.sh` ① 现在扫的是**全仓** `.conf` / `.yaml`（含 Egern 侧与 `config_old/` 归档），但它只认这两种扩展名 —— `docs/`、`manual/`、`skill/` 里的 markdown 与 Python 仍需另扫一遍：",
     "`check_secrets.py` 扫的是**全仓** `.conf` / `.yaml`（含 Egern 侧），但它只认这两种扩展名 —— markdown 与 Python 仍需另扫一遍："),
    ("bash skill/tests/surge/run.sh              # 6 阶段，19 个断言\nSKIP_NET=1 bash skill/tests/surge/run.sh   # 跳过联网阶段",
     "python skill/scripts/surge/check_surge_dns.py surge/profiles/lazy.conf surge/profiles/routing.conf"),
    ("1. bash skill/tests/surge/run.sh                      → 15 passed, 0 failed",
     "1. python skill/scripts/surge/check_surge_dns.py …    → 退出码 0"),
    ("8. （push 前）grep 一遍敏感串 + 跑一次 `architecture.sh`",
     "8. （push 前）跑一次 `check_secrets.py`"),
    ("> 📌 `run.sh` 已经把上面第 2–6 步全跑了一遍（含联网阶段）。",
     "> 📌 CI 在 push 后把同组检查再跑一遍。"),
    ("| 2 | `[Rule]` 的顺序（`direct.txt` 挪到 REJECT 前） | 广告拦截失效 | `architecture.sh` ③-b |",
     "| 2 | `[Rule]` 的顺序（`direct.txt` 挪到 REJECT 前） | 广告拦截失效 | 人工核对 |"),
    ("| 3 | IP 类规则的 `no-resolve`（删掉） | DNS 泄露 | `architecture.sh` ③-d + `check_12` |",
     "| 3 | IP 类规则的 `no-resolve`（删掉） | DNS 泄露 | `check_surge_dns.py` |"),
    ("| 4 | 只改 `.conf` 或只改 `.min.conf` 的 DNS 段 | 两份行为不一致；使用者拿到的与文档说的不一致 | `architecture.sh` ②（只覆盖 DNS 段） |",
     "| 4 | 只改 `.conf` 或只改 `.min.conf` | 两份行为不一致；使用者拿到的与文档说的不一致 | `check_min_pair.py` |"),
    ("> ⚠️ **第 4 条的覆盖是部分的**：`architecture.sh` ② 只比对 **16 个 DNS 键**，",
     "> ⚠️ **第 4 条的覆盖是部分的**：`check_min_pair.py` 对拍整份去注释正文，"),
])

# ================= script comments =================
patch("skill/scripts/egern/probe_dns_endpoints.py", [
    ("#    自检就是为它立的；放在模块级是为了**不可能静默失效**（`check_tools.py` 的 T1 只判可编译，",
     "#    自检就是为它立的；放在模块级是为了**不可能静默失效**（"),
])
patch("skill/scripts/surge/audit_ruleset_content.py", [
    ("    与 `bump_version.py` 头注讲的「当前版」同一条罪：读数说得出名字、说不出事实。",
     "    与「当前版」纪律同一条罪：读数说得出名字、说不出事实。"),
])
patch("skill/tests/make_min.py", [
    ("   本脚本只在计划里点名提醒，处置办法是升版（`bump_version.py`），不是代它改历史。",
     "   本脚本只在计划里点名提醒，处置办法是升版（改头注 `#! version=`），不是代它改历史。"),
    ("        # `with` 收口（A-8）：写完必须确定性关闭，不依赖引用计数（同 `bump_version.write`）。",
     "        # `with` 收口（A-8）：写完必须确定性关闭，不依赖引用计数。"),
])
patch("skill/tests/check_min_pair.py", [
    ('OLD_DIR = "config_old"',
     'OLD_DIR = "config_old"          # 归档目录（2026-09-27 起已删除；保留常量仅为兼容 make_min 快照提醒逻辑）'),
    ("        # 实测：把 surge/profiles/config_old/ 清空成 0 个文件，输出照旧",
     "        # 历史注记：归档目录存在时把清空成 0 个文件，输出照旧"),
])

print("PASS5 DONE")
