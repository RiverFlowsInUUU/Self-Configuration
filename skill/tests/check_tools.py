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

四条判据（**固定条数**，不随 .py 文件数增长 —— 与其余判据同一口径）：
  · T1 全部被跟踪 .py 可编译      · T2 `make_min.py --selftest`
  · T3 `apply_edits.py --selftest` · T4 `surge/check_links.py --selftest`

两个刻意的实现选择：
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

import os
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


def check(root):
    """[(判据名, 通过?, 说明)]，固定 4 条。"""
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
