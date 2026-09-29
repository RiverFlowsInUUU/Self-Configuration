# -*- coding: utf-8 -*-
"""Release 发布器：一个分工版本 = 一个 GitHub Release（tag = <family>-vX.Y）

用法（仓库根目录）:
    python skill/scripts/release_publish.py                     # 计划模式：只列清单与说明样例，一个字不发
    python skill/scripts/release_publish.py --apply             # 按计划发布全部缺失的 Release（需 --token 或环境变量 GITHUB_TOKEN）
    python skill/scripts/release_publish.py --family lazy --apply   # 日常动线⑦：只发指定分工缺失的 Release

规矩（详见 skill/reference/shared/ops.md §6.9，断言在 skill/tests/check_releases.py）:
    - tag 允许带版本号（`lazy-v1.8` / `routing-v3`）；资产文件名一律不带版本号（固定名四件脸）；
    - 说明中明确版本号（`lazy_v1.8`）；历史条目标注 📦 补发（retroactive），现行版标注现行；
    - 资产 = 该分工该版本两内核现有所属文件（完整版 + .min），缺口侧如实注明，不硬凑；
    - 内容未变的分工不单独发 Release —— Release 挂的是分工版本，不是改动事件。
"""
import argparse, json, os, re, subprocess, sys, urllib.request

REPO = os.environ.get('GITHUB_REPO', 'RiverFlowsInUUU/Self-Configuration')
API = f'https://api.github.com/repos/{REPO}'
UPLOAD = f'https://uploads.github.com/repos/{REPO}/releases'
BULK_MARK = '流程补课'          # 大重构一次性归档的 commit，不逐版重建变更说明
FAMS = ('lazy', 'routing')

def git(*a):
    return subprocess.check_output(['git', *a], text=True).strip()

def repo_root():
    return git('rev-parse', '--show-toplevel')

def parse_ver(name):
    m = re.search(r'_(v\d+(?:\.\d+)?)\.', name)
    return m.group(1) if m else None

def vkey(ver):
    return tuple(int(x) for x in ver[1:].split('.'))

def active_versions(root):
    """现役版本：从头注 #! version= 读，两内核应同号。"""
    out = {}
    for fam in FAMS:
        vers = set()
        for kern, ext in (('surge', '.conf'), ('egern', '.yaml')):
            p = os.path.join(root, kern, 'profiles', f'{fam}{ext}')
            with open(p, encoding='utf-8') as fh:
                m = re.search(r'^#!\s+version=(\S+)', fh.read(400), re.M)
            vers.add(m.group(1).split('_', 1)[-1])
        assert len(vers) == 1, f'{fam} 两内核头注版本不一致: {vers}'
        out[fam] = vers.pop()
    return out

def archive_file(root, kern, fam, ver):
    ext = '.conf' if kern == 'surge' else '.yaml'
    return os.path.join(root, kern, 'profiles', 'config_old', f'{fam}_{ver}{ext}')

def archive_min(root, kern, fam, ver):
    ext = '.conf' if kern == 'surge' else '.yaml'
    return os.path.join(root, kern, 'profiles', 'config_old', f'{fam}_{ver}.min{ext}')

def archive_meta(root, kern, fam, ver):
    """归档快照的入档时间与提交主题（取最近一次入档）。"""
    p = os.path.join(kern, 'profiles', 'config_old', f'{fam}_{ver}{".conf" if kern == "surge" else ".yaml"}')
    try:
        log = git('log', '--diff-filter=A', '--format=%as%x00%s', '--', p)
    except subprocess.CalledProcessError:
        return None, None
    lines = [l for l in log.splitlines() if l.strip()]
    if not lines:
        return None, None
    date, subj = lines[-1].split('\x00', 1)
    return date, subj

