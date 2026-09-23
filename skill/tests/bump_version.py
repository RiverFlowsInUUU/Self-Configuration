#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升版一条命令：复制两份形态 → 钉刷新秒数 → 改全仓活指向 → 交给闸门验收。

    python skill/tests/bump_version.py routing_v3.1 routing_v3.2                # 只出计划，一个字都不写
    python skill/tests/bump_version.py routing_v3.1 routing_v3.2 --apply         # 落盘（不跑检查）
    python skill/tests/bump_version.py routing_v3.1 routing_v3.2 --apply --gate   # 落盘后跑 all.sh

为什么需要它：上一轮 v3 → v3.1 是手工做的 —— 四份形态 + 90 多处指向同步，占了整轮时间的一大块。
这里把那部分机械劳动收进脚本，**人的判断留在脚本之外**：

    · 它做：复制四份形态（两内核 × 带注释 / .min）、把新文件的远程规则集刷新秒数钉成约定值、
            新文件内部的自称、全仓"活指向"改写（三份 runner 里 CURRENT 那一行也在其中）。
    · 它**不**做：CHANGELOG 与各篇「版本沿革」里的历史表述（那是当时的口径记录，改了就是篡改）、
            裸版本号提法（`v3.1` 这种没带 routing_ 前缀的，可能指版本、可能指段落标题，机器判不了）、
            以及升版说明的文案。这些它只**列清单**，交给人。
    · 它也**不**碰"哪一版该被推荐"这件事：`CURRENT` 常量是承诺值，升版后仍要有人显式确认。
            本仓完全独立，全仓所有检查只看本仓库的文件 —— 不存在"与别的仓库对账"这一步。

排除口径（默认）：
    CHANGELOG.md            历史条目不改
    沿革                    "哪一版改了什么"的记述
    (surge|egern)/profiles/ 存档 profile 一律不动；新建那四份由本脚本按规则单独生成
    bump_version.py      本脚本自身（含头部用法示例里的版本号 —— 那是演示值，不是活指向）
    额外排除用 --keep <子串>（可多次）。

⚠️ 关于源码里的换行：本文件刻意用 NL / CRLF 两个常量表示换行，不写字面转义 —— 一旦有人用
   heredoc 或补丁生成改写盘脚本，反斜杠转义会被吃掉，真实换行嵌进字符串就是语法错误。
   另：所有改写都**按原文件自身的换行写回**，不假设它是 LF 还是 CRLF。仓根 `.gitattributes`
   已把检出钉成 `eol=lf`（覆盖 Windows 系统级 `core.autocrlf=true`），但别人的机器上若有人
   手工放进来一个 CRLF 文件，按原样写回才不会顺手把整份文件的字节改掉 —— 该不该出现 CRLF
   由 `check_portability.py` 判，不归本脚本管。
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys

# 本文件位于 <仓库根>/skill/tests/ ⇒ 上溯三级即仓库根；检查入口同目录。
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALL_SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "all.sh")

EXPECT_INTERVAL = 604800
NL = chr(10)               # 换行：唯一允许的写法
CRLF = chr(13) + NL
RUNNER_FILES = [           # CURRENT 承诺值所在的三处，改完顺手核对命中数
    "skill/tests/surge/run.sh",
    "skill/tests/surge/architecture.sh",
    "skill/tests/egern/run.sh",
]


def read(p):
    """返回 (正文（LF）, 原换行形态)。本仓 core.autocrlf=true ⇒ 工作树是 CRLF，写回按原样。"""
    raw = io.open(p, encoding="utf-8", newline="").read()
    return raw.replace(CRLF, NL), (CRLF if CRLF in raw else NL)


def write(p, text, eol):
    io.open(p, "w", encoding="utf-8", newline="").write(text.replace(NL, eol))


