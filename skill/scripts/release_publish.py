# -*- coding: utf-8 -*-
"""Release 发布器：一个分工版本 = 一个 GitHub Release（tag = <family>-vX.Y）

用法（仓库根目录）:
    python skill/scripts/release_publish.py                     # 计划模式：只列清单与说明样例，一个字不发
    python skill/scripts/release_publish.py --apply             # 按计划发布全部缺失的 Release（需 --token 或环境变量 GITHUB_TOKEN）
    python skill/scripts/release_publish.py --family lazy --apply   # 日常动线⑦：只发指定分工缺失的 Release

规矩（详见 skill/reference/shared/ops.md §6.9，断言在 skill/tests/check_releases.py）:
    - tag 允许带版本号（`lazy-v1.8` / `routing-v3`）；资产文件名一律不带版本号（固定名四件脸）；
    - 说明中明确版本号（`lazy_v1.8`）；历史条目标注 📦 历史版本，现行版标注 🟢 当前版本；
    - **说明是面向公众的产品更新日志**：变更摘要一律取自 PUBLIC_NOTES 表（公众向措辞），
      禁止把内部 commit subject（用户拍板 / 实测 / 入档等过程语言）直接贴上去；
    - 资产 = 该分工该版本两内核现有所属文件（完整版 + .min），缺口侧如实注明，不硬凑；
    - 内容未变的分工不单独发 Release —— Release 挂的是分工版本，不是改动事件。
"""
import argparse, json, os, re, subprocess, sys, urllib.request

REPO = os.environ.get('GITHUB_REPO', 'RiverFlowsInUUU/Self-Configuration')
API = f'https://api.github.com/repos/{REPO}'
UPLOAD = f'https://uploads.github.com/repos/{REPO}/releases'
FAMS = ('lazy', 'routing')
RAW = f'https://raw.githubusercontent.com/{REPO}/main'
DL = f'https://github.com/{REPO}/releases/download'
# 下载按钮 = shields.io 在线徽章（for-the-badge 风格，各内核一个主题色）
BADGES = {
    'surge': 'https://img.shields.io/badge/Surge-下载配置-0A84FF?style=for-the-badge',
    'egern': 'https://img.shields.io/badge/Egern-下载配置-10B981?style=for-the-badge',
}
BADGE_ALT = {'surge': 'Download Surge', 'egern': 'Download Egern'}

# 公众向更新摘要（Release 页是产品对外的更新日志，不搬运内部 commit subject）。
# 键：(family, version)。发新版本前必须先在此补一行 —— 动线⑦的一部分。
PUBLIC_NOTES = {
    ('lazy', 'v1.0'): '首个公开版本：固定订阅槽位、广告拦截、AI 与常用服务分流，开箱即用。',
    ('lazy', 'v1.1'): '维护性更新：文档与注释口径修正，配置行为不变。',
    ('lazy', 'v1.2'): '新增隐藏订阅槽位与占位节点，客户端导入后直接填入订阅即可使用。',
    ('lazy', 'v1.3'): '新增按 Wi-Fi 网络自动暂停（SSID Setting）：回到可信网络时自动停用代理。',
    ('lazy', 'v1.4'): '维护性更新：历史版本归档机制恢复，配置行为不变。',
    ('lazy', 'v1.5'): '维护性更新：配置内注释指向修正。',
    ('lazy', 'v1.6'): '维护性更新：文件结构对齐与注释清理，分流行为不变。',
    ('lazy', 'v1.7'): '国内域名规则集更名为 CN-Domains，日志中更易识别，分流行为不变。',
    ('lazy', 'v1.8'): 'AI 服务规则集更换为持续维护的上游，覆盖 ChatGPT、Gemini、Grok、Sora 等更多 AI 服务。',
    ('lazy', 'v1.9'): '新增自托管 AI 域名整合列表：Google、GitHub 伴生域名并入 AI 分流，ChatGPT 相关基础设施域名不再漏出；AI 组改为默认手动指定出口。',
    ('routing', 'v1'): '分流版初始发布：完整的应用 / 地区分组与流媒体规则（本版本仅提供 Egern 侧文件）。',
    ('routing', 'v2'): '分流版早期演进版本：分组与规则结构调整。',
    ('routing', 'v2.1'): '分流版早期演进版本：分组与规则结构调整。',
    ('routing', 'v2.2'): '分流版早期演进版本：分组与规则结构调整。',
    ('routing', 'v2.3'): '分流版早期演进版本：分组与规则结构调整。',
    ('routing', 'v2.4'): '分流版早期演进版本：分组与规则结构调整。',
    ('routing', 'v3'): '分组与规则体系重构，两内核结构对齐。',
    ('routing', 'v3.1'): '维护性更新。',
    ('routing', 'v3.2'): '维护性更新：配置内注释修正。',
    ('routing', 'v3.3'): '新增隐藏订阅槽位与占位节点，客户端导入后直接填入订阅即可使用。',
    ('routing', 'v3.4'): '维护性更新：注释读数修正（本版本仅提供 Egern 侧文件）。',
    ('routing', 'v3.5'): '维护性更新：历史版本归档机制恢复，配置行为不变。',
    ('routing', 'v3.6'): '维护性更新：结构对齐与注释清理。',
    ('routing', 'v3.7'): '国内域名规则集更名为 CN-Domains，日志中更易识别，分流行为不变。',
    ('routing', 'v3.8'): 'AI 服务规则集更换为持续维护的上游，覆盖 ChatGPT、Gemini、Grok、Sora 等更多 AI 服务。',
    ('routing', 'v3.9'): '新增自托管 AI 域名整合列表：伴生域名精确并入 AI 分流，ChatGPT 相关基础设施域名不再漏出。',
}

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