def build_plan(root):
    act = active_versions(root)
    plan = []
    for fam in FAMS:
        vers = set()
        for kern in ('surge', 'egern'):
            d = os.path.join(root, kern, 'profiles', 'config_old')
            for f in os.listdir(d):
                if parse_ver(f) and f.startswith(fam + '_v'):
                    vers.add(parse_ver(f))
        vers.add(act[fam])
        for ver in sorted(vers, key=vkey):
            entry = {'family': fam, 'version': ver, 'tag': f'{fam}-{ver}',
                     'is_current': ver == act[fam], 'kerns': {}}
            for kern in ('surge', 'egern'):
                ext = '.conf' if kern == 'surge' else '.yaml'
                if entry['is_current']:
                    full = os.path.join(root, kern, 'profiles', f'{fam}{ext}')
                else:
                    full = archive_file(root, kern, fam, ver)
                if not os.path.exists(full):
                    entry['kerns'][kern] = None
                    continue
                mn = full[:full.rindex(ext)] + f'.min{ext}'
                date, subj = (None, None) if entry['is_current'] else archive_meta(root, kern, fam, ver)
                entry['kerns'][kern] = {'full': os.path.relpath(full, root), 'min': os.path.relpath(mn, root),
                                        'date': date, 'subj': subj}
            plan.append(entry)
    return plan

def asset_name(path):
    """固定名四件脸：归档原名（lazy_v1.8.conf）剥掉版本段（→ lazy.conf）。"""
    return re.sub(r'_(v\d+(?:\.\d+)?)', '', os.path.basename(path))

def build_notes(e):
    fam, ver, tag = e['family'], e['version'], e['tag']
    kerns = [k for k in ('surge', 'egern') if e['kerns'][k]]
    lines = [f"## `{fam}_{ver}` · {'🟢 现行版' if e['is_current'] else '📦 补发（retroactive）'}", '']
    if e['is_current']:
        lines += ['> 🟢 现行服役版的钉版快照：内容与 `raw/main` 固定名文件一致；此后以新 Release 为准，本条不再更新。', '']
    else:
        lines += ['> 📦 历史版本补发：内容取自 `config_old/` 归档快照，与其服役时逐字节相同（`check_min_pair.py` V6 断言守）。', '']
    lines.append(f'- **版本号**：`{fam}_{ver}`' + ('（Surge 与 Egern 同号）' if len(kerns) == 2 else ''))
    dates = {e['kerns'][k]['date'] for k in kerns if e['kerns'][k]['date']}
    if dates:
        lines.append(f'- **归档时间**：{" / ".join(sorted(dates))}')
    if e['is_current']:
        lines.append('- **变更摘要**：现行版钉版发布，变更历史见 git log')
    else:
        subjs = {e['kerns'][k]['subj'] for k in kerns if e['kerns'][k]['subj']}
        if subjs and all(BULK_MARK not in (s or '') for s in subjs):
            lines.append(f'- **变更摘要**：{sorted(subjs)[0]}')
        else:
            lines.append('- **变更摘要**：补发条目不逐版重建变更说明；版本演进见 git 历史（备份 tag `pre-cleanup-20260927`）')
    assets = []
    if 'surge' in kerns:
        assets.append(f"Surge `{asset_name(e['kerns']['surge']['full'])}` / `{asset_name(e['kerns']['surge']['min'])}`")
    if 'egern' in kerns:
        assets.append(f"Egern `{asset_name(e['kerns']['egern']['full'])}` / `{asset_name(e['kerns']['egern']['min'])}`")
    lines.append(f'- **资产**：{" · ".join(assets)} —— 文件名不含版本号，版本号仅存在于本说明与 tag')
    missing = [k for k in ('surge', 'egern') if k not in kerns]
    if missing:
        lines.append(f'- **缺口**：{"、".join(missing)} 侧无本版归档（历史缺口，按仓库纪律保留不补）')
    lines += ['', f'- 版本号与命名规则：[ops.md §6.9](../../blob/main/skill/reference/shared/ops.md)']
    return '\n'.join(lines)

def api_req(url, token, method='GET', data=None, ctype='application/json', raw=None):
    body = raw if raw is not None else (json.dumps(data, ensure_ascii=False).encode() if data is not None else None)
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('User-Agent', 'self-configuration-release')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    if body is not None:
        req.add_header('Content-Type', ctype)
    return urllib.request.urlopen(req)

