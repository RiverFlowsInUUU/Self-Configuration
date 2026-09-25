#!/usr/bin/env bash
# 一条命令跑完本仓**全部本地检查**：改完配置或文档，只需要记这一条。
#
# 为什么要有这个入口：
#   本仓刻意不挂 CI（理由见 docs/注意事项.md），可检查项并不止一处 ——
#   两套内核的回归（Surge 六阶段里已含架构不变量、全仓 markdown 链接与锚点、
#   全部 profile 的刷新参数）+ 两版形态对拍 + 换设备可移植性 + 文档读数与实测对拍
#   + 工具自检（三套自带回归、全部被跟踪 .py 可编译、顶层死绑定与「用了没绑」，见 check_tools.py 头注：
#     生成器与那批从不被闸执行的脚本都属于"还没坏"，不是"有防护" ——
#     闸外脚本的名单由 check_tools.py 现算并打印，此处不写死个数（写死必漂））
#   + 回归断言数与本轮实测 TOTAL 对拍（见 check_assert_counts.py 头注：文档写死的
#     「19 断言 / 18 断言」此前没有任何检查会因为 runner 加了断言而报错）。
#   分开跑要记七条命令、读七段输出，串起来一条就能判定"这次改动有没有把什么弄坏"。
#
# 本仓完全独立：这一条命令跑的所有检查**只看本仓库的文件**，
# 不需要任何其他仓库在旁边，也不依赖本机路径、盘符、用户名。仓库根由本脚本自身位置反推
# （$BASH_SOURCE → skill/tests 的上两级），所以 clone 到哪里、叫什么名字都一样能跑。
#
# 用法：
#   bash skill/tests/all.sh                        # 全跑（含联网审计）
#   bash skill/tests/all.sh --offline              # 跳过联网项（离线机器 / 无外网时）
#   bash skill/tests/all.sh --landed               # 提交并推送**之后**复核这批是否落地
#
# 检查对象恒为 profiles/ 顶层的固定名四件（routing / lazy 各两形态）。存档版在
# profiles/config_old/ 里，**不参与任何检查**（2026-09-24 定：丢掉历史包袱、加快速度）；
# 要复核旧版本，带着路径直接调对应脚本。
#
# 退出码：0 判据全过 · 1 有判负 · 2 前置环境不达标
#   （2 = 缺 Python 或缺 PyYAML，或固定名 profile 不存在，或 --landed 的前置不成立 —— 后者刻意不静默）
#
# ── 「判据过了」与「这批落地了」是两件事，本脚本用两档分开判 ──────────────
# 为什么要分开：AGENTS.md §1 的顺序是 跑闸 → commit → push，而"未提交 / 落后 / 未推送
# 全 0"只有 push 之后才可达 ⇒ 把三数塞进默认档会让它**永远红**，淹掉真正的判据失败。
# 所以：默认档只**报**三数（退出码不因它变），`--landed` 才把三数**判负**（复用退出码 1）。
# `--landed` 是**按批开关**，不是新默认：维护者说"先改本地、不提交不推送"的那批，
# 按设计就该不跑它（跑了必红，那是设计而不是故障）。
# ⚠️ 两档都**不判**"有没有把垃圾文件扫进提交" —— 那由提交前点名 stage 挡，不在本脚本覆盖面内。
# 组合口径：`--offline --landed` 在参数解析处就 exit 2（离线时 Surge 侧少跑联网阶段，
# 拿它宣布"已落地"就是假绿），刻意不等跑完 8 秒才报。

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT" || exit 2

# 中文 Windows 的控制台与管道默认 GBK：脚本 print emoji 会崩成退出码 1，
# 与"期望判负"的用例撞码 ⇒ 假绿。另：不许往工作树里掉 .pyc。
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1

OFFLINE=0
LANDED=0
for a in "$@"; do
  case "$a" in
    --offline) OFFLINE=1 ;;
    --landed)  LANDED=1 ;;
    # 未知参数不静默吞掉：打错一个字母就退化成默认档，正是本仓最忌讳的"看着跑过了"。
    *) printf '❌ 未知参数：%s（本脚本只认 --offline / --landed）\n' "$a" >&2; exit 2 ;;
  esac
