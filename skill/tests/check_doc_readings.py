#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文档读数对拍：把散在十来篇文档里的「X 组 / Y 条 / Z 份 / 当前版本」跟实测值比一遍。

为什么要有这一项（治的是本项目反复发生的那类返工）：
  本仓的读数组数、规则条数、规则集条数、profile 份数、图标数、检查项数、当前推荐版
  在 README / AGENTS / docs / skill / 两份 DetailsReadme 里**各写一遍**，而此前
  **没有任何检查会因为"改了 profile 忘了改文档"而报错** —— 只能一轮轮 grep 反查、逐个数字重测。
  这一项把它变成一条命令：不吻合就直接点名「哪个文件第几行写的 24，实测 23」。

固定规则清单（每条 = 1 个断言，**共 11 条、不随文件数增长**）：
    D0 两内核逐位对齐：组数 / 规则条数 / 规则集条数 三对 × 两形态必须相等（抓"只动了一侧"）
    D1 策略组数      —— 「N 组 / N 个策略组」类声明 == 实测组数
    D2 规则条数      —— 「N 条 … 规则」类声明 == 实测 `[Rule]` / `rules` 非注释条目数
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
# 排除关键词：文件路径里含这些片段的整篇不扫（历史记录，旧数字是对的）
HISTORY = ("日志旧版原文", "CHANGELOG", "体检报告", "/docs/07-")
# 固定名四件 = 永久订阅地址；头注所在 = 这四件（.min 形态由对拍器保证与完整版同内容，不再单独钉版本）
FIXED_NAMES = {"routing.conf", "routing.min.conf", "lazy.conf", "lazy.min.conf",
               "routing.yaml", "routing.min.yaml", "lazy.yaml", "lazy.min.yaml"}
HEAD_FILES = ("surge/profiles/routing.conf", "surge/profiles/lazy.conf",
              "egern/profiles/routing.yaml", "egern/profiles/lazy.yaml")
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
          "八": 8, "九": 9, "十": 10}

# ── D10：豁免行 ───────────────────────────────────────────────────────────
# 这条正则**逐字抄自消费方** `skill/scripts/surge/check_surge_dns.py:load_waivers()`。
# 为什么要逐字：豁免的失效方式全是静默的 —— 形状差一点，`finditer` 一条都不匹配，
# profile 里明明写着"这一处是刻意的"，审计器却按没豁免判（或反过来，多下一条重复编号时
# `_waivers[cid] = 理由` 后写覆盖先写，先那份理由从此没人看得见）。
WAIVE_CONSUMER = re.compile(r"#\s*audit-waive:\s*(\d+)\s+(.*)")


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
    for rel in LIVE:
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p) and is_live(rel):
            out.append((rel, p))
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
    return m


# ── 一行属于哪个「形态 / 内核」 ─────────────────────────────────────────────
def form_of(line, path):
    low = line.lower() + " " + path.lower()
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


def candidates(m, kern, form, kind):
    """这一类声明在当前行的定位下，实测值可能是哪些。"""
    keys = [("surge", "egern")] if not kern else [(kern, kern)]
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
    if kind in ("icons", "items"):
        return m[kind]
    if kind == "files":
        if kern:
            return m["%s_files" % kern]
        vals = {m["surge_files"], m["egern_files"]}
        return next(iter(vals)) if len(vals) == 1 else None
    vals = {x.split("=")[1] for x in candidates(m, kern, form, kind)}
    return next(iter(vals)) if len(vals) == 1 else None


