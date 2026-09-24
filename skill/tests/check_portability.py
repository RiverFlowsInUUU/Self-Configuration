#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""换设备可移植性检查：只读仓库自身的 tracked 文件，不需要任何其他仓库在场。

为什么要有这一项：本仓的使用方式承诺的是「任何一台机器 clone → 直接改 → 推上去，
双端一致」。会悄悄破坏这件事的只有两类东西——**同一份 commit 在不同机器上落盘成不同字节**，
以及**换个机器就打不开/打错名字的路径**。两类都能在纯静态下判死，所以固化成检查。

规则清单（每条 = 1 个断言，**共 18 条、不随文件数增长**）：
    E1 .gitattributes 在场，且把 `*` 钉成 `text=auto eol=lf`   —— 系统级 autocrlf=true 会被它覆盖
    E2 工作树文本文件零 CRLF                                   —— 磁盘字节 == 提交字节 == raw 字节的前提
    E2b 工作树文本文件零孤立 CR（老 Mac 行尾，同样破坏按 `\n` 写的正则）
    （前置）被跟踪文件全部存在于工作树 —— 缺任何一个即退回退出码 2，不静默跳过
    E3 工作树文本文件零 BOM                                   —— BOM 会让 shebang 与 YAML 头解析当场失效
    N1 所有路径为 Unicode NFC                                 —— macOS 会以 NFD 落盘，同一名字变两个文件
    N2 无 Windows/macOS 非法字符 `\\ / : * ? " < > |`
    N3 无 Windows 保留设备名（CON / PRN / AUX / NUL / COMn / LPTn）
    N4 路径段无首尾空格                                        —— Windows 静默剥掉，两边就对不上
    N4b 路径段无尾点                                           —— 同上，且 git 里留着它 checkout 会失败
    N5 大小写折叠后无冲突                                      —— Windows 的 core.ignorecase=true 会让后者覆盖前者
    N6 机器消费的路径纯 ASCII（skill/ · profiles/ · scripts/ · tests/ · icons/ · 根文件）
       人读的详解正文（docs/）允许中文，且必须过 N1
    L1 相对路径 ≤ 120 字符                                    —— Windows MAX_PATH 260，给 clone 目录留余量
    H1 无单机残留被跟踪（__pycache__ · *.pyc · .DS_Store · Thumbs.db · desktop.ini · *.bak …）
    H2 零字节跟踪文件                                          —— 通常是上一次写入中断的壳
    H3 无符号链接                                              —— 在 Windows 上 checkout 出来就是普通文本文件
    H3b 无 submodule                                           —— 换机器后 clone 下来是空目录，检查跟着失效
    H4 .gitignore 对上述单机残留与 OS 垃圾文件有兜底
    S1 每个 .sh 的首行是 `#!/` shebang                            —— 换机器后行首多了空格/BOM 就跑不起来了

