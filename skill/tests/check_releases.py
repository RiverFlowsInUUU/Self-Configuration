# -*- coding: utf-8 -*-
r"""Release 方案断言（时间线模型：一个更新日 = 一个 Release，tag = vYYYY-MM-DD）。

用法（仓库根目录）:
    python skill/tests/check_releases.py
    可选环境变量 GITHUB_TOKEN：抬高 API 限额（公共仓无 token 也能读，60 次/小时）。

判据（规矩来源：skill/reference/shared/ops.md §6.9）:
    R1 每个 Release 的 tag 匹配 ^v\d{4}-\d{2}-\d{2}$（版本诞生日期），且无重复；
    R2 资产文件名 ∈ 固定名集合（两产品线 × 两内核 × 完整版/.min，共 8 种），且不含版本号样式；
    R3 标题 = emoji + 日期 + 当日主题（与 release_publish.release_title 同源，取真 plan），
       说明正文含当日各产品线的版本号条目（**vX.Y(.Z)** 形式）与产品线名；
    R4 覆盖：config_old 全部归档版本 + 现役版本，每个 (产品线, 版本) 都按其诞生日期
       出现在对应日期 Release 的正文里（同日多版本合并进同一张，资产只挂当日末版）；
    R5 仓库级 Latest 必须是含现行版本的那张（最新日期）Release。
"""
import json, os, re, subprocess, sys, urllib.error, urllib.request, importlib.util

REPO = os.environ.get('GITHUB_REPO', 'RiverFlowsInUUU/Self-Configuration')
API = f'https://api.github.com/repos/{REPO}'
TAG_RE = re.compile(r'^v(\d{4}-\d{2}-\d{2})$')
VER_STYLE = re.compile(r'(?i)_?v\d+(\.\d+)?')          # 资产文件名里任何版本号样式都算违规
# 资产固定名白名单从 release_publish.ASSET_NAMES 派生（单一真源，手抄两份必漂移），
# 在 main() 里装载 rp 后赋值。
FAM_CN = {'lazy': '懒人版', 'routing': '分流版'}

def git(*a):
    return subprocess.check_output(['git', *a], text=True).strip()

def local_versions():
    """config_old 全部归档版本 + 现役头注版本 → {(fam, ver)} 集合与现行 (fam, ver) 集合。"""
    root = git('rev-parse', '--show-toplevel')
    pairs, current = set(), set()
    for fam in ('lazy', 'routing'):
        for kern, ext in (('surge', '.conf'), ('egern', '.yaml')):
            d = os.path.join(root, kern, 'profiles', 'config_old')
            for f in os.listdir(d):
                m = re.match(rf'^{fam}_(v\d+(?:\.\d+){{0,2}})(\.min)?{ext}$', f)
                if m:
                    pairs.add((fam, m.group(1)))
            p = os.path.join(root, kern, 'profiles', f'{fam}{ext}')
            with open(p, encoding='utf-8') as fh:
                ver = re.search(r'^#!\s+version=(\S+)', fh.read(400), re.M).group(1)
            cur = (fam, ver.split('_', 1)[-1])
            pairs.add(cur)
            current.add(cur)
    return pairs, current

