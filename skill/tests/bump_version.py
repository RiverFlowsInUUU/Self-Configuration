#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升版一条命令：当前版逐字节进归档 → 头注按进位规则自增 → 全仓活指向 → 交给闸门验收。

    python skill/tests/bump_version.py                       # 只出计划，一个字都不写（分流版）
    python skill/tests/bump_version.py --family lazy         # 懒人版
    python skill/tests/bump_version.py --apply               # 落盘（不跑检查）
    python skill/tests/bump_version.py --apply --gate        # 落盘后再跑一遍 skill/tests/all.sh
    python skill/tests/bump_version.py --to routing_v4.0     # 显式指定新版本号（默认按进位规则自增）
    python skill/tests/bump_version.py --changelog-stub      # 末尾附一段可粘贴的 CHANGELOG 骨架

为什么长这样（2026-09-24 订阅地址固定化之后）：
    订阅地址是**永久**的 —— 顶层恒为 `routing` / `lazy` 四个文件名，升版**不改文件名**。
    从前"升版"= 新建四份带版本号的文件 + 全仓改指向 + 通知订阅端换地址（每升一版就让一批旧链接失效，
    本仓历史上已经因此断过三次）；现在是"旧内容进归档、新内容留在原地址"：
      · 归档：把当前版**逐字节复制**进 `profiles/config_old/<家族>_v<旧号>`（对拍器 V6 判据要的
              就是这个"同版本 ⇒ 逐字节快照"，所以复制不是移动、也不重新格式化）
      · 版本号：只剩一处显式承诺 —— profile 第一行 `#! version=routing_vX.Y`
              （从前是三处 runner 各一行 `CURRENT=`，改一漏二）
      · 自增规则：小数点后加一个数（3.2 → 3.3）；到 x.9 进位成 (x+1).0；只保留一位小数
      · 订阅端：**不需要再改地址**
    归档不参与任何检查（检查路径上的 glob 都是非递归的），所以升版不会让回归越跑越慢。
    要复核某一版的行为，带着路径直接调对应脚本，例如
    `python skill/scripts/surge/check_surge_dns.py surge/profiles/config_old/routing_v3.2.conf`。

它**不**做：CHANGELOG、各篇「版本沿革」与两份读数快照（`docs/体检报告.md`、`docs/日志旧版原文.md`）
    里的历史表述（那是当时的口径记录，改了就是篡改）；裸版本号提法（`v3.2` 这种没带家族前缀的，
    可能指版本、可能指段落标题，机器判不了）。这些都只**列清单**，交给人。
它也不做 `.min`：本脚本只搬完整版，`.min` 由 `skill/tests/make_min.py` 从完整版重算
    （判据仍由对拍器 `check_min_pair.py` 兜）。改了完整版的**配置本体**之后的顺序是
    `make_min.py --apply` → `bump_version.py --apply`，两步都不动 `config_old/`。

排除口径（默认）：
    CHANGELOG.md            历史条目不改（根那一份；2026-09-24 起它是唯一的日志）
    沿革                    "哪一版改了什么"的记述，靠这一条排除 {surge,egern}/docs/07-*
    docs/体检报告.md        审计读数快照：每节写的都是**那一轮**的观测值，不是活指向
    docs/日志旧版原文.md    合并前日志的只读存档，整篇是历史表述
    (surge|egern)/profiles/ 归档 profile 一律不动（它们带自己的版本头注，改了就等于篡改历史）；
                            当前版四件由本脚本按家族单独处理，其中 `.min` 不碰
    bump_version.py         本脚本自身（用法示例里的版本号是演示值，不是活指向）
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
import time

# 本文件位于 <仓库根>/skill/tests/ ⇒ 上溯两级即仓库根；检查入口同目录。
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALL_SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "all.sh")

EXPECT_INTERVAL = 604800
NL = chr(10)               # 换行：唯一允许的写法
CRLF = chr(13) + NL
OLD_DIR = "config_old"     # 归档目录，住在各侧 profiles/ 下
HEAD_RE = re.compile(r"^#! version=(routing|lazy)_v([0-9]+)\.([0-9])$")

# 家族 ⇒ 顶层固定名。升版时四件都逐字节进归档；只有**完整版两件**参与原地改写，
# `.min` 是"同一份配置去掉注释"，由对拍器 `check_min_pair.py` 判，本脚本不碰。
FULL = {"routing": ["surge/profiles/routing.conf", "egern/profiles/routing.yaml"],
        "lazy": ["surge/profiles/lazy.conf", "egern/profiles/lazy.yaml"]}
