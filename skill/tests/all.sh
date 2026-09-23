#!/usr/bin/env bash
# 一条命令跑完本仓**全部本地检查**：改完配置或文档，只需要记这一条。
#
# 为什么要有这个入口：
#   本仓刻意不挂 CI（理由见 docs/注意事项.md），可检查项并不止一处 ——
#   两套内核的回归（Surge 六阶段里已含架构不变量、全仓 markdown 链接与锚点、
#   全部 profile 的刷新参数）+ 两版形态对拍。分开跑要记三条命令、读三段输出，
#   串起来一条就能判定"这次改动有没有把什么弄坏"。
#
# 刻意不含的两项（它们不属于日常自检）：
#   · 与两个前身仓逐字节对账 —— 需要那两个仓的克隆在旁边，属合并工程的一次性验收；
#   · "旧仓是否被改动"的红线检查 —— 同上，且只对维护者本机有意义。
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
printf '当前推荐版：%s   联网：%s\n\n' "${CURRENT:-routing_v3.1}" "$([ "$OFFLINE" = "1" ] && echo 跳过 || echo 开)"

item "Surge 回归（六阶段）"  bash skill/tests/surge/run.sh
item "Egern 回归（两阶段）"  bash skill/tests/egern/run.sh
item "两版形态去注释对拍"    "$PY" skill/tests/check_min_pair.py

printf '\n'
if [ -d "$ROOT/.git" ]; then
  printf '   ℹ️  未提交 %s 个文件 · HEAD=%s\n' \
    "$(git -C "$ROOT" status --porcelain | wc -l | tr -d ' ')" \
    "$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo '?')"
fi

DT=$((SECONDS - T0))
if [ "$final" = "0" ]; then
  printf 'ALL GREEN · %s 项检查通过 · %ss\n' "$n" "$DT"
else
  printf '❌ %s 项判负 / %s 项环境不达标 · %ss\n' "$reds" "$envs" "$DT"
fi
exit "$final"