def fetch_releases(token):
    """分页抓全量 Release。"""
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

    root = git('rev-parse', '--show-toplevel')
    spec = importlib.util.spec_from_file_location(
        'release_publish', os.path.join(root, 'skill', 'scripts', 'release_publish.py'))
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)

    days = rp.build_days(git('rev-parse', '--show-toplevel'))
    allowed_assets = rp.ASSET_NAMES          # R2 白名单 = 发布器单一真源派生
    day_by_tag = {d['tag']: d for d in days}

    # 覆盖期望：(fam, ver) → 应出现的日期 tag（取该版本的诞生日期）
    want_pair_day = {}
    for d in days:
        for fam in d['fams']:
            for e in d['fams'][fam]['entries']:
                want_pair_day[(fam, e['version'])] = d['tag']
    expected_pairs, current_pairs = local_versions()

    ok, bad = [], []
    def judge(cond, rid, msg):
        (ok if cond else bad).append((rid, msg))

    # R0：每个更新日必须在 DAY_THEMES 有当日主题 —— 缺了会静默落
    # 「📦 配置更新」兜底标题（发布器 DAY_THEMES.get 兜底），发版前在这里拦住。
    for d in days:
        judge(d['date'] in rp.DAY_THEMES, 'R0',
              f"{d['tag']}: DAY_THEMES 有当日主题" if d['date'] in rp.DAY_THEMES
              else f"{d['tag']}: DAY_THEMES 缺 {d['date']} 条目 —— 标题会落「📦 配置更新」兜底，"
                   f"先在 release_publish.py DAY_THEMES 补一行再发版")

    judge(bool(releases), 'R0', '仓库至少有一个 Release（尚无 → 先跑 release_publish.py --apply）')
    judge(bool(days), 'R0', '本地能构建出日期分组 plan')

    seen = set()
    for r in releases:
        tag = r['tag_name']
        m = TAG_RE.match(tag)
        judge(bool(m), 'R1', f'{tag}: tag 形状' if m else f'{tag}: tag 不匹配 ^vYYYY-MM-DD$')
        judge(tag not in seen, 'R1', f'{tag}: tag 重复' if tag in seen else f'{tag}: tag 唯一')
        seen.add(tag)
        for a in r.get('assets', []):
            name = a['name']
            judge(name in allowed_assets and not VER_STYLE.search(name), 'R2',
                  f'{tag}/{name}: 资产命名' if name in allowed_assets and not VER_STYLE.search(name)
                  else f'{tag}/{name}: 资产文件名带版本号或不在固定名集合（{sorted(allowed_assets)}）')
        day = day_by_tag.get(tag)
        if day:
            want_title = rp.release_title(day)
            name_ok = (r.get('name') or '') == want_title
            body = r.get('body') or ''
            # H1 置顶（0929 二次定稿）：正文首行必须是「# … 更新日志」，
            # 防止 build_notes 改坏后 H1 丢失而版本子串断言仍绿
            first_line = body.splitlines()[0] if body else ''
            h1_ok = first_line.startswith('# ') and first_line.endswith(' 更新日志')
            fams_ok = all(FAM_CN[fam] in body for fam in day['fams'])
            judge(name_ok and h1_ok and fams_ok, 'R3',
                  f'{tag}: 标题与正文模板一致（{want_title}）' if name_ok and h1_ok and fams_ok
                  else f'{tag}: 标题/正文与模板不一致 —— 标题应为「{want_title}」，'
                       f'正文首行须为「# … 更新日志」且含各产品线名；跑 release_publish.py --apply 幂等回写')
        else:
            judge(False, 'R1', f'{tag}: tag 不在本地日期分组 plan 里（{sorted(day_by_tag)}）')

    # R4 覆盖：每个 (fam, ver) 都按诞生日期出现在对应 Release 正文
    missing = expected_pairs - set(want_pair_day)
    judge(not missing, 'R4', 'R4 归档版本全覆盖' if not missing
          else f'R4 未被任何日期 Release 覆盖的版本: {sorted(missing)}')
    for r in releases:
        tag = r['tag_name']
        day = day_by_tag.get(tag)
        if not day:
            continue
        body = r.get('body') or ''
        for fam in day['fams']:
            for e in day['fams'][fam]['entries']:
                # 新模板（0929 定稿）：版本号在引言或条目前缀出现即可，
                # 单版本日无加粗前缀（引言已给版本），不再要求 **vX.Y(.Z)** 形态。
                # 三段制（0929 起）：版本子串加 (?!\.\d) 边界 —— v2.0 不得被正文里的 v2.0.1 误满足
                present = re.search(re.escape(e['version']) + r'(?!\.\d)', body) is not None
                judge(present, 'R4',
                      f'{tag} 提到 {FAM_CN[fam]} {e["version"]}' if present
                      else f'{tag}: 正文缺少 {FAM_CN[fam]} {e["version"]} 条目')

    # R5 Latest = 含现行版本的那张（最新日期）
    latest_req = urllib.request.Request(f'{API}/releases/latest')
    latest_req.add_header('User-Agent', 'self-configuration-release')
    if tok:
        latest_req.add_header('Authorization', f'Bearer {tok}')
    want_latest = next((d['tag'] for d in days if d['is_current']), None)
    try:
        latest_tag = json.load(urllib.request.urlopen(latest_req))['tag_name']
        judge(latest_tag == want_latest, 'R5',
              f'R5 Latest={latest_tag}（现行日）' if latest_tag == want_latest
              else f'R5 Latest={latest_tag} ≠ 现行日 {want_latest} —— '
                   f'跑 python skill/scripts/release_publish.py --apply reconcile')
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