done
if [ "$OFFLINE" = "1" ] && [ "$LANDED" = "1" ]; then
  printf '❌ --landed 不认 --offline：离线时 Surge 侧少跑联网阶段 ⇒ 用它宣布"已落地"是假绿。\n' >&2
  printf '   要复核落地就带联网跑：bash skill/tests/all.sh --landed\n' >&2
  exit 2
fi
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
  # 把通过数交给调用方：第 7 项拿这六个数去对文档里写死的断言数（check_assert_counts.py）。
  # 没有 TOTAL 行时置空 —— 第 7 项据此判"前置不达标"，而不是拿一个缺失值当 0 去对拍。
  if [ -n "$total" ]; then
    LAST_NUM="${total#TOTAL: }"; LAST_NUM="${LAST_NUM%% passed*}"
  else
    LAST_NUM=""
  fi
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
      # 先点名失败行，再兜底末尾若干行：子日志是六阶段 / 两阶段的长输出，失败在阶段 1 时
      # `tail` 只剩阶段 6 的汇总 ⇒ 判负原因看不见，只能再单跑一次那个 runner（实测确认：
      # 把 Surge 阶段 1 的期望码改错，`all.sh` 摘要里那条失败出现 0 次、单跑 runner 才看得见）。
      local marks
      marks="$(grep -nE '❌|Traceback|FAIL|[1-9][0-9]* failed' "$log" | head -14)"
      if [ -n "$marks" ]; then
        printf '%s\n' "$marks" | sed 's/^/        /'
      else
        tail -14 "$log" | sed 's/^/        /'
      fi
      ;;
  esac
}

printf '仓库根：%s\n' "$ROOT"
# 「当前是哪一版」只剩一个来源：profile 头注 `#! version=routing_vX.Y`（形状由 check_min_pair.py 判）。
printf '订阅地址固定名 · 当前版：%s   联网：%s   档位：%s\n\n' \
  "$(sed -n '1s/^#! version=//p' surge/profiles/routing.conf 2>/dev/null)" \
  "$([ "$OFFLINE" = "1" ] && echo 跳过 || echo 开)" \
  "$([ "$LANDED" = "1" ] && echo '落地复核（三数计入判负）' || echo '默认（三数只报不判）')"

# MEASURED：本轮前 6 项的通过数，按 key 交给第 7 项去和文档里写死的断言数对拍。
# key 就写在各条命令旁边（不另立一张位置表）—— 位置表会跟着调顺序漂，键不会。
MEASURED=()
item "Surge 回归（六阶段）"  bash skill/tests/surge/run.sh;      MEASURED+=("surge=$LAST_NUM")
item "Egern 回归（两阶段）"  bash skill/tests/egern/run.sh;      MEASURED+=("egern=$LAST_NUM")
item "两版形态去注释对拍"    "$PY" skill/tests/check_min_pair.py;  MEASURED+=("min_pair=$LAST_NUM")
item "换设备可移植性"        "$PY" skill/tests/check_portability.py; MEASURED+=("portability=$LAST_NUM")
item "文档读数与实测对拍"    "$PY" skill/tests/check_doc_readings.py; MEASURED+=("doc_readings=$LAST_NUM")
item "工具自检 + 覆盖矩阵"  "$PY" skill/tests/check_tools.py;  MEASURED+=("tools=$LAST_NUM")

# 第 7 项：文档写死的断言数 ↔ 上面这六个实测 TOTAL。它自己不跑测试（判据的判据会递归）。
# ⚠️ 离线档**不调它**：离线时 Surge 侧少跑 4 条联网断言（实测 15），与文档的联网口径是两个数
#    ⇒ 比了必假红；而"跳过"也不能算成一条通过（那正是本仓忌的假绿），所以只出声、不进项数。
if [ "$OFFLINE" = "0" ]; then
item "断言数与文档对拍"      "$PY" skill/tests/check_assert_counts.py "${MEASURED[@]}"
else
  printf '   %-2s ↷ %-30s · 跳过：离线档 Surge 侧实测 %s，与文档写死的联网口径不是一个数\n' \
    "$((n + 1))" "断言数与文档对拍" "${MEASURED[0]#surge=}"
fi