# ── 远程规则集刷新参数（与两份 audit_ruleset_refresh.py 同一判据口径）────────
def set_interval_surge(text, seconds, tag):
    """`RULE-SET,<url>,<policy>[,…]` → 在第 4 个字段处钉 "update-interval=N"。"""
    out, touched, added, updated = [], 0, 0, 0
    for line in text.split(NL):
        if re.match(r"^(?:RULE-SET|DOMAIN-SET),\s*https?://", line.strip()):
            touched += 1
            if re.search(r"update-interval=\d+", line):
                new = re.sub(r"update-interval=\d+", "update-interval=" + str(seconds), line)
                updated += (new != line)
                out.append(new)
            else:
                f = line.split(",")
                if len(f) < 3:
                    raise SystemExit("❌ " + tag + ": 规则行字段不足 —— " + line)
                f.insert(3, '"update-interval=' + str(seconds) + '"')
                added += 1
                out.append(",".join(f))
        else:
            out.append(line)
    return NL.join(out), touched, added, updated


def set_interval_egern(text, seconds, tag):
    """`- rule_set:` 且 match 为 http 的块：有 update_interval 就改值，没有就在 policy 后插一行。"""
    lines = text.split(NL)
    out, touched, added, updated = [], 0, 0, 0
    i = 0
    while i < len(lines):
        if not re.match(r"^- rule_set:", lines[i]):
            out.append(lines[i]); i += 1; continue
        # 块边界 = 缩进连续段的末尾（不能把下一个顶层列表项吃进来）
        j = i + 1
        while j < len(lines) and lines[j].startswith(" ") and not re.match(r"^- ", lines[j]):
            j += 1
        blk = lines[i:j]
        touched += 1
        if not any(re.match(r"^\s+match: https?://", x) for x in blk):
            out.extend(blk); i = j; continue          # 本地文件路径型规则集，不涉及下载刷新
        if any(re.search(r"update_interval:\s*\d+", x) for x in blk):
            nb = [re.sub(r"update_interval:\s*\d+", "update_interval: " + str(seconds), x)
                  for x in blk]
            # 只有**真的改了值**才计入 updated：从已钉好一周的版本复制出来的新档，这里应为 0。
            # （原先无条件 +1，把"字段本就等于约定值"也算成改值，读数会虚高一倍。）
            updated += (nb != blk)
            blk = nb
        else:
            k = next((n for n, x in enumerate(blk) if re.match(r"^\s+policy:", x)), None)
            if k is None:
                raise SystemExit("❌ " + tag + ": rule_set 块没有 policy 行，不知该插在哪")
            blk.insert(k + 1, "    update_interval: " + str(seconds))
            added += 1
        out.extend(blk); i = j
    return NL.join(out), touched, added, updated


def walk_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for fn in filenames:
            if fn.endswith((".md", ".conf", ".yaml", ".yml", ".sh", ".py", ".json")):
                yield os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/")


