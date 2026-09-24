#!/usr/bin/env bash
# 一条命令跑完本仓**全部本地检查**：改完配置或文档，只需要记这一条。
#
# 为什么要有这个入口：
#   本仓刻意不挂 CI（理由见 docs/注意事项.md），可检查项并不止一处 ——
#   两套内核的回归（Surge 六阶段里已含架构不变量、全仓 markdown 链接与锚点、
#   全部 profile 的刷新参数）+ 两版形态对拍 + 换设备可移植性。分开跑要记四条命令、
#   读四段输出，串起来一条就能判定"这次改动有没有把什么弄坏"。
#
# 本仓完全独立：这一条命令跑的所有检查**只看本仓库的文件**，
# 不需要任何其他仓库在旁边，也不依赖本机路径、盘符、用户名。仓库根由本脚本自身位置反推
# （$BASH_SOURCE → skill/tests 的上两级），所以 clone 到哪里、叫什么名字都一样能跑。
#
# 用法：
#   bash skill/tests/all.sh                        # 全跑（含联网审计）
#   bash skill/tests/all.sh --offline              # 跳过联网项（离线机器 / 无外网时）
#   CURRENT=routing_v3 bash skill/tests/all.sh     # 覆盖成任意版本（如历史存档版）
#
# 退出码：0 全绿 · 1 有判负 · 2 前置环境不达标
#   （2 = 缺 Python 或缺 PyYAML，或 $CURRENT 指向的 profile 不存在 —— 后者刻意不静默）

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT" || exit 2

# 中文 Windows 的控制台与管道默认 GBK：脚本 print emoji 会崩成退出码 1，
# 与"期望判负"的用例撞码 ⇒ 假绿。另：不许往工作树里掉 .pyc。
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1

OFFLINE=0
for a in "$@"; do
  [ "$a" = "--offline" ] && OFFLINE=1
done
# 外部已经设了 SKIP_NET（有人直接 `SKIP_NET=1 bash all.sh`）也算离线，
# 否则头部会印「联网：开」而下面的阶段其实跳过了 —— 读数与事实不符。
[ "${SKIP_NET:-0}" = "1" ] && OFFLINE=1
if [ "$OFFLINE" = "1" ]; then
  export SKIP_NET=1
fi

PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys" >/dev/null 2>&1; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  printf '❌ 前置：找不到可用的 Python 3（两侧回归与审计脚本都要它）\n' >&2
  exit 2
fi
if ! "$PY" -c "import yaml" >/dev/null 2>&1; then
  printf '❌ 前置：%s 缺 PyYAML（Egern 侧脚本依赖） ⇒ %s -m pip install pyyaml\n' "$PY" "$PY" >&2
  exit 2
fi

LOG="${TMPDIR:-/tmp}/self-configuration-all-$$"
mkdir -p "$LOG" || { printf '❌ 前置：建不了临时目录 %s\n' "$LOG" >&2; exit 2; }
trap 'rm -rf "$LOG"' EXIT INT TERM

T0=$SECONDS
final=0
reds=0
envs=0
n=0

# item <名称> <命令...>
item() {
  local name="$1"; shift
  n=$((n + 1))
  local log="$LOG/$n" t0=$SECONDS rc
  if "$@" >"$log" 2>&1; then rc=0; else rc=$?; fi
  local dt=$((SECONDS - t0))
  local total
  total="$(grep -o 'TOTAL: [0-9]* passed, [0-9]* failed' "$log" | tail -1)"
  case "$rc" in
    0)
      printf '   %-2s ✅ %-30s · %s · %ss\n' "$n" "$name" "${total:-通过}" "$dt"
      ;;
    2)
      envs=$((envs + 1)); [ "$final" = "0" ] && final=2
      printf '   %-2s ❌ %-30s · 前置/环境不达标（退出码 2）\n' "$n" "$name"
      tail -6 "$log" | sed 's/^/        /'
      ;;
    *)
      reds=$((reds + 1)); [ "$final" = "0" ] && final=1
      printf '   %-2s ❌ %-30s · %s · %ss\n' "$n" "$name" "${total:-判负}" "$dt"
      tail -14 "$log" | sed 's/^/        /'
      ;;
  esac
}

printf '仓库根：%s\n' "$ROOT"
printf '当前推荐版：%s   联网：%s\n\n' "${CURRENT:-routing_v3.2}" "$([ "$OFFLINE" = "1" ] && echo 跳过 || echo 开)"

