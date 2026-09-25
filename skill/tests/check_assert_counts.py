#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回归断言数对拍（`all.sh` 第 7 项）：文档里写死的「19 断言 / 22 断言」↔ 本轮实测的 TOTAL。

为什么单独立一项，而不是并进 `check_doc_readings.py` 的 D 规则：
  D1–D3 对拍的是**解析 profile 就能算出来**的读数（组数 / 规则条数 / 规则集条数）。
  而那个脚本的头注里明写着**不判**"判据 / 回归的断言数 —— 那要真跑测试才有值，递归且不划算"。
  这一项不推翻那个判断，而是把它缺的那个输入从外面喂进来：`all.sh` 刚跑完前 6 项，
  手里正有本轮的六个 TOTAL ⇒ 本脚本只做"文档数 ↔ 实测数"的比对，**自己不跑任何测试**（不递归）。
  治的是这类漂移：runner 加了一条断言（23 → 27 那种），十来篇文档一处没跟，
  而仓里**没有任何检查会因为"断言数变了"而报错** —— 只能一轮轮 grep 反查。

六条判据（**固定条数**，不随文档数 / 声明数增长 —— 与其余判据同一口径）：
  C1 Surge 侧总数声明 == 本轮 Surge 实测（且**至少有一处**在声明它，否则判据空转）
  C2 Egern 侧总数声明 == 本轮 Egern 实测（同上）
  C3 认不出内核的并排声明（表行里没有表头、格子里又没写内核名）里的数，都要是本轮某个实测值
  C4 判别自证：同一串数字换措辞**不红** · 数字改一个**必红** · 三种写法都认得下来 ·
     无表头可依那一类也真的判得到（四条缺一条 ⇒ C4 红）
  C5 文档写给 `check_tools.py` 的「固定 N 条判据」== 本轮 tools 实测（同样不许空转；
     判别自证随条内置 —— 改一个数必红 · 同数换措辞不红 · 别的脚本名行不许归进来）
  C6 文档写给 `check_portability.py` / `check_doc_readings.py` 的「固定 N 条规则」== 本轮实测
     （同样不许空转 —— 两个实测键各自至少命中 1 处；锚点同行认**脚本名或类别短语**，
      因为 `AGENTS.md §1` 里那两个数与脚本名换了行）

归属怎么认（决定红在哪一侧）：先按**表格列**问表头「这一列在说哪一侧」，再退到格子文本里的
内核名、整行的内核名、文件路径（`surge/` / `egern/`）。全落空才交 C3。

C5 治的是复测出来的一个洞（2026-09-24 定）：`all.sh` 早把 `tools=$LAST_NUM` 传了进来，
但 `KERNEL_KEYS` 只有两侧内核 —— 文档写给 `check_tools.py` 的「固定 6 条判据」没有任何判据
拿它比本轮实测，T6 一加（6→7）那个数就静默陈旧。锚点**按行取**：数字与 `check_tools.py`
必须同在一行 —— 宁可在文档重排 wrapping 时"命中 0 处 ⇒ 判负"出声，也不拿 ±1 行的窗口
去猜归属（`AGENTS.md` §1 那两句「固定 6 条」「固定 4 条」恰好上下相邻，放宽窗口就是串台）。
本数的口径：它**不钉自己的 6**（判据判自己的条数是递归，`all.sh` 里"判据的判据会递归"那句
同样管这里）。`portability` 的 18 与 `doc_readings` 的 11 原先也属"同类未钉"，**C6 起已钉**
（2026-09-25 定：那两个数在 `AGENTS.md §1` 里写死，此前没有任何判据拿它比本轮实测）。

只判**总数**，不判分项表（`surge/docs/08` 那张逐阶段表、`run.sh` 注释里的"3 个断言"）：
  分项数要么随 fixture 数漂、要么一行只覆盖一个阶段，把它们钉成死数会让每次加断言都要改表格；
  总数是文档对外承诺的那个数，也正是"改了 runner 忘同步"最容易漏的那个。
  这类"没判到"不静默：末尾照 `check_doc_readings.py` 的口径报「跳过 N 处」。

