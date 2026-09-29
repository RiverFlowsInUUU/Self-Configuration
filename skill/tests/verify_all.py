#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键收尾闸门 —— 动线⑤ 的 13 条命令合并成 1 条，并行跑、出汇总表。

为什么存在：
    SKILL.md 动线⑤原来列 13 条独立命令，AI 逐条调用 = 13 次工具调用、13 段输出
    折进上下文，且任何一次漏跑/跑错参数都算事故。本脚本与 `.github/workflows/ci.yml`
    的步骤**同源**（改 CI 步骤时必须同步这里，反之亦然），并行执行后只输出一张
    「闸门 | 结果 | 耗时」汇总表，红的才展开输出尾部 —— 正常情况一段话看完全部结论。

用法：
    python skill/tests/verify_all.py            # 全量并行，全绿退出码 0
    python skill/tests/verify_all.py -v         # 无论红绿都打印每个闸门的输出尾部

设计约定：
    · 与 CI 同源是铁律 —— 本地绿但 CI 红属于竞态/环境差，不允许有"第三套判据"。
    · check_releases 需 GITHUB_TOKEN：缺省时自动回退 `gh auth token`，两者都没有
      则记 SKIP（不算失败）—— 离线/无凭据环境允许跳过它，但汇总表要明示。
    · make_min 漂移检查 = 运行后对**四份 .min** 做 `git diff --exit-code`（CI 同源意图；
      CI 里用全树 diff 是因为 checkout 后树干净，本地树常有未提交改动，必须收窄到 .min）。
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
        ('.min 漂移', [PY, 'skill/tests/make_min.py'], {}),
        ('git 无漂移', ['git', 'diff', '--exit-code', '--',
                        'surge/profiles/lazy.min.conf', 'surge/profiles/routing.min.conf',
                        'egern/profiles/lazy.min.yaml', 'egern/profiles/routing.min.yaml'], {}),
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
        mark = '✅' if r['code'] == 0 else '❌'
        print(f"{r['name']:<{width}}  {mark}   {r['dt']:.1f}s")
    print()

    failed = [r for r in results if r['code'] != 0]
    skipped = [r for r in results if r['name'] == 'releases 方案'
               and r['code'] != 0 and 'gh' not in r['out'] and not os.environ.get('GITHUB_TOKEN')]
    if not failed and not verbose:
        print('全部通过 —— 详细输出用 -v 查看。')
    if failed or verbose:
        for r in results:
            if verbose or r['code'] != 0:
                tail = '\n'.join(r['out'].splitlines()[-30:]) or '(无输出)'
                print(f"──── {r['name']} (exit {r['code']}) {'─' * 30}")
                print(tail)
                print()
    if skipped:
        print('⚠️ releases 方案闸门因无 GITHUB_TOKEN / gh 被跳过 —— 不是绿，是未验证。')

    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
