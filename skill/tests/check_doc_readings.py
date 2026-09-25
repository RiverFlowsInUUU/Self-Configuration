#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文档读数对拍：把散在十来篇文档里的「X 组 / Y 条 / Z 份 / 当前版本」跟实测值比一遍。

为什么要有这一项（治的是本项目反复发生的那类返工）：
  本仓的读数组数、规则条数、规则集条数、profile 份数、图标数、检查项数、当前推荐版
  在 README / AGENTS / docs / skill / 两份 DetailsReadme 里**各写一遍**，而此前
  **没有任何检查会因为"改了 profile 忘了改文档"而报错** —— 只能一轮轮 grep 反查、逐个数字重测。
  这一项把它变成一条命令：不吻合就直接点名「哪个文件第几行写的 24，实测 23」。

固定规则清单（每条 = 1 个断言，**共 18 条、不随文件数增长**）：
  🆕 2026-09-25 A-4：扫描面从「`LIVE` 逐篇点名的 13 篇」扩到 `LIVE` + `manual/**/*.md` +
     `skill/reference/**/*.md`（通配，见 `LIVE_GLOBS`）⇒ 新增一篇手册/参考文档**自动在闸里**。
     判据条数不变（新落的两处扩展 —— 徽章两类数、审计器编号引用 —— 都折进已有那条 ck）。
    D0 两内核逐位对齐：组数 / 规则条数 / 规则集条数 三对 × 两形态必须相等（抓"只动了一侧"）
    D1 策略组数      —— 「N 组 / N 个策略组」类声明 == 实测组数
                      🆕 含 README 门面上 `Groups` 徽章里的两个数（A-11：URL 参数里的数，
                      位置即语义 —— 左 Surge｜右 Egern、形态钉死分流版）
    D2 规则条数      —— 「N 条 … 规则」类声明 == 实测 `[Rule]` / `rules` 非注释条目数
                      🆕 含 README 门面上 `Rules` 徽章里的两个数（同上）
    D3 规则集条数    —— 「N 条 … 规则集 / rule_set」类声明 == 实测 RULE-SET / rule_set 引用数
    D4 订阅文件份数  —— 「N 份 `.conf` / `.yaml`」类声明 == 两内核 `profiles/` 下的文件数
    D5 图标数        —— 「N 个策略组图标」== `icons/` 文件数
    D6 检查项数      —— 与 `all.sh` 同行的「N 项检查」== `all.sh` 里 `item` 调用的个数（中文数词也认）
    D7 自托管落点    —— profile 里写出的 `Self-Configuration/main/<路径>` 必须真在仓里
    D8 引用不悬空    —— 文档里写出的 profile 文件名（含 `.min`）必须真在 `profiles/` 或
                      `profiles/config_old/` 里；而**订阅 URL** 一律必须是固定名 —— 带版本号的
                      订阅地址正是这次要根治的东西，写回去就等于把永久地址弄坏
    D9 头注即当前版  —— 四份 profile 头注 `#! version=` 必须齐全一致（两内核、routing/lazy 各一对），
                      且顶层固定名四件都在。从前"哪一版"是三处 `CURRENT=` 各写一遍，改一漏二。
    D10 豁免行可被读到 —— 当前版 profile（含 `.min`）里每一行 `# audit-waive:` 必须**与消费方的
                      正则同形**（`# audit-waive: <编号> <理由>`，理由非空），且**同一文件内编号不重复**。
                      消费方是 `skill/scripts/surge/check_surge_dns.py` 的 `load_waivers()`。
    D11 DNS 键数      —— 「N 个(相关)键」类声明 == `architecture.sh` 的 `DNS_KEYS` 长度（**现算**）
    D12 阶段数        —— 「N 阶段」类声明 == 该侧 runner 里「`#   阶段 N ·`」头的计数（**现算**）
    D13 fixture 数    —— 「N fixture」类声明 == 该侧 runner 里 `CASES` 的行数（**现算**）
                       ⚠️ D11–D13 是 2026-09-25 补的：这三类数此前散在文档里写死、**无任何判据管**。
                      期望值一律从源头现算 —— 写死进判据就等于给判据自己造下一个会漂的硬编码。
                      同批**刻意没做**「审计脚本数」：仓里这个词有两种口径（产出读数的 6 个 /
                      `skill/scripts/<侧>/*.py` 的 10 个），判据接不住 ⇒ 不判（宁可少判）。
    D15 加固清单项数  —— 文件名 `N项` 与 H1 `（N 项）` == 表格里 `| N |` 的行数（**现算**）
    D16 TOTAL 槽位数  —— 「N 个 TOTAL」== `all.sh` 里 `MEASURED+=(` 的个数（**现算**）
    D17 surge 审计器判据数 —— 「N 项审计清单 / 判据 / 检查」== `check_surge_dns.py` 里 `def check_N_` 的
                      个数（**现算**）。含 egern 的行不判（那句「Egern 18 项」指的是加固清单，D15 管）
                      🆕 A-4 折进同一条 ck：文档写「`check_surge_dns.py` 第 N 项」时 N 必须在
                      `def check_N_` 的**编号集合**里（只比个数会漏「删掉一号、文档仍指它」）。
                      只认同行带工具名的，三查自证见 `checker_ref_selfproof()`。
    D18 共用规则集份数 —— 「N 份…共用规则集」/「N 个 URL」/「懒人版 N 个逐字相同」== 两侧同形态规则集
                      URL 的**交集**（**现算**：分流版 21 / 懒人版 6，**含被注释的 `Proxy.list`** ——
                      文档承诺的是 URL 集合层面"逐字相同"，不是活跃规则数；与 D3 的"每形态引用数"
                      是两个口径，不可合并，合并即对着正确的 21 报假红）。不带形态的行默认按**分流版**
                      判（仓内口径旗舰；懒人版的数一律同行带「懒人版」，实测）。⚠️「Egern 独有 2 项」
                      是集合差、不是共用份数 ⇒ **刻意不判**（挂进本类即名实不符；单立判据的连带面
                      =全链「固定 18 条」改 19，2026-09-25 三轮对拍审定案走最小面，升 D19 需维护者点名）。
                      附**行内判别自证**（D15 先例）：真话不红 · 改数必红 · 无锚措辞不误伤。
                       ⚠️ D1–D18 全部**命中 0 处即判负**（0 命中 = 判据空转，不是"没有漂移"）。

**刻意不判的东西**（判了会误伤，交给人）：
  · 判据/回归的断言数（27 / 50 / 14 / 18）—— 那要真跑测试才有值，递归且不划算。
  · 正文里出现的旧版本号 —— 一行常常同时写"当前 v3.2 + 存档 v3 / v3.1"，判它必误伤；
    版本漂移由 D8 / D9 这两条结构性判据兜住（引用了不存在的文件 ⇒ D8 红；头注与固定名脱节 ⇒ D9 红）。
  · 历史沿革类文件（`docs/07-*`、`日志旧版原文`、`CHANGELOG`、`体检报告`）整篇不扫 —— 旧数字在那儿是对的。
  · 一行里同一类数字出现多次又判不出形态（既没说 lazy 也没说分流）⇒ 跳过不判，
    并在末尾报「跳过 N 处」，让"没判到"这件事本身可见。
  · 豁免编号**是否连续、是否落在审计器现有的检查号区间内** —— 前者本来就无意义（删一条豁免
    不该逼着后面重编号），后者要把判据钉在 `check_surge_dns.py` 的源码上、检查号一加一删就误伤。
    D10 只判"写了却读不到 / 读了却没痕迹 / 后一条把前一条顶掉"这**三种静默失效**。

