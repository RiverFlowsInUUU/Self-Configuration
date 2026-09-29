# -*- coding: utf-8 -*-
"""Release 方案断言：tag 形状、资产文件名不带版本号、说明含版本号、归档版本全覆盖。

用法（仓库根目录）:
    python skill/tests/check_releases.py
    可选环境变量 GITHUB_TOKEN：抬高 API 限额（公共仓无 token 也能读，60 次/小时）。

判据（规矩来源：skill/reference/shared/ops.md §6.9）:
    R1 每个 Release 的 tag 匹配 ^(lazy|routing)-v\d+(\.\d+)?$，且无重复；
    R2 资产文件名 ∈ 固定名四件脸（两内核 × 完整版/.min），且不含版本号样式；
    R3 说明正文含 tag 对应的版本号字符串（如 tag=lazy-v1.8 → 正文含 lazy_v1.8）；
    R4 config_old 全部归档版本 + 现役两分工版本，每个都有对应 Release（全覆盖）；
    R5 仓库级 Latest 必须落在现行两分工版本之一 —— 补发批跑只按创建时间决定 Latest
       会把 Latest 留在旧版上（实测：26 个补发后 Latest=lazy-v1.8，现行却是 v1.9）。
"""
import json, os, re, subprocess, sys, urllib.error, urllib.request

REPO = os.environ.get('GITHUB_REPO', 'RiverFlowsInUUU/Self-Configuration')
API = f'https://api.github.com/repos/{REPO}'
TAG_RE = re.compile(r'^(lazy|routing)-(v\d+(?:\.\d+)?)$')
VER_STYLE = re.compile(r'(?i)_?v\d+(\.\d+)?')          # 资产文件名里任何版本号样式都算违规
ALLOWED_ASSETS = {f'{fam}{ext}' for fam in ('lazy', 'routing')
                  for ext in ('.conf', '.min.conf', '.yaml', '.min.yaml')}
BULK_MARK = '流程补课'

def git(*a):
    return subprocess.check_output(['git', *a], text=True).strip()

def local_expected():
    """config_old 全部归档版本 + 现役头注版本 → 应存在的 tag 集合（含现行两 tag 单独返回）。"""
    root = git('rev-parse', '--show-toplevel')
    tags, current = set(), set()
    for fam in ('lazy', 'routing'):
        for kern, ext in (('surge', '.conf'), ('egern', '.yaml')):
            d = os.path.join(root, kern, 'profiles', 'config_old')
            for f in os.listdir(d):
                if not f.endswith(ext) or f'{fam}_' != f[:len(fam) + 1]:
                    continue
                m = re.match(rf'^{fam}_(v\d+(?:\.\d+)?)(\.min)?{ext}$', f)
                if m:
                    tags.add(f'{fam}-{m.group(1)}')
            p = os.path.join(root, kern, 'profiles', f'{fam}{ext}')
            with open(p, encoding='utf-8') as fh:
                ver = re.search(r'^#!\s+version=(\S+)', fh.read(400), re.M).group(1)
            tags.add(f'{fam}-{ver.split("_", 1)[-1]}')
            current.add(f'{fam}-{ver.split("_", 1)[-1]}')
    return tags, current

def fetch_releases(token):
    """分页抓全量 Release（>100 条时单页抓取会让 R4 假红）。"""
    out, page = [], 1
    while True:
        req = urllib.request.Request(f'{API}/releases?per_page=100&page={page}')
        req.add_header('User-Agent', 'self-configuration-release')
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        batch = json.load(urllib.request.urlopen(req))
        out += batch
        if len(batch) < 100:
            return out
        page += 1

def main():
    tok = os.environ.get('GITHUB_TOKEN')
    releases = fetch_releases(tok)

    ok, bad = [], []
    def judge(cond, rid, msg):
        (ok if cond else bad).append((rid, msg))

    judge(bool(releases), 'R0', '仓库至少有一个 Release（尚无 → 先跑 release_publish.py 补发）')

    seen = set()
    for r in releases:
        tag = r['tag_name']
        m = TAG_RE.match(tag)
        judge(bool(m), 'R1', f'{tag}: tag 形状' if m else f'{tag}: tag 不匹配 ^(lazy|routing)-vX.Y$')
        judge(tag not in seen, 'R1', f'{tag}: tag 重复' if tag in seen else f'{tag}: tag 唯一')
        seen.add(tag)
        ver = m.group(2) if m else None
        for a in r.get('assets', []):
            name = a['name']
            judge(name in ALLOWED_ASSETS and not VER_STYLE.search(name), 'R2',
                  f'{tag}/{name}: 资产命名' if name in ALLOWED_ASSETS and not VER_STYLE.search(name)
                  else f'{tag}/{name}: 资产文件名带版本号或不在固定名集合（{sorted(ALLOWED_ASSETS)}）')
        body = r.get('body') or ''
        if ver:
            fam = m.group(1)
            judge(f'{fam}_{ver}' in body, 'R3',
                  f'{tag}: 说明含版本号 {fam}_{ver}' if f'{fam}_{ver}' in body
                  else f'{tag}: 说明未写版本号 {fam}_{ver}')

    expected, current_tags = local_expected()
    missing = expected - seen
    judge(not missing, 'R4', 'R4 归档版本全覆盖' if not missing else f'R4 缺 Release 的版本: {sorted(missing)}')

    # R5 仓库级 Latest 必须是现行两分工版本之一
    latest_req = urllib.request.Request(f'{API}/releases/latest')
    latest_req.add_header('User-Agent', 'self-configuration-release')
    if tok:
        latest_req.add_header('Authorization', f'Bearer {tok}')
    try:
        latest_tag = json.load(urllib.request.urlopen(latest_req))['tag_name']
        judge(latest_tag in current_tags, 'R5',
              f'R5 Latest={latest_tag}（现行之一）' if latest_tag in current_tags
              else f'R5 Latest={latest_tag} 不在现行两分工版本 {sorted(current_tags)} 里 —— '
                   f'跑 python skill/scripts/release_publish.py --apply reconcile（会幂等跳过，只重钉 Latest）')
    except urllib.error.HTTPError as exc:
        judge(False, 'R5', f'R5 /releases/latest 不可读（HTTP {exc.code}）')

    for rid, msg in ok:
        print(f'   ✅ {msg}')
    for rid, msg in bad:
        print(f'   ❌ {msg}')
    print(f'\nTOTAL: {len(ok)} passed, {len(bad)} failed')
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
