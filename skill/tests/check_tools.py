#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工具自检项（`all.sh` 第 6 项）：把"仓里这些脚本自己还能不能跑"并进闸。

为什么要有这一项（2026-09-24 定，两条实测依据）：
  1. **三套自带回归原本不在闸里** —— `all.sh` 里 `grep -c selftest` 实测为 0。
     `make_min.py` 是生成 `.min` 的那只手，而形态对拍器只比对**已经存在的两份产物**：
     生成器自己坏了，闸看不出来，只会等下一次有人手工跑它时才发现。
     三套串起来的实测成本 0.554s，换进来的是一条"这些工具自己还活着"的判据。
  2. **有 6 个被跟踪的 .py 闸永远不执行**（`_egern_common` / `audit_ruleset_noresolve` /
     probe_dns_endpoints / probe_doh / profile_ruleset / weigh_ruleset —— 在三个 runner 里
     0 引用）。实测 24 个被跟踪 .py 现在全部可编译，所以那是"还没坏"，不是"有防护"。

六条判据（**固定条数**，不随 .py 文件数增长 —— 与其余判据同一口径）：
  · T1 全部被跟踪 .py 可编译      · T2 `make_min.py --selftest`
  · T3 `apply_edits.py --selftest` · T4 `surge/check_links.py --selftest`
  · T5① 无未用顶层 import         · T5② 无本文件死常量

T5 补的是 T1 的那半边（2026-09-24 定）：可编译只保证"语法还读得动"，判不到"顶层绑了
却再没人用的名字"。实测 26 个被跟踪 .py 里有 9 处，其中两处的坑叫**跨内核同名**：
`IP_RULE_TYPES` 在 `egern/check_egern_dns.py:46` 定义并在 :377 在用，`surge/audit_routing_coverage.py:174`
那份同名同形却无人用 —— 所以口径必须按"文件内"算，拿全仓 grep 词频判会把它读成活的。

四条活路（每条都实测过它救回了什么，别删）：
  · 本文件内有 `Load` 引用 ⇒ 活 —— 主判据，走 AST 不走文本，注释里提一句不算用。
  · 行上有 `# t5-keep: 理由`（理由非空）⇒ 保留 —— 给"故意留着的别名"记名用，实测 1 处（`APPLE_PROBES`）。
  · import 的名字在**源模块顶层被裸调用** ⇒ 活 —— "import 即生效"的编码垫片，
    实测救回 7 处 `from _surge_common / _egern_common import force_utf8_stdout`：
    importing 文件自己不点它，
    但 `_egern_common.py:121` / `_surge_common.py:294` 在模块顶层调了一次。
  · 常量在全文件字面出现 ≥2 次 ⇒ 放过 —— 只在散文/注释里被提的名字不当死绑定判。
    这条让误差方向固定在**漏报**（宁可放过不误报），代价实测：`_egern_common.py:98 ep_ip`
    字面出现 4 次（含头注里那句"给别人用的清单"）而全仓无人 import ⇒ 它不会被 T5 点亮。
    记在这里，是为了让下一个读代码的人知道那是**口径选择**，不是漏了。

两条判据共享：def/class 不进面（它们本来就该允许只被别人用）、只扫模块体第一层
（`try:`/`if:` 里的绑得不判，方向同样是漏报）、`__` 开头与 `import *` 不判。

另两个刻意的实现选择：
  · **不落 .pyc**：T1 用内置 `compile()` 在内存里判语法，不调 `compileall`（那会往仓里掉
    `__pycache__`；`all.sh` 虽然 `PYTHONDONTWRITEBYTECODE=1`，但这一项也会被手工单独跑）。
    语法不可编译正是 `compileall` 唯一能抓的东西，两者覆盖面等价。
  · **文件清单只吃 `git ls-files`**：不用 `**/*.py` glob —— 磁盘上总有历史手跑留下的
    `__pycache__`/临时副本，glob 会把它们算进来，读数就跟着环境漂了。
    非 git 环境（打包外发的归档）退一步走目录遍历，但仍跳过 `__pycache__` 与 `.git`。

三套自测的"过法"各不相同，所以各判各的（实测）：
    make_min.py    →  ALL GREEN · 自带回归 7 条        （无 TOTAL 行）
    apply_edits.py →  TOTAL: 13 passed, 0 failed
    check_links.py →  ✅ 自检通过                       （只有一行，条数不可读 ⇒ 只认退出码）
  `surge/check_links.py` 在冻结名单里，**不改它的输出形状**去迁就这里的解析。

