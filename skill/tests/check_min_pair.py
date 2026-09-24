#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""".min 与完整版对拍 —— 去掉注释与空行后必须逐字相同。

为什么单独要这一项：
    每份 profile 都有两份形态（`.conf` / `.min.conf`、`.yaml` / `.min.yaml`）。
    `.min` 的定位是**同一份配置去掉注释**，不是"裁剪配置"。一旦两版的配置本体漂移，
    照着文档改完整版、实际导入的却是 `.min` ⇒ 改了个寂寞，而且肉眼看不出来。

    既有检查各守了一角、都不覆盖这条：`architecture.sh` 的 ② 只逐字比 DNS 段的键、
    ④-b 只比组顺序，且**只管 Surge 侧**；Egern 侧过去完全没有人对拍过两版形态。

判据（与人工核对时的口径一致）：
    · 删行尾注释（`空格/制表符 + #` 或 `;` 起的部分）
    · 删整行注释与空行
    · 删行尾空白
    剩下逐行比对；任何一处不同即判负，并打印**第一处**差异的行号与两侧内容。

版本与归档序列（2026-09-24 起，订阅地址固定化之后一并由本脚本判）：
    订阅地址钉成 `routing.*` / `lazy.*`，历史版本进 `config_old/` ⇒ "当前是哪一版"只剩
    profile **头注**这一处显式承诺（从前是三份 runner 里各一行 `CURRENT=`，改一处漏两处）。
    判据是固定 14 条：两侧各 6 条（顶层只有固定名四件 · 头注版本标记形状合法 · 归档目录在 ·
    归档文件名形状合法 · 每版成对齐全 · 归档不高于当前版且同版本仍是逐字快照）+ 跨侧 2 条（两侧 routing 版本一致 ·
    两侧 lazy 版本一致）。**条数不随归档文件数增长** —— 与 `CURRENT` 是承诺值同一条纪律。