一行算不算"总数声明"，看它有没有**阶段总数标记** = 数字出现在「阶段」二字**前面**
（`6 阶段` / `六个阶段` / `两阶段`）。这一条同时把四种写法挡在外面：
  · `阶段 1（… = 10 断言）+ 阶段 2（…）`   —— 数字挂在单个阶段上 ⇒ 数字在「阶段」**后面** ⇒ 不判
  · `把五份同时喂给两个脚本、共 10 个断言` —— 同上，无阶段总数标记 ⇒ 不判
  · `共 3 条断言` / `16 键一致性断言`      —— 单位不是「(个)断言」⇒ 不判
  · `DNS 段已被阶段 3 断言为逐字相同`      —— 「断言」在这儿是**动词**：看「阶段」前面有没有
                                            数词（`两阶段 18` 有 ⇒ 是条数；`被阶段 3` 没有 ⇒ 不判）

用法：python skill/tests/check_assert_counts.py surge=19 egern=18 min_pair=18 ...
      （由 `all.sh` 第 7 项自动带上本轮六个 TOTAL；`--offline` 档 all.sh **不调本脚本**，
       因为离线时 Surge 侧少跑 4 条联网断言（实测 15），与文档的联网口径是两个数 ——
       拿它比对必然假红，而把它算成一条通过更是假绿。）