退出码：0 全绿 · 1 有判负 · 2 前置环境不达标（不在 git 仓库里 / 拿不到 tracked 清单）
"""

import os
import re
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))          # <仓根>/skill/tests
ROOT = os.path.dirname(os.path.dirname(HERE))               # → skill → 仓根

ILLEGAL = set('\\:*?"<>|')
WIN_RESERVED = {"CON", "PRN", "AUX", "NUL"}
WIN_RESERVED |= {"COM%d" % i for i in range(1, 10)}
WIN_RESERVED |= {"LPT%d" % i for i in range(1, 10)}
# ⚠️ 自检：清单里不许留下**未格式化**的模板串。
#    2026-09-25 实测：上面那行原本写成 `{"LPT%d" for i in ...}`（漏了 `% i`），
#    于是加进去的是字面量 `LPT%d` 而不是 `LPT1`…`LPT9` —— N3 声称覆盖 LPTn，实际一个都不判。
#    这类"集合内容写错"`check_tools.py` 的 T5/T6 都判不到（它们只判绑定与引用），
#    所以在源头立一条 fail-loud 自检：带 `%` 的名字一定是漏了格式化。
if any("%" in n for n in WIN_RESERVED):
    raise SystemExit("❌ 前置：WIN_RESERVED 里有未格式化的模板串 %s ⇒ 检查集合推导式是不是漏了 `%% i`"
                     % sorted(n for n in WIN_RESERVED if "%" in n))
TEXT_EXT = (".md", ".py", ".sh", ".conf", ".yaml", ".yml", ".txt", ".list",
            ".json", ".js", ".html", ".gitignore", ".gitattributes")
BINARY_EXT = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".icns", ".mmdb", ".pcap",
              ".p12", ".pfx", ".pem", ".key", ".crt")
# 这些前缀下的路径必须纯 ASCII：脚本、配置、图标、测试、fixture 都是被程序消费的
MACHINE_PREFIXES = ("skill/", "icons/", "surge/profiles/", "egern/profiles/",
                    "surge/scripts/", "egern/scripts/", "surge/tests/", "egern/tests/")
GARBAGE = ("__pycache__/", ".pyc", ".pyo", ".DS_Store", "Thumbs.db", "desktop.ini",
           ".pytest_cache/", ".mypy_cache/", ".ruff_cache/", ".orig", ".bak", ".tmp",
           ".log", ".swp", "~")


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True)
    if out.returncode != 0:
        return None
    return [f.decode("utf-8", "replace") for f in out.stdout.split(b"\0") if f]


def is_text(path):
    """E2/E2b/E3 的判定域：哪些跟踪文件该是 LF 文本。

    无扩展名的跟踪文件（`LICENSE` / `NOTICE` / `README` 之类）**同样是文本** ——
    早先只按扩展名白名单判，`LICENSE` 落在白名单外，成了字节层的一个盲区。
    将来若真要放一个无扩展名的二进制，必须在 `.gitattributes` 里显式标 `binary`，
    并同时加进 BINARY_EXT，别靠"没有扩展名所以不算文本"蒙过去。
    """
    if path.endswith(BINARY_EXT):
        return False
    name = os.path.basename(path)
    return "." not in name or name.startswith(".") or path.endswith(TEXT_EXT)


def read(path):
    with open(os.path.join(ROOT, path), "rb") as fh:
        return fh.read()


def main():
    files = tracked_files()
    if files is None:
        print("❌ 前置不达标：这里不是 git 仓库，拿不到 tracked 清单")
        print("   仓库根按本文件定位：%s" % ROOT)
        return 2
    # ⚠️ 前置：被跟踪文件必须都在工作树里。
    #    少任何一个（`git rm` 未提交 / 改到一半 / 误删）时，下面的 read() 会抛
    #    FileNotFoundError ⇒ traceback + **退出码 1 + 没有 TOTAL 行**：既让后面 18 条判据
    #    一条都不跑，又把"没跑成"伪装成"判负"（本仓最忌的那种假绿的反面）。
    #    2026-09-25 实测：`rm icons/grok.png` 就是这个表现。
    #    ⇒ 归到退出码 2（前置/环境不达标），与"不是 git 仓库"同一档。
    missing = [p for p in files if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        print("❌ 前置不达标：%d 个被跟踪文件在工作树里不存在" % len(missing))
        for p in missing[:6]:
            print("     · %s" % p)
        if len(missing) > 6:
            print("     · …另有 %d 个" % (len(missing) - 6))
        print("   ⇒ 先 `git status` 看清是删除还是改名；本项不判内容，退回退出码 2"
              "（没跑成 ≠ 跑绿）")
        return 2
    print("仓库根：%s" % ROOT)
    print("tracked 文件：%d 个" % len(files))

    checks = []          # (编号, 说明, [违规样例])

    # ── E1 .gitattributes ────────────────────────────────────────────
    if ".gitattributes" not in files:
        checks.append(("E1", ".gitattributes 在场", ["缺文件"]))
    else:
        txt = read(".gitattributes").decode("utf-8", "replace")
        ok = re.search(r"^\*\s+text=auto\s+eol=lf\s*$", txt, re.M)
        checks.append(("E1", ".gitattributes 把 * 钉成 text=auto eol=lf",
                       [] if ok else ["没有 `* text=auto eol=lf` 这一行"]))

    # ── E2 / E3 / H2 / S1 字节层 ─────────────────────────────────────
    crlf, lone_cr, bom, empty, no_shebang = [], [], [], [], []
    for p in files:
        b = read(p)
        if not b and not p.endswith(BINARY_EXT):
            empty.append(p)
        if p.endswith(BINARY_EXT) or not is_text(p):
            continue
        if b.startswith(b"\xef\xbb\xbf"):
            bom.append(p)
        if b"\r\n" in b:
            crlf.append(p)
        elif b"\r" in b:
            lone_cr.append(p)
        if p.endswith(".sh"):
            if not b.startswith(b"#!/"):
                no_shebang.append(p)
    checks.append(("E2", "工作树文本文件无 CRLF", crlf))
    checks.append(("E2b", "工作树文本文件无孤立 CR", lone_cr))
    checks.append(("E3", "工作树文本文件无 BOM", bom))
    checks.append(("H2", "无零字节跟踪文件", empty))
    checks.append(("S1", "每个 .sh 以 #!/ 开头", no_shebang))

    # ── 命名层 ───────────────────────────────────────────────────────
    non_nfc = [p for p in files if unicodedata.normalize("NFC", p) != p]
    illegal = [p for p in files if set(p) & ILLEGAL]
    reserved, spaced, tail_dot = [], [], []
    ascii_bad, too_long = [], []
    for p in files:
        for seg in p.split("/"):
            if seg.split(".")[0].upper() in WIN_RESERVED:
                reserved.append(p)
            if seg != seg.strip():
                spaced.append(p)
            if seg.endswith("."):
                tail_dot.append(p)
        if any(ord(c) > 127 for c in p) and p.startswith(MACHINE_PREFIXES):
            ascii_bad.append(p)
        if len(p) > 120:
            too_long.append(p)
    folded = {}
    for p in files:
        folded.setdefault(p.lower(), []).append(p)
    collide = [v for v in folded.values() if len(v) > 1]

    checks.append(("N1", "所有路径为 NFC", non_nfc))
    checks.append(("N2", "无 Windows/macOS 非法字符", illegal))
    checks.append(("N3", "无 Windows 保留设备名", reserved))
    checks.append(("N4", "路径段无首尾空格", spaced))
    checks.append(("N4b", "路径段无尾点", tail_dot))
    checks.append(("N5", "大小写折叠无冲突", [" + ".join(v) for v in collide]))
    checks.append(("N6", "机器消费的路径纯 ASCII（docs 正文允许中文）", ascii_bad))
    checks.append(("L1", "相对路径 ≤ 120 字符", too_long))

    # ── 残留与外链结构 ───────────────────────────────────────────────
    garbage = [p for p in files if any(g in p for g in GARBAGE)]
    checks.append(("H1", "无单机残留被跟踪", garbage))
    links = [p for p in files
             if os.path.islink(os.path.join(ROOT, p))]
    checks.append(("H3", "无符号链接", links))
    checks.append(("H3b", "无 submodule", [] if ".gitmodules" not in files else [".gitmodules"]))
    gi = read(".gitignore").decode("utf-8", "replace") if ".gitignore" in files else ""
    # 期望的是 `.gitignore` 里的**字面条目**；`*.py[cod]` 一条覆盖 .pyc/.pyo/.pyd 三种后缀
    missing = [g for g in ("__pycache__/", "*.py[cod]", ".DS_Store", "Thumbs.db",
                           "desktop.ini", "*.bak", "*.tmp", "*.log") if g not in gi]
    checks.append(("H4", ".gitignore 兜底覆盖单机残留与 OS 垃圾", missing))

    bad = 0
    for cid, desc, viol in checks:
        if viol:
            bad += 1
            print("   ❌ %s %s · %d 处：" % (cid, desc, len(viol)))
            for v in viol[:6]:
                print("        · %s" % v)
        else:
            print("   ✅ %s %s" % (cid, desc))
    total = len(checks)
    print("TOTAL: %d passed, %d failed" % (total - bad, bad))
    if bad:
        print("   修法：换设备一致性靠 `.gitattributes` 与命名纪律，不靠任何人改本机 git 配置。")
        print("   详见 docs/注意事项.md 的「换设备 / 双端一致」一节。")
    return 1 if bad else 0


if __name__ == "__main__":
    # Windows GBK 终端里 print 中文/emoji 会 UnicodeEncodeError ⇒ 退出码 1，
    # 看着像判负、其实一条都没判。与 bump_version.py / make_min.py 同款兜底。
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:                                      # noqa: BLE001
            pass
    sys.exit(main())
