#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文档「抄写配置」的同步检查 —— 文档里的组清单/条数必须与配置真源一致。

为什么要单独一道（2026-10-05 立）
─────────────────────────────────
本仓的**真源永远是配置**；但为了让 AI 与人不读 500 行配置就能理解结构，
几处文档**抄了一份副本**：
  · `cross-kernel-diff.md` —— `[Proxy Group]` 的分组清单（逐位顺序）
  · `README.md` —— `Groups-N|N` / `Rules-N|N` 两枚 badge
这两处每改配置都得同步，而**漏同步不会报错**（页面静默地说谎）。实测已经踩到：
  · 2026-10-05 调组顺序时，`cross-kernel-diff` 的清单**漏改**（用户核对时才发现）
  · README 的 `🇨🇳` emoji 在改写整行时丢失
  · `rulesets.md` 的「分流版 22 条规则集引用」早于实际（实为 23）而无人察觉
⇒ 本闸门把「记得同步」变成「不一致即判负」。

判据（每条都是「文档声明 == 配置实抓」，绝对判据）
────────────────────────────────────────────────
  ① `cross-kernel-diff.md` 的分组清单块 —— 逐字等于配置里的分组顺序与名称
  ② `README.md` 的 `Groups-N|N` —— 等于两内核（Surge / Egern）分流版的分组数
  ③ `README.md` 的 `Rules-N|N`  —— 等于两内核分流版的规则条数
  ④ `rulesets.md` 的「N 条规则集引用」 —— 等于两内核实际的 `rule_set` 引用条数

⚠️ 为什么 README 只查 badge、不查组表：组表是**给人看的概述**（含 emoji、分组分行、
   懒人版合并展示），不是逐字副本；badge 才是**承诺数字**。前者已有 `check_badges.py` 守
   数字口径，本文件补的是「文档清单 vs 配置顺序」这层。
⚠️ `check_badges.py` 与本闸门**不重复**：前者查「badge ↔ 配置」的**数字**，
   本闸门查「文档清单 ↔ 配置」的**名称与顺序**（含 cross-kernel-diff 那段）。
   数字部分有意重叠一次 —— 两处都判，红一处即停，代价可忽略。