退出码：0 全过 · 1 有判负 · 2 前置不达标（没给实测值 / 值不是整数 / 一篇文档都没找到）
"""

import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))              # <仓根>/skill/tests
ROOT = os.path.dirname(os.path.dirname(HERE))                   # → skill → 仓根

# 阶段总数标记：`6 阶段` / `六个阶段` / `两阶段`（数字在「阶段」前面才算总数）
_CN = "一二三四五六七八九十两"
MARKER = re.compile(r"(?:[0-9]+|[%s])\s*个?\s*阶段" % _CN)
# 总数声明本体：`19 断言` / `19 个断言` / `… = 18 断言`。
# `(?<!\d)` 挡的是"从 18 里截一个 8 出来"这种回退匹配（实测撞在 `两阶段 18 断言` 上）。
DECL = re.compile(r"(?<!\d)(\d+)\s*(?:个\s*)?断言")
# 「阶段 3 断言为逐字相同」里的「断言」是**动词**（实测在 surge/docs/08:81），不是条数。
# 分不开形状、只看「阶段」前面是什么：跟着数词 ⇒ 那是阶段总数标记、后面的数是条数；
# 跟着别的字 ⇒ 那是"第 N 阶段" + 动词，不判。
_STAGE_TAIL = re.compile(r"阶段\s*$")
_NUM_TAIL = re.compile(r"(?:[0-9]|[%s])\s*个?\s*$" % _CN)
# 历史记录类整篇不扫：那里的旧数字是**那一轮**的观测值，改成现在的数才是错。
HISTORY = ("CHANGELOG", "体检报告", "日志旧版原文", "/docs/07-", "/.git/")

# C5：写给 check_tools.py 的判据条数。行级锚点 —— 数字与脚本名不同行就不算（见头注）。
TOOL_DECL = re.compile(r"固定\s*(\d+)\s*条判据")
TOOL_ANCHOR = "check_tools.py"

# C6：写给 portability / doc_readings 的**规则条数**。同 C5 的行级锚点口径。
# 为什么单列一条：那两个数（`AGENTS.md §1` 的「固定 18 条规则」「固定 11 条规则」）此前
# 没有任何判据拿它比本轮实测 —— 加一条规则、数字忘了改，静默陈旧（2026-09-25 定）。
RULE_DECL = re.compile(r"固定\s*(\d+)\s*条规则")
# 治 gate1 静默丢（2026-09-25 对拍审问题 2）：有人在锚点行把「固定 18 条规则」改写成
# 「固定 11 条」（漏了单位词「规则」），`RULE_DECL` 不匹配 ⇒ 整行在 gate1 前 `continue` 掉，
# 连 skipped 都不进 ⇒ C6 命中数 6→5 仍绿（E4b）。这条**只配合锚点行**用的宽松式专门接这种
# "带锚点却漏单位词"的声明，折进 decls 按本轮实测判红——不靠"命中数下限"那种一改文档就抖的脆判据。
RULE_LOOSE = re.compile(r"固定\s*(\d+)\s*条")
# ⚠️ 锚点要**同时**认脚本名与类别短语：`AGENTS.md §1` 里那两个数与脚本名**换了行**
#    （数字在 :34 / :35，脚本名在 :36 / :37），只按脚本名锚定会一条都命中不了 ——
#    实测：C6 第一次上线就报「check_doc_readings.py 一处声明都没有 ⇒ 判据空转」。
#    按行取仍是硬口径：类别短语与数字必须**同一行**。
RULE_ANCHORS = (("portability", ("check_portability.py", "换设备可移植性")),
                ("doc_readings", ("check_doc_readings.py", "文档读数与实测对拍")))


def find_rule_decls(text, rel):
    """→ (decls, skipped)。decls = [(行号, 实测键, N)]；skipped = 有「固定 N 条规则」但认不出归属的行。

    同一行命中多个锚点只算一次；认不出归属的**不静默**（进 skipped，末尾照常报「跳过 N 处」）——
    例：`docs/跨内核差异对照.md` 里那句「它报的是固定 18 条规则通过与否」只有代词、没有锚点。
    ⚠️ 锚点行写了「固定 N 条」却漏单位词「规则」的，折进 decls 按实测判（治 E4b 的 gate1 静默丢）。
    """
    decls, skipped = [], []
    for i, line in enumerate(text.splitlines(), 1):
        keys = [k for k, anchors in RULE_ANCHORS if any(a in line for a in anchors)]
        if RULE_DECL.search(line):
            if not keys:
                skipped.append("%s:%d 「固定 N 条规则」认不出归属（同行既无脚本名也无类别短语，只报不判）"
                               % (rel, i))
                continue
            for key in keys:
                decls.extend((i, key, int(m.group(1))) for m in RULE_DECL.finditer(line))
        elif keys and RULE_LOOSE.search(line):
            # 带锚点、有「固定 N 条」、却漏「规则」二字 ⇒ 静默漏判的漂移声明，折进来判红。
            for key in keys:
                decls.append((i, key, int(RULE_LOOSE.search(line).group(1))))
    return decls, skipped

KERNEL_KEYS = ("surge", "egern")
MEASURED_KEYS = KERNEL_KEYS + ("min_pair", "portability", "doc_readings", "tools")


def docs():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        if any(h in "/" + rel for h in HISTORY):
            continue
        out.append((rel, p))
    return out


def cell_kernel(text):
    """这一格里只出现一侧的内核名时，它就在说那一侧。"""
    low = text.lower()
    found = tuple(k for k in KERNEL_KEYS if re.search(r"\b%s\b" % k, low))
    return found[0] if len(found) == 1 else None


def col_kernels(lines, idx):
    """表格行：往上找表头，认「哪一列在说哪一侧」→ {列号: 内核}。

    为什么要这一层：README 的门面表与 `docs/跨内核差异对照.md` 的脚本表把两侧的断言数写在
    **同一行的两格里**，格子里只有数字、内核名在表头。光看格子与整行都认不出归属 ⇒ 那一行
    的 19 与 18 只能退成"是本轮某个实测值就行"。实测：把两格的 19/18 整整齐齐互换，
    不认列的判据**照样绿**（两个数都还在实测里）；认了列之后互换必红（18 落进 Surge 列）。
    找不到表头就返回空 ⇒ 退回逐格判断，不硬猜。
    """
    if not lines[idx].strip().startswith("|"):
        return {}
    rows, i = [], idx - 1
    while i >= 0 and lines[i].strip().startswith("|"):
        rows.append(i)
        i -= 1
    for j in reversed(rows):                       # 从上往下，第一个能把两侧分开的就算表头
        cells = lines[j].split("|")
        km = dict((n, cell_kernel(c)) for n, c in enumerate(cells) if cell_kernel(c))
        if len(set(km.values())) == 2:
            return km
    return {}


def kernel_of(cell, line, rel):
    """这一处声明属于哪一侧？格子里没有就到整行，行里没有就到路径；再没有就交 C3。"""
    for text in (cell, line, rel):
        low = text.lower()
        found = tuple(k for k in KERNEL_KEYS if re.search(r"\b%s\b" % k, low))
        if len(found) == 1:
            return found[0]
    return None                      # 认不出 ⇒ 交给 C3（只要求是本轮某个实测值）


def _is_verb(text, start):
    """「…被阶段 3 断言为逐字相同」里的数是阶段号，不是条数 —— 看「阶段」前面有没有数词。"""
    m = _STAGE_TAIL.search(text[:start])
    return bool(m) and not _NUM_TAIL.search(text[:m.start()])


def decl_nums(text):
    """一段文本里的**总断言数**声明（已过动词过滤）。"""
    return [int(m.group(1)) for m in DECL.finditer(text) if not _is_verb(text, m.start())]


def find_decls(text, rel):
    """→ (decls, skipped)。decls = [(行号, 内核 or None, [数, ...])]；skipped = 有「断言」无总数标记的行。"""
    decls, skipped = [], []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if "断言" not in line:
            continue
        if not MARKER.search(line):
            m = DECL.search(line)
            if m and not _is_verb(line, m.start()):
                skipped.append("%s:%d [%s] `%s`（分项 / 无阶段总数标记，只报不判）"
                               % (rel, i, "/".join(str(x) for x in decl_nums(line)), line.strip()[:60]))
            continue
        kmap = col_kernels(lines, i - 1)
        for n, cell in enumerate(line.split("|")):
            nums = decl_nums(cell)
            if nums:
                decls.append((i, kmap.get(n) or kernel_of(cell, line, rel), nums))
    return decls, skipped


def find_tool_decls(text, rel):
    """C5 取数：含 `check_tools.py` 的行上的「固定 N 条判据」→ [(行号, N)]。"""
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if TOOL_ANCHOR in line:
            out.extend((i, int(m.group(1))) for m in TOOL_DECL.finditer(line))
    return out


# C5 的判别样本（内存，不碰仓文件）—— 按 C4 先例立"红的是数、不是措辞"，
# 外加两条**归属门**的反例：光有"条判据"三个字不许归进来（那是别的脚本的数）。
TOOL_FIX_SAME = (
    ("x", "**固定 %d 条判据**，见 `skill/tests/check_tools.py`）·"),
    ("y", "`skill/tests/check_tools.py`（**固定 %d 条判据**）由 all.sh 第 6 项串跑"),
)
TOOL_FIX_OTHER_SCRIPT = "回归断言数对拍（**固定 4 条判据**，见 `skill/tests/check_assert_counts.py`）"
TOOL_FIX_NO_ANCHOR = "本模块**固定 9 条判据**，不随文档数增长"


def selfproof_tool(measured):
    """→ (通过?, 说明)。四条：同数换措辞取数一致 · 改一个数必被抓 · 别的脚本名行不归 · 无锚点行不归。"""
    errs = []
    n = measured["tools"]
    got = [x for _ln, x in find_tool_decls(TOOL_FIX_SAME[0][1] % n, "AGENTS.md")]
    got2 = [x for _ln, x in find_tool_decls(TOOL_FIX_SAME[1][1] % n, "skill/README.md")]
    if got != [n] or got2 != [n]:
        errs.append("同数换措辞取数不稳 %s/%s（应各 [%d]）" % (got, got2, n))
    drift = [x for _ln, x in find_tool_decls(TOOL_FIX_SAME[0][1] % (n + 1), "AGENTS.md")]
    if drift != [n + 1]:
        errs.append("样本里的 %d 没被提出来 ⇒ C5 对数字不敏感" % (n + 1))
    if find_tool_decls(TOOL_FIX_OTHER_SCRIPT, "AGENTS.md"):
        errs.append("写着 check_assert_counts.py 的行被归给了 tools ⇒ 归属门漏（串台到别人的数）")
    if find_tool_decls(TOOL_FIX_NO_ANCHOR, "docs/x.md"):
        errs.append("无脚本名的「固定 9 条判据」被归进来 ⇒ 锚点是措辞不是脚本名")
    return (not errs), "；".join(errs)


def parse_measured(argv):
    """`all.sh` 传进来的 `k=v`；缺键或值不是整数 ⇒ 前置不达标（没跑成不等于跑绿）。"""
    got = {}
    for a in argv:
        if "=" not in a:
            sys.stderr.write("❌ 前置：实测值写法应为 key=value，收到 `%s`\n" % a)
            sys.exit(2)
        k, v = a.split("=", 1)
        if k not in MEASURED_KEYS:
            sys.stderr.write("❌ 前置：不认识的 key %s（本脚本认：%s）\n"
                             % (k, " ".join(MEASURED_KEYS)))
            sys.exit(2)
        if not re.fullmatch(r"-?\d+", v.strip()):
            sys.stderr.write("❌ 前置：%s 的实测值不是整数：%s ⇒ 上一项没跑出 TOTAL？\n" % (k, v))
            sys.exit(2)
        got[k] = int(v)
    missing = [k for k in KERNEL_KEYS if k not in got]
    if missing:
        sys.stderr.write("❌ 前置：缺少 %s 的实测值 ⇒ 无法对拍（给全 %s）\n"
                         % (" ".join(missing), " ".join(MEASURED_KEYS)))
        sys.exit(2)
    if "tools" not in got:
        # C5 的比数来源是第 6 项的 TOTAL。缺它不是"少判一条"，是拿缺失值空转 —— 按前置算，
        # 与"上一项没跑出 TOTAL"同一条罪（没跑成不等于跑绿）。
        sys.stderr.write("❌ 前置：缺少 tools 的实测值 ⇒ C5 无从对拍（第 7 项需要第 6 项的 TOTAL）\n")
        sys.exit(2)
    return got


# ── 判别自证用的三份内存样本（不碰仓里任何文件） ────────────────────────────
# 为什么要在判据里带样本：解析式一旦过度贴合"今天这几个文件的措辞"，下一次改文档的人会拿到
# 一次红给左手的失败，最省事的处置是放宽正则 —— 那是 CHANGELOG 里点名过的作弊路径。
# 立住"同数换措辞不红 / 改一个数必红"，才说明红的是**数**、不是**措辞**。
# ⚠️ 样本里的数必须**参数化**成本轮实测值（照 C5 的 `TOOL_FIX_SAME` 那套写法）。
#    原先写死 18：回归断言数一变（例：给 runner 加一条断言），C4 就会红在
#    「同数换措辞提取不一致 [[18], [18]]（应 [22]）」—— 真因只是样本里的死数字，
#    解析器完全正常；维护者会被这条红引向错误方向，还得为一个常量去动冻结文件。
#    2026-09-25 实测坐实（`--` 传 egern=22 复现）。
FIX_SAME_NUMBER = (
    ("a", "两阶段共 **%d 个断言**，退出码非 0 即失败："),
    ("b", "两阶段 · %d 断言（阶段 1 · 5 fixture ×2；阶段 2 · 四件 ×2）"),
)


def wrong_number_sample(measured):
    """C4 ②「改一个数必红」的样本：那个数要**现算**成"本轮实测里不存在"的值（实测最大值 +1）。

    写死一个数（原先是 20）迟早会撞上某个实测值 —— 那时 C4 会以假红的面目出现。
    与 `FIX_SAME_NUMBER` 写死 18 是同一个病：样本与本轮实测耦合，却耦合在常量上。
    """
    return ("| 自检读数 | 5 个审计脚本 + 6 阶段 · %d 断言 | "
            "10 个审计脚本 + 2 阶段 · 18 断言 |" % (max(measured.values()) + 1))
FIX_THREE_SPELLINGS = (
    ("6 阶段 · 19 断言", [19]),
    ("6 阶段 · 19 个断言", [19]),
    ("回归测试两阶段（10 + 8 = 18 断言）", [18]),
)
# ④ 认不出内核的那一类（C3）也要有反例：不认列的表行里塞一个不存在的数 ⇒ 必须判出来。
#    不立这一条，C3 在"当前仓里恰好没有无表头的表行"时就是一条**永远不会红**的判据
#    —— 与本轮刚修掉的 `check_min_pair.py:115` 同一种罪。
FIX_UNATTRIBUTED = "| 回归规模 | 6 阶段 · 77 断言 · 3 fixture | 2 阶段 · 18 断言 · 5 fixture |"


def selfproof(measured):
    """→ (通过?, 说明)。四条都要立：同数换措辞不红、改数必红、三式都认、无表头表行也判得到。"""
    errs = []
    # ① 同一串数字换措辞 ⇒ 提取结果必须一样，且都不红
    n_egern = measured["egern"]
    got = []
    for _, line in FIX_SAME_NUMBER:
        d, _sk = find_decls(line % n_egern, "egern/docs/x.md")
        got.append(d[0][2] if d else None)
    if got[0] != got[1] or got[0] != [measured["egern"]]:
        errs.append("同数换措辞提取不一致 %s（应 %s）" % (got, [measured["egern"]]))
    # ② 改一个数 ⇒ 必须红（这里 red = 该数不在实测里）；样本的数现算，不写死
    d2, _sk2 = find_decls(wrong_number_sample(measured), "README.md")
    nums2 = [x for _, _k, ns in d2 for x in ns]
    if not (nums2 and max(nums2) not in set(measured.values())):
        errs.append("样本里的 %d 没被判成漂移（%s）⇒ 解析式对数字不敏感"
                    % (max(measured.values()) + 1, nums2))
    # ③ 三种写法都认得下来
    for text, want in FIX_THREE_SPELLINGS:
        d3, _sk3 = find_decls(text, "docs/x.md")
        have = [x for _, _k, ns in d3 for x in ns]
        if have != want:
            errs.append("`%s` 应提取 %s，实测 %s" % (text, want, have))
    # ④ 认不出内核归属时（无表头的表行），C3 那条"数要落在实测值里"确实会判
    d4, _sk4 = find_decls(FIX_UNATTRIBUTED, "docs/x.md")
    if any(k for _l, k, _n in d4):
        errs.append("样本本该认不出内核（交 C3），却归属成了 %s" % [k for _l, k, _n in d4])
    if not any(77 in ns for _l, _k, ns in d4):
        errs.append("样本里的 77 没被提出来 ⇒ C3 那一类其实判不到（%s）" % d4)
    return (not errs), "；".join(errs)


def main(argv):
    measured = parse_measured(argv)
    files = docs()
    if not files:
        sys.stderr.write("❌ 前置：一篇 .md 都没找到 ⇒ 扫描面空了，不算跑过\n")
        return 2
    all_decls, all_skipped, all_tool, all_rule = [], [], [], []
    for rel, p in files:
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError as exc:
            sys.stderr.write("❌ 前置：%s 读不出（%s）\n" % (rel, exc))
            return 2
        d, sk = find_decls(text, rel)
        all_decls.extend((rel, ln, k, ns) for ln, k, ns in d)
        all_skipped.extend(sk)
        all_tool.extend((rel, ln, n) for ln, n in find_tool_decls(text, rel))
        rd, rsk = find_rule_decls(text, rel)
        all_rule.extend((rel, ln, k, n) for ln, k, n in rd)
        all_skipped.extend(rsk)

    print("实测：%s · 扫描 %d 篇 .md（历史类整篇不扫）· 总数声明 %d 处 / %d 个数 · 跳过 %d 处"
          % (" · ".join("%s=%s" % (k, measured[k]) for k in MEASURED_KEYS if k in measured),
             len(files), len(all_decls),
             sum(len(ns) for _r, _l, _k, ns in all_decls), len(all_skipped)))

    checks = []
    ck = lambda name, cond, extra="": checks.append((name, bool(cond), extra))  # noqa: E731

    for kern in KERNEL_KEYS:
        hits = [(rel, ln, ns) for rel, ln, k, ns in all_decls if k == kern]
        bad = ["%s:%d 文档写 %s，实测 %s" % (rel, ln, "/".join(str(x) for x in ns), measured[kern])
               for rel, ln, ns in hits if any(x != measured[kern] for x in ns)]
        # 「命中 0 处」也判负：文档里一处都不声明这一侧的断言数 ⇒ 这条判据就空转了，
        # 那不是"没有漂移"，是"没人承诺过" —— 与 check_tools 的"清单为空"同一条罪。
        ck("C%s %s 侧总数声明与本轮实测一致（命中 %d 处）" % (1 if kern == "surge" else 2,
                                                             kern.upper(), len(hits)),
           bool(hits) and not bad,
           ("一处声明都没有 ⇒ 判据空转" if not hits else "") + "；".join(bad[:6]))
    amb = [(rel, ln, ns) for rel, ln, k, ns in all_decls if k is None]
    vals = set(measured.values())
    amb_bad = ["%s:%d %s 不在本轮实测值里（%s）"
               % (rel, ln, "/".join(str(x) for x in ns), sorted(vals))
               for rel, ln, ns in amb if any(x not in vals for x in ns)]
    ck("C3 无表头可依的并排声明逐数落在实测值里（命中 %d 处）" % len(amb),
       not amb_bad, ("本仓当前没有这一类声明 ⇒ 由 C4 ④ 的样本自证它会红"
                     if not amb else "") + "；".join(amb_bad[:6]))
    ok4, why4 = selfproof(measured)
    ck("C4 判别自证（同数换措辞不红 · 改一个数必红 · 三式写法都认 · 无表头表行也判得到）",
       ok4, why4)
    tbad = ["%s:%d 文档写 %s，实测 tools=%s" % (rel, ln, n, measured["tools"])
            for rel, ln, n in all_tool if n != measured["tools"]]
    ok5, why5 = selfproof_tool(measured)
    why5_parts = (["一处声明都没有 ⇒ 判据空转"] if not all_tool else []) + tbad[:6]
    ck("C5 check_tools 的文档写死判据条数与本轮实测一致（命中 %d 处 · 含判别自证）" % len(all_tool),
       bool(all_tool) and not tbad and ok5,
       "；".join(why5_parts) + (("；自证不通过：" + why5) if not ok5 else ""))

    rbad, rn = [], 0
    for key, _anchors in RULE_ANCHORS:
        hits = [(rel, ln, n) for rel, ln, k, n in all_rule if k == key]
        rn += len(hits)
        if not hits:
            rbad.append("%s 一处声明都没有 ⇒ 判据空转" % key)
        rbad += ["%s:%d 文档写 %d，实测 %s=%s" % (rel, ln, n, key, measured[key])
                 for rel, ln, n in hits if n != measured[key]]
    ck("C6 portability / doc_readings 的「固定 N 条规则」与实测一致（命中 %d 处）" % rn,
       not rbad, "；".join(rbad[:6]))

    for s in all_skipped[:8]:
        print("   ↷ " + s)
    if len(all_skipped) > 8:
        print("   ↷ …另有 %d 处" % (len(all_skipped) - 8))
    bad_ = [c for c in checks if not c[1]]
    for name, ok_, extra in checks:
        print("   %s %s%s" % ("✅" if ok_ else "❌", name,
                              (" · " + extra) if (extra and not ok_) else ""))
    print("TOTAL: %d passed, %d failed" % (len(checks) - len(bad_), len(bad_)))
    return 1 if bad_ else 0


if __name__ == "__main__":
    # Windows GBK 终端里 print 中文/emoji 会 UnicodeEncodeError ⇒ 退出码 1，
    # 看着像判负、其实一条都没判。与 check_doc_readings.py / check_tools.py 同款兜底。
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:                                      # noqa: BLE001
            pass
    sys.exit(main(sys.argv[1:]))