def main():
    ap = argparse.ArgumentParser(description="分流版升版：四份形态 + 全仓活指向 + CURRENT 行")
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--root", default=REPO_ROOT,
                    help="仓库根（默认取本文件所在位置的上一上一级 ⇒ 任何克隆、任何 cwd 都能跑）")
    ap.add_argument("--interval", type=int, default=EXPECT_INTERVAL)
    ap.add_argument("--keep", action="append", default=[], help="额外排除的路径子串（可多次）")
    ap.add_argument("--apply", action="store_true", help="真正写盘（默认只出计划）")
    ap.add_argument("--gate", action="store_true", help="写完后跑一次 skill/tests/all.sh")
    a = ap.parse_args()

    old, new, root = a.old, a.new, a.root
    if not re.fullmatch(r"routing_v[\d.]+", old) or not re.fullmatch(r"routing_v[\d.]+", new):
        raise SystemExit("❌ 版本号形态应为 routing_v3.1 这样；只支持分流版升版（lazy 版不升号）")
    if old == new:
        raise SystemExit("❌ 新旧版本号相同")
    # 负向断言是关键，但要断掉的是**更长的版本号**，不是文件名后缀：
    #   routing_v3 → 遇到 routing_v3.1 / routing_v32 必须跳过（否则会吃掉长名的头），
    #   routing_v3.1.conf 里的 `.conf` 后缀则是合法命中 —— 所以只在
    #   「后面紧跟数字」或「紧跟 . + 数字」时才排除。
    #   （早先写的是 (?![0-9.])，结果 routing_v3.1.conf 一条都匹配不上，计划只报了 27 处。）
    OLD_RE = re.compile(re.escape(old) + r"(?!\d)(?!\.\d)")
    EXC = [re.compile(r"(^|/)CHANGELOG\.md$"), re.compile("沿革"),
           re.compile(r"(^|/)(surge|egern)/profiles/"),
           # 本脚本自己的用法示例里那两个版本号是**演示值**，不是活指向 —— 跟着改会自变成
           # `bump_version.py routing_v3.2 routing_v3.2` 这种废话。
           re.compile(r"(^|/)bump_version\.py$")] + [re.compile(re.escape(k)) for k in a.keep]
    short = re.sub(r"^routing_", "", old)              # routing_v3.1 → v3.1（裸版本提法）

    if not a.apply:
        print("（计划模式：一个字都不写。加 --apply 才落盘）" + NL)

    # ── 1) 四份形态 ────────────────────────────────────────────────────────
    pairs = []
    for rel in ["surge/profiles/" + old + ".conf", "surge/profiles/" + old + ".min.conf",
                "egern/profiles/" + old + ".yaml", "egern/profiles/" + old + ".min.yaml"]:
        src = os.path.join(root, *rel.split("/"))
        dst = os.path.join(root, *rel.replace(old, new).split("/"))
        if not os.path.isfile(src):
            raise SystemExit("❌ 找不到升版起点：" + rel)
        if os.path.isfile(dst):
            raise SystemExit("❌ 目标已存在，不覆盖：" + rel.replace(old, new))
        pairs.append((rel, dst))
    for rel, dst in pairs:
        print("新建 " + os.path.relpath(dst, root) + "  ←  " + rel)
        if a.apply:
            shutil.copyfile(os.path.join(root, *rel.split("/")), dst)

    # ── 2) 新文件内部：钉刷新秒数 + 自称改写 ───────────────────────────────
    if a.apply:
        T = A = U = S = 0
        for rel, dst in pairs:
            text, eol = read(dst)
            fn = set_interval_surge if dst.endswith(".conf") else set_interval_egern
            text, t, ad, up = fn(text, a.interval, os.path.basename(dst))
            text, ns = OLD_RE.subn(new, text)
            write(dst, text, eol)
            T += t; A += ad; U += up; S += ns
            print("   " + os.path.relpath(dst, root) + "：远程规则集 " + str(t) + " 条"
                  "（新补 " + str(ad) + " / 改值 " + str(up) + "）、自称改写 " + str(ns) + " 处")
        print("   合计 规则集 " + str(T) + " 条 · 新补 " + str(A) + " · 改值 " + str(U)
              + " · 自称 " + str(S) + " 处")
    else:
        print("（钉刷新秒数与新文件自称改写只在 --apply 时执行）")

    # ── 3) 全仓"活指向"改写 ────────────────────────────────────────────────
    hits, skipped = [], []
    for rel in walk_files(root):
        p = os.path.join(root, *rel.split("/"))
        if any(rx.search(rel) for rx in EXC):
            if OLD_RE.search(read(p)[0]):
                skipped.append(rel)
            continue
        text, eol = read(p)
        n = len(OLD_RE.findall(text))
        if n:
            hits.append((rel, n, text, eol))
    print(NL + "活指向改写：" + str(len(hits)) + " 个文件、"
          + str(sum(x[1] for x in hits)) + " 处")
    for rel, n, _, _ in sorted(hits):
        print("   " + rel + "  ×" + str(n))
    if a.apply:
        for rel, n, text, eol in hits:
            write(os.path.join(root, *rel.split("/")), OLD_RE.sub(new, text), eol)
    else:
        print("（--apply 才写）")

    # ── 4) CURRENT 行核对（三份 runner 各一条）─────────────────────────────
    print(NL + "CURRENT 承诺值：")
    for rel in RUNNER_FILES:
        p = os.path.join(root, *rel.split("/"))
        if not os.path.isfile(p):
            print("   ❌ 找不到 " + rel)
            continue
        for l in [x for x in read(p)[0].split(NL) if "CURRENT=" in x and ":-" in x]:
            if new in l:
                mark = "✅ 已是新版"
            elif old in l:
                mark = "⏳ 待改写" if not a.apply else "❌ 改写没生效，检查 OLD_RE"
            else:
                mark = "❌ 既非新也非旧，手工看"
            print("   " + mark + "  " + rel + ": " + l.strip())

    # ── 5) 脚本故意不碰的东西：列给人看 ───────────────────────────────────
    print(NL + "本脚本**不**改，需要你手工处理的：")
    print("   · CHANGELOG（根 / surge / egern 三处）新章节 —— 升版说明是人写的文案")
    print("   · docs 里的「版本沿革」类记述 —— 历史口径，改了就是篡改")
    print("   · 断言数：两侧回归的阶段计数随 profile 份数增长（新增 2 份 Surge ⇒ 离线 19→23；"
          "新增 2 份 Egern ⇒ 46→50），README / skill/README / checker.md 里写死的读数要同步")
    for rel in skipped:
        print("   · 排除路径里仍有旧名：" + rel + "（确认是历史表述而非活指向）")
    bare, bare_total = [], 0
    for rel in walk_files(root):
        if any(rx.search(rel) for rx in EXC):
            continue
        # 先把"将被改写的全名指涉"抹掉，剩下的才是真·裸版本提法
        body = OLD_RE.sub("", read(os.path.join(root, *rel.split("/")))[0])
        for ln, l in enumerate(body.split(NL), 1):
            if re.search(re.escape(short) + r"(?!\d)(?!\.\d)", l):
                bare_total += 1
                if len(bare) < 24:
                    bare.append(rel + ":" + str(ln) + "  " + l.strip()[:72])
    if bare_total:
        print("   · 裸版本「" + short + "」还有 " + str(bare_total) + " 处，需人判断是否随本次升版一起改：")
        for x in bare:
            print("       " + x)
        if bare_total > len(bare):
            print("       …另有 " + str(bare_total - len(bare)) + " 处同类")
    else:
        print("   · 裸版本「" + short + "」：无残留")
    print("   · 订阅端 URL 换成 " + new + "（在你自己的服务器上，不在这个仓库里）")
    print("   · 新建的 profile 与 `.min`：由仓根 `.gitattributes` 钉成 LF，无需手工处理；"
          "提交前 `bash skill/tests/all.sh` 的第 4 项会实测「磁盘字节 == 提交字节」")

    # ── 6) 验收 ───────────────────────────────────────────────────────────
    if a.apply and a.gate:
        print(NL + "跑闸门：")
        rc = subprocess.call(["bash", ALL_SH])
        print("检查退出码 " + str(rc))
        return 0 if rc == 0 else 1
    print(NL + ("已落盘。验收：bash skill/tests/all.sh" if a.apply
                else "计划已出，未写盘。确认后加 --apply（可再带 --gate）"))
    return 0


if __name__ == "__main__":
    # Windows GBK 终端里 print 中文/emoji 会 UnicodeEncodeError ⇒ 退出码 1，
    # 而"计划模式"绝不该因为编码问题看起来像失败。统一按 UTF-8 输出。
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:                                      # noqa: BLE001
            pass
    sys.exit(main())