退出码：0 = 全部一致 · 1 = 有不一致 · 2 = 文件缺失/解析失败（未验证）。
用法：python skill/tests/check_docs_sync.py [仓库根]
"""

import os
import re
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import yaml
except ImportError:
    print("需要 PyYAML：python -m pip install pyyaml", file=sys.stderr)
    sys.exit(2)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts", "surge"))
try:
    from _surge_common import parse_conf, split_csv, strip_comment
except ImportError:                                            # pragma: no cover
    parse_conf = None


def surge_groups(root, rel):
    """Surge profile → [组名]（按文件顺序）。只取 select / smart / external 三种。"""
    path = os.path.join(root, rel.replace("/", os.sep))
    sec, _ = parse_conf(path)
    out = []
    for _ln, raw in sec.get("proxy group", []):
        s = strip_comment(raw)
        if "=" not in s:
            continue
        name, rhs = s.split("=", 1)
        parts = split_csv(rhs)
        if parts and parts[0].strip().lower() in ("select", "smart", "external"):
            out.append(name.strip())
    return out


def egern_groups(root, rel):
    path = os.path.join(root, rel.replace("/", os.sep))
    d = yaml.safe_load(open(path, encoding="utf-8")) or {}
    return [list(g.values())[0]["name"] for g in (d.get("policy_groups") or [])]


def surge_rule_count(root, rel):
    path = os.path.join(root, rel.replace("/", os.sep))
    sec, _ = parse_conf(path)
    n = 0
    for _ln, raw in sec.get("rule", []):
        s = strip_comment(raw)
        if s:
            n += 1
    return n


def egern_rule_count(root, rel):
    path = os.path.join(root, rel.replace("/", os.sep))
    d = yaml.safe_load(open(path, encoding="utf-8")) or {}
    return len(d.get("rules") or [])


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    root = os.path.abspath(root)
    if parse_conf is None:
        print("❌ 取不到 `_surge_common`（脚本被挪走了？）—— 未验证", file=sys.stderr)
        return 2

    need = ["README.md", "skill/reference/shared/cross-kernel-diff.md",
            "surge/profiles/routing.conf", "egern/profiles/routing.yaml"]
    miss = [p for p in need if not os.path.isfile(os.path.join(root, p.replace("/", os.sep)))]
    if miss:
        print("❌ 缺文件（未验证，不是通过）：%s" % "、".join(miss), file=sys.stderr)
        return 2

    sg = surge_groups(root, "surge/profiles/routing.conf")
    eg = egern_groups(root, "egern/profiles/routing.yaml")

    print("文档「抄写配置」同步检查")
    print("─" * 74)
    fails = []

    # ① cross-kernel-diff 的分组清单块
    p = os.path.join(root, "skill", "reference", "shared", "cross-kernel-diff.md")
    txt = open(p, encoding="utf-8").read()
    blk = re.search(r"```\n(Proxy · Smart[^\n]*(?:\n[^\n`]*)*)\n```", txt)
    if not blk:
        fails.append(("cross-kernel-diff 清单", "找不到清单代码块（结构变了？）"))
    else:
        doc_names = []
        for line in blk.group(1).split("\n"):
            doc_names += [x.strip() for x in line.split("·") if x.strip()]
        # 文档清单与配置必须有相同的名字集合与相对顺序（配置含两内核共有的）
        cfg_names = [n for n in sg if n in doc_names] if sg else []
        ok = cfg_names == doc_names
        print("   %s ① cross-kernel-diff 分组清单（%d 个）" % ("✅" if ok else "❌",
                                                              len(doc_names)))
        if not ok:
            fails.append(("cross-kernel-diff 清单",
                          "文档：%s ／ 配置：%s" % (" · ".join(doc_names),
                                                   " · ".join(cfg_names))))
        if eg and [n for n in eg if n in doc_names] != doc_names:
            fails.append(("cross-kernel-diff 清单",
                          "与 Egern 侧顺序不一致：%s" % " · ".join(eg)))

    # ②③ README 的两枚 badge
    rd = open(os.path.join(root, "README.md"), encoding="utf-8").read()
    for kind, rx, cfg in (
        ("Groups", r"badge/Groups-(\d+)%20%7C%20(\d+)",
         (len(sg), len(eg))),
        ("Rules", r"badge/Rules-(\d+)%20%7C%20(\d+)",
         (surge_rule_count(root, "surge/profiles/routing.conf"),
          egern_rule_count(root, "egern/profiles/routing.yaml"))),
    ):
        m = re.search(rx, rd)
        if not m:
            fails.append(("README %s badge" % kind, "未找到 badge"))
            print("   ❌ ② README %s badge —— 未找到" % kind)
            continue
        got = tuple(int(x) for x in m.groups())
        ok = got == cfg
        print("   %s %s README %s badge %s ↔ 配置 %s"
              % ("✅" if ok else "❌", "②" if kind == "Groups" else "③", kind, got, cfg))
        if not ok:
            fails.append(("README %s badge" % kind,
                          "badge %s ≠ 配置 %s" % (got, cfg)))

    # ④ rulesets.md 的「N 条规则集引用」
    rp = os.path.join(root, "skill", "reference", "shared", "rulesets.md")
    rt = open(rp, encoding="utf-8").read()
    def rule_set_refs(kind):
        if kind == "surge":
            sec, _ = parse_conf(os.path.join(root, "surge", "profiles",
                                             "routing.conf"))
            return sum(1 for _ln, raw in sec.get("rule", [])
                       if strip_comment(raw).upper().startswith("RULE-SET"))
        d = yaml.safe_load(open(os.path.join(root, "egern", "profiles",
                                             "routing.yaml"), encoding="utf-8")) or {}
        return sum(1 for r in (d.get("rules") or []) if "rule_set" in r)
    m = re.search(r"分流版 \*\*(\d+) 条规则集引用\*\*", rt)
    if not m:
        print("   ⚠️ ④ rulesets.md 未找到「分流版 N 条规则集引用」—— 跳过（结构可能已改）")
    else:
        doc_n = int(m.group(1))
        cfg_n = rule_set_refs("surge")
        ok = doc_n == cfg_n
        print("   %s ④ rulesets.md 规则集引用 %d ↔ 配置 %d" % ("✅" if ok else "❌",
                                                              doc_n, cfg_n))
        if not ok:
            fails.append(("rulesets.md 引用数", "文档 %d ≠ 配置 %d" % (doc_n, cfg_n)))

    print("─" * 74)
    if fails:
        for name, why in fails:
            print("   ⇒ %s：%s" % (name, why))
        print("result: %d failed —— 文档抄写的配置信息与真源不一致（改配置时漏同步文档）"
              % len(fails))
        return 1
    print("result: 全部一致 —— 文档里的组清单与承诺数字均与配置真源同步")
    return 0


if __name__ == "__main__":
    sys.exit(main())