用法：python skill/tests/check_tools.py [仓库根]     # 默认取本文件所在的仓库根
退出码：0 全过 · 1 有判负 · 2 前置不达标（读不到 git 清单且找不到 .py）
"""

import ast
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))               # <仓根>/skill/tests
ROOT = os.path.dirname(os.path.dirname(HERE))

# 三套自带回归：相对仓根的路径 + 人读的名字。判"过"一律用退出码 0（理由见头注）。
SUITES = (("skill/tests/make_min.py", "make_min 生成器自测"),
          ("skill/tests/apply_edits.py", "apply_edits 锚点守门自测"),
          ("skill/tests/surge/check_links.py", "check_links 链接器自测"))


def tracked_py(root):
    """被跟踪的 .py 清单；非 git 环境退一步遍历目录（仍跳过 __pycache__ / .git）。"""
    try:
        out = subprocess.run(["git", "-C", root, "ls-files", "*.py"],
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace").stdout
    except OSError:
        out = ""
    files = [l.strip() for l in out.splitlines() if l.strip()]
    if files:
        return files, "git ls-files"
    files = []
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for n in names:
            if n.endswith(".py"):
                files.append(os.path.relpath(os.path.join(dirpath, n), root).replace("\\", "/"))
    return sorted(files), "目录遍历"


# ── T5 顶层死绑定：两条判据共用一次扫描 ────────────────────────────────────
# 标记的形状写死在这里：`# t5-keep: 理由`，理由必须非空（空理由等于没记名，判负）。
KEEP_RX = re.compile(r"#\s*t5-keep:\s*(\S.*)")


def top_bindings(tree):
    """模块体**第一层**的 import 绑定与赋值目标 ⇒ (imports, consts)。

    imports = [(名字, 行号, 原名, 源模块)] · consts = [(名字, 行号)]
    def/class 不进面（它们允许只被别人用）；`try:`/`if:` 块里的绑得不进面。
    """
    imports, consts = [], []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports += [(a.asname or a.name.split(".")[0], node.lineno, a.name, None)
                        for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imports += [(a.asname or a.name, node.lineno, a.name, node.module)
                        for a in node.names if a.name != "*"]
        elif isinstance(node, ast.Assign):
            consts += [(t.id, node.lineno) for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            consts.append((node.target.id, node.lineno))
    return imports, consts


def top_called(tree):
    """模块**顶层**被裸调用的名字 —— 这些名字的 import 是"import 即生效"的垫片。"""
    return {n.value.func.id for n in tree.body
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Name)}


def dead_bindings(corpus):
    """corpus = {相对路径: 源码} ⇒ {'imp': […], 'con': […], 'keep': […], 'unparsed': N}。

    写成"吃内存里的源码字典"而不是"自己读仓"，是为了能用假样本单独验它有没有判别力
    （真仓里造红它的 fixture 就得改仓库文件，那是闸门最不该干的事）。
    口径、四条活路、以及它刻意只漏报不误报的取向，全在头注里。
    """
    trees, loaded, called = {}, {}, {}
    for rel, text in corpus.items():
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError):
            continue                        # 读不懂是 T1 的活，这里不重复判、也不猜
        trees[rel] = tree
        loaded[rel] = {n.id for n in ast.walk(tree)
                       if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        called[rel] = top_called(tree)

    res = {"imp": [], "con": [], "keep": [], "unparsed": len(corpus) - len(trees)}
    for rel in sorted(trees):
        lines = corpus[rel].splitlines()
        imports, consts = top_bindings(trees[rel])
        for name, lineno, raw, mod in imports:
            if name.startswith("__") or name in loaded[rel]:
                continue
            src = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
            mk = KEEP_RX.search(src)
            if mk:
                res["keep"].append((rel, lineno, "import", name, raw, mk.group(1).strip()))
                continue
            if mod and any(os.path.basename(r)[:-3] == mod.split(".")[0]
                           and name in called[r] for r in trees):
                continue                    # 源模块顶层调它 ⇒ import 即生效
            res["imp"].append((rel, lineno, "未用 import", name, src.strip()[:56]))
        for name, lineno in consts:
            if name.startswith("__") or name in loaded[rel]:
                continue
            src = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
            mk = KEEP_RX.search(src)
            if mk:
                res["keep"].append((rel, lineno, "常量", name, "", mk.group(1).strip()))
                continue
            if len(re.findall(r"\b%s\b" % re.escape(name), corpus[rel])) != 1:
                continue                    # 散文/注释里还提到 ⇒ 放过（只漏报不误报）
            res["con"].append((rel, lineno, "死常量", name, src.strip()[:56]))
    return res


def check(root):
    """[(判据名, 通过?, 说明)]，固定 6 条。"""
    out = []

    # ── T1 全部被跟踪 .py 可编译 ─────────────────────────────────────────
    files, src = tracked_py(root)
    if not files:
        out.append(("T1 被跟踪 .py 可编译", False, "清单为空（%s）⇒ 没跑成不等于跑绿" % src))
        n_bad, sample = 0, ""
    else:
        bad = []
        for rel in files:
            full = os.path.join(root, rel.replace("/", os.sep))
            try:
                with open(full, "rb") as f:
                    compile(f.read(), full, "exec")
            except SyntaxError as exc:
                bad.append("%s:%s %s" % (rel, exc.lineno, exc.msg))
            except OSError as exc:
                bad.append("%s 读不出：%s" % (rel, exc))
        n_bad = len(bad)
        sample = " · ".join(bad[:3]) + (" …" if len(bad) > 3 else "")
    out.append(("T1 被跟踪 .py 可编译（%d 个 · %s）" % (len(files), src),
                n_bad == 0, sample or ("%d/%d 通过" % (len(files), len(files)))))

    # ── T2–T4 三套自带回归 ──────────────────────────────────────────────
    for rel, name in SUITES:
        full = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.isfile(full):
            out.append((name, False, "脚本不在：%s" % rel))
            continue
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            p = subprocess.run([sys.executable, full, "--selftest"],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", cwd=root, env=env, timeout=120)
        except Exception as exc:                                  # noqa: BLE001
            out.append((name, False, "跑不起来：%s" % exc))
            continue
        tail = (p.stdout or p.stderr or "").strip().splitlines()
        line = tail[-1][:70] if tail else "（无输出）"
        out.append((name, p.returncode == 0,
                    "exit=%d · %s" % (p.returncode, line) if p.returncode else line))

    # ── T5①② 顶层死绑定（两条共用一次扫描，口径见头注）──────────────────
    corpus = {}
    for rel in files:
        try:
            with open(os.path.join(root, rel.replace("/", os.sep)),
                      encoding="utf-8", errors="replace") as f:
                corpus[rel] = f.read()
        except OSError:
            pass                                       # 读不出：T1 已经点了名
    res = dead_bindings(corpus)
    # 保留数按各判据自己的面报：常量行的标记不该出现在 import 那条的读数里。
    kept = {"imp": len([k for k in res["keep"] if k[2] == "import"]),
            "con": len([k for k in res["keep"] if k[2] == "常量"])}
    unparsed = " · %d 个文件读不懂（T1 已判负）" % res["unparsed"] if res["unparsed"] else ""
    for key, label in (("imp", "T5① 无未用顶层 import"), ("con", "T5② 无本文件死常量")):
        hits = res[key]
        k = " · 另 %d 处 `t5-keep` 保留" % kept[key] if kept[key] else ""
        if not files:
            out.append((label, False, "清单为空 ⇒ 没跑成不等于跑绿"))
            continue
        detail = " · ".join("%s:%s %s" % (h[0], h[1], h[3]) for h in hits[:4])
        out.append(("%s（%d 个 .py）" % (label, len(files)), not hits,
                    ("%d 处判死：%s%s" % (len(hits), detail, " …" if len(hits) > 4 else ""))
                    if hits else ("0/%d 通过%s%s" % (len(files), k, unparsed))))
    return out


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT
    if not os.path.isdir(root):
        print("❌ 前置：仓库根不存在：%s" % root)
        return 2
    checks = check(root)
    bad_ = [c for c in checks if not c[1]]
    for name, ok_, extra in checks:
        print("   %s %-38s %s" % ("✅" if ok_ else "❌", name, extra))
    print("TOTAL: %d passed, %d failed" % (len(checks) - len(bad_), len(bad_)))
    return 1 if bad_ else 0


if __name__ == "__main__":
    # Windows GBK 终端里 print 中文/emoji 会 UnicodeEncodeError ⇒ 退出码 1，看着像判负。
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:                                      # noqa: BLE001
            pass
    sys.exit(main())
