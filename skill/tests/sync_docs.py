#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文档「抄写配置」的生成器 —— 从配置真源重写文档里的 AUTO 段。

为什么有这个（2026-10-05 立）
─────────────────────────────
文档里有几处**抄了配置**的信息（分组清单、分组数、规则数、规则集引用数）。
它们是**副本**：改配置时得同步改，而**漏同步不会报错** —— 页面静默地说谎。
实测已踩三次：组清单漏改（用户核对才发现）· README 的 emoji 丢失 · 引用数过期。

本仓对这类"真源 → 产物"已有成功范式（`make_min.py`：完整版 → `.min`）：
  · 有单一真源 · 有生成产物 · 有 `--check` 漂移闸门 · 产物**不手改**
本脚本把同一范式用到**文档**上 ⇒ 副本从"要靠人记得同步"变成"脚本自动重写"。

AUTO 段语法（HTML 注释，GitHub 渲染时不可见）
─────────────────────────────────────────────
    <!-- auto:KEY -->  旧内容（任意行数）  <!-- /auto:KEY -->

一行内联式（数字类，标记可嵌在句中）：
    现役两侧各 **<!-- auto:group-count -->22<!-- /auto:group-count --> 个分组**

生成器只**替换标记之间的内容**，标记本身与其外的文字一字不动。

已支持的 KEY
────────────
  group-list      分组清单（`cross-kernel-diff.md`，代码块内的多行 · 分隔）
  group-count     分组数（同上，内联数字）
  rule-count      规则条数（同上，内联数字）
  ruleset-refs    `rulesets.md` 的分流版规则集引用数

⚠️ 换行策略（`group-list`）：按 ` · ` 边界打包到不超过 **82 字符**。
   首次 `--apply` 会把现有清单**重排一次**（现状是人工语义分段、无固定规则）；
   此后同一份配置永远产出同一份文本 ⇒ `--check` 稳定通过。
   要调整观感就改 `LIST_WIDTH` 常量，**不要手改文档里的那段**（会被下次生成覆盖）。

用法
────
    python skill/tests/sync_docs.py              # 计划模式：只报哪些段会变
    python skill/tests/sync_docs.py --check      # 闸门：有不一致 exit 1（替代专门的对拍闸门）
    python skill/tests/sync_docs.py --apply      # 写盘