FORMS = {"routing": FULL["routing"] + ["surge/profiles/routing.min.conf",
                                        "egern/profiles/routing.min.yaml"],
         "lazy": FULL["lazy"] + ["surge/profiles/lazy.min.conf",
                                 "egern/profiles/lazy.min.yaml"]}


def read(p):
    """返回 (正文（LF）, 原换行形态)。工作树正常是 LF，但别人手工放进来的 CRLF 也按原样写回。"""
    raw = io.open(p, encoding="utf-8", newline="").read()
    return raw.replace(CRLF, NL), (CRLF if CRLF in raw else NL)


def write(p, text, eol):
    io.open(p, "w", encoding="utf-8", newline="").write(text.replace(NL, eol))


def same_bytes(a, b):
    """归档目录里可能已有同名快照 ⇒ 用**字节**判同一份（文本判会放过换行差异）。"""
    try:
        return io.open(a, "rb").read() == io.open(b, "rb").read()
    except OSError:
        return False


def at(root, p):
    """绝对路径 ⇒ 仓内相对名（正斜杠）。给人看的是仓内地址，本机绝对路径不出口。"""
    return os.path.relpath(p, root).replace(os.sep, "/")


def changelog_stub(fam, old, new, date):
    """升版说明的骨架：确定的部分（家族 · 号 · 订阅地址 · 归档去向）写全，正文留空给人。

    只出文本、**不写文件** —— `CHANGELOG.md` 是文案，机器不代笔（见开头"它**不**做"）。
    根文件那三条体例里，脚本能钉的只有「一天一段」和「句首单 emoji」，
    段落归属（`Surge` / `Egern` / `共享层`）与正文由人定 —— 升版两核都动，通常落在各自段里。
    """
    label = {"routing": "分流版", "lazy": "懒人版"}[fam]
    urls = []
    for rel in FULL[fam]:
        d, base = rel.rsplit("/", 1)
        stem, ext = base.rsplit(".", 1)
        urls.append("`" + d + "/" + stem + ".{,.min}." + ext + "`")
    return NL.join([
        "## " + date + "    ← 一天只有一段：仓里已有今天的段就把下面几条并进去，别开第二段",
        "",
        "- 🏷️ **" + label + "升版 `" + old + "` → `" + new + "`**：订阅地址不变（"
        + " · ".join(urls) + "），旧内容逐字节进各侧 `profiles/config_old/`。"
          "这一轮实际改了什么：＿＿",
        "- 🧷 `.min` 由 `python skill/tests/make_min.py --family " + fam + " --apply` 同步"
          "（生成器不碰归档；同号快照存在时它只点名提醒）",
        "- 🔢 验收：`bash skill/tests/all.sh` 五项 TOTAL ＿＿ · ＿＿ · ＿＿ · ＿＿ · ＿＿；"
          "这轮若动了判据，README / 两侧 docs/08 / 两份 checker.md 的读数要同步",
    ])


def head_of(root, rel):
    """读 profile 第一行的版本标记 ⇒ 'routing_v3.2'；读不出或形状不对 ⇒ None。"""
    try:
        first = io.open(os.path.join(root, *rel.split("/")), encoding="utf-8",
                        newline="").readline()
    except OSError:
        return None
    m = HEAD_RE.match(first.rstrip(CRLF).rstrip(NL))
    return "%s_v%s.%s" % (m.group(1), m.group(2), m.group(3)) if m else None