退出码：0 全绿 · 1 有不吻合 · 2 前置不达标（profile 解析不出来 / 找不到 CURRENT）
"""

import os
import re
import sys
import glob
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))              # <仓根>/skill/tests
ROOT = os.path.dirname(os.path.dirname(HERE))                   # → skill → 仓根
sys.path.insert(0, os.path.join(ROOT, "skill", "scripts", "surge"))

# 扫描范围：只有"讲当前状态"的文档参与对拍
LIVE = ["README.md", "AGENTS.md", "docs/注意事项.md", "docs/规则集与来源.md",
        "docs/跨内核差异对照.md", "skill/README.md",
        "surge/docs/11-分流版设计.md", "surge/docs/08-审计读数.md",
        "egern/docs/08-审计读数.md", "surge/DetailsReadme/DetailsReadme.md",
        "egern/DetailsReadme/DetailsReadme.md",
        "skill/reference/surge/public-repo.md", "skill/reference/egern/public-repo.md"]
# 🆕 A-4（2026-09-25）：权威操作层与参考层用**通配**接进来，不再逐篇点名。
#    为什么必须用通配：这一族判据的前提就是「文档写了一个数、闸门得知道」，
#    逐篇点名的话，每加一篇文档就把那条路重新敞开一次（事实即如此：`manual/` 落进仓那天起，
#    13 篇一篇都不在 LIVE 里，而没有任何一条判据会因为「整层没进名单」出声）。
#    实测（同一份代码，只把 LIVE_GLOBS 置空 = 扩面前）：扫描 13 → 35 篇 ·
#    命中 185 → 254 处 · 比较 60 → 70 处 · 判负 0 ⇒ 这些文档今天说的是真话，
#    但此前**没有任何一条判据知道**。
LIVE_GLOBS = ("manual/**/*.md", "skill/reference/**/*.md")
# 排除关键词：文件路径里含这些片段的整篇不扫（历史记录，旧数字是对的）
#    🆕 `manual/99-版本历史.md` 同此一类：那一章通篇在讲"当时是什么状态"，旧数在那儿是对的。
HISTORY = ("日志旧版原文", "CHANGELOG", "体检报告", "/docs/07-", "manual/99-")
# 固定名四件 = 永久订阅地址；头注所在 = 这四件（.min 形态由对拍器保证与完整版同内容，不再单独钉版本）
FIXED_NAMES = {"routing.conf", "routing.min.conf", "lazy.conf", "lazy.min.conf",
               "routing.yaml", "routing.min.yaml", "lazy.yaml", "lazy.min.yaml"}
HEAD_FILES = ("surge/profiles/routing.conf", "surge/profiles/lazy.conf",
              "egern/profiles/routing.yaml", "egern/profiles/lazy.yaml")
CN_NUM = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
          "八": 8, "九": 9, "十": 10}

# ── D10：豁免行 ───────────────────────────────────────────────────────────
# 这条正则**逐字抄自消费方** `skill/scripts/surge/check_surge_dns.py:load_waivers()`。
# 为什么要逐字：豁免的失效方式全是静默的 —— 形状差一点，`finditer` 一条都不匹配，
# profile 里明明写着"这一处是刻意的"，审计器却按没豁免判（或反过来，多下一条重复编号时
# `_waivers[cid] = 理由` 后写覆盖先写，先那份理由从此没人看得见）。
WAIVE_CONSUMER = re.compile(r"#\s*audit-waive:\s*(\d+)\s+(.*)")


def checklist_problems(checklists):
    """加固清单项数对拍 ⇒ 问题清单（空 = 全过）。

    吃参数是为了能用假数据验判别力（`selfproof` 写在 D15 那条判据里）。
    口径：文件名里的 `N项` 与 H1 的 `（N 项）` 都必须等于**表格里 `| N |` 的行数** ——
    文件名是最显眼的承诺，而它此前没有任何判据管（实测 Surge 那份停在 12、表里 14 行）。
    """
    out = []
    for rel, (fn, h1, rows) in sorted(checklists.items()):
        if fn != rows:
            out.append("%s：文件名写 %d 项，表里 %d 行" % (rel, fn, rows))
        if h1 != rows:
            out.append("%s：H1 写 %d 项，表里 %d 行" % (rel, h1, rows))
    return out


def waive_files():
    """当前版 profile（两内核、含 `.min` 形态）。`config_old/` 归档不参与 ——
    归档里的豁免随着旧订阅地址一起作废，且 glob 只取顶层，天然排除子目录。"""
    return sorted(glob.glob(os.path.join(ROOT, "surge", "profiles", "*.conf")) +
                  glob.glob(os.path.join(ROOT, "egern", "profiles", "*.yaml")))


def waive_readings(files=None):
    r"""返回 (豁免行数, 涉及文件数, 坏行清单)。三种坏法：
      ① **写了却读不到** —— 形状不合消费方的 `finditer`（用 `//` 起头、编号与理由之间没空格等）；
      ② **理由是空的** —— 注意消费方的 `\s+` 会吃掉换行符，所以 `# audit-waive: 2` 单独一行
         确实**被读到**了，finding 被降级成「已豁免（profile 内声明）：」后面空无一物：
         豁免生效、痕迹没了，而这正是"写在 profile 里而不是写在审计器里"的全部意义；
      ③ **同文件内编号重复** —— `_waivers[cid] = 理由` 后写覆盖先写，先那份理由从此没人看得见，
         审计输出与"只有一条豁免"时逐字相同 ⇒ 不跑这条判据永远不会有人发现。
    编号不要求连续、也不要求落在审计器现有的检查号区间内 —— 见头部「刻意不判」。
    """
    bad, n, touched = [], 0, set()
    for p in (files if files is not None else waive_files()):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError as exc:
            bad.append("%s: 读不出来（%s）" % (rel, exc))
            continue
        got = {}                                   # 行号 -> (编号, 理由)
        for mm in WAIVE_CONSUMER.finditer(text):
            got[text.count("\n", 0, mm.start()) + 1] = (int(mm.group(1)), mm.group(2).strip())
        first = {}
        for i in sorted(got):
            cid, reason = got[i]
            n += 1
            touched.add(rel)
            if not reason:
                bad.append("%s:%d 编号 %d **没写理由** ⇒ 豁免照样生效，但报告里"
                           "「已豁免（profile 内声明）：」后面空无一物" % (rel, i, cid))
            elif cid in first:
                bad.append("%s:%d 编号 %d 与本文件第 %d 行重复 ⇒ 审计器按后写覆盖先写，"
                           "第 %d 行那份理由没人看得见" % (rel, i, cid, first[cid], first[cid]))
            else:
                first[cid] = i
        for i, line in enumerate(text.splitlines(), 1):
            if "audit-waive" in line and i not in got:
                n += 1
                touched.add(rel)
                bad.append("%s:%d 形状不合 ⇒ 审计器**一条都读不到**（口径：`# audit-waive: "
                           "<编号> <理由>`，编号与理由之间要空格） ｜ %s"
                           % (rel, i, line.strip()[:60]))
    return n, len(touched), bad


def is_live(path):
    return not any(h in path.replace("\\", "/") for h in HISTORY)


def live_docs():
    out = []
    rels = list(LIVE)
    for g in LIVE_GLOBS:
        for p in glob.glob(os.path.join(ROOT, g.replace("/", os.sep)), recursive=True):
            rels.append(os.path.relpath(p, ROOT).replace("\\", "/"))
    for rel in sorted(set(rels)):
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p) and is_live(rel):
            out.append((rel, p))
    # ⚠️ 通配面**空转**要出声：`manual/` 整层被挪走时 `glob` 安静地返回空 ⇒ 扫描面缩水到
    #    看起来和昨天一样绿。与 `architecture.sh` ① 的「walk 不到 LIVE 就退出码 2」同一条纪律。
    for g in LIVE_GLOBS:
        # ⚠️ 判的是**这条通配自己**扫到没有，不能判「扫描面里有没有这个目录前缀」——
        #    `skill/reference/**` 的前缀 `skill/` 下面还躺着 `skill/README.md`，那样判等于永不发声。
        got = [os.path.relpath(x, ROOT).replace("\\", "/")
               for x in glob.glob(os.path.join(ROOT, g.replace("/", os.sep)), recursive=True)]
        if not [r for r in got if is_live(r)]:
            print("❌ 前置：通配", g, "一篇活的都没扫到 —— 整层被挪走了，"
                  "这不是「没有漂移」。", file=sys.stderr)
            sys.exit(2)
    return out


# ── 实测值 ────────────────────────────────────────────────────────────────
def measure():
    m = {}
    try:
        import _surge_common as sc
        import yaml
    except Exception as exc:                                  # noqa: BLE001
        sys.stderr.write("❌ 前置：导入解析器失败（%s）⇒ 需要 Python3 + PyYAML\n" % exc)
        sys.exit(2)

    for kern, ext, sect in (("surge", "conf", "Proxy Group"), ("egern", "yaml", None)):
        d = os.path.join(ROOT, kern, "profiles")
        for p in sorted(glob.glob(os.path.join(d, "*." + ext))):
            base = os.path.basename(p)
            if ".min." in base:
                continue
            stem = base[:-len("." + ext)]
            form = "lazy" if stem == "lazy" else "routing"
            if ext == "conf":
                s, _ = sc.parse_conf(p)
                grp = [l for _, l in s.get(sect.lower(), []) if sc.strip_comment(l)]
                rul = [l for _, l in s.get("rule", []) if sc.strip_comment(l)]
                rset = [sc.strip_comment(l) for _, l in s.get("rule", [])
                        if sc.strip_comment(l).upper().startswith("RULE-SET")]
            else:
                try:
                    y = yaml.safe_load(open(p, encoding="utf-8"))
                except Exception as exc:                       # noqa: BLE001
                    sys.stderr.write("❌ 前置：%s 解析失败（%s）\n" % (base, exc))
                    sys.exit(2)
                grp = y.get("policy_groups") or []
                rul = y.get("rules") or []
                rset = [r for r in rul if isinstance(r, dict) and "rule_set" in r]
            m["%s_%s_groups" % (kern, form)] = len(grp)
            m["%s_%s_rules" % (kern, form)] = len(rul)
            m["%s_%s_rulesets" % (kern, form)] = len(rset)
        m["%s_files" % kern] = len(glob.glob(os.path.join(d, "*." + ext)))

    m["icons"] = len([p for p in glob.glob(os.path.join(ROOT, "icons", "*"))
                      if os.path.isfile(p)])
    # ── 2026-09-25 补的四类读数：此前这些数在文档里写死、**没有任何判据管**（逐条落位清单共 48 处）
    # ⚠️ 期望值一律**从源头现算** —— 把 16 / 6 / 2 这些数写进判据，判据自己就成了下一个会漂的硬编码。
    arch = open(os.path.join(ROOT, "skill", "tests", "surge", "architecture.sh"),
                encoding="utf-8").read()
    blk = re.search(r"DNS_KEYS = \[(.*?)\]", arch, re.S)
    m["dns_keys"] = len(re.findall(r'"[^"]+"', blk.group(1))) if blk else -1
    for _kern, _runner in (("surge", "skill/tests/surge/run.sh"),
                           ("egern", "skill/tests/egern/run.sh")):
        _txt = open(os.path.join(ROOT, _runner.replace("/", os.sep)), encoding="utf-8").read()
        m["%s_stages" % _kern] = len(re.findall(r"^#   阶段 [0-9]+ · ", _txt, re.M))
        # fixture 数 = **阶段 1 的 CASES 行数** —— 那才是「回归规模」表里的那个数（与断言数同表）。
        # ⚠️ 不是「目录里的 .conf 个数」：`skill/tests/surge/` 另有 `fixtures/bad_region_filter.conf`，
        #    按目录数得 4，而全仓「N fixture」在回归规模语境下都是 3。两种口径并存，判据只能认一种，
        #    取 CASES（会变的那个）；目录注释那句另行改准（见 2026-09-25 CHANGELOG）。
        _cases = re.search(r'CASES="(.*?)"', _txt, re.S)
        m["%s_fixtures" % _kern] = len([
            l for l in (_cases.group(1).splitlines() if _cases else []) if l.strip()])
    # TOTAL 槽位：`all.sh` 里 `MEASURED+=(...)` 的个数（现算）。文档里那句「本轮六个 TOTAL」归它管。
    _csd = open(os.path.join(ROOT, "skill", "scripts", "surge", "check_surge_dns.py"),
                encoding="utf-8").read()
    # 编号**集合**（不只是个数）：A-4 的另一半判据判的是「文档写 `第 N 项`，而审计器里没有
    # 这个号」。只比个数的话，检查号 12 被删掉、文档仍写「第 12 项」就悄悄悬空了。
    m["checker_ids"] = sorted({int(x) for x in re.findall(r"^def check_(\d+)_", _csd, re.M)})
    m["checker_criteria"] = len(m["checker_ids"])
    m["totals"] = len(re.findall(r"MEASURED\+=\(",
                                open(os.path.join(ROOT, "skill", "tests", "all.sh"),
                                     encoding="utf-8").read()))
    # 加固清单项数：**文件名与 H1 里的「N 项」必须等于表格行数**（2026-09-25 补）。
    # ⚠️ 文件名里的数字是"最显眼的承诺"，此前**没有任何判据管** —— 实测 Surge 那份名字停在 12
    #    而表里 14 行（正文自己都引用了第 13/14 项），已随本批改名并留旧名。
    m["checklists"] = {}
    for _p in glob.glob(os.path.join(ROOT, "*", "docs", "03-加固清单-*项.md")):
        _rel = os.path.relpath(_p, ROOT).replace("\\", "/")
        _txt2 = open(_p, encoding="utf-8", errors="replace").read()
        _nm = re.search(r"-([0-9]+)项\.md$", os.path.basename(_p))
        _h1 = re.search(r"^# .*?（([0-9]+) 项）", _txt2, re.M)
        m["checklists"][_rel] = (int(_nm.group(1)) if _nm else -1,
                                 int(_h1.group(1)) if _h1 else -1,
                                 len(re.findall(r"^\| *[0-9]+ *\|", _txt2, re.M)))
    allsh = open(os.path.join(ROOT, "skill/tests/all.sh"), encoding="utf-8").read()
    m["items"] = len(re.findall(r"^item ", allsh, re.M))
    # 「当前是哪一版」自 2026-09-24 起只有一个来源：profile 头注 `#! version=routing_vX.Y`
    #（订阅地址固定化之后，三处 runner 里的 CURRENT 常量已退役）。
    heads = {}
    for rel in HEAD_FILES:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        first = ""
        try:
            with open(p, encoding="utf-8", newline="") as f:
                first = f.readline()
        except OSError:
            pass
        mm = re.match(r"^#! version=((?:routing|lazy)_v[0-9]+\.[0-9])\s*$", first.rstrip("\r\n"))
        heads[rel] = mm.group(1) if mm else None
    m["heads"] = heads
    rout = [heads[f] for f in HEAD_FILES if "routing." in f]
    if len(set(rout)) != 1 or rout[0] is None:
        sys.stderr.write("❌ 前置：两内核 routing 头注读不出或不一致：%s\n" % heads)
        sys.exit(2)
    m["version"] = rout[0]
    m["current_version_num"] = m["version"].split("_v")[-1]
    m["fixed_missing"] = [r for r in HEAD_FILES if not os.path.isfile(os.path.join(ROOT, r.replace("/", os.sep)))]
    # 只要求**同族跨内核相同**：routing 一对、lazy 一对，两族本来就各有版本号
    fams = {f: sorted({heads[r] or "（读不出）" for r in HEAD_FILES if "/%s." % f in r.replace(os.sep, "/")})
            for f in ("routing", "lazy")}
    m["family_drift"] = ["%s 两侧不一致：%s" % (f, v) for f, v in fams.items() if len(v) > 1]
    m["heads_note"] = " · ".join("%s=%s" % (f, "/".join(v)) for f, v in fams.items())
    m["current_ok"] = not m["fixed_missing"] and not m["family_drift"]
    m["current_missing"] = m["fixed_missing"] or m["family_drift"]
    asl = os.path.join(ROOT, "egern", "apple_system.list")
    m["apple_system"] = len([l for l in open(asl, encoding="utf-8").read().splitlines()
                             if l.strip() and not l.startswith("#")]) if os.path.isfile(asl) else -1
    # 本仓自托管的规则集 URL：profile 里写了 `Self-Configuration/main/<路径>`，那个路径必须真实存在
    self_urls = set()
    for p in glob.glob(os.path.join(ROOT, "*/profiles/*")):
        # 只看当前版（顶层固定名四件）；config_old/ 是目录，整段跳过 —— 归档里的 URL
        # 随着旧订阅地址一起作废，不再对外承诺
        if ".min." in os.path.basename(p) or not os.path.isfile(p):
            continue
        for mm in re.finditer(r"Self-Configuration/main/([A-Za-z0-9._/\-]+)",
                              open(p, encoding="utf-8", errors="replace").read()):
            self_urls.add(mm.group(1))
    m["self_urls"] = sorted(self_urls)
    m["self_missing"] = [u for u in sorted(self_urls)
                         if not os.path.isfile(os.path.join(ROOT, u.replace("/", os.sep)))]
    # D18 共用规则集份数的实测值：**同形态**两侧 URL 集合的交集（分流版 21 / 懒人版 6）。
    # ⚠️ 口径：**含被注释的条目** —— 两侧 `Proxy.list` 都注释掉了，但文档承诺的是
    #    「URL 集合逐字相同」（`docs/规则集与来源.md` 的括注写明含它），不是"活跃规则数"。
    #    拿活跃口径去对，一上线就会对着正确的 21 报假红（实测：活跃交集 20 / 含注释 21 / 单侧引用 22+）。
    def _rs_urls(path, key):
        out = set()
        try:
            for line in open(path, encoding="utf-8", errors="replace"):
                if key in line:
                    for mm in re.finditer(r"https?://[^\s,\"'）]+", line):
                        u = mm.group(0)
                        if u.endswith(".list") or u.endswith(".txt"):
                            out.add(u)
        except OSError:
            return set()
        return out
    m["shared_routing"] = len(
        _rs_urls(os.path.join(ROOT, "surge", "profiles", "routing.conf"), "RULE-SET")
        & _rs_urls(os.path.join(ROOT, "egern", "profiles", "routing.yaml"), "match:"))
    m["shared_lazy"] = len(
        _rs_urls(os.path.join(ROOT, "surge", "profiles", "lazy.conf"), "RULE-SET")
        & _rs_urls(os.path.join(ROOT, "egern", "profiles", "lazy.yaml"), "match:"))
    return m


# ── 一行属于哪个「形态 / 内核」 ─────────────────────────────────────────────
def form_of(line, path):
    """这一行讲的是哪个形态。⚠️ **只认行内词，不认文件路径**（A-20 的 ③）。

    路径能推出**内核**（`surge/docs/**` 就是 Surge 侧，稳定），推不出**形态**：
    分流版的设计文档里天生要摆两形态对照表（`| 规则 | 10 条 | 24 条 |`），
    旧写法拿路径里的「分流版」给懒人版那一格配上 expected=24 ⇒ **正确的话被判红**。
    实测（2026-09-25，同一份真 scan() 上对跑）：路径参与推导 4 处假红 → 收成行内只剩 1 处
    （剩下那处是"1 条联网项"的量词歧义，另配行内 filter），代价 3 处比较退回判不出。
    为什么接受这个代价：判不出会出声（进 skipped 并在末尾报数），判错了不出声 ——
    而 ④ 之后"比较数"是打在行上的可见量，少 3 处比较看得见，假红看不见。
    `path` 形参保留：调用方按 (行, 文件) 传，同族的 `kern_of` 仍然要用它。
    """
    low = line.lower()
    lazy = bool(re.search(r"lazy|懒人", low))
    rout = bool(re.search(r"routing|分流|v\d", low))
    if lazy and not rout:
        return "lazy"
    if rout and not lazy:
        return "routing"
    return None


def kern_of(line, path):
    low = line.lower() + " " + path.lower()
    e = bool(re.search(r"egern", low))
    s = bool(re.search(r"surge", low))
    if e and not s:
        return "egern"
    if s and not e:
        return "surge"
    return None


# ── D18 的两个声明模式（scan 与行内判别自证共用同一份，防止"自证测的不是在用的正则"）────
# 判别**只靠同行语义锚，不靠距离参数**。上一轮注释说「个↔逐字相同正好隔 ` URL ` = 5 字符 ⇒
# {0,4} 只是碰巧安全」—— 那是**过期理由**：`expected` 现已按 `form_of` 分形态取数（分流→21/懒人→6），
# 所以即便 SHARED_B 吃到分流版的「21 个 URL 逐字相同」，期望值也是 21 不是 6，不会假红。
# 真正的分工是：SHARED_A 吃「份…共用规则集」与「N 个 URL」，SHARED_B 吃「N 个逐字相同」，
# 两个 filter 各自要求同行语义锚；分流/懒人靠 `form_of` 分流取数，不靠距离参数防串台。）
SHARED_A_RX = re.compile(r"(\d+)\s*份[^。\n]{0,8}共用规则集|(\d+)\s*个\s*URL")


def _shared_a_filter(line):
    # P12（D4 先例）：裸的「N 个 URL」不加限定就吃 —— LIVE 名单里有两份 DetailsReadme，
    # 哪天出现一句「2 个 URL 指向同一文件」就会误判红。语义锚：共用规则集 或 逐字相同/共用。
    return ("共用规则集" in line
            or ("URL" in line and ("逐字相同" in line or "共用" in line)))


SHARED_B_RX = re.compile(r"(\d+)\s*个\s*逐字相同")


def _shared_b_filter(line):
    # 形态词同行才吃（分流版→shared_routing / 懒人版→shared_lazy）。
    # 光有「N 个逐字相同」不带形态词 ⇒ 判不出比哪一形态，跳过（无锚措辞不误伤）。
    # ⚠️ 上一轮这里只认懒人版，分流版一旦不写 URL（`docs/规则集与来源:4` 的「21 个 URL 逐字相同」
    #    被简写成「20 个逐字相同」）就整行漏判 —— 命中数 3→2 仍绿（E3 静默漏判）。补分流版形态词。
    return ("懒人版" in line or "分流版" in line
            or "lazy" in line.lower() or "routing" in line.lower())


# ── README 门面徽章里的读数（A-11，折进 D1/D2 两条、不单立判据）────────────────────
# 为什么单开一条模式：shields.io 把数写死在 **URL 参数**里（`badge/Groups-26%20%7C%2026`），
# 上面那些按中文量词匹配的正则**一个字都吃不到** ⇒ 徽章是全仓最显眼的读数，也是唯一没人对拍的。
# 位置即语义：`A%20%7C%20B` 左 = Surge、右 = Egern（与本仓「Surge/Egern」一贯的排列同序），
# 形态**钉死分流版**（Groups 链到 `#-井然有序` 那张两形态对照表，Rules 链到跨内核差异对照）。
# ⚠️ 左右顺序是一条**假设**，但它只可能造成假红、不可能造成假绿：两侧真分叉时 D0 先判负，
#    而徽章这条对每个数都独立比一次实测 —— 没有「判不出就放过」那一步。
BADGE_RX = re.compile(r"img\.shields\.io/badge/(Groups|Rules)-(\d+)%20%7C%20(\d+)")
BADGE_KIND = {"Groups": "groups", "Rules": "rules"}


def _badge_line(label, a, b):
    """行内判别自证用的合成徽章行（与 README 那两行同形）。"""
    return ("[![%s](https://img.shields.io/badge/%s-%d%%20%%7C%%20%d-8250df"
            "?style=flat-square)](x)" % (label, label, a, b))


# ── A-4 的另一半：文档引用 `check_surge_dns.py` 第 N 项 ⇒ N 必须是真有的编号 ──────────
# ⚠️ **只认同行带工具名的**。手册里还有「第 3 项 / 第 12 项」这种不带工具名的写法
#    （`manual/07-故障排查.md` 那张表的第三列），同一列里混着 `all.sh` 的项数、加固清单编号
#    与审计器编号 —— 靠行内词分不开 ⇒ 判了必误伤，本轮**刻意不判**（宁可少判），
#    并把这条缺口写进 CHANGELOG。
CHECKER_TOOL_ANCHOR = "check_surge_dns.py"
CHECKER_ITEM_RX = re.compile(r"第\s*(\d+)\s*项")


def checker_ref_nums(line):
    """这一行里指向审计器检查项的编号；行内不带工具名 ⇒ 返回空。"""
    return ([int(x.group(1)) for x in CHECKER_ITEM_RX.finditer(line)]
            if CHECKER_TOOL_ANCHOR in line else [])


def checker_ref_problems(m, line):
    """行内判别自证与 `scan()` **共用**这一份（自证测的必须是在用的判据）。"""
    return [n for n in checker_ref_nums(line) if n not in m["checker_ids"]]


def checker_ref_selfproof(m):
    """三查（D15 / D18 / 徽章先例）：① 真话不红 · ② 编错号必红 · ③ 不带工具名不误伤。"""
    hi = max(m["checker_ids"])
    ok = "`check_surge_dns.py` 第 %d 项专查这条" % hi
    bad_ = "`check_surge_dns.py` 第 %d 项专查这条" % (hi + 1)
    bare = "第 %d 项专查这条" % (hi + 1)
    out = []
    if _scan_line(m, ok, "checker"):
        out.append("① 真实编号的引用被判红")
    if not _scan_line(m, bad_, "checker"):
        out.append("② 引用不存在的编号没判红（这条模式空转）")
    if _scan_line(m, bare, "checker"):
        out.append("③ 不带工具名的「第 N 项」被误吃")
    return out


def candidates(m, kern, form, kind):
    """这一类声明在当前行的定位下，实测值可能是哪些。"""
    if kind == "dns_keys":
        return ["dns_keys=%s" % m["dns_keys"]]
    if kind in ("stages", "fixtures"):
        ks = ["surge", "egern"] if not kern else [kern]
        return ["%s=%s" % (k, m["%s_%s" % (k, kind)]) for k in ks]
    # ⚠️ A-20（2026-09-25 四轮对拍审确认）：这里**必须存内核名，不能存元组**。
    #    旧写法 `keys = [("surge", "egern")]` 配下面的 `for k in keys` ⇒ 拼出来的是
    #    `('surge', 'egern')_routing_groups` 这种永不存在的名，`m.get()` 恒 None
    #    ⇒ 这一类**一个候选都给不出**：D1/D2/D3 自引入那次提交起「命中 51 · 实际比较 0」
    #    却整族 ✅（判据空转，且没有任何一条判据看得见）。
    #    为什么不是「把循环改成 `for k, _ in keys`」那六字符修法：元组截断后
    #    行内不带内核名的声明只剩 surge 单边候选 ⇒ **egern 侧改坏测不到**
    #    （注入实测：内核名版报出真分叉，截断版报 0 条）。判据自证见 `k3_selfproof()`。
    keys = ["surge", "egern"] if not kern else [kern]
    forms = [form] if form else ["routing", "lazy"]
    out = []
    for k in keys:
        for f in forms:
            v = m.get("%s_%s_%s" % (k, f, kind))
            if v is not None:
                out.append("%s_%s=%s" % (k, f, v))
    return out


def expected(m, kern, form, kind):
    """按内核 / 形态取实测值；两内核同值时允许不指定内核。"""
    if kind == "version":
        return m["version"]
    if kind in ("icons", "items", "dns_keys", "totals", "checker", "shared"):
        if kind == "checker":
            return m["checker_criteria"]
        if kind == "shared":
            # 不带形态的行按**分流版**判：仓内"N 份共用规则集"的旗舰口径就是分流版
            # （README 门面 · 规则集与来源），懒人版的数实测一律同行带「懒人版」（form_of 认得到）。
            return m["shared_lazy"] if form == "lazy" else m["shared_routing"]
        return m[kind]
    if kind in ("stages", "fixtures"):
        if kern:
            return m["%s_%s" % (kern, kind)]
        vals = {m["surge_%s" % kind], m["egern_%s" % kind]}
        return next(iter(vals)) if len(vals) == 1 else None
    if kind == "files":
        if kern:
            return m["%s_files" % kern]
        vals = {m["surge_files"], m["egern_files"]}
        return next(iter(vals)) if len(vals) == 1 else None
    vals = {x.split("=")[1] for x in candidates(m, kern, form, kind)}
    return next(iter(vals)) if len(vals) == 1 else None


K3 = ("groups", "rules", "rulesets")
# 判的是**集合归属**、没有"与实测比"那条分支的一类 ⇒ ④ 的空转判据对它们不适用
# （实测 deadref 命中 75 · 比较 0：按数判会当场假红）。
NO_CMP = ("deadref",)


def _forked(cands):
    """两内核实测是否**真的**分叉：只把「同一形态内 surge≠egern」算分叉。

    ⚠️ 不能写成"候选值集合大小 > 1"（那是修 ① 之前的旧判据，当时候选恒空所以它从不触发）：
    分流版与懒人版的组数/规则数**本来就该不同**（实测 分流 26 组 / 懒人 3 组）。
    ① 修好后两形态都会进候选表，旧写法就把**跨形态的正常差**当成"两侧已分叉"——
    最终代码上现测：换回旧判据 ⇒ 判负 42 处（正确实现是 0）、跳过 36 行塌到 4 行。
    ⇒ 按形态分桶，桶内凑齐两内核且不等才算分叉；跨形态差只判不出、不判负。
    """
    by = {}
    for c in cands:
        tag, _, val = c.partition("=")
        kern, _, form = tag.partition("_")
        by.setdefault(form, {})[kern] = val
    return any(len(set(v.values())) > 1 for v in by.values() if len(v) == 2)


# 判别自证用的**两组**合成措辞：必须**在用的**三条 RULES 正则吃得到（不另抄一份判据）。
#   ANCH = 内核与形态都写全 ⇒ 真的走到"与实测比"那一步，测 ①真话不红 / ②改数必红；
#   BARE = 内核与形态**都不写** ⇒ 候选表里同时摆着分流/懒人的正常差，
#          测 ③跨形态差不算分叉 / ④单边改坏必红 —— 这两条正是两种坏法的分界，
#          用 ANCH 那句测不出来（它只有单边候选，新旧分叉判据在那句上同形）。
K3_ANCH = {"groups": "Surge 分流版 %d 个策略组",
           "rules": "Surge 分流版 %d 条规则",
           "rulesets": "Surge 分流版 %d 条规则集"}
K3_BARE = {"groups": "两侧各 %d 个策略组",
           "rules": "两侧各 %d 条规则",
           "rulesets": "两侧各 %d 条规则集"}


def _scan_line(m, line, kind):
    """把一行合成措辞喂给**在用的** scan()，返回该类的判负（判别自证的共用底座）。

    只写进临时目录，仓内一个字节都不动 —— 与 `make_min.py` 的 selftest 同一口径。
    """
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "probe.md")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")
        _, bad, _, _ = scan([("probe.md", p)], m)
    return [b for b in bad if "[%s]" % kind in b]


def k3_selfproof(m, kind):
    """D1/D2/D3 的行内判别自证（D15 / D18 先例）：四种坏法各钉一条，缺一条就判负。

      ① 真话不红 —— ANCH 那句（内核 + 形态写全、值取本轮实测）⇒ 不判负；
      ② 改数必红 —— 同一句 +1 ⇒ 判负。**这条就是 A-20 本体**：candidates() 存元组时
         候选恒空 ⇒ 假话也"判不出" ⇒ 此处必红，空转再也绿不了；
      ③ 跨形态正常差不红 —— BARE 那句（不写内核也不写形态，候选表里分流/懒人两形态并列，
         实测 26 与 3 本来就不同）⇒ 只能判不出、不许判负。这条钉住 `_forked` 的形状：
         拿"候选值集合大小 > 1"当分叉判据的写法在此处必红（真仓现测：那样新增 42 处假红）；
      ④ 单边改坏必红 —— BARE 那句 + 只把 egern 侧挪 1 ⇒ 必须判负。
         这条钉住 ① 的修法：元组截断版（`for k, _ in keys`）只剩 surge 单边候选，在此处
         判不出 ⇒ 必红。（①②用 ANCH、③④用 BARE：同一句措辞测不出这两种坏法的差别。）
      ⑤–⑦ README 徽章（A-11）—— 徽章把数写在 shields.io 的 URL 参数里，量词模式吃不到
         ⇒ 单开一条模式，三查：⑤ 真话不红 · ⑥ 右半边（Egern）改数必红 ·
         ⑦ 左半边（Surge）改数必红。这条模式只服务徽章，空转时 D1/D2 仍会靠正文命中数绿着，
         所以自证必须挂在同一条 ck 上（判据条数不变，全仓「固定 18 条规则」的表述不改）。
    """
    out = []
    key = "surge_routing_%s" % kind
    val = int(m[key])
    if _scan_line(m, K3_ANCH[kind] % val, kind):
        out.append("① 真话被判红")
    if not _scan_line(m, K3_ANCH[kind] % (val + 1), kind):
        out.append("② 改数没判红（判据空转，A-20 的坏法）")
    if _scan_line(m, K3_BARE[kind] % val, kind):
        out.append("③ 跨形态正常差被判成分叉")
    m2 = dict(m)
    m2["egern_routing_%s" % kind] = val + 1
    if not _scan_line(m2, K3_BARE[kind] % val, kind):
        out.append("④ 只改坏 egern 侧、行内不写内核名 ⇒ 没判出来（单边候选的坏法）")
    # ⑤–⑦ README 徽章（A-11）：这条模式**只**服务徽章，它空转时 D1/D2 仍会靠正文命中数绿着
    #    ⇒ 必须单独自证。徽章的数在 URL 参数里，中文量词那三条正则碰不到，所以真话/改数各验一次。
    if kind in BADGE_KIND.values():
        _lbl = [k for k, v in BADGE_KIND.items() if v == kind][0]
        _s = int(m["surge_routing_%s" % kind])
        _e = int(m["egern_routing_%s" % kind])
        if _scan_line(m, _badge_line(_lbl, _s, _e), kind):
            out.append("⑤ 徽章真话被判红")
        if not _scan_line(m, _badge_line(_lbl, _s, _e + 1), kind):
            out.append("⑥ 徽章右半边（Egern）改数没判红")
        if not _scan_line(m, _badge_line(_lbl, _s + 1, _e), kind):
            out.append("⑦ 徽章左半边（Surge）改数没判红")
    return out


def scan(docs, m):
    """返回 (checks, bad, skipped, compared)：checks 是「每条规则命中几处声明」，
    compared 是其中**真的走到与实测比**那一步的命中数（与 hits 同单位：逐命中）。"""
    hits = {k: 0 for k in ("groups", "rules", "rulesets", "files", "icons", "items", "deadref",
                          "dns_keys", "stages", "fixtures", "totals", "checker", "shared",
                          "checker_ref")}
    compared = {k: 0 for k in hits}   # 逐命中：与 hits 同单位（同一行两个同类数 = 2 处）
    bad, skipped = [], []
    skipped_seen = set()   # 行级去重：同一 (文件, 行, kind) 只记一处（finditer 一行匹配多个数会重复）

    RULES = [
        # ⚠️ 措辞要放宽：`26 个策略组图标` / `26 个分流组图标` / `26 个图标` 三种写法都在仓里
        #    实测（2026-09-25）：只认「策略组图标」会**漏掉 3 处**（egern/DetailsReadme 的
        #    `:74` 分流组图标、`:398`/`:529` 图标）。锚点写在措辞上就会漏 —— 与 C6 的教训同型。
        ("icons", re.compile(r"(\d+)\s*个(?:策略组|分流组)?图标")),
        # 「N 项检查」只认与 `all.sh` 同行的（否则会把 check_surge_dns.py 的"12 项检查"也算进来）
        ("items", re.compile(r"([0-9]+|[一二三四五六七八九十])\s*项(?:检查|检查通过)"),
         lambda line: "all.sh" in line),
        ("groups", re.compile(r"(\d+)\s*(?:个)?\s*(?:策略组|分组|组)(?!件|织|图标)")),
        # 「N 份」：⚠️ 2026-09-25 实测原模式（`N 份 ` + 反引号扩展名）在**全部 live 文档里 0 命中** ⇒
        #    判据一直空转。文档里真实的写法是「**顶层固定名四件**」（8 处）⇒ 改认「N 件」，
        #    并加**行内过滤**：只认同一行出现「顶层 / 固定名 / 形态」的（否则「三件事」「一份代码」
        #    「两份逐字节相同的拷贝」这类会误命中）。
        ("files", re.compile(r"([0-9]+|[一二三四五六七八九十两])\s*件(?:\s*形态)?"),
         lambda line: ("顶层" in line or "固定名" in line or "形态" in line)),
        # ⚠️ 行内过滤：**「联网项」与「N 条」同行 ⇒ 那个「条」数的是断言条数，不是规则集条数**。
        #    实测反例 `egern/docs/08-审计读数.md` 阶段 2 分项那句「另**完整版两份** × 1 条联网项
        #    （规则集内容 / 分流覆盖）= **2**」—— 正则跨过括号里的「规则集」把"1 条断言"吃成
        #    "1 条规则集"，实测 22 ⇒ 假红。这类"量词相同、所指不同"的行判不出比判错好
        #    （与 C6 的双锚点同口径）。
        ("rulesets", re.compile(r"(\d+)\s*条[^。\n]{0,16}(?:规则集|rule_set)|(?:规则集|rule_set)[^。\n]{0,12}?(\d+)\s*条"),
         lambda line: "联网项" not in line),
        # D18「共用规则集份数」两个模式（正则与 filter 提到模块级，行内判别自证共用同一份）——
        # ⚠️ 不能并进 D3 的正则：D3 对的是**每形态 RULE-SET 引用数**（现 22/8），这里的口径是
        #    **两内核同形态 URL 交集**（现 分流 21 / 懒人 6），扩了正则就是拿错口径判正确的文档
        #    （2026-09-25 双机对拍审确认的陷阱）。所以单立一类、单独实测。
        ("shared", SHARED_A_RX, _shared_a_filter),
        ("shared", SHARED_B_RX, _shared_b_filter),
        ("rules", re.compile(r"(\d+)\s*条[^。\n]{0,10}规则(?!集)|(?:规则|`rules`)[^。\n]{0,8}?(\d+)\s*条")),
        # ── 2026-09-25 补的四类（此前无判据）──────────────────────────────────
        # 「N 个键」的「个」可省：落位清单里 `16 键` 与 `16 个 DNS 键` 两种写法各占一半。
        ("dns_keys", re.compile(r"(\d+)\s*个?\s*(?:DNS\s*)?(?:相关)?键")),
        ("stages", re.compile(r"([0-9]+|[一二三四五六七八九十两])\s*个?\s*阶段")),
        ("fixtures", re.compile(r"(\d+)\s*(?:个|份)?\s*fixture")),
        ("totals", re.compile(r"([0-9]+|[一二三四五六七八九十两])\s*个\s*TOTAL")),
        # surge 审计器的判据数（`def check_N_` 的个数，现算）。
        # ⚠️ 行内过滤：**排除含 egern 的行** —— `docs/跨内核差异对照` 那句「Surge 12 项 / Egern 18 项」
        #    里 18 指的是加固清单（D15 管），与这里的 checker 判据数不是一回事。
        ("checker", re.compile(r"(\d+)\s*项(?:审计清单|判据|检查)"),
         lambda line: "egern" not in line.lower()),
        # ⚠️ 「N 个审计脚本」**刻意不判**（2026-09-25 实测后撤掉）：仓里这个词有两种口径，
        #    且都成立 —— ① `egern/docs/08` 记的是**产出读数的 6 个**；② `skill/scripts/egern/*.py`
        #    去掉共享模块是 **10 个**（多出 probe_* / profile_ruleset / weigh_ruleset 四个探针工具）。
        #    判据按 ② 判会把 ① 那句**正确的话**判负 ⇒ 接不住就不判（宁可少判）。
    ]
    for rel, p in docs:
        text = open(p, encoding="utf-8").read()
        for i, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            form, kern = form_of(line, rel), kern_of(line, rel)
            for spec in RULES:
                kind, rx = spec[0], spec[1]
                if len(spec) > 2 and not spec[2](line):
                    continue
                for mm in rx.finditer(line):
                    g = next((x for x in mm.groups() if x), None)
                    if g is None:
                        continue
                    if kind in ("items", "stages", "totals", "files") and g in CN_NUM:
                        g = str(CN_NUM[g])
                    hits[kind] += 1
                    # 「N 件」这种写法不带扩展名 ⇒ 内核只能靠行/路径判（`kern`），不再从格子里取。
                    k2 = kern
                    want = expected(m, k2, form, kind)
                    if want is not None:
                        compared[kind] = compared.get(kind, 0) + 1
                    if want is None:
                        cands = candidates(m, k2, form, kind)
                        if kind in ("groups", "rules", "rulesets") and _forked(cands):
                            # 两内核 / 两形态实测本身就分了叉 —— 这正是本仓最不能容忍的状态，
                            # 不能当成"判不出"放过
                            bad.append("%s:%d [%s] 两侧实测已分叉 %s，文档写 %s ｜ %s"
                                       % (rel, i, kind, " ".join(cands), g, line.strip()[:70]))
                        else:
                            _sk = (rel, i, kind)   # 行级：同一行同类只记一处（治 skipped 双报）
                            if _sk not in skipped_seen:
                                skipped_seen.add(_sk)
                                skipped.append("%s:%d [%s] `%s`（形态/内核判不出）"
                                               % (rel, i, kind, line.strip()[:60]))
                        continue
                    if str(want).isdigit() and int(g) != int(want):
                        bad.append("%s:%d [%s] 文档写 %s，实测 %s ｜ %s"
                                   % (rel, i, kind, g, want, line.strip()[:70]))
            # `check_surge_dns.py 第 N 项`（A-4）：编号必须真实存在。计数走 `checker_ref` 这个
            # 独立键（不混进 `checker` 的「N 项审计清单」声明数，那是两种口径），但判负行
            # 统一打 `[checker]` 标签 ⇒ 归 D17 那条 ck 收尾，判据条数不变。
            _crn = checker_ref_nums(line)
            hits["checker_ref"] += len(_crn)
            compared["checker_ref"] += len(_crn)
            for _n in checker_ref_problems(m, line):
                bad.append("%s:%d [checker] 文档引用 check_surge_dns.py 第 %d 项，"
                           "实测编号 %s ｜ %s"
                           % (rel, i, _n, m["checker_ids"], line.strip()[:70]))
            # README 徽章（A-11）：一行两个数，左 Surge｜右 Egern、形态分流版（见 BADGE_RX 注释）。
            # 计数记在 groups / rules 这两类上 ⇒ D1/D2 的**判据条数不变**（全仓「18 条」的表述不改）。
            for mm in BADGE_RX.finditer(line):
                _bk = BADGE_KIND[mm.group(1)]
                for _pos, _kern in ((2, "surge"), (3, "egern")):
                    hits[_bk] += 1
                    compared[_bk] += 1
                    _want = m["%s_routing_%s" % (_kern, _bk)]
                    if int(mm.group(_pos)) != int(_want):
                        bad.append("%s:%d [%s] 徽章（%s · %s 侧）写 %s，实测 %s ｜ %s"
                                   % (rel, i, _bk, mm.group(1), _kern,
                                      mm.group(_pos), _want, line.strip()[:70]))
            # 引用不悬空：写出的 profile 文件名要么在当前版固定名里，要么在 config_old/ 归档里；
            # 但**订阅 URL**（Self-Configuration/main/…/profiles/xxx）只准用固定名 —— 那是永久地址。
            for mm in re.finditer(r"\b(routing[A-Za-z0-9._]*|lazy)\.((?:min\.)?)(conf|yaml)\b", line):
                name = "%s.%s%s" % (mm.group(1), mm.group(2), mm.group(3))
                hits["deadref"] = hits.get("deadref", 0) + 1
                side = "surge" if mm.group(3) == "conf" else "egern"
                d = os.path.join(ROOT, side, "profiles")
                if not (os.path.isfile(os.path.join(d, name))
                        or os.path.isfile(os.path.join(d, "config_old", name))):
                    bad.append("%s:%d [deadref] 文档指向 %s，profiles/ 与 profiles/config_old/ 里都没有 ｜ %s"
                               % (rel, i, name, line.strip()[:70]))
            for mm in re.finditer(r"Self-Configuration/main/[A-Za-z0-9._/\-]*?profiles/"
                                  r"([A-Za-z0-9._\-]+?\.(?:min\.)?(?:conf|yaml))", line):
                name = mm.group(1)
                hits["deadref"] = hits.get("deadref", 0) + 1
                if name not in FIXED_NAMES:
                    bad.append("%s:%d [deadref] 订阅 URL 用了非固定名 %s（永久地址只认这四个）｜ %s"
                               % (rel, i, name, line.strip()[:70]))
    return hits, bad, skipped, compared


def main():
    m = measure()
    docs = live_docs()
    if not docs:
        sys.stderr.write("❌ 前置：找不到任何待扫描的文档\n")
        return 2
    print("实测：懒人版 组 %s/%s 规则 %s/%s 规则集 %s/%s（Surge/Egern）· "
          "分流版 组 %s/%s 规则 %s/%s 规则集 %s/%s · profile 文件 %s/%s · "
          "图标 %s · 检查项 %s · 当前版 %s · apple_system %s 条 · 扫描 %d 篇文档"
          % (m["surge_lazy_groups"], m["egern_lazy_groups"],
             m["surge_lazy_rules"], m["egern_lazy_rules"],
             m["surge_lazy_rulesets"], m["egern_lazy_rulesets"],
             m["surge_routing_groups"], m["egern_routing_groups"],
             m["surge_routing_rules"], m["egern_routing_rules"],
             m["surge_routing_rulesets"], m["egern_routing_rulesets"],
             m["surge_files"], m["egern_files"], m["icons"], m["items"],
             m["version"], m["apple_system"], len(docs)))

    checks = []
    ck = lambda name, cond, extra="": checks.append((name, bool(cond), extra))  # noqa: E731
    hits, bad, skipped, compared = scan(docs, m)

    # D0：结构不变量本身 —— 两内核的组数 / 规则条数 / 规则集条数必须成对相等。
    #      文档声明类判据抓的是"文档没跟上"，这一条抓的是"两侧不一致"：
    #      只动一侧时，很多声明行因为带内核名仍然各说各话、逐条看都不算错，
    #      只有把两侧放一起比才红得出来（实测：把 Surge 懒人版一条规则注释掉 ⇒ 只有 D0 报）。
    pairs = [(f, k) for f in ("routing", "lazy")
             for k in ("groups", "rules", "rulesets")]
    off = ["%s %s：%s≠%s" % (f, k, m["surge_%s_%s" % (f, k)], m["egern_%s_%s" % (f, k)])
           for f, k in pairs if m["surge_%s_%s" % (f, k)] != m["egern_%s_%s" % (f, k)]]
    ck("D0 两内核逐位对齐（实测 %d 对）" % len(pairs), not off, "\n      " + "\n      ".join(off))
    NAMES = {"groups": "D1 策略组数", "rules": "D2 规则条数", "rulesets": "D3 规则集条数",
             "files": "D4 订阅文件份数", "icons": "D5 图标数", "items": "D6 检查项数",
             "deadref": "D8 profile 引用不悬空·订阅 URL 用固定名",
             "dns_keys": "D11 DNS 键数", "stages": "D12 阶段数",
             "fixtures": "D13 fixture 数", "totals": "D16 TOTAL 槽位数",
             "checker": "D17 surge 审计器判据数", "shared": "D18 共用规则集份数（含注释项·同形态交集口径）"}
    for kind in ("groups", "rules", "rulesets", "files", "icons", "items", "deadref",
                 "dns_keys", "stages", "fixtures", "totals", "checker"):
        sub = [b for b in bad if "[%s]" % kind in b]
        n = hits.get(kind, 0)
        # ⚠️ **命中 0 处也判负**：0 命中说明这一类声明在文档里根本不存在（措辞变了 / 判据写死了），
        #    判据在**空转**却不是"没有漂移" —— 与 C1/C2/C5/C6 同一条纪律（2026-09-25 补，
        #    起因：D4 实测 0 命中却一直 ✅）。
        # ⚠️ A-20 的 ④：上面那条纪律治"命中 0"，这一条治**命中 >0 却一次都没比** ——
        #    旧写法只看 `n > 0` ⇒ D1/D2/D3 长期「命中 51 ｜ 比较 0」而整族 ✅。
        #    比较数打在行上，这一轮涨到哪儿一眼可见，不必再靠人翻代码确认有没有真比。
        #    `NO_CMP` 那类判的是集合归属、天然没有比较分支，豁免并在注释里写明理由。
        #    K3 三类另带**行内判别自证**（`k3_selfproof`）：折进同一条 ck ⇒
        #    判据条数不变（全仓「18 条」的表述有 19 处、其中 4 处被 C6 锚住，单立第 19 条
        #    等于把这 4 处同时改红，属维护者裁决面）。
        cmp_n = compared.get(kind, 0)
        proof = (k3_selfproof(m, kind) if kind in K3
                 else checker_ref_selfproof(m) if kind == "checker" else [])
        _tail = ""
        if kind in K3:
            _tail = (" · 含判别自证：真话不红 · 改数必红 · 跨形态差不算分叉 · 单边改坏必红"
                     + (" · 徽章两类数左右各判一次" if kind in BADGE_KIND.values() else ""))
        elif kind == "checker":
            _tail = (" · 另判 `check_surge_dns.py 第 N 项` 引用 %d 处"
                     "（编号须真实存在 · 自证：真话不红 · 编错号必红 · 不带工具名不误吃）"
                     % hits.get("checker_ref", 0))
        ck("%s（命中 %d 处声明 ｜ 实际比较 %d 处%s）"
           % (NAMES[kind], n, cmp_n, _tail),
           not sub and n > 0 and (kind in NO_CMP or cmp_n > 0) and not proof,
           "\n      " + "\n      ".join(sub[:6] + proof))

    # D18 单独收尾：通用断言 + **行内判别自证**（D15 先例）。自证吃的是**在用的**那两个
    # 正则与 filter（模块级共用），断言「真话不红 · 改数必红 · 无锚措辞不误伤」，
    # 并把上一轮只能手改手回的反例固化成任何机器 `python check_doc_readings.py` 都可复跑。
    def _shared_nums(line):
        out = []
        for rx, flt in ((SHARED_A_RX, _shared_a_filter), (SHARED_B_RX, _shared_b_filter)):
            if flt(line):
                for g in rx.finditer(line):
                    v = next((x for x in g.groups() if x), None)
                    if v:
                        out.append(int(v))
        return out

    def _shared_check(line):
        want = expected(m, None, form_of(line, "fixture.md"), "shared")
        return [(g, want) for g in _shared_nums(line) if want is not None and g != want]

    _sp_bad = []
    if _shared_check("分流版两侧 %d 个 URL 逐字相同" % m["shared_routing"]):
        _sp_bad.append("分流版真话被判红")
    if not _shared_check("分流版两侧 %d 个 URL 逐字相同" % (m["shared_routing"] + 1)):
        _sp_bad.append("分流版改数没判红")
    # E3（本轮补）：分流版**不写 URL** 的简写措辞也要判得到 —— 上一版 SHARED_B 只认懒人版，
    # 「分流版 20 个逐字相同」整行漏判、命中数 3→2 仍绿。扩形态词后必红。
    if _shared_check("分流版两侧 %d 个逐字相同" % m["shared_routing"]):
        _sp_bad.append("分流版漏 URL 的真话被判红")
    if not _shared_check("分流版两侧 %d 个逐字相同" % (m["shared_routing"] + 1)):
        _sp_bad.append("分流版漏 URL 改数没判红（E3 静默漏判）")
    if _shared_check("懒人版两侧 %d 个逐字相同" % m["shared_lazy"]):
        _sp_bad.append("懒人版真话被判红")
    if not _shared_check("懒人版两侧 %d 个逐字相同" % (m["shared_lazy"] + 1)):
        _sp_bad.append("懒人版改数没判红")
    if _shared_nums("这 2 个 URL 指向同一文件"):
        _sp_bad.append("无锚措辞被误吃")
    sub = [b for b in bad if "[shared]" in b]
    n = hits.get("shared", 0)
    ck("%s（命中 %d 处声明 · 含判别自证：分流/懒人真话不红 · 改数必红 · 分流版漏 URL 也判得到 · 无锚措辞不误伤）"
       % (NAMES["shared"], n), not sub and n > 0 and not _sp_bad,
       "；".join(["\n      " + x for x in (sub[:6] + _sp_bad)]))
    ck("D7 本仓自托管 URL 的落点存在（%d 个）" % len(m["self_urls"]), not m["self_missing"],
       "\n      缺文件：%s" % ", ".join(m["self_missing"]))
    ck("D9 头注即当前版·同族跨内核一致且固定名四件齐：%s" % m["version"],
       m["current_ok"], "问题：%s ｜ 头注：%s"
       % (", ".join(m["current_missing"]), m["heads_note"]))
    _ck = checklist_problems(m["checklists"])
    _ck_ok = (not _ck
              and checklist_problems({"x": (3, 3, 3)}) == []
              and checklist_problems({"x": (3, 3, 4)}) != []
              and checklist_problems({"x": (3, 4, 3)}) != [])
    ck("D15 加固清单项数：文件名与 H1 == 表格行数（%d 份 · 含判别自证：同名不红 · 文件名错必红 · H1 错必红）"
       % len(m["checklists"]), bool(m["checklists"]) and _ck_ok, "；".join(_ck[:4]))

    n_wv, n_wvf, wv_bad = waive_readings()
    ck("D10 豁免行形状与消费方正则同形·编号文件内唯一（当前版 %d 行 / %d 个文件）"
       % (n_wv, n_wvf), not wv_bad, "\n      " + "\n      ".join(wv_bad[:6]))

    print("\n对拍 %d 处声明 ｜ 实际比较 %d 处 ｜ 判据 %d 条 ｜ 无法判定跳过 %d 行"
          % (sum(hits.values()), sum(compared.values()), len(checks), len(skipped)))
    for s in skipped[:8]:
        print("   ↷ " + s)
    if len(skipped) > 8:
        print("   ↷ …另有 %d 处" % (len(skipped) - 8))
    bad_ = [c for c in checks if not c[1]]
    for name, ok_, extra in checks:
        print("   %s %s%s" % ("✅" if ok_ else "❌", name,
                              extra if not ok_ and extra.strip() else ""))
    print("TOTAL: %d passed, %d failed" % (len(checks) - len(bad_), len(bad_)))
    return 1 if bad_ else 0


if __name__ == "__main__":
    # Windows GBK 终端里 print 中文/emoji 会 UnicodeEncodeError ⇒ 退出码 1，
    # 看着像判负、其实一条都没判。与 bump_version.py / make_min.py 同款兜底。
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:                                      # noqa: BLE001
            pass
    sys.exit(main())
