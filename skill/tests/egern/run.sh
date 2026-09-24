#!/usr/bin/env bash
# Egern 审计脚本回归测试 —— 两阶段，退出码非 0 即失败。
#
#   阶段 1 · DNS 面 fixture 回归
#     把 skill/tests/ 的 5 个 fixture 同时喂给 check_egern_dns.py 与 audit_dns_forward.py
#     （5 × 2 = 10 个断言）。
#
#   阶段 2 · 地区组 filter 同步回归
#     对仓库里**全部** profiles/*.yaml 跑 audit_region_filters.py，期望全部 rc=0。
#     ⚠️ 为什么不并进阶段 1：阶段 1 的 fixture 是 DNS 面的合成配置，**没有地区组**，
#        喂给 audit_region_filters.py 只会走"无需校验"分支 —— 看着绿，其实什么都没测。
#        这个脚本的断言对象必须是**真实 profile**。
#
# 为什么需要阶段 1（2026-09-20 二次核查报告 P1 #3）：
#   此前 fixture 只手工喂给 check_egern_dns.py，audit_dns_forward.py 那一半从没跑过，
#   于是 `ok_route.yaml` 差一点就能抓到 `audit_dns_forward.py` 的 UnboundLocalError 崩溃。
#   ⇒ 把「N 个 fixture × 2 个脚本」串成一条命令，退出码非 0 即失败。
#
# 用法：
#   bash skill/tests/egern/run.sh                       # 用 PATH 里的 python
#   PY=/path/to/python bash skill/tests/egern/run.sh    # 指定解释器
#   在仓库根目录执行（脚本会自己定位 skill/tests/ 的上级）。

set -u
# Windows 中文环境默认 GBK(cp936)：内联 python 一 print emoji 就崩成退出码 1，
# 而回归里"期望判负"的 fixture 期望的恰恰也是 1 ⇒ 会假绿。统一按 UTF-8 输出。
export PYTHONIOENCODING=utf-8

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$(cd "$HERE/../../scripts/egern" && pwd)"
PROFILES="$(cd "$HERE/../../../egern/profiles" 2>/dev/null && pwd || true)"
PY="${PY:-python3}"
# 当前版词干：与 Surge 侧 run.sh 同一个固定名（阶段 2 的 --strict 名单由它派生）。
# 「哪一版」由 egern/profiles/routing.yaml 的头注说了算，两侧版本一致性由 check_min_pair.py 判。
export CURRENT="routing"

# ⚠️ Git Bash / MSYS 下 `pwd` 返回 `/c/Users/...` 这种 MSYS 风格路径，
#    Windows 版 Python 打不开（会报 `can't open file 'C:\\c\\Users\\...'`）。
#    用 cygpath -w 转成 `C:\Users\...`；非 MSYS 环境（cygpath 不存在）保持原样。
if command -v cygpath >/dev/null 2>&1; then
  HERE_W="$(cygpath -w "$HERE")"
  SCRIPTS_W="$(cygpath -w "$SCRIPTS")"
  PROFILES_W="$([ -n "$PROFILES" ] && cygpath -w "$PROFILES" || printf '')"
else
  HERE_W="$HERE"
  SCRIPTS_W="$SCRIPTS"
  PROFILES_W="$PROFILES"
fi

# ⚠️ 拼接路径一律用 `/`，不要用 `\\`。
#    cygpath -w 给的是 `C:\Users\...`（反斜杠），若再拼 `\\check.py` 会得到
#    `C:\Users\...\scripts\check.py` —— 在 MSYS 下侥幸能跑；但在 Linux 上
#    `SCRIPTS_W` 是 `/home/runner/...`，拼出来变成 `/home/runner/.../scripts\check.py`，
#    反斜杠成了文件名的一部分 ⇒ file not found。（本仓库不挂 CI，只影响将来若在本地 Linux 上跑。）
#    Windows 的路径 API 同时接受 `/` 和 `\`，所以统一用 `/` 两边都安全。

# ── 前置检查：解释器与依赖必须在位 ──────────────────────────────────────────
# ⚠️ 为什么必须有这一段：解释器坏掉（不存在 / 缺 pyyaml）时，脚本会以**退出码 1**
#    结束 —— 而 `bad_foreign` / `bad_hostname` 这两个「期望判负」的 fixture 期望的
#    恰恰也是 1。于是它们会**假绿**，整轮输出变成 `2 passed, 3 failed`，读起来像
#    "部分断言没过"，实际是"环境根本没跑起来"。审计器的故障绝不能被计成"判负通过"。
#    退出码 2 专用于此，与「断言失败 = 1」区分开。
if ! "$PY" -c "import yaml" >/dev/null 2>&1; then
  printf '\n❌ 前置检查失败：解释器不可用或缺依赖。\n' >&2
  printf '   PY=%s\n' "$PY" >&2
  printf '   请安装依赖（pip install pyyaml），或用 PY=<python 路径> 指定解释器后重跑。\n' >&2
  printf '   （若跳过此检查，脚本会以退出码 1 结束，bad_* 会被误判为通过。）\n' >&2
  exit 2