def existing_releases(token):
    out, page = [], 1
    while True:
        with api_req(f'{API}/releases?per_page=100&page={page}', token) as r:
            batch = json.load(r)
        out += batch
        if len(batch) < 100:
            return out
        page += 1

def apply(plan, token, only_family=None):
    ex = {r['tag_name']: r for r in existing_releases(token)}
    created, skipped, failed = [], [], []
    for e in plan:
        if only_family and e['family'] != only_family:
            continue
        tag = e['tag']
        try:
            if tag in ex:
                rel = ex[tag]
            else:
                # 现行版钉仓库 Latest：批量补发时按处理次序 last-wins；
                # 日常动线⑦（--family X）会把 Latest 钉到刚发的那个分工
                with api_req(API + '/releases', token, 'POST',
                             {'tag_name': tag, 'target_commitish': 'main', 'name': tag,
                              'body': build_notes(e),
                              'make_latest': 'true' if e['is_current'] else 'false'}) as r:
                    rel = json.load(r)
                created.append(tag)
            have = {a['name'] for a in rel.get('assets', [])}
            for kern in ('surge', 'egern'):
                info = e['kerns'][kern]
                if not info:
                    continue
                for key in ('full', 'min'):
                    path = os.path.join(repo_root(), info[key])
                    name = asset_name(info[key])
                    if name in have:
                        continue
                    with open(path, 'rb') as fh:
                        raw = fh.read()
                    api_req(f"{UPLOAD}/{rel['id']}/assets?name={name}", token, 'POST',
                            raw=raw, ctype='application/octet-stream')
            # 幂等 reconcile：已存在的现行版 Release 也钉一次 Latest
            # （补发批跑漏钉的根因：Latest 由创建时间决定，与版本无关）
            if e['is_current']:
                api_req(f"{API}/releases/{rel['id']}", token, 'PATCH', {'make_latest': 'true'})
            if tag not in created:
                skipped.append(tag)
        except Exception as exc:                       # noqa: BLE001 —— 逐条报告，不中断后续
            failed.append((tag, str(exc)[:120]))
    print(f'\n创建 {len(created)}：{", ".join(created) or "—"}')
    print(f'已存在跳过 {len(skipped)}：{", ".join(skipped) or "—"}')
    print(f'失败 {len(failed)}：{failed or "—"}')
    return 0 if not failed else 1

def show_plan(plan):
    cur = 0
    for e in plan:
        mark = '现行' if e['is_current'] else '补发'
        cur += e['is_current']
        k = '/'.join(k for k in ('surge', 'egern') if e['kerns'][k])
        miss = ','.join(k for k in ('surge', 'egern') if not e['kerns'][k]) or '-'
        date = next((e['kerns'][x]['date'] for x in ('surge', 'egern') if e['kerns'][x] and e['kerns'][x]['date']), '-')
        print(f"{e['tag']:16s} {mark}  内核={k:12s} 缺口={miss:6s} 归档={date}")
    print(f'\n共 {len(plan)} 个 Release（现行 {cur} + 补发 {len(plan) - cur}）')
    sample = next((e for e in plan if e['family'] == 'lazy' and not e['is_current']), plan[0])
    print(f'\n──── 说明样例（{sample["family"]}_{sample["version"]}）────')
    print(build_notes(sample))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='真发（默认只出计划）')
    ap.add_argument('--family', choices=FAMS, help='只处理一个分工（日常动线⑦）')
    ap.add_argument('--token', default=os.environ.get('GITHUB_TOKEN'), help='GitHub token（--apply 必需）')
    args = ap.parse_args()
    plan = build_plan(repo_root())
    if not args.apply:
        show_plan(plan)
        print('\n（计划模式：一个 Release 都不发。加 --apply 才发布，需 --token 或 GITHUB_TOKEN）')
        return 0
    if not args.token:
        print('❌ --apply 需要 --token 或环境变量 GITHUB_TOKEN'); return 2
    return apply(plan, args.token, args.family)

if __name__ == '__main__':
    sys.exit(main())