退出码：0 = 全部成对相同 · 1 = 有不一致 · 2 = 目录/参数问题（profiles 目录不存在）。
用法：python skill/tests/check_min_pair.py [仓库根]     # 默认取本文件所在的仓库根
"""

import os
import re
import sys

# Windows 中文环境的控制台与管道默认 GBK(cp936)：emoji 一 print 就 UnicodeEncodeError、
# 进程以退出码 1 结束 —— 与"期望判负"的用例撞码会假绿。统一钉成 UTF-8。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROFILE_DIRS = ("surge/profiles", "egern/profiles")
TRAIL = re.compile(r"[ \t]+[#;].*$")      # 行尾注释
WHOLE = re.compile(r"^\s*[#;]")           # 整行注释


def normalize(text):
    """去注释、去空行、去行尾空白；CRLF 先归一化成 LF。"""
    lines = text.replace("\r\n", "\n").split("\n")
    out = []
    for ln in lines:
        ln = TRAIL.sub("", ln)
        if not ln.strip() or WHOLE.match(ln):
            continue
        out.append(ln.rstrip())
    return out


def first_diff(a, b):
    """返回第一处不同的 0-based 行号；仅长度不同则返回较短长度。"""
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


VERSION_RE = re.compile(r"^#! version=(routing|lazy)_v([0-9]+)\.([0-9])$")
# 归档名里的版本号按「主.一位小数」起；本仓 2026-09-24 固定化之前有一批只写主号
# （`routing_v3.conf`），一并认 —— V4 要抓的是"新归档没按进位规则起名"，不是考古。
ARCHIVE_RE = re.compile(r"^(routing|lazy)_v([0-9]+(?:\.[0-9])?)(\.min)?\.(conf|yaml)$")
OLD_DIR = "config_old"


def ver_tuple(v):
    """'3.2' / '3' → (3, 2) / (3, 0)，用于比版本先后。"""
    major, _, minor = v.partition(".")
    return (int(major), int(minor or 0))


def head_version(path):
    """读 profile 第一行的版本标记 ⇒ ("routing", "3.2")；读不出或形状不对 ⇒ None。"""
    try:
        with open(path, encoding="utf-8", newline="") as f:
            first = f.readline()
    except OSError:
        return None
    m = VERSION_RE.match(first.rstrip("\r\n"))
    return (m.group(1), "%s.%s" % (m.group(2), m.group(3))) if m else None


def version_checks(root):
    """固定名与归档序列 ⇒ [(判据名, 通过?, 说明)]；两侧各 6 条 + 跨侧 2 条，固定条数。"""
    out, heads = [], {}
    for d in PROFILE_DIRS:
        side = d.split("/")[0]
        ext = "conf" if side == "surge" else "yaml"
        dirpath = os.path.join(root, d.replace("/", os.sep))
        fixed = sorted(["routing.%s" % ext, "routing.min.%s" % ext,
                        "lazy.%s" % ext, "lazy.min.%s" % ext])
        top = sorted(n for n in os.listdir(dirpath) if n.endswith("." + ext))
        out.append(("%s V1 顶层只有固定名四件" % side, top == fixed,
                    "实有：%s" % (", ".join(top) or "（空）")))
        vr = head_version(os.path.join(dirpath, "routing.%s" % ext))
        vl = head_version(os.path.join(dirpath, "lazy.%s" % ext))
        heads[side] = (vr, vl)
        out.append(("%s V2 头注版本标记形状合法" % side,
                    vr is not None and vl is not None and vr[0] == "routing" and vl[0] == "lazy",
                    "routing=%s · lazy=%s（读不出多半是第一行被挪走或写成了 x.y.z）" % (vr, vl)))
        old_dir = os.path.join(dirpath, OLD_DIR)
        if not os.path.isdir(old_dir):
            for k in (3, 4, 5, 6):
                out.append(("%s V%d 归档目录 %s/" % (side, k, OLD_DIR), False, "缺目录"))
            continue
        names = sorted(n for n in os.listdir(old_dir) if not n.startswith("."))
        # V3 的"存在"两字由上面那个 `isdir` 分支兜着（缺目录时 V3–V6 一并判负），
        # 走到这里存在性已成事实 ⇒ 这条唯一还能判的东西是"非空"。从前它写的是字面量 True，
        # 实测：把 surge/profiles/config_old/ 清空成 0 个文件，输出照旧
        # `✅ surge V3 归档目录存在（0 个文件）` · TOTAL: 18 passed ⇒ 一条永远绿的判据占着计数。
        out.append(("%s V3 归档目录存在且非空（%d 个文件）" % (side, len(names)), bool(names),
                    "空归档：每退一版留一份快照是这套沿革制度的前提 ⇒ 目录空 = 快照被手工挪走，"
                    "或归档根本没建起来（缺目录不在此条，由上面的 缺目录 分支判）"))
        groups, illegal = {}, []
        for n in names:
            m = ARCHIVE_RE.match(n)
            if m:
                groups.setdefault((m.group(1), m.group(2)), []).append(n)
            else:
                illegal.append(n)
        out.append(("%s V4 归档文件名形状合法" % side, not illegal, "非法名：%s" % ", ".join(illegal)))
        unpaired = ["/".join(k) + "→" + ",".join(v) for k, v in sorted(groups.items())
                    if len(v) != 2 or sum(1 for x in v if ".min." in x) != 1]
        out.append(("%s V5 归档每版成对齐全（完整版 + .min）" % side, not unpaired,
                    "不齐：%s" % "; ".join(unpaired)))
        # V6：归档里出现"当前版"只有一种正当情况 —— 升版前打的快照，与线上文件逐字节相同。
        #      版本号比当前版更高 ⇒ 归档了一个没发布过的号；同名而内容已漂 ⇒ 线上改了没升版，
        #      或归档被人当工作文件动过（归档目录是只读历史，这条也守住它）。
        v6_bad = []
        for n in names:
            m = ARCHIVE_RE.match(n)
            hv = vr if (m and m.group(1) == "routing") else vl
            if not m or not hv:
                continue
            if ver_tuple(m.group(2)) > ver_tuple(hv[1]):
                v6_bad.append("%s 版本号高于当前版 v%s" % (n, hv[1]))
            elif m.group(2) == hv[1]:
                p_old = os.path.join(old_dir, n)
                p_live = os.path.join(dirpath, "%s%s.%s" % (m.group(1), m.group(3) or "", ext))
                try:
                    same = (open(p_old, "rb").read() == open(p_live, "rb").read())
                except OSError:
                    same = False
                if not same:
                    v6_bad.append("%s 与线上同版本但内容已漂（改了没升版，或归档被动过）" % n)
        out.append(("%s V6 归档不高于当前版·同版本仍是逐字快照" % side, not v6_bad,
                    " ".join(v6_bad)))
    for kind in ("routing", "lazy"):
        a = heads.get("surge", (None, None))[0 if kind == "routing" else 1]
        b = heads.get("egern", (None, None))[0 if kind == "routing" else 1]
        out.append(("X 两侧 %s 版本一致" % kind, bool(a) and a == b, "%s vs %s" % (a, b)))
    return out


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    root = os.path.abspath(root)
    pairs = bad = 0
    for d in PROFILE_DIRS:
        dirpath = os.path.join(root, d.replace("/", os.sep))
        if not os.path.isdir(dirpath):
            sys.stderr.write("找不到 %s —— 参数应当是仓库根（本仓自身）\n" % d)
            return 2
        for name in sorted(os.listdir(dirpath)):
            if ".min." not in name:
                continue
            stem, ext = os.path.splitext(name)
            ann = stem.replace(".min", "") + ext
            full_p, min_p = os.path.join(dirpath, ann), os.path.join(dirpath, name)
            try:
                with open(full_p, encoding="utf-8", newline="") as f:
                    a = normalize(f.read())
                with open(min_p, encoding="utf-8", newline="") as f:
                    b = normalize(f.read())
            except (OSError, UnicodeDecodeError) as e:
                sys.stderr.write("读取失败 %s：%s\n" % (name, e))
                return 2
            pairs += 1
            i = first_diff(a, b)
            if i is None:
                print("✅ %s/%s  ↔  %s（去注释后 %d 行逐字相同）" % (d, ann, name, len(a)))
                continue
            bad += 1
            print("❌ %s/%s ↔ %s  去注释后仍有差异（%d 行 vs %d 行）" % (d, ann, name, len(a), len(b)))
            left = a[i] if i < len(a) else "<此侧已无更多行>"
            right = b[i] if i < len(b) else "<此侧已无更多行>"
            print("   第 %d 行：\n     完整版: %s\n     .min  : %s" % (i + 1, left, right))
    v_out = version_checks(root)
    v_bad = 0
    print("\n固定名与归档序列（判据条数不随归档文件数增长）：")
    for name, ok_, note in v_out:
        print("   %s %s%s" % ("✅" if ok_ else "❌", name, "" if ok_ else "   " + note))
        if not ok_:
            v_bad += 1
    v_pass = len(v_out) - v_bad
    # 与两侧 runner 同一口径的合计行，便于 all.sh / 文档按断言数对账。
    print("\n共 %d 对形态相同 · 归档判据 %d/%d 过" % (pairs - bad, v_pass, len(v_out)))
    print("TOTAL: %d passed, %d failed" % (pairs - bad + v_pass, bad + v_bad))
    return 1 if (bad or v_bad) else 0


if __name__ == "__main__":
    sys.exit(main())