printf '\n'
# 「落地状态」三个数：默认档只报（下面末行据它换措辞），--landed 档才判负。
DIRTY=0; BEHIND=0; UNPUSHED=0; HAVE_GIT=0; HAVE_UP=0; UP=""
if [ -d "$ROOT/.git" ]; then
  HAVE_GIT=1
  DIRTY="$(git -C "$ROOT" status --porcelain | wc -l | tr -d ' ')"
  # 与线上的关系：clone 出来的仓天然有上游，这里顺手报"改完有没有推上去"。
  # 刻意不配 remote、不写凭据 —— 那是各台机器自己的事，见 docs/注意事项.md。
  UP="$(git -C "$ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
  printf '   ℹ️  未提交 %s 个文件 · HEAD=%s' "$DIRTY" \
    "$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo '?')"
  if [ -n "$UP" ]; then
    HAVE_UP=1
    set -- $(git -C "$ROOT" rev-list --count --left-right "$UP...HEAD" 2>/dev/null || echo "0 0")
    BEHIND="${1:-0}"; UNPUSHED="${2:-0}"
    printf ' · 上游 %s：落后 %s · 未推送 %s\n' "$UP" "$BEHIND" "$UNPUSHED"
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
        "skill/tests/check_doc_readings.py",
        "skill/tests/surge/run.sh", "skill/tests/surge/architecture.sh",
        "skill/tests/surge/check_links.py", "skill/tests/egern/run.sh",
        "skill/tests/check_tools.py", "skill/tests/check_assert_counts.py")

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
else:
    print("\n   ✅  闸门未被动过（冻结 %d 个文件 · 名单见 AGENTS.md §2 第 5 条）" % len(GATE))
PYEOF
fi

# --landed 的前置：没 git、没上游都判 2 —— 那种环境下"三数全 0"根本无从判定，
# 让它退化成 0 就等于"没跑成却宣布落地"，与本仓「没跑成不等于跑绿」同一条罪。
if [ "$LANDED" = "1" ] && [ "$final" = "0" ]; then
  if [ "$HAVE_GIT" != "1" ]; then
    printf '❌ --landed 需要 git 仓库（当前目录下没有 .git）⇒ 无法判定落地状态\n' >&2
    exit 2
  fi
  if [ "$HAVE_UP" != "1" ]; then
    printf '❌ --landed 需要上游 %s（现在未配置）⇒ "落后 / 未推送" 无从判起\n' "$UP" >&2
    printf '   clone 出来的仓天然有上游；本仓不代管 remote 与凭据，见 AGENTS.md §4。\n' >&2
    exit 2
  fi
fi

LANDED_OK=0
if [ "$HAVE_GIT" = "1" ] && [ "$DIRTY" = "0" ] && [ "$BEHIND" = "0" ] && [ "$UNPUSHED" = "0" ]; then
  LANDED_OK=1
fi

DT=$((SECONDS - T0))
if [ "$final" != "0" ]; then
  printf '❌ %s 项判负 / %s 项环境不达标 · %ss\n' "$reds" "$envs" "$DT"
elif [ "$LANDED" = "1" ]; then
  if [ "$LANDED_OK" = "1" ]; then
    printf '✅ 已落地 · %s 项检查通过 · 未提交 0 · 落后 0 · 未推送 0 · %ss\n' "$n" "$DT"
  else
    printf '❌ 判据全过但未落地（未提交 %s · 落后 %s · 未推送 %s）· %ss\n' \
      "$DIRTY" "$BEHIND" "$UNPUSHED" "$DT"
    printf '   ⇒ 这批还没走完 §1：点名 stage 提交、push，再回来跑 `bash skill/tests/all.sh --landed`。\n' >&2
    final=1
  fi
elif [ "$HAVE_GIT" = "1" ] && [ "$LANDED_OK" != "1" ]; then
  # 默认档：状态没落地就不说 ALL GREEN —— 那三个字在 §1 里被借去描述"三数全 0"，
  # 一个词背两个意思就是这次要治的误读面。退出码**不变**，中途跑闸不该变红灯。
  printf '✅ 判据全过 · %s 项 · %ss —— 但状态未落地（未提交 %s · 落后 %s · 未推送 %s）\n' \
    "$n" "$DT" "$DIRTY" "$BEHIND" "$UNPUSHED"
  printf '   这还不算完成：提交、推送后跑 `bash skill/tests/all.sh --landed` 复核这批。\n'
else
  printf 'ALL GREEN · %s 项检查通过 · %ss\n' "$n" "$DT"
fi
exit "$final"
