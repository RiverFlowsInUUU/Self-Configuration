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
    print("\n共 %d 对，去注释后不一致 %d 对" % (pairs, bad))
    # 与两侧 runner 同一口径的合计行，便于 all.sh / 文档按断言数对账。
    print("TOTAL: %d passed, %d failed" % (pairs - bad, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