def scan(docs, m):
    """返回 (checks, bad, skipped)：checks 是「每条规则命中几处声明」。"""
    hits = {k: 0 for k in ("groups", "rules", "rulesets", "files", "icons", "items", "deadref")}
    bad, skipped = [], []

    RULES = [
        ("icons", re.compile(r"(\d+)\s*个\s*策略组图标")),
        # 「N 项检查」只认与 `all.sh` 同行的（否则会把 check_surge_dns.py 的"12 项检查"也算进来）
        ("items", re.compile(r"([0-9]+|[一二三四五六七八九十])\s*项(?:检查|检查通过)"),
         lambda line: "all.sh" in line),
        ("groups", re.compile(r"(\d+)\s*(?:个)?\s*(?:策略组|分组|组)(?!件|织|图标)")),
        # 「N 份」只认紧跟 `.conf` / `.yaml` 的写法，内核由扩展名定（不看行内有没有 surge/egern 字样）
        ("files", re.compile(r"([0-9]+)\s*份\s*`\.(conf|yaml)`")),
        ("rulesets", re.compile(r"(\d+)\s*条[^。\n]{0,16}(?:规则集|rule_set)|(?:规则集|rule_set)[^。\n]{0,12}?(\d+)\s*条")),
        ("rules", re.compile(r"(\d+)\s*条[^。\n]{0,10}规则(?!集)|(?:规则|`rules`)[^。\n]{0,8}?(\d+)\s*条")),
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
                    if kind == "items" and g in CN_NUM:
                        g = str(CN_NUM[g])
                    hits[kind] += 1
                    k2 = {"conf": "surge", "yaml": "egern"}.get(
                        mm.group(2) if kind == "files" else None, kern)
                    want = expected(m, k2, form, kind)
                    if want is None:
                        cands = candidates(m, k2, form, kind)
                        if kind in ("groups", "rules", "rulesets") and len(
                                {x.split("=")[1] for x in cands}) > 1:
                            # 两内核 / 两形态实测本身就分了叉 —— 这正是本仓最不能容忍的状态，
                            # 不能当成"判不出"放过
                            bad.append("%s:%d [%s] 两侧实测已分叉 %s，文档写 %s ｜ %s"
                                       % (rel, i, kind, " ".join(cands), g, line.strip()[:70]))
                        else:
                            skipped.append("%s:%d [%s] `%s`（形态/内核判不出）"
                                           % (rel, i, kind, line.strip()[:60]))
                        continue
                    if str(want).isdigit() and int(g) != int(want):
                        bad.append("%s:%d [%s] 文档写 %s，实测 %s ｜ %s"
                                   % (rel, i, kind, g, want, line.strip()[:70]))
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
    return hits, bad, skipped


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
    hits, bad, skipped = scan(docs, m)

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
             "deadref": "D8 profile 引用不悬空·订阅 URL 用固定名"}
    for kind in ("groups", "rules", "rulesets", "files", "icons", "items", "deadref"):
        sub = [b for b in bad if "[%s]" % kind in b]
        n = hits.get(kind, 0)
        ck("%s（命中 %d 处声明）" % (NAMES[kind], n), not sub, "\n      " + "\n      ".join(sub[:6]))
    ck("D7 本仓自托管 URL 的落点存在（%d 个）" % len(m["self_urls"]), not m["self_missing"],
       "\n      缺文件：%s" % ", ".join(m["self_missing"]))
    ck("D9 头注即当前版·同族跨内核一致且固定名四件齐：%s" % m["version"],
       m["current_ok"], "问题：%s ｜ 头注：%s"
       % (", ".join(m["current_missing"]), m["heads_note"]))
    n_wv, n_wvf, wv_bad = waive_readings()
    ck("D10 豁免行形状与消费方正则同形·编号文件内唯一（当前版 %d 行 / %d 个文件）"
       % (n_wv, n_wvf), not wv_bad, "\n      " + "\n      ".join(wv_bad[:6]))

    print("\n对拍 %d 处声明 ｜ 判据 %d 条 ｜ 无法判定跳过 %d 处"
          % (sum(hits.values()), len(checks), len(skipped)))
    for s in skipped[:8]:
        print("   ↷ " + s)
    if len(skipped) > 8:
        print("   ↷ …另有 %d 处" % (len(skipped) - 8))
    bad_ = [c for c in checks if not c[1]]
    for name, ok_, extra in checks:
        print("   %s %s%s" % ("✅" if ok_ else "❌", name,
                              ("" if ok_ else "" ) + (extra if not ok_ and extra.strip() else "")))
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