fi
for _s in check_egern_dns.py audit_dns_forward.py audit_region_filters.py; do
  if [ ! -f "$SCRIPTS/$_s" ]; then
    printf '\n❌ 前置检查失败：缺少脚本 %s/%s\n' "$SCRIPTS" "$_s" >&2
    exit 2
  fi
done
# 阶段 2 的断言对象是仓库里的真实 profile —— 目录不在就没得测，必须报错而不是静默跳过。
if [ -z "$PROFILES" ] || [ ! -d "$PROFILES" ]; then
  printf '\n❌ 前置检查失败：找不到 profiles/ 目录（期望在 <root>/egern/profiles）\n' "$HERE" >&2
  printf '   阶段 2 需要它来跑 audit_region_filters.py。\n' >&2
  exit 2
fi
# ⚠️ 固定名不在 ⇒ 阶段 2 的 --strict 名单一条都套不上，全部按「历史存档版」只查非正值 ⇒ 假绿。
if [ ! -f "$PROFILES/$CURRENT.yaml" ]; then
  printf '\n❌ 前置检查失败：%s 不存在（固定名是永久订阅地址，不能被改名或挪走）\n' "$CURRENT.yaml" >&2
  exit 2
fi

# 断言表：fixture 期望退出码（check_egern_dns / audit_dns_forward）
#   ok_route      : 判据 A 生效 -> 两脚本都应通过（0 / 0）
#   bad_foreign   : 兜底全境外 IP -> 两脚本都应判负（1 / 1）
#   bad_hostname  : 兜底含主机名   -> 两脚本都应判负（1 / 1）
#   ipv6_only     : 端点仅 IPv6 国内解析器 -> 两脚本必须**同结论**且都通过（0 / 0）
#                   （这是 ep_ip IPv6 截断 bug 的守卫：修之前是 0 / 1）
#   scheme_case   : 端点 scheme 写成大写（HTTPS:// / TLS://）-> 结论必须与 ok_route
#                   完全一致（0 / 0）。（这是 hostpart scheme 白名单回归的守卫：
#                   修之前是 1 / 1 —— scheme 拼法不该有能力改变审计结论。）
CASES="
ok_route.yaml:0:0
bad_foreign.yaml:1:1
bad_hostname.yaml:1:1
ipv6_only.yaml:0:0
scheme_case.yaml:0:0
"

pass=0; fail=0
printf '%s\n' "阶段 1 · DNS 面 fixture 回归"
printf '%-22s %-18s %-20s %s\n' "FIXTURE" "check_egern_dns" "audit_dns_forward" "RESULT"
printf '%s\n' "--------------------------------------------------------------------------------"

for case in $CASES; do
  f="${case%%:*}"; rest="${case#*:}"
  exp_chk="${rest%%:*}"; exp_adf="${rest##*:}"
  path="$HERE/$f"
  path_w="$HERE_W/$f"
  [ -f "$path" ] || { printf '%-22s %s\n' "$f" "❌ fixture 缺失（两个判据都测不了）"; fail=$((fail+2)); continue; }

  "$PY" "$SCRIPTS_W/check_egern_dns.py" "$path_w" >/dev/null 2>&1; got_chk=$?
  "$PY" "$SCRIPTS_W/audit_dns_forward.py" "$path_w" >/dev/null 2>&1; got_adf=$?

  # ⚠️ 计数口径：**按脚本对账计数，不按表格行**。一行 fixture 同时校两个脚本的期望退出码
  #    （check_egern_dns 与 audit_dns_forward 是两个独立判据，各算一条断言），
  #    所以 5 行 = 10 条断言 —— 与 README / docs 里「阶段 1 · 10 断言」的口径对齐。
  #    早先这里每行只 +1，runner 报 5、文档写 10，两边都对不上号。
  n_ok=0
  if [ "$got_chk" = "$exp_chk" ]; then n_ok=$((n_ok+1)); fi
  if [ "$got_adf" = "$exp_adf" ]; then n_ok=$((n_ok+1)); fi
  if [ "$n_ok" = 2 ]; then
    res="✅ OK"; pass=$((pass+2))
  else
    res="❌ 期望 ${exp_chk}/${exp_adf}（${n_ok}/2 对账成立）"; fail=$((fail + 2 - n_ok))
  fi
  printf '%-22s %-18s %-20s %s\n' "$f" "exit=$got_chk" "exit=$got_adf" "$res"
