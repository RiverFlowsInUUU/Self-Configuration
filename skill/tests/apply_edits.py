#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""锚点守门的批量编辑执行器：一份 JSON 说清「哪些文件、把哪句改成哪句」，全中才落盘。

为什么要有这个工具（治的是本项目反复踩的两类返工）：
  1. **改一处必对全部** —— 组数 / 规则条数 / 断言数 / 版本号在十来篇文档里各写一遍，
     一次批量改动要几十条替换。手工一条条改：锚点撞车（命中 2 次）会静默改错地方，
     锚点失效（命中 0 次）要跑完才发现，一轮来回就是几分钟。
  2. **半套落地** —— 第 3 条失败时前 2 条已经写进磁盘，仓里留下"改了一半"的状态，
     只能靠 git checkout 回滚。
本工具把这两类变成**跑之前就报出来**的错：**任何一条不达标 ⇒ 一个字节都不写**。

四条守门：
  · 每条替换的锚点必须在**当前内容**（同文件的前序替换已应用后的样子）里命中 `count` 次，
    默认 1 次；命中 0 次或多于 `count` 次都判负，并打印命中所在行号。
  · 整批先在内存里算完再写盘（唯一的落盘入口是 `commit()`，且只在校验零失败后才允许调用）；
    写盘用 `newline='\n'`，不碰行尾、不补尾换行。
  · 目标含 `\\r` 直接判负 —— 本工具只写 LF，CRLF 文件要先单独归一（AGENTS.md §2 第 3 条）。
  · 冻结闸门文件（AGENTS.md §2 第 5 条那份名单，现 10 个）默认拒绝，必须显式 `--allow-gate`；
    拒绝消息里就写着请示要附哪两条。

用法：
  python skill/tests/apply_edits.py edits.json                 # 干跑：只校验，不写盘
  python skill/tests/apply_edits.py edits.json --apply         # 校验全过才落盘
  python skill/tests/apply_edits.py --selftest                 # 自带回归，不碰仓库任何文件

edits.json 两种写法都行：顶层直接是数组，或 `{"edits": [...], "root": "相对仓根的子目录"}`。
每条：`{"path": "docs/x.md", "old": "23 个断言", "new": "27 个断言", "count": 1}`
     `count` 可省（=1）；`"count": "all"` = 有几处改几处（至少 1 处）；`new` 写空串即删除该片段。

退出码：0 全过 · 1 有守门失败（未写盘） · 2 前置不达标（JSON 读不出 / 路径越出仓根 / 没给文件）
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))               # <仓根>/skill/tests
ROOT = os.path.dirname(os.path.dirname(HERE))                    # → skill → 仓根

# 与 AGENTS.md §2 第 5 条同源；--selftest 的 A9 拿 it 跟 all.sh 里的 GATE 逐字对拍（代码 ↔ 代码，
# 有序比），A13 再拿它当真相去对文档侧的名单块与三处写死个数 —— 合计「真相 1 + 对拍 5」。
GATE = (".gitattributes", "skill/tests/all.sh", "skill/tests/check_portability.py",
        "skill/tests/check_min_pair.py", "skill/tests/bump_version.py",
        "skill/tests/check_doc_readings.py",
        "skill/tests/surge/run.sh", "skill/tests/surge/architecture.sh",
        "skill/tests/surge/check_links.py", "skill/tests/egern/run.sh")

# ── 文档侧的闸门「写死个数」：三处，全都要 == len(GATE) ─────────────────────
# 口径是**真相 1 + 对拍 5**：名单 3 副本（all.sh · 本模块 · AGENTS.md §2 的块）
# 与个数 3 处（下面这三条模式）。名单里 all.sh ↔ 本模块是代码对代码，由 A9 逐字有序对拍；
# AGENTS.md 的块与三处个数由 A13 判 —— 文档侧**按集合比、不比顺序**，因为那个块是
# 5 行 × 每行 2 列的排版产物（实测：块内行主序与 GATE 在第 6/7 位天然互换，
# 拿有序 `==` 裸比会让 A13 上线第一天就红给自己、还误报成"AGENTS.md 漂移"）。
GATE_DOC_PATTERNS = (
    ("AGENTS.md §2 标题", r"(\d+)\s*个文件是[「『]?闸"),
    ("docs/注意事项.md 浓缩句", r"(\d+)\s*[个份条]\s*[「『]?闸门"),
    ("apply_edits.py 头注", r"现\s*(\d+)\s*个"),
)