退出码：0 = 一致/已写 · 1 = --check 发现漂移 · 2 = 环境不达标（缺文件/解析失败）。
"""

import argparse
import io
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "skill", "scripts", "surge"))
try:
    from _surge_common import parse_conf, split_csv, strip_comment
except ImportError:                                           # pragma: no cover
    print("❌ 取不到 `_surge_common` —— 环境不达标", file=sys.stderr)
    sys.exit(2)

R_CONF = "surge/profiles/routing.conf"
R_YAML = "egern/profiles/routing.yaml"
L_CONF = "surge/profiles/lazy.conf"
L_YAML = "egern/profiles/lazy.yaml"

LIST_WIDTH = 82          # group-list 的打包宽度（见头注「换行策略」）


# ============================================================================
# 配置真源：提取
# ============================================================================

def _groups_of_conf(rel):
    """Surge .conf → [(组名, 类型)]，按文件顺序。"""
    sec, _ = parse_conf(os.path.join(ROOT, rel.replace("/", os.sep)))
    out = []
    for _ln, raw in sec.get("proxy group", []):
        s = strip_comment(raw)
        if "=" not in s:
            continue
        name, rhs = s.split("=", 1)
        parts = split_csv(rhs)
        if parts and parts[0].strip().lower() in ("select", "smart", "external"):
            out.append((name.strip(), parts[0].strip().lower()))
    return out


def _groups_of_yaml(rel):
    d = yaml.safe_load(open(os.path.join(ROOT, rel.replace("/", os.sep)),
                            encoding="utf-8")) or {}
    return [(list(g.values())[0]["name"], list(g.keys())[0])
            for g in (d.get("policy_groups") or [])]


def _rule_count_conf(rel):
    sec, _ = parse_conf(os.path.join(ROOT, rel.replace("/", os.sep)))
    return sum(1 for _ln, raw in sec.get("rule", []) if strip_comment(raw))


def _rule_count_yaml(rel):
    d = yaml.safe_load(open(os.path.join(ROOT, rel.replace("/", os.sep)),
                            encoding="utf-8")) or {}
    return len(d.get("rules") or [])


def _ruleset_refs_conf(rel):
    """指向规则集的条目数（`RULE-SET` 开头，含规则集引用位）。"""
    sec, _ = parse_conf(os.path.join(ROOT, rel.replace("/", os.sep)))
    return sum(1 for _ln, raw in sec.get("rule", [])
               if strip_comment(raw).upper().startswith("RULE-SET"))


def _ruleset_refs_yaml(rel):
    d = yaml.safe_load(open(os.path.join(ROOT, rel.replace("/", os.sep)),
                            encoding="utf-8")) or {}
    return sum(1 for r in (d.get("rules") or []) if "rule_set" in r)


def pack_list(names, width=LIST_WIDTH):
    """把名字用 ` · ` 连接并按宽度打包成多行（` · ` 处断行，不拆名字）。"""
    lines, cur = [], ""
    for n in names:
        cand = n if not cur else cur + " · " + n
        if cur and len(cand) > width:
            lines.append(cur)
            cur = n
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def build_values():
    """→ {KEY: 生成内容(字符串，多行用 \\n)}"""
    sg = [n for n, _t in _groups_of_conf(R_CONF)]
    eg = [n for n, _t in _groups_of_yaml(R_YAML)]
    surf_ok = sg == eg
    # 清单取 Surge 侧（两内核顺序本就要求一致；不一致时本脚本不负责裁决，
    # 那是 audit_routing_coverage 的 Z0 与 check_docs_sync 的活）
    vals = {
        "group-list": "\n".join(pack_list(sg)),
        "group-count": str(len(sg)),
        "rule-count": str(_rule_count_conf(R_CONF)),
        "ruleset-refs": str(_ruleset_refs_conf(R_CONF)),
    }
    return vals, surf_ok


# ============================================================================
# AUTO 段：定位与替换
# ============================================================================
# 一段 = `<!-- auto:KEY -->` ... `<!-- /auto:KEY -->`（可跨行）

def find_segments(text):
    """→ [(KEY, start_of_inner, end_of_inner)]（按出现顺序）。"""
    out = []
    for m in re.finditer(r"<!--\s*auto:([A-Za-z0-9_-]+)\s*-->(.*?)<!--\s*/auto:\1\s*-->",
                         text, re.S):
        key = m.group(1)
        s = m.start(2)
        e = m.end(2)
        out.append((key, s, e))
    return out


def rewrite(text, vals, apply_):
    """→ (新文本, [变了的 KEY])。不改动标记本身。"""
    changed = []
    # 从后往前替换，避免位移影响
    segs = find_segments(text)
    for key, s, e in reversed(segs):
        if key not in vals:
            continue
        new = vals[key]
        # 多行段：把内容包在换行里，保持可读
        if "\n" in new:
            new = "\n" + new + "\n"
        if text[s:e] != new:
            changed.append(key)
            text = text[:s] + new + text[e:]
    return text, list(dict.fromkeys(reversed(changed)))


# ============================================================================
# 主流程
# ============================================================================

TARGETS = [
    "skill/reference/shared/cross-kernel-diff.md",
    "README.md",
    "skill/reference/shared/rulesets.md",
]


def main():
    ap = argparse.ArgumentParser(description="文档 AUTO 段生成器（真源=配置）")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="闸门：有不一致 exit 1")
    g.add_argument("--apply", action="store_true", help="写盘")
    a = ap.parse_args()

    # 前置：四份现役 profile 都在（缺了就是环境不达标，不是"没有漂移"）
    need = [R_CONF, R_YAML, L_CONF, L_YAML] + TARGETS
    miss = [p for p in need if not os.path.isfile(os.path.join(ROOT, p.replace("/", os.sep)))]
    if miss:
        print("❌ 缺文件（环境不达标，不是通过）：%s" % "、".join(miss), file=sys.stderr)
        return 2

    vals, surf_ok = build_values()
    if not surf_ok:
        print("⚠️ 两内核分组顺序不一致 —— 本脚本按 Surge 侧生成；"
              "顺序问题由 Z0 / check_docs_sync 报，不在此处裁决。")

    print("文档 AUTO 段同步（真源 = 配置）")
    print("─" * 72)
    total_changed = []
    for rel in TARGETS:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        text = io.open(path, encoding="utf-8").read()
        segs = find_segments(text)
        keys = [k for k, _s, _e in segs]
        if not segs:
            print("   ⏭  %-46s 无 AUTO 段" % rel)
            continue
        new, changed = rewrite(text, vals, a.apply)
        mark = "�’" if changed else "✅"
        print("   %s %-46s %d 段 %s" % (mark, rel, len(segs),
                                        ("（变了：%s）" % "、".join(changed)) if changed else ""))
        if changed:
            total_changed += [(rel, k) for k in changed]
        if a.apply and changed:
            io.open(path, "w", encoding="utf-8", newline="").write(new)

    print("─" * 72)
    if a.apply:
        print("已写盘：%d 处" % len(total_changed))
        return 0
    if a.check:
        if total_changed:
            print("result: %d 处漂移 —— 跑 `python skill/tests/sync_docs.py --apply` 重写"
                  % len(total_changed))
            return 1
        print("result: 全部一致 —— 文档 AUTO 段与配置真源同步")
        return 0
    print("（计划模式：一个字都不写。加 --apply 落盘，加 --check 作闸门）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
