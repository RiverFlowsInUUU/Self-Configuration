#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文档读数对拍：把散在十来篇文档里的「X 组 / Y 条 / Z 份 / 当前版本」跟实测值比一遍。

为什么要有这一项（治的是本项目反复发生的那类返工）：
  本仓的读数组数、规则条数、规则集条数、profile 份数、图标数、检查项数、当前推荐版
  在 README / AGENTS / docs / skill / 两份 DetailsReadme 里**各写一遍**，而此前
  **没有任何检查会因为"改了 profile 忘了改文档"而报错** —— 只能一轮轮 grep 反查、逐个数字重测。
  这一项把它变成一条命令：不吻合就直接点名「哪个文件第几行写的 24，实测 23」。

固定规则清单（每条 = 1 个断言，**共 10 条、不随文件数增长**）：
    D0 两内核逐位对齐：组数 / 规则条数 / 规则集条数 三对 × 两形态必须相等（抓"只动了一侧"）
    D1 策略组数      —— 「N 组 / N 个策略组」类声明 == 实测组数
    D2 规则条数      —— 「N 条 … 规则」类声明 == 实测 `[Rule]` / `rules` 非注释条目数
    D3 规则集条数    —— 「N 条 … 规则集 / rule_set」类声明 == 实测 RULE-SET / rule_set 引用数
    D4 订阅文件份数  —— 「N 份 `.conf` / `.yaml`」类声明 == 两内核 `profiles/` 下的文件数
    D5 图标数        —— 「N 个策略组图标」== `icons/` 文件数
    D6 检查项数      —— 与 `all.sh` 同行的「N 项检查」== `all.sh` 里 `item` 调用的个数（中文数词也认）
    D7 自托管落点    —— profile 里写出的 `Self-Configuration/main/<路径>` 必须真在仓里
    D8 不悬空指向    —— 文档里写出的 `routing_v*.conf|yaml`（含 `.min`）必须真在 `profiles/` 里
    D9 当前版四件齐  —— 三处 `CURRENT=` 必须一致，且当前版的 `.conf` / `.min.conf` / `.yaml` / `.min.yaml` 都在

**刻意不判的东西**（判了会误伤，交给人）：
  · 判据/回归的断言数（27 / 50 / 14 / 18）—— 那要真跑测试才有值，递归且不划算。
  · 正文里出现的旧版本号 —— 一行常常同时写"当前 v3.2 + 存档 v3 / v3.1"，判它必误伤；
    版本漂移由 D8 / D9 这两条结构性判据兜住（存档被删 ⇒ D8 红；`CURRENT=` 忘改 ⇒ D9 红）。
  · 历史沿革类文件（`docs/07-*`、`日志旧版原文`、`CHANGELOG`、`体检报告`）整篇不扫 —— 旧数字在那儿是对的。
  · 一行里同一类数字出现多次又判不出形态（既没说 lazy 也没说分流）⇒ 跳过不判，
    并在末尾报「跳过 N 处」，让"没判到"这件事本身可见。

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
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
          "八": 8, "九": 9, "十": 10}


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
    cur = {}
    for rel in ("skill/tests/surge/run.sh", "skill/tests/surge/architecture.sh",
                "skill/tests/egern/run.sh"):
        mm = re.search(r'CURRENT:-([A-Za-z0-9._\-]+)',
                       open(os.path.join(ROOT, rel), encoding="utf-8").read())
        if mm:
            cur[rel] = mm.group(1)
    if len(set(cur.values())) != 1:
        sys.stderr.write("❌ 前置：三处 CURRENT= 不一致或找不到：%s\n" % cur)
        sys.exit(2)
    m["version"] = sorted(set(cur.values()))[0]
    m["current_version_num"] = m["version"].split("_")[-1].lstrip("v")
    want = ["surge/profiles/%s.conf" % m["version"],
            "surge/profiles/%s.min.conf" % m["version"],
            "egern/profiles/%s.yaml" % m["version"],
            "egern/profiles/%s.min.yaml" % m["version"]]
    m["current_missing"] = [w for w in want if not os.path.isfile(os.path.join(ROOT, w))]
    m["current_ok"] = len(cur) == 3 and not m["current_missing"]
    asl = os.path.join(ROOT, "egern", "apple_system.list")
    m["apple_system"] = len([l for l in open(asl, encoding="utf-8").read().splitlines()
                             if l.strip() and not l.startswith("#")]) if os.path.isfile(asl) else -1
    # 本仓自托管的规则集 URL：profile 里写了 `Self-Configuration/main/<路径>`，那个路径必须真实存在
    self_urls = set()
    for p in glob.glob(os.path.join(ROOT, "*/profiles/*")):
        if ".min." in os.path.basename(p):
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
            # 悬空指向：文档里写出的 profile 文件名必须真在 profiles/ 里
            for mm in re.finditer(r"\b(routing_v[A-Za-z0-9.]*|lazy)\.((?:min\.)?)(conf|yaml)\b", line):
                name = "%s.%s%s" % (mm.group(1), mm.group(2), mm.group(3))
                hits["deadref"] = hits.get("deadref", 0) + 1
                d = os.path.join(ROOT, "surge" if mm.group(3) == "conf" else "egern", "profiles")
                if not os.path.isfile(os.path.join(d, name)):
                    bad.append("%s:%d [deadref] 文档指向 %s，profiles/ 里没有这个文件 ｜ %s"
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
             "deadref": "D8 profile 文件名不悬空"}
    for kind in ("groups", "rules", "rulesets", "files", "icons", "items", "deadref"):
        sub = [b for b in bad if "[%s]" % kind in b]
        n = hits.get(kind, 0)
        ck("%s（命中 %d 处声明）" % (NAMES[kind], n), not sub, "\n      " + "\n      ".join(sub[:6]))
    ck("D7 本仓自托管 URL 的落点存在（%d 个）" % len(m["self_urls"]), not m["self_missing"],
       "\n      缺文件：%s" % ", ".join(m["self_missing"]))
    ck("D9 三处 CURRENT= 一致且当前版四件齐：%s" % m["version"],
       m["current_ok"], "缺文件：%s" % ", ".join(m["current_missing"]))

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
    sys.exit(main())