def gate_block_names(agents_text):
    """AGENTS.md §2 第 5 条那个围栏块 → 文件名列表。

    块的实际排版是 **每行 2 列、空格对齐**（`.gitattributes` 与 `skill/tests/all.sh` 同一行）
    ⇒ 按 2+ 个空格切列，逐行取 `split()[0]` 只会拿到 5 个。锚点取"含 `.gitattributes`
    的围栏块"这个**结构**特征，不取周围的措辞 —— 改字不改名单时不该红。
    """
    import re
    for blk in re.findall(r"```[^\n]*\n(.*?)```", agents_text, re.S):
        if ".gitattributes" in blk:
            return [tok for line in blk.splitlines()
                    for tok in re.split(r"\s{2,}", line.strip()) if tok]
    return []


def gate_doc_check(agents_text, note_text, own_text, truth=GATE):
    """文档侧对拍：返回失败原因列表（空 = 全过）。真相是 all.sh 那份 GATE（经 A9 钉住本模块副本）。"""
    import re
    errs = []
    names = gate_block_names(agents_text)
    if not names:
        errs.append("AGENTS.md §2 的名单围栏块没找到（围栏没了？还是 .gitattributes 挪了位置？）")
    else:
        # 槽位数与唯一性两条都要立：只比集合会放过"在册项原样 + 多抄一行"（11 槽 / 10 唯一
        # ⇒ 集合仍相等），而"少一个 + 多一个"那种真漂移才由集合差抓到。
        if len(names) != len(truth):
            errs.append("§2 块 %d 个槽位 ≠ 真相 %d 个" % (len(names), len(truth)))
        dupes = sorted({x for x in names if names.count(x) > 1})
        if dupes:
            errs.append("§2 块有重复项：%s" % " ".join(dupes))
        miss = sorted(set(truth) - set(names))
        extra = sorted(set(names) - set(truth))
        if miss:
            errs.append("§2 块缺：%s" % " ".join(miss))
        if extra:
            errs.append("§2 块多出：%s" % " ".join(extra))
    srcs = {"AGENTS.md §2 标题": agents_text,
            "docs/注意事项.md 浓缩句": note_text,
            "apply_edits.py 头注": own_text}
    for tag, pat in GATE_DOC_PATTERNS:
        m = re.search(pat, srcs[tag])
        if not m:
            errs.append("%s 的写死个数没匹配到（措辞被改？模式 `%s`）" % (tag, pat))
        elif int(m.group(1)) != len(truth):
            errs.append("%s 写的是 %s 个 · 真相 %d 个" % (tag, m.group(1), len(truth)))
    return errs


def die(msg):
    print("❌ %s" % msg)
    sys.exit(2)


def norm_rel(path, root):
    """收成相对仓根的 posix 路径；越出仓根一律拒绝。"""
    p = path.replace("\\", "/")
    full = os.path.normpath(p if os.path.isabs(p) else os.path.join(root, p))
    rel = os.path.relpath(full, root).replace("\\", "/")
    if rel.startswith("..") or os.path.isabs(rel):
        die("路径越出仓库根，拒绝执行：%s（root=%s）" % (path, root))
    return rel


def line_of(text, pos):
    """字符下标 → 1 基行号，报错时给人能直接跳过去的定位。"""
    return text.count("\n", 0, pos) + 1


def preview(s, n=48):
    s = s.replace("\n", "\\n")
    return s if len(s) <= n else s[:n] + "…"