def next_version(ver):
    """进位规则：小数点后加一（3.2→3.3）；x.9 → (x+1).0；只保留一位小数。"""
    fam, _, num = ver.partition("_v")
    major, _, minor = num.partition(".")
    major, minor = int(major), int(minor)
    return "%s_v%d.%d" % (fam, major + 1, 0) if minor == 9 else "%s_v%d.%d" % (fam, major, minor + 1)


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
            # 只有**真的改了值**才计入 updated：已经钉好一周的配置，这里应为 0。
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
    ap = argparse.ArgumentParser(
        description="升版：当前版进 config_old 归档 + 头注自增 + 全仓活指向（订阅地址不变）")
    ap.add_argument("--family", choices=("routing", "lazy"), default="routing",
                    help="升哪个家族（默认分流版）")
    ap.add_argument("--to", help="新版本号，形如 routing_v3.3；默认按进位规则自增当前头注")
    ap.add_argument("--root", default=REPO_ROOT,
                    help="仓库根（默认取本文件所在位置往上两级 ⇒ 任何克隆、任何 cwd 都能跑）")
    ap.add_argument("--interval", type=int, default=EXPECT_INTERVAL)
    ap.add_argument("--keep", action="append", default=[], help="额外排除的路径子串（可多次）")
    ap.add_argument("--apply", action="store_true", help="真正写盘（默认只出计划）")
    ap.add_argument("--gate", action="store_true", help="写完后跑一次 skill/tests/all.sh")
    ap.add_argument("--changelog-stub", action="store_true",
                    help="末尾打一段可粘贴的 CHANGELOG 骨架（只出文本，不写文件）")
    a = ap.parse_args()

    root, fam = a.root, a.family
    # ── 0) 头注是唯一版本来源：两内核必须齐全且一致 ─────────────────────────
    heads = {rel: head_of(root, rel) for rel in FULL[fam]}
    if any(v is None for v in heads.values()):
        raise SystemExit("❌ 有 profile 缺 `#! version=` 头注，先补齐再升版："
                         + " · ".join("%s=%s" % kv for kv in sorted(heads.items())))
    if len(set(heads.values())) != 1:
        raise SystemExit("❌ 两内核头注不一致，升版会把分叉固化："
                         + " · ".join("%s=%s" % kv for kv in sorted(heads.items())))
    old = heads[FULL[fam][0]]
    new = a.to or next_version(old)
    if not re.fullmatch(fam + r"_v[0-9]+\.[0-9]", new):
        raise SystemExit("❌ --to 形态应为 " + fam + "_v3.3（一位小数，家族前缀要和 --family 一致）")
    if new == old:
        raise SystemExit("❌ 新旧版本号相同：" + old)
    if a.to and a.to != next_version(old):
        print("⚠️ 你显式指定的 " + a.to + " 不是 " + old + " 的下一个进位值 —— 按你的指定走。")

    # 负向断言要断掉的是**更长的版本号**，不是文件名后缀：
    #   routing_v3 → 遇到 routing_v3.1 / routing_v32 必须跳过；`.conf` 后缀是合法命中。
    OLD_RE = re.compile(re.escape(old) + r"(?!\d)(?!\.\d)")
    short = re.sub(r"^" + fam + r"_", "", old)              # routing_v3.2 → v3.2（裸版本提法）
    EXC = [re.compile(r"(^|/)CHANGELOG\.md$"), re.compile("沿革"),
           # 读数快照类文档：里面「v3.2 那轮的读数是 0 high / 2 low」这类句子是**当时的观测**，
           # 跟着升版改就等于把证据改成现在。它们会经 `skipped` 列进人工清单，不静默。
           re.compile(r"(^|/)docs/体检报告\.md$"), re.compile(r"(^|/)docs/日志旧版原文\.md$"),
           re.compile(r"(^|/)(surge|egern)/profiles/"),
           # 归档目录：里面的文件带自己的版本头注，任何情况下都不改写
           re.compile(r"(^|/)(surge|egern)/profiles/" + OLD_DIR + r"/"),
           re.compile(r"(^|/)bump_version\.py$")] + [re.compile(re.escape(k)) for k in a.keep]

    if not a.apply:
        print("（计划模式：一个字都不写。加 --apply 才落盘）" + NL)
    print("家族：" + fam + " · 当前头注 " + old + " → 新版 " + new
          + "（订阅地址不变，仍是 " + " / ".join(FULL[fam]) + "）" + NL)

    # ── 1) 逐字节归档当前版（四件形态全进：对拍器 V5 要求每版"完整版 + .min"成对）
    plan_copy, reuse, keep = [], [], []
    for rel in FORMS[fam]:
        # 归档名 = <家族>_v<旧号> + 原后缀：routing.conf → routing_v3.2.conf
        #                                     routing.min.conf → routing_v3.2.min.conf
        suffix = os.path.basename(rel)[len(fam):]
        # dst 必须是 `--root` 下的绝对路径 —— 早先这里存的是仓内相对路径，于是 isfile / copyfile
        # 全按**当前工作目录**解析：从仓外跑一次，"同号快照"这条守卫根本不会触发，`--apply` 还会
        # 把归档写到仓外去。打印仍用仓内相对名（给人看的是地址，不是本机路径）。
        dst = os.path.join(root, os.path.dirname(rel).replace("/", os.sep), OLD_DIR, old + suffix)
        src = os.path.join(root, *rel.split("/"))
        if not os.path.isfile(src):
            raise SystemExit("❌ 当前版不在了，先跑 all.sh 看第 3 项：" + rel)
        if os.path.isfile(dst):
            # 同号快照只允许两种正当情形，都**不覆盖**归档（config_old 是只读历史）：
            #   · 逐字节相同 ⇒ 升版前刚打的照（本轮 lazy 的起点就是这样），不重复复制；
            #   · 内容不同 ⇒ 这个版本已发布过、之后线上又改了没升版 ⇒ 保留已发布那一份，
            #     线上这份未发布的改动随 new 出厂，下次退休时才归档成 <new>。V6 的告警随升号自动消解
            #     （归档号 < new）。从前这里直接拒走，而 --to 改的是新号、动不了归档名 ⇒ 死路一条。
            if same_bytes(src, dst):
                reuse.append(dst)
            else:
                keep.append((dst, rel))
            continue
        plan_copy.append((src, dst, rel))
    for dst in reuse:
        print("快照已就位 " + at(root, dst) + "  ←  与当前版逐字节相同，不重复复制")
    for dst, rel in keep:
        print("⚠️ 保留已发布快照 " + at(root, dst) + "（与线上 " + rel + " 不同）"
              "  ←  不覆盖归档；线上这份改动随 " + new + " 出厂，下次退休才归档 " + new)
    for src, dst, rel in plan_copy:
        print("归档 " + at(root, dst) + "  ←  " + rel + "（逐字节复制）")
        if a.apply:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)

    # ── 2) 当前版原地升号：头注 + 自称 + 刷新秒数 ──────────────────────────
    print(NL + "原地升号（完整版；`.min` 由对拍器兜，本脚本不碰）：")
    for rel in FULL[fam]:
        p = os.path.join(root, *rel.split("/"))
        text, eol = read(p)
        fn = set_interval_surge if p.endswith(".conf") else set_interval_egern
        t = A = U = S = 0
        if a.apply:
            text, t, A, U = fn(text, a.interval, os.path.basename(rel))
            text, S = OLD_RE.subn(new, text)
            if HEAD_RE.match(text.split(NL)[0]) and new not in text.split(NL)[0]:
                raise SystemExit("❌ " + rel + "：头注没被改写，检查 OLD_RE")
            write(p, text, eol)
        print("   " + rel + "：远程规则集 " + str(t) + " 条（新补 " + str(A) + " / 改值 " + str(U)
              + "）、版本指涉改写 " + str(S) + " 处")
    if not a.apply:
        print("   （钉刷新秒数与自称改写只在 --apply 时执行）")

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

    # ── 4) 脚本故意不碰的东西：列给人看 ───────────────────────────────────
    print(NL + "本脚本**不**改，需要你手工处理的：")
    print("   · CHANGELOG.md（根那一份）新章节 —— 升版说明是人写的文案"
          + ("（要骨架：加 --changelog-stub）" if not a.changelog_stub else ""))
    print("   · docs 里的「版本沿革」类记述 —— 历史口径，改了就是篡改")
    print("     （`docs/体检报告.md` 与 `docs/日志旧版原文.md` 同属此列；若确实有活指向混在中间，"
          "按下面「排除路径里仍有旧名」逐条人工确认）")
    print("   · `.min` 形态：改了完整版**配置本体**要跑 "
          "`python skill/tests/make_min.py --family " + fam + " --apply`（生成器，不碰归档），"
          "all.sh 第 3 项实测逐字相同")
    print("   · 断言数**不随版本累积**（归档不进检查路径），但若你这轮动了判据，"
          "README / 两侧 docs/08 / checker.md 的读数要同步")
    for rel in skipped:
        print("   · 排除路径里仍有旧名：" + rel + "（确认是历史表述而非活指向）")
    bare, bare_total = [], 0
    for rel in walk_files(root):
        if any(rx.search(rel) for rx in EXC):
            continue
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
    print("   · 订阅端**无需改动** —— 地址是固定名，这一条正是这次固定化的目的")
    print("   · 归档是新文件：`git add surge/profiles/config_old egern/profiles/config_old`，"
          "别让它们以 untracked 状态漏在提交外")
    print("   · 新建的头注与文档改写都由 `.gitattributes` 钉成 LF；提交前 `bash skill/tests/all.sh`")

    # ── 4-b) CHANGELOG 骨架（要了才给；只出文本，不碰文件）───────────────────
    if a.changelog_stub:
        print(NL + "── CHANGELOG 骨架（贴进根 CHANGELOG.md，正文自己写）──" + NL + NL
              + changelog_stub(fam, old, new, time.strftime("%Y-%m-%d")))

    # ── 5) 验收 ───────────────────────────────────────────────────────────
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