def version_date(root, kern, fam, ver):
    """该版本内容的诞生日期：归档快照的 blob 在现役 profile 历史中首次出现的提交。

    （旧实现取"归档文件被加入 repo 的提交"= 退役提交，永远晚一个版本 —— 已废弃。）
    历史重写过的早期版本可能找不到，返回 None 由调用方决定省略。"""
    ext = '.conf' if kern == 'surge' else '.yaml'
    arch = os.path.join(kern, 'profiles', 'config_old', f'{fam}_{ver}{ext}')
    try:
        sha = git('rev-parse', f'HEAD:{arch.replace(os.sep, "/")}')
        log = git('log', '--reverse', '--format=%as', '--find-object=' + sha,
                  '--', f'{kern}/profiles/{fam}{ext}'.replace(os.sep, '/'))
        lines = [l for l in log.splitlines() if l.strip()]
        return lines[0] if lines else None
    except subprocess.CalledProcessError:
        return None

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
                date = None if entry['is_current'] else version_date(root, kern, fam, ver)
                entry['kerns'][kern] = {'full': os.path.relpath(full, root), 'min': os.path.relpath(mn, root),
                                        'date': date}
            plan.append(entry)
    return plan

def asset_name(path):
    """固定名四件脸：归档原名（lazy_v1.8.conf）剥掉版本段（→ lazy.conf）。"""
    return re.sub(r'_(v\d+(?:\.\d+)?)', '', os.path.basename(path))

def build_notes(e):
    """Release 说明（面向公众的产品更新日志，不是内部 commit 记录）。"""
    fam, ver, tag = e['family'], e['version'], e['tag']
    kerns = [k for k in ('surge', 'egern') if e['kerns'][k]]
    lines = [f"## `{fam}_{ver}` · {'🟢 当前版本' if e['is_current'] else '📦 历史版本'}", '']
    if e['is_current']:
        lines += ['> 与仓库固定订阅地址（raw/main）内容一致。更新配置请以后续新版本为准。', '']
    else:
        lines += ['> 历史版本的完整快照，仅供回滚与对照。日常使用请选择最新版本。', '']
    summary = PUBLIC_NOTES.get((fam, ver))
    lines.append(f'- **版本**：`{fam}_{ver}`')
    dates = sorted({e['kerns'][k]['date'] for k in kerns if e['kerns'][k]['date']})
    if dates:
        lines.append(f'- **发布日期**：{dates[0]}')
    if summary:
        lines.append(f'- **更新内容**：{summary}')
    buttons = []
    for kern in ('surge', 'egern'):
        if kern not in kerns:
            continue
        name = asset_name(e['kerns'][kern]['full'])
        buttons.append(f'[![{BADGE_ALT[kern]}]({BADGES[kern]})]({DL}/{tag}/{name})')
    if buttons:
        lines.append(f'{" ".join(buttons)}')
        lines.append('')
        lines.append('<sub>.min 精简版与各内核完整文件见本页底部 Assets。</sub>')
    missing = [k for k in ('surge', 'egern') if k not in kerns]
    if missing:
        lines.append(f'- **说明**：本版本仅提供 {"、".join(missing)} 侧文件（历史缺口，如实保留）')
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
    created, updated, skipped, failed = [], [], [], []
    current_tags = {e['tag'] for e in plan if e['is_current']}
    # Latest 已指向任一现行版就不再碰 make_latest：逐个 PATCH 会让指针在
    # 两个现行版之间抖动，与 CI 的 Releases 检查步构成竞态（0929 实测红过一次）
    req = urllib.request.Request(f'{API}/releases/latest',
                                 headers={'User-Agent': 'self-configuration-release'})
    try:
        latest_ok = json.load(urllib.request.urlopen(req)).get('tag_name') in current_tags
    except Exception:                                  # 404 = 仓库还没有任何 Latest
        latest_ok = False
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
            # 幂等 reconcile：已存在的 Release 说明与当前模板不一致就回写
            # （公众向模板改版 / 摘要修订都靠这一步落到既有 Release 上）
            new_body = build_notes(e)
            if (rel.get('body') or '') != new_body:
                api_req(f"{API}/releases/{rel['id']}", token, 'PATCH', {'body': new_body})
                updated.append(tag)
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
            # 幂等 reconcile：仅在 Latest 未指向现行版时补钉（见函数头部说明）
            if e['is_current'] and not latest_ok:
                api_req(f"{API}/releases/{rel['id']}", token, 'PATCH', {'make_latest': 'true'})
            if tag not in created:
                skipped.append(tag)
        except Exception as exc:                       # noqa: BLE001 —— 逐条报告，不中断后续
            failed.append((tag, str(exc)[:120]))
    print(f'\n创建 {len(created)}：{", ".join(created) or "—"}')
    print(f'说明回写 {len(updated)}：{", ".join(updated) or "—"}')
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
