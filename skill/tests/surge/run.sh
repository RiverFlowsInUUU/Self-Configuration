#!/usr/bin/env bash
# Surge 审计脚本回归测试 —— 六阶段，退出码非 0 即失败。
#
#   阶段 1 · DNS 面 fixture 回归
#     把 skill/tests/ 的 3 个 fixture 喂给 check_surge_dns.py（3 个断言）。
#     里面有两个**期望判负**的坏配置 —— 它们的存在是为了证明"审计器真的有判别力"，
#     而不是恒返回 0。
#
#   阶段 2 · 真实 profile 回归
#     对仓库里**全部** profiles/*.conf 跑 check_surge_dns.py，期望全部通过。
#     ⚠️ 为什么不并进阶段 1：阶段 1 的 fixture 是**合成**配置（不含完整 DNS 段、
#        不引用远程规则集），喂给 architecture.sh 会因为"缺少 DNS 键"而假红；
#        而 architecture.sh 的断言对象必须是**真实 profile**（它守的是占位符纪律）。
#
#   阶段 3 · 架构不变量（占位符纪律 / 两份形态 DNS 段一致性 / 规则顺序铁律）
#   阶段 4 · 规则集内容 + 分流覆盖（需联网，SKIP_NET=1 可跳过）
#   阶段 5 · 地区组正则一致性（fixtures/bad_region_filter.conf 期望判负）
#   阶段 6 · markdown 相对链接与锚点
#
# 为什么必须有"解释器与依赖"的前置检查：
#   解释器坏掉时脚本会以**退出码 1** 结束 —— 而 bad_* 期望的恰恰也是 1。
#   于是它们会**假绿**，整轮输出读起来像"部分断言没过"，实际是"环境根本没跑起来"。
#   审计器的故障绝不能被计成"判负通过"。退出码 2 专用于此。
#
# 用法：
#   bash skill/tests/surge/run.sh                        # 用 PATH 里的 python
#   PY=/path/to/python bash skill/tests/surge/run.sh     # 指定解释器
#   SKIP_NET=1 bash skill/tests/surge/run.sh             # 跳过需要联网的阶段 4
#
# 订阅地址固定化（2026-09-24）之后：当前版恒为 `routing.conf` / `routing.min.conf`，
# 「哪一版」只看 profile 头注 `#! version=routing_vX.Y`，由 skill/tests/check_min_pair.py 判。
# 要复核存档版：带着路径直接调对应脚本（见 docs/注意事项.md），runner 不再接受版本覆盖。