def hit_lines(text, needle, cap=5):
    """前 cap 个命中的行号。"""
    out, k = [], text.find(needle)
    while k != -1 and len(out) < cap:
        out.append(str(line_of(text, k)))
        k = text.find(needle, k + 1)
    return out


def plan(edits, root):
    """校验 + 在内存里算出目标内容。返回 (files, failures)，**一个字节都不写**。"""
    files = {}                                    # rel -> 已应用前序替换的当前内容
    done = 0
    fails = []

    for i, e in enumerate(edits, 1):
        tag = "#%d" % i
        if not isinstance(e, dict):
            fails.append("%s 不是 JSON 对象：%r" % (tag, e))
            continue
        path, old, new = e.get("path"), e.get("old"), e.get("new")
        count = e.get("count", 1)
        if not path or not isinstance(path, str):
            fails.append("%s 缺 `path`" % tag)
            continue
        if not old:
            fails.append("%s 锚点为空（`old` 必须是非空字符串）：%s" % (tag, path))
            continue
        if new is None:
            fails.append("%s 缺 `new`（要删掉就把 `new` 写成空串）：%s" % (tag, path))
            continue
        rel = norm_rel(path, root)
        full = os.path.join(root, rel)

        if rel in GATE and "--allow-gate" not in sys.argv:
            fails.append("%s 目标是冻结闸门文件：%s ⇒ 按 AGENTS.md §2 第 5 条先请示，"
                         "要附「不改会漏掉哪个具体文件」+「改完能抓住什么」；批了就加 --allow-gate"
                         % (tag, rel))
            continue
        if not os.path.isfile(full):
            fails.append("%s 文件不存在：%s" % (tag, rel))
            continue
        if rel not in files:
            with open(full, "rb") as f:
                raw = f.read()
            if b"\r" in raw:
                fails.append("%s 文件含 CR（CRLF / 老 Mac 行尾），本工具只写 LF：%s"
                             % (tag, rel))
                continue
            try:
                files[rel] = raw.decode("utf-8")
            except UnicodeDecodeError:
                fails.append("%s 不是 UTF-8 文本：%s" % (tag, rel))
                continue

        cur = files[rel]
        hits = cur.count(old)
        if count == "all":
            if hits == 0:
                fails.append("%s 锚点命中 0 次（要求 ≥1）：%s · 锚点 `%s`"
                             % (tag, rel, preview(old)))
                continue
            want = hits
        else:
            want = count if isinstance(count, int) else 1
            if hits != want:
                where = (" 第 %s 行" % ",".join(hit_lines(cur, old))) if hits else ""
                fails.append("%s 锚点命中 %d 次、期望 %d 次：%s%s · 锚点 `%s`"
                             % (tag, hits, want, rel, where, preview(old)))
                continue
        files[rel] = cur.replace(old, new)
        done += 1
    return files, done, fails


def commit(files, root):
    """唯一的落盘入口。调用方必须先确认 failures 为空。"""
    for rel, text in sorted(files.items()):
        with open(os.path.join(root, rel), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)