done

printf '%s\n' "--------------------------------------------------------------------------------"
printf 'result: %d passed, %d failed\n' "$pass" "$fail"

# ── 阶段 2：地区组 filter 与 Other Regions 负向断言的「两份拷贝」同步 ────────────
# 断言对象是**仓库里的真实 profile**（不是上面的合成 fixture）。
# 期望全部 rc=0：
#   · routing_v1 / routing_v2 / routing_v2.1 / routing_v2.2 / routing_v2.3 / routing_v2.4 / routing_v3 / routing_v3.1 / routing_v3.2 → 6 个地区组的关键词必须逐字出现在负向断言里
#   · lazy 没有该结构 → 脚本打印"无需校验"并 rc=0
# rc=1 = 有地区关键词漏同步（两组不再互斥）；rc=2 = 解析失败 / 用法错误。两者都算失败。
#
# 同一轮循环里再跑 audit_ruleset_refresh.py（离线）：当前推荐版与懒人版（含 .min）
# 要求钉到约定值 604800，历史存档版只查非正值。
printf '\n'
printf '%s\n' "阶段 2 · 地区组 filter 同步 + 规则集刷新参数（跑全部 profiles/*.yaml）"
printf '%-26s %-20s %s\n' "PROFILE" "audit_region_filters" "RESULT"
printf '%s\n' "--------------------------------------------------------------------------------"

pass2=0; fail2=0
for _p in "$PROFILES"/*.yaml; do
  [ -f "$_p" ] || continue
  _name="$(basename "$_p")"
  "$PY" "$SCRIPTS_W/audit_region_filters.py" "$PROFILES_W/$_name" >/dev/null 2>&1; _rc=$?
  if [ "$_rc" = "0" ]; then
    _res="✅ OK"; pass2=$((pass2+1))
  else
    # 单独重跑一次把原因打出来 —— 这里只保留 rc 的话，失败时看不出是漏同步还是解析错。
    case "$_rc" in
      1) _why="地区关键词漏同步";;
      2) _why="解析失败 / 用法错误";;
      *) _why="未知退出码";;
    esac
    _res="❌ ${_why}"; fail2=$((fail2+1))
    printf '\n---- %s 的详细输出 ----\n' "$_name"
    "$PY" "$SCRIPTS_W/audit_region_filters.py" "$PROFILES_W/$_name" 2>&1 | sed 's/^/    /'
    printf '%s\n' "------------------------"
  fi
  printf '%-26s %-20s %s\n' "$_name" "exit=$_rc" "$_res"
  # 规则集刷新参数（离线判定）：当前推荐版与懒人版要求钉到约定值；
  # 历史存档版（`routing_v1` ~ `routing_v2.3` 本就没写这个字段）只查非正值。
  case "$_name" in
    lazy.yaml|lazy.min.yaml|$CURRENT.yaml|$CURRENT.min.yaml) _rf_flag="--strict";; *) _rf_flag="";;
  esac
  "$PY" "$SCRIPTS_W/audit_ruleset_refresh.py" "$PROFILES_W/$_name" $_rf_flag --quiet >/dev/null 2>&1
  _rrc=$?
  if [ "$_rrc" = "0" ]; then
    _rres="✅ OK"; pass2=$((pass2+1))
  else
    _rres="❌ 刷新参数"; fail2=$((fail2+1))
    printf '\n---- %s 的刷新参数输出 ----\n' "$_name"
    "$PY" "$SCRIPTS_W/audit_ruleset_refresh.py" "$PROFILES_W/$_name" $_rf_flag 2>&1 | sed 's/^/    /'
    printf '%s\n' "------------------------"
  fi
  printf '%-26s %-20s %s\n' "$_name (refresh)" "exit=$_rrc" "$_rres"
done

printf '%s\n' "--------------------------------------------------------------------------------"
printf 'result: %d passed, %d failed\n' "$pass2" "$fail2"

# 两阶段合计的总数（与 Surge 侧 run.sh 的 TOTAL 同格式）：
#   阶段 1 = fixture 数 × 2 个脚本，阶段 2 = profile 数 × 2 个脚本。
#   闸门工具直接抓这一行，省得再去两处 result 手工相加。
printf 'TOTAL: %d passed, %d failed\n' "$((pass + pass2))" "$((fail + fail2))"

[ $((fail + fail2)) = "0" ] || exit 1
exit 0
