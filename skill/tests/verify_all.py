#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键收尾闸门 —— 动线⑤ 的闸门命令合并成 1 条，并行跑、出汇总表。

为什么存在：
    SKILL.md 动线⑤原来列一堆独立命令，AI 逐条调用 = 多次工具调用、多段输出
    折进上下文，且任何一次漏跑/跑错参数都算事故。本脚本与 `.github/workflows/ci.yml`
    的步骤**同源**（改 CI 步骤时必须同步这里，反之亦然），并行执行后只输出一张
    「闸门 | 结果 | 耗时」汇总表，红的才展开输出尾部 —— 正常情况一段话看完全部结论。

用法：
    python skill/tests/verify_all.py            # 全量并行，全绿退出码 0
    python skill/tests/verify_all.py -v         # 无论红绿都打印每个闸门的输出尾部

设计约定：
    · 与 CI 同源是铁律 —— 本地绿但 CI 红属于竞态/环境差，不允许有"第三套判据"。
    · check_releases 需 GITHUB_TOKEN：缺省时自动回退 `gh auth token`。两者都没有、
      或 API 离线/限流时，check_releases 返回**专用退出码 2**（SKIP），verify_all
      以 ⚠️ 明示「未验证」且**不计入失败**（exit 0）—— 0929 外部审查：原实现用输出
      文本嗅探判定、且被跳过仍 exit 1，提示与实际矛盾，现改为按退出码判定。
    · make_min 漂移检查 = `make_min.py --check`（0929 起）：--check 直接比对磁盘 .min 与
      生成器输出，有差异即非 0。旧写法「计划模式 + git diff」两半恒空/恒 0，是永远绿的
      空操作（2026-09-29 外部审查实锤后废除，原『git 无漂移』闸门随之合并）。
"""

import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable or 'python'


def _token():
    """check_releases 用：环境变量 → gh auth token → None。"""
    if os.environ.get('GITHUB_TOKEN'):
        return os.environ['GITHUB_TOKEN']
    try:
        r = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None


def build_gates():
    """与 ci.yml 步骤一一对应；(名称, argv, 额外环境)。"""
    gates = [
        ('secrets 扫描', [PY, 'skill/tests/check_secrets.py'], {}),
        ('portability', [PY, 'skill/tests/check_portability.py'], {}),
        ('min-pair 一致', [PY, 'skill/tests/check_min_pair.py'], {}),
        ('README 徽章', [PY, 'skill/tests/check_badges.py'], {}),
        ('markdown 链接', [PY, 'skill/tests/check_links.py', '.'], {}),
        ('releases 方案', [PY, 'skill/tests/check_releases.py'],
         {'GITHUB_TOKEN': _token() or ''}),
        ('Surge DNS lazy', [PY, 'skill/scripts/surge/check_surge_dns.py', 'surge/profiles/lazy.conf'], {}),
        ('Surge DNS routing', [PY, 'skill/scripts/surge/check_surge_dns.py', 'surge/profiles/routing.conf'], {}),
        ('Egern DNS 双份', [PY, 'skill/scripts/egern/check_egern_dns.py',
                            'egern/profiles/lazy.yaml', 'egern/profiles/routing.yaml'], {}),
        ('.min 漂移', [PY, 'skill/tests/make_min.py', '--check'], {}),
    ]
    return gates


def run_one(name, argv, extra_env):
    t0 = time.perf_counter()
    env = dict(os.environ)
    env.update({k: v for k, v in extra_env.items() if v})
    if 'GITHUB_TOKEN' in extra_env and not extra_env['GITHUB_TOKEN']:
        env.pop('GITHUB_TOKEN', None)
    try:
        r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', env=env, timeout=600)
        return {'name': name, 'argv': argv, 'code': r.returncode,
                'dt': time.perf_counter() - t0,
                'out': (r.stdout or '') + (r.stderr or '')}
    except Exception as e:                                   # noqa: BLE001
        return {'name': name, 'argv': argv, 'code': -1,
                'dt': time.perf_counter() - t0, 'out': f'{type(e).__name__}: {e}'}


def main():
    verbose = '-v' in sys.argv
    gates = build_gates()
    print(f'并行跑 {len(gates)} 道闸门（与 ci.yml 同源）…\n')
    with ThreadPoolExecutor(max_workers=min(len(gates), 8)) as ex:
        results = list(ex.map(lambda g: run_one(*g), gates))

    width = max(len(r['name']) for r in results)
    print(f"{'闸门':<{width}}  结果  耗时")
    print('-' * (width + 16))
    for r in results:
        mark = '✅' if r['code'] == 0 else ('⚠️' if r['code'] == 2 else '❌')
        print(f"{r['name']:<{width}}  {mark}   {r['dt']:.1f}s")
    print()

    # 退出码语义（0929 外部审查后统一）：0 = 过；1 = 断言失败；2 = SKIP（未能验证）
    failed = [r for r in results if r['code'] not in (0, 2)]
    skipped = [r for r in results if r['code'] == 2]
    if not failed and not verbose:
        print('全部通过 —— 详细输出用 -v 查看。' if not skipped
              else '闸门全过（有 SKIP 项，见下）。')
    if failed or skipped or verbose:
        for r in results:
            if verbose or r['code'] != 0:
                tail = '\n'.join(r['out'].splitlines()[-30:]) or '(无输出)'
                print(f"──── {r['name']} (exit {r['code']}) {'─' * 30}")
                print(tail)
                print()
    if skipped:
        print('⚠️ 以下闸门被跳过（未验证 ≠ 绿）：'
              + '、'.join(r['name'] for r in skipped))

    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