set -u
# Windows 中文环境默认 GBK(cp936)：内联 python 一 print emoji 就崩成退出码 1，
# 而回归里"期望判负"的 fixture 期望的恰恰也是 1 ⇒ 会假绿。统一按 UTF-8 输出。
export PYTHONIOENCODING=utf-8

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$(cd "$HERE/../../scripts/surge" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
PROFILES="$ROOT/surge/profiles"
PY="${PY:-python3}"

# ── 当前版词干：固定名，不随版本变 ──────────────────────────────────────────
# 阶段 2 的 --strict 名单、阶段 4、阶段 5 仍由它派生，但它恒等于 routing。
# 留这一行只为把文件名集中一处；赋值不带 `:-` ⇒ **环境变量覆盖不进来**（从前那种
# `CURRENT=routing_v3` 指向存档版的用法已作废，存档版根本不在检查路径上）。
export CURRENT="routing"

# ⚠️ Git Bash / MSYS 下 `pwd` 返回 `/c/Users/...`，Windows 版 Python 打不开
#    （会报 `can't open file 'C:\\c\\Users\\...'`）。用 cygpath -w 转换；
#    非 MSYS 环境（cygpath 不存在）保持原样。
if command -v cygpath >/dev/null 2>&1; then
  HERE_W="$(cygpath -w "$HERE")"
  SCRIPTS_W="$(cygpath -w "$SCRIPTS")"
  ROOT_W="$(cygpath -w "$ROOT")"
  PROFILES_W="$(cygpath -w "$PROFILES")"
else
  HERE_W="$HERE"; SCRIPTS_W="$SCRIPTS"; ROOT_W="$ROOT"; PROFILES_W="$PROFILES"
fi

# ⚠️ 拼接路径一律用 `/`，不要用 `\\` —— cygpath -w 给的是 `C:\Users\...`（反斜杠），
#    再拼 `\\check.py` 在 Linux 上会把反斜杠变成文件名的一部分 ⇒ file not found。

# ── 前置检查 ────────────────────────────────────────────────────────────────
if ! "$PY" -c "import sys" >/dev/null 2>&1; then
  printf '\n❌ 前置检查失败：解释器不可用。PY=%s\n' "$PY" >&2
  exit 2
fi
for _s in check_surge_dns.py audit_ruleset_content.py audit_routing_coverage.py \
          audit_region_filters.py _surge_common.py; do
  if [ ! -f "$SCRIPTS/$_s" ]; then
    printf '\n❌ 前置检查失败：缺少脚本 %s/%s\n' "$SCRIPTS" "$_s" >&2
    exit 2
  fi
done
if [ -z "$PROFILES" ] || [ ! -d "$PROFILES" ]; then
  printf '\n❌ 前置检查失败：找不到 profiles/ 目录\n' >&2
  exit 2
fi
# ⚠️ 固定名是「永久地址」，也是阶段 4 / 5 的入口：那两段对不存在的文件是 `continue` 跳过的，
#    文件一旦不见了会静默不跑 —— 输出照样全绿。缺文件必须在这里就炸。
if [ ! -f "$PROFILES/$CURRENT.conf" ]; then
  printf '\n❌ 前置检查失败：%s 在 %s 里不存在（订阅地址是永久承诺，这个名字不能被挪走或改名）\n' "$CURRENT.conf" "$PROFILES" >&2
  printf '   顶层现存：%s\n' "$(ls "$PROFILES" | tr '\n' ' ')" >&2
  printf '   ⇒ 存档版在 %s/config_old/ 里，不参与检查；要恢复当前版就从那里放回固定名。\n' "$PROFILES" >&2
  exit 2
fi

# 断言表：fixture 期望退出码
#   ok_minimal              : 该做对的都做对了 -> 0
#   bad_bootstrap           : dns-server 写 system / 端点用主机名 / follow=true -> 1
#   bad_order_and_policy    : 直连抢在 REJECT 前 / 拦截指向策略组 / IP 规则缺 no-resolve -> 1
CASES="
ok_minimal.conf:0
bad_bootstrap.conf:1
bad_order_and_policy.conf:1
"

pass=0; fail=0
printf '%s\n' "阶段 1 · DNS 面 fixture 回归（check_surge_dns.py）"
printf '%-30s %-14s %s\n' "FIXTURE" "EXIT" "RESULT"
printf '%s\n' "------------------------------------------------------------------"

for case in $CASES; do
  f="${case%%:*}"; exp="${case##*:}"
  [ -f "$HERE/$f" ] || { printf '%-30s %-14s %s\n' "$f" "—" "❌ fixture 缺失"; fail=$((fail+1)); continue; }
  "$PY" "$SCRIPTS_W/check_surge_dns.py" "$HERE_W/$f" >/dev/null 2>&1
  got=$?
  if [ "$got" = "$exp" ]; then
    res="✅ OK"; pass=$((pass+1))
  else
    res="❌ 期望 $exp"; fail=$((fail+1))
  fi
  printf '%-30s %-14s %s\n' "$f" "exit=$got" "$res"
done
printf '%s\n' "------------------------------------------------------------------"
printf 'result: %d passed, %d failed\n' "$pass" "$fail"

# ── 阶段 2：真实 profile ────────────────────────────────────────────────────
printf '\n%s\n' "阶段 2 · 真实 profile 回归（check_surge_dns.py + audit_ruleset_refresh.py）"
printf '%-30s %-14s %s\n' "PROFILE" "EXIT" "RESULT"
printf '%s\n' "------------------------------------------------------------------"

pass2=0; fail2=0
for _p in "$PROFILES"/*.conf; do
  [ -f "$_p" ] || continue
  _name="$(basename "$_p")"
  "$PY" "$SCRIPTS_W/check_surge_dns.py" "$PROFILES_W/$_name" >/dev/null 2>&1
  _rc=$?
  if [ "$_rc" = "0" ]; then
    _res="✅ OK"; pass2=$((pass2+1))
  else
    _res="❌ 有 high"; fail2=$((fail2+1))
    printf '\n---- %s 的详细输出 ----\n' "$_name"
    "$PY" "$SCRIPTS_W/check_surge_dns.py" "$PROFILES_W/$_name" 2>&1 | sed 's/^/    /'
    printf '%s\n' "------------------------"
  fi
  printf '%-30s %-14s %s\n' "$_name" "exit=$_rc" "$_res"
  # 规则集刷新参数（离线判定，不依赖网络）：当前推荐版与懒人版要求钉到约定值，
  # 历史存档版只查「非正值 = 关掉自动更新」这一条实质风险。
  case "$_name" in
    lazy.conf|lazy.min.conf|$CURRENT.conf|$CURRENT.min.conf) _rf_flag="--strict"; _rf_why="偏离约定值即失败";;  # ← 与 --expect 604800 同口径
    *) _rf_flag=""; _rf_why="仅非正值为失败";;
  esac
  "$PY" "$SCRIPTS_W/audit_ruleset_refresh.py" "$PROFILES_W/$_name" $_rf_flag --quiet >/dev/null 2>&1
  _rrc=$?
  if [ "$_rrc" = "0" ]; then
    _rres="✅ OK"; pass2=$((pass2+1))
  else
    _rres="❌ 刷新参数（$_rf_why）"; fail2=$((fail2+1))
    printf '\n---- %s 的刷新参数输出 ----\n' "$_name"
    "$PY" "$SCRIPTS_W/audit_ruleset_refresh.py" "$PROFILES_W/$_name" $_rf_flag 2>&1 | sed 's/^/    /'
    printf '%s\n' "------------------------"
  fi
  printf '%-30s %-14s %s\n' "$_name (refresh)" "exit=$_rrc" "$_rres"
done
printf '%s\n' "------------------------------------------------------------------"
printf 'result: %d passed, %d failed\n' "$pass2" "$fail2"

# ── 阶段 3：架构不变量（占位符纪律 / DNS 段一致性 / 规则顺序铁律）────────────
printf '\n%s\n' "阶段 3 · 架构不变量检查（architecture.sh）"
printf '%s\n' "------------------------------------------------------------------"
if PY="$PY" bash "$HERE/architecture.sh"; then
  pass3=1; fail3=0
else
  rc3=$?
  if [ "$rc3" = "2" ]; then
    printf '\n❌ 阶段 3 环境问题（退出码 2）\n'
  fi
  pass3=0; fail3=1
fi
printf '%s\n' "------------------------------------------------------------------"
printf 'result: %d passed, %d failed\n' "$pass3" "$fail3"

# ── 阶段 4（可选）：需要联网的规则集审计 ────────────────────────────────────
if [ "${SKIP_NET:-0}" != "1" ]; then
  printf '\n%s\n' "阶段 4 · 规则集内容 + 分流覆盖（需要联网，SKIP_NET=1 可跳过）"
  printf '%s\n' "------------------------------------------------------------------"
  pass4=0; fail4=0
  # ⚠️ 只对**带注释的完整版**跑联网审计：min 版是同一份配置去掉注释，
  #    跑两遍纯属浪费（且两者 DNS 段已被阶段 3 断言为逐字相同）。
  for _p in "$PROFILES"/lazy.conf "$PROFILES"/$CURRENT.conf; do
    [ -f "$_p" ] || continue
    _name="$(basename "$_p")"
    for _s in audit_ruleset_content.py audit_routing_coverage.py; do
      "$PY" "$SCRIPTS_W/$_s" "$PROFILES_W/$_name" >/dev/null 2>&1
      _rc=$?
      if [ "$_rc" = "0" ]; then
        _res="✅ OK"; pass4=$((pass4+1))
      else
        _res="❌ 退出码 $_rc"; fail4=$((fail4+1))
      fi
      printf '%-30s %-30s %s\n' "$_name" "$_s" "$_res"
    done
  done
  printf '%s\n' "------------------------------------------------------------------"
  printf 'result: %d passed, %d failed\n' "$pass4" "$fail4"
else
  pass4=0; fail4=0
  printf '\n⏭️  阶段 4 已跳过（SKIP_NET=1）\n'
fi

# ── 阶段 5：地区组正则一致性 ──────────────────────────────────────────────
# ⚠️ 这是**本项目最容易静默退化的地方**：$CURRENT.conf 里 6 个地区组的关键词
#    在 Other Regions 的负向断言里被逐字抄了一遍（Surge 的 filter 不支持引用变量，
#    消灭不掉这份拷贝）。漏同步的后果是"两个组的内容不再互斥"，
#    面板上看不出异常、Surge 也不报错 ⇒ 只能靠脚本守。
#
#    3 个断言：
#      a) 真实 $CURRENT.conf 通过（关键词同步完好）
#      b) 合成坏配置 fixtures/bad_region_filter.conf 判负（证明审计器有判别力）
#      c) 合成坏配置必须**只**因"漏关键词"判负（防它因别的原因假绿）
printf '\n%s\n' "阶段 5 · 地区组正则一致性（audit_region_filters.py）"
printf '%-30s %-14s %s\n' "TARGET" "EXIT" "RESULT"
printf '%s\n' "------------------------------------------------------------------"
pass5=0; fail5=0

"$PY" "$SCRIPTS_W/audit_region_filters.py" "$PROFILES_W/$CURRENT.conf" >/dev/null 2>&1
rc=$?
if [ "$rc" = "0" ]; then
  res="✅ OK"; pass5=$((pass5+1))
else
  res="❌ 退出码 $rc"; fail5=$((fail5+1))
  printf '\n---- %s 的详细输出 ----\n' "$CURRENT.conf"
  "$PY" "$SCRIPTS_W/audit_region_filters.py" "$PROFILES_W/$CURRENT.conf" 2>&1 | sed 's/^/    /'
  printf '%s\n' "------------------------"
fi
printf '%-30s %-14s %s\n' "$CURRENT.conf" "exit=$rc" "$res"

if [ -f "$HERE/fixtures/bad_region_filter.conf" ]; then
  # ⚠️ (c)：坏 fixture 必须**只**因"漏关键词"判负 —— 光看 rc==1 分不清"审到了漏关键词"
  #    与"因别的原因 rc=1"（本文件开头那段"解释器坏掉也是 1 ⇒ 假绿"同理）。
  #    锚点取审计器 ① 那条具名 finding 的固定前缀（`Other Regions` 的负向断言漏了 …，
  #    见 skill/scripts/surge/audit_region_filters.py 的 ① 分支）。
  _bout="$("$PY" "$SCRIPTS_W/audit_region_filters.py" "$HERE_W/fixtures/bad_region_filter.conf" 2>&1)"
  rc=$?
  if [ "$rc" = "1" ] && printf '%s' "$_bout" | grep -q '负向断言漏了'; then
    res="✅ OK（判负，且原因是漏关键词）"; pass5=$((pass5+1))
  elif [ "$rc" = "1" ]; then
    res="❌ rc=1 但不是因漏关键词判负（判据可能已失效）"; fail5=$((fail5+1))
    printf '\n---- bad_region_filter.conf 的输出（未命中「负向断言漏了」）----\n'
    printf '%s\n' "$_bout" | sed 's/^/    /'
    printf '%s\n' "------------------------"
  else
    res="❌ 期望 1"; fail5=$((fail5+1))
  fi
  printf '%-30s %-14s %s\n' "bad_region_filter.conf" "exit=$rc" "$res"
else
  printf '%-30s %-14s %s\n' "bad_region_filter.conf" "—" "❌ fixture 缺失"; fail5=$((fail5+1))
fi
printf '%s\n' "------------------------------------------------------------------"
printf 'result: %d passed, %d failed\n' "$pass5" "$fail5"

# ── 阶段 6：markdown 相对链接与锚点 ────────────────────────────────────────
# 改标题之后，引用它的所有链接会**静默失效**（GitHub 不报错，读者点 404）。
# 锚点里含中文 / emoji / 全角标点时肉眼扫不出来 ⇒ 必须靠脚本。
printf '\n%s\n' "阶段 6 · markdown 链接与锚点（check_links.py）"
printf '%s\n' "------------------------------------------------------------------"
"$PY" "$HERE_W/check_links.py" "$ROOT_W" >/dev/null 2>&1
rc6=$?
if [ "$rc6" = "0" ]; then
  pass6=1; fail6=0; printf '%s\n' "   ✅ 全部相对链接与锚点均可解析"
else
  pass6=0; fail6=1
  printf '%s\n' "   ❌ 有失效链接（详细输出：）"
  "$PY" "$HERE_W/check_links.py" "$ROOT_W" 2>&1 | sed 's/^/    /'
fi
printf '%s\n' "------------------------------------------------------------------"
printf 'result: %d passed, %d failed\n' "$pass6" "$fail6"

total_pass=$((pass + pass2 + pass3 + pass4 + pass5 + pass6))
total_fail=$((fail + fail2 + fail3 + fail4 + fail5 + fail6))
printf '\n%s\n' "=================================================="
printf 'TOTAL: %d passed, %d failed\n' "$total_pass" "$total_fail"
[ "$total_fail" = "0" ] || exit 1
exit 0