item "Surge 回归（六阶段）"  bash skill/tests/surge/run.sh
item "Egern 回归（两阶段）"  bash skill/tests/egern/run.sh
item "两版形态去注释对拍"    "$PY" skill/tests/check_min_pair.py
item "换设备可移植性"        "$PY" skill/tests/check_portability.py

printf '\n'
if [ -d "$ROOT/.git" ]; then
  printf '   ℹ️  未提交 %s 个文件 · HEAD=%s' \
    "$(git -C "$ROOT" status --porcelain | wc -l | tr -d ' ')" \
    "$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo '?')"
  # 与线上的关系：clone 出来的仓天然有上游，这里顺手报"改完有没有推上去"。
  # 刻意不配 remote、不写凭据 —— 那是各台机器自己的事，见 docs/注意事项.md。
  UP="$(git -C "$ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
  if [ -n "$UP" ]; then
    set -- $(git -C "$ROOT" rev-list --count --left-right "$UP...HEAD" 2>/dev/null || echo "0 0")
    printf ' · 上游 %s：落后 %s · 未推送 %s\n' "$UP" "${1:-0}" "${2:-0}"
  else
    printf ' · 上游 未配置（clone 后自动有；本仓不代管凭据）\n'
  fi

  # ── 闸门自检：本轮有没有动到「检查器自己」────────────────────────────
  # 见 AGENTS.md §2 第 5 条。这里**只报不判负** —— 越界与否由人裁决，
  # 但必须让人在下图腾一眼看见，而不是翻 diff 才发现。
  # 注意：不往子进程传 $ROOT —— 那是 bash 形式的 `/c/...`，Windows 原生 Python 不认。
  # 本脚本上面已经 `cd "$ROOT"`，Python 继承 cwd 即可。
  "$PY" - <<'PYEOF'
import os, subprocess

GATE = (".gitattributes", "skill/tests/all.sh", "skill/tests/check_portability.py",
        "skill/tests/check_min_pair.py", "skill/tests/bump_version.py",
        "skill/tests/surge/run.sh", "skill/tests/surge/architecture.sh",
        "skill/tests/surge/check_links.py", "skill/tests/egern/run.sh")

if not os.path.isdir(".git"):
    raise SystemExit                      # 非 git 环境（如打包后的归档）：这一栏跳过


def git(*a):
    # 首参必须是可执行文件名：`subprocess.run(["rev-parse", ...])` 会 FileNotFoundError。
    return subprocess.run(["git", *a], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def paths(out, status_form=False):
    """把 git status --porcelain / diff --name-only 的输出还原成路径。"""
    res = []
    for line in out.splitlines():
        if not line.strip():
            continue
        if status_form and len(line) > 3 and line[2] == " ":
            line = line[3:]                            # 剥掉 XY<空格> 前缀
        line = line.split(" -> ")[-1].strip().strip('"')   # 重命名取新名
        if line:
            res.append(line)
    return res


up = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").strip()
if up:
    src, changed = "未推送的提交", git("diff", "--name-only", "%s...HEAD" % up)
else:
    # 没有上游时退一步：至少看最近一次提交（agent 常常先 commit 再跑检查）
    src, changed = "最近一次提交", git("diff", "--name-only", "HEAD^", "HEAD")

hits, seen = [], set()
for tag, lst in (("未提交", paths(git("status", "--porcelain"), True)),
                 (src, paths(changed))):
    for p in lst:
        if p in GATE and p not in seen:
            seen.add(p)
            hits.append((tag, p))

if hits:
    print("\n   ⚠️  闸门被改动 %d 处 —— AGENTS.md §2 第 5 条：改前先请示维护者，"
          "并附「不改会漏掉什么」的反例" % len(hits))
    for tag, p in hits:
        print("      · %-12s %s" % (tag, p))
    print("      例外：`CURRENT=` 那一行由 skill/tests/bump_version.py 改写，不算越界。")
else:
    print("\n   ✅  闸门未被动过（冻结 %d 个文件 · 名单见 AGENTS.md §2 第 5 条）" % len(GATE))
PYEOF
fi

DT=$((SECONDS - T0))
if [ "$final" = "0" ]; then
  printf 'ALL GREEN · %s 项检查通过 · %ss\n' "$n" "$DT"
else
  printf '❌ %s 项判负 / %s 项环境不达标 · %ss\n' "$reds" "$envs" "$DT"
fi
exit "$final"