def load(spec, root):
    try:
        with open(spec, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:                       # noqa: BLE001 —— 报错要原样给人看
        die("读不出 %s：%s" % (spec, exc))
    sub = root
    if isinstance(data, dict):
        sub = os.path.normpath(os.path.join(root, data.get("root", "")))
        data = data.get("edits")
    if not isinstance(data, list) or not data:
        die("%s 里没有非空的 edits 数组" % spec)
    return data, sub


def report(files, done, fails, applied):
    if files:
        print("涉及 %d 个文件 · %d 条替换：%s"
              % (len(files), done, " · ".join(sorted(files))))
    if fails:
        print("\n❌ 守门失败 %d 条 ⇒ 一个字节都没写" % len(fails))
        for m in fails:
            print("   · %s" % m)
    else:
        print("✅ 已写盘" if applied else "✅ 干跑全过（未写盘；加 --apply 落盘）")
    print("TOTAL: %d passed, %d failed" % (0 if fails else done, len(fails)))
    return 1 if fails else 0


# ── 自带回归：只在临时目录里演，不读也不写仓库里的任何文件 ──────────────────
def selftest():
    checks = []

    def ck(name, cond, extra=""):
        checks.append((name, bool(cond), extra))

    with tempfile.TemporaryDirectory() as td:
        def put(rel, text):
            p = os.path.join(td, rel)
            d = os.path.dirname(p)
            if d:
                os.makedirs(d, exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)

        def readb(rel):
            with open(os.path.join(td, rel), "rb") as f:
                return f.read()

        put("a.md", "规则 23 个断言\n第二行\n")
        put("b.md", "x\ny\nz\n")
        put("d.md", "dup\nline2\ndup\n")
        put("skill/tests/all.sh", "GATE = (...)\n")
        put("crlf.md", "a\r\nb\r\n")

        fs, dn, fl = plan([{"path": "a.md", "old": "23 个断言", "new": "27 个断言"}], td)
        ck("A1 唯一命中通过、其余字节不动",
           not fl and "27 个断言" in fs["a.md"] and "第二行" in fs["a.md"], str(fl))

        fs, dn, fl = plan([{"path": "a.md", "old": "不存在", "new": "?"}], td)
        ck("A2 锚点落空判负", len(fl) == 1 and "命中 0 次" in fl[0], str(fl))

        fs, dn, fl = plan([{"path": "d.md", "old": "dup", "new": "x"}], td)
        ck("A3 重复锚点判负并报行号",
           len(fl) == 1 and "命中 2 次" in fl[0] and "第 1,3 行" in fl[0], str(fl))

        fs, dn, fl = plan([{"path": "a.md", "old": "23 个", "new": "27 个"},
                           {"path": "a.md", "old": "27 个断言", "new": "27 断言"}], td)
        ck("A4 同文件按顺序应用（第 2 条吃第 1 条的产物）",
           not fl and "27 断言" in fs["a.md"] and "27 个断言" not in fs["a.md"] and dn == 2, str(fl))

        fs, dn, fl = plan([{"path": "a.md", "old": "第二行", "new": "改了"},
                           {"path": "b.md", "old": "nope", "new": "?"}], td)
        ck("A5 一批里有条目失败 ⇒ 内存外的磁盘内容不变（不 commit 就不写）",
           len(fl) == 1 and readb("a.md") == "规则 23 个断言\n第二行\n".encode(), str(fl))

        fs, dn, fl = plan([{"path": "b.md", "old": "y\n", "new": ""}], td)
        ck("A6 new 为空串 = 删除片段", not fl and fs["b.md"] == "x\nz\n", str(fl))

        fs, dn, fl = plan([{"path": "d.md", "old": "dup", "new": "x", "count": "all"}], td)
        ck("A7 count=all 两处都改", not fl and fs["d.md"] == "x\nline2\nx\n" and dn == 1, str(fl))

        fs, dn, fl = plan([{"path": "skill/tests/all.sh", "old": "GATE", "new": "X"}], td)
        ck("A8 闸门文件默认拒绝", len(fl) == 1 and "冻结闸门" in fl[0], str(fl))

        fs, dn, fl = plan([{"path": "crlf.md", "old": "a", "new": "b"}], td)
        ck("A10 含 CR 的文件拒改", len(fl) == 1 and "含 CR" in fl[0], str(fl))

        put("e.md", "hello world\n")
        fs, dn, fl = plan([{"path": "e.md", "old": "hello", "new": "HI"}], td)
        commit(fs, td)
        ck("A12 落盘字节精确（LF、不多补尾换行）", readb("e.md") == b"HI world\n",
           repr(readb("e.md")))

    # A9：闸门名单与 all.sh 里的 GATE 逐字一致（真仓文件，只读）
    listed = GATE                     # 读不到 all.sh 时退回本模块副本（A13 也据此判）
    try:
        with open(os.path.join(ROOT, "skill/tests/all.sh"), encoding="utf-8") as f:
            src = f.read()
    except OSError:
        src = ""
    if not src:
        ck("A9 闸门名单对拍跳过（找不到 all.sh）", True)
    else:
        import ast
        import re as _re
        m = _re.search(r"GATE = \((.*?)\)", src, _re.S)
        listed = tuple(ast.literal_eval("(" + m.group(1) + ")")) if m else ()
        ck("A9 闸门名单与 all.sh 逐字一致", listed == GATE, "%s vs %s" % (listed, GATE))

    # A13：文档侧的名单块 + 三处写死个数。真相取 **all.sh 里现读出来的那份**（listed），
    # 不是本模块副本 —— 这样"只往 all.sh 加一个闸门、文档四处一处没跟"会同时点亮 A9 与 A13，
    # 而不是只由 A9 单独挡（少一层"靠 A9 没跑歪"的间接信任）。读不到 all.sh 时 listed 退回 GATE。
    def _read(rel):
        try:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""

    agents_src, note_src = _read("AGENTS.md"), _read("docs/注意事项.md")
    own_src = ""
    try:
        with open(__file__, encoding="utf-8") as f:
            own_src = f.read()
    except OSError:
        pass
    if not (agents_src and note_src and own_src):
        ck("A13 文档侧对拍跳过（AGENTS.md / 注意事项 / 自身源码读不到）", True)
    else:
        errs = gate_doc_check(agents_src, note_src, own_src, listed)
        # 判别自证 ①（正例）：在册 10 项原样 + 把其中一行抄第二遍 ⇒ 11 槽 / 10 唯一。
        #   纯集合比在这一步是**放行**的，红它的只有"恰 10 槽"和"互不重复"两条。
        ln = next((l for l in agents_src.splitlines() if "skill/tests/egern/run.sh" in l), "")
        twin = agents_src.replace(ln, ln + "  skill/tests/egern/run.sh", 1)
        pos = gate_doc_check(twin, note_src, own_src, listed)
        # 判别自证 ②（反例）：个数不变的纯润色 ⇒ 不许红。不立这条，解析式就会过度贴合
        #   当前措辞，下一个改文档的人拿到一次"A9 红给左手"，最省事的处置是放宽正则 ——
        #   那正是 CHANGELOG 里点名过的那条作弊路径。
        neg = gate_doc_check(agents_src,
                             note_src.replace("10 个「闸门文件」", "10 份闸门文件", 1),
                             own_src, listed)
        ck("A13 文档侧名单块与三处写死个数对拍（含判别自证：多抄一行必红 · 纯润色不红）",
           not errs and any("槽位" in x for x in pos) and any("重复" in x for x in pos)
           and not neg,
           "实测 %s · 正例 %s · 反例 %s" % (errs, pos, neg))

    # A11：越出仓根的路径要判越界（norm_rel 会 die，这里只验判定分支）
    rel = os.path.relpath(os.path.abspath("/etc/passwd"), os.getcwd()).replace("\\", "/")
    ck("A11 仓外路径被认成越界", rel.startswith("..") or os.path.isabs(rel), rel)

    bad = [c for c in checks if not c[1]]
    for name, ok_, extra in checks:
        print("   %s %s%s" % ("✅" if ok_ else "❌", name,
                              (" · " + extra) if (extra and not ok_) else ""))
    print("TOTAL: %d passed, %d failed" % (len(checks) - len(bad), len(bad)))
    return 1 if bad else 0


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    spec = next((a for a in args if not a.startswith("--")), None)
    if not spec:
        die("用法：apply_edits.py <edits.json> [--apply] [--allow-gate] | --selftest")
    edits, root = load(spec, ROOT)
    files, done, fails = plan(edits, root)
    applied = False
    if not fails and "--apply" in args:
        commit(files, root)
        applied = True
    return report(files, done, fails, applied)


if __name__ == "__main__":
    sys.exit(main())
