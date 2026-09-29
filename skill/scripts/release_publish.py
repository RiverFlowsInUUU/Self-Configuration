# -*- coding: utf-8 -*-
"""Release 发布器：一个分工版本 = 一个 GitHub Release（tag = <family>-vX.Y）

用法（仓库根目录）:
    python skill/scripts/release_publish.py                     # 计划模式：只列清单与说明样例，一个字不发
    python skill/scripts/release_publish.py --apply             # 按计划发布全部缺失的 Release（需 --token 或环境变量 GITHUB_TOKEN）
    python skill/scripts/release_publish.py --family lazy --apply   # 日常动线⑦：只发指定分工缺失的 Release

规矩（详见 skill/reference/shared/ops.md §6.9，断言在 skill/tests/check_releases.py）:
    - tag 允许带版本号（`lazy-v1.8` / `routing-v3`）；资产文件名一律不带版本号（固定名四件脸）；
    - Release 标题 = emoji + 一句主题（HEADLINES 表），版本号由 tag 芯片承载，正文不重复；
    - 说明正文分工名贯穿（状态行 / 下载按钮 / Assets 提示各带「懒人版 / 分流版」）；
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
# 下载按钮 = shields.io 在线徽章（for-the-badge 风格）：颜色编码内核，文字编码分工
FAM_CN = {'lazy': '懒人版', 'routing': '分流版'}
KERN_LABEL = {'surge': 'Surge', 'egern': 'Egern'}
KERN_COLOR = {'surge': '0A84FF', 'egern': '10B981'}

def badge_url(kern, fam):
    return (f"https://img.shields.io/badge/{KERN_LABEL[kern]}-{FAM_CN[fam]}_下载-"
            f"{KERN_COLOR[kern]}?style=for-the-badge")

# Release 标题 = 分类 emoji + 分工 + 诞生日期 + 一句主题（版本号由 tag 芯片承载）。
# 与 PUBLIC_NOTES 一一对应，26 个标题各不相同 —— 禁止「维护性更新」这类通用标题复用。
# 分工与日期由 release_title 统一拼装，此处只写主题，不要重复出现「懒人版/分流版」字样。
HEADLINES = {
    ('lazy', 'v1.0'): ('🚀', '首个公开版本'),
    ('lazy', 'v1.1'): ('📝', '注释口径修正：规则条数不写死'),
    ('lazy', 'v1.2'): ('🛫', '订阅槽位上线，导入即用'),
    ('lazy', 'v1.3'): ('📶', 'Wi-Fi 自动暂停'),
    ('lazy', 'v1.4'): ('📚', '文档引用路径修正'),
    ('lazy', 'v1.5'): ('📚', '文档迁移至新目录结构'),
    ('lazy', 'v1.6'): ('🧹', '广告组语义收紧 + Apple 集自托管'),
    ('lazy', 'v1.7'): ('🏷️', '规则集更名 CN-Domains'),
    ('lazy', 'v1.8'): ('🔄', 'AI 规则集换源，覆盖更多 AI 服务'),
    ('lazy', 'v1.9'): ('🧩', '自托管 AI 域名整合 + AI 组改手动'),
    ('routing', 'v1'): ('🚀', '初始发布，应用 / 地区分组成形'),
    ('routing', 'v2'): ('🛡️', 'DNS 段重构，明文通路压到最小'),
    ('routing', 'v2.1'): ('🧹', '清理默认值配置键'),
    ('routing', 'v2.2'): ('🛫', '机场槽位精简，MAX 低倍率筛选'),
    ('routing', 'v2.3'): ('🛠️', '修复断流空组与 MAX 筛选误判'),
    ('routing', 'v2.4'): ('⏱️', '规则集补齐每日自动刷新'),
    ('routing', 'v3'): ('🧭', '规则段对齐 Surge，订阅入口合一'),
    ('routing', 'v3.1'): ('⏱️', '规则集刷新周期统一为每周'),
    ('routing', 'v3.2'): ('🔬', 'no-resolve 精细取舍 + System 快照集'),
    ('routing', 'v3.3'): ('👥', '占位节点上线，两种填法都能跑'),
    ('routing', 'v3.4'): ('📝', '订阅占位符口径修正'),
    ('routing', 'v3.5'): ('📶', 'Wi-Fi 自动暂停'),
    ('routing', 'v3.6'): ('📚', '文档迁移至新目录结构'),
    ('routing', 'v3.7'): ('🏷️', '规则集更名 CN-Domains'),
    ('routing', 'v3.8'): ('🔄', 'AI 规则集换源，覆盖更多 AI 服务'),
    ('routing', 'v3.9'): ('🧩', '自托管 AI 域名整合集上线'),
}

# 公众向更新摘要（Release 页是产品对外的更新日志，不搬运内部 commit subject）。
# 键：(family, version)，值 = 要点列表（1~4 条，逐版本如实总结，禁止模板句复用）。
# 内容依据 = config_old 相邻版本快照的逐行 diff（行为改动 + 有意义的注释修正）。
# 发新版本前必须先在此补一组 —— 动线⑦的一部分。
PUBLIC_NOTES = {
    ('lazy', 'v1.0'): [
        '首个公开版本：内置隐藏订阅槽位与占位节点，导入填上自己的订阅即可使用。',
        '分流规则覆盖：白名单放行、广告拦截、AI 服务分流、系统与国内域名直连。',
        'DNS 全链路加密解析，防泄露结构完整。',
    ],
    ('lazy', 'v1.1'): [
        '配置内注释口径修正：国内直连规则集的条数不再写死精确数字 —— 上游每周更新，写死的数字必然过期，改为「要现值就现抓」。分流行为不变。',
    ],
    ('lazy', 'v1.2'): [
        '新增隐藏订阅槽位（Airport）：填入机场订阅链接，节点直接灌进主出口与 AI 两组。',
        '移除原有的 HTTPS 中转链示例节点，占位节点精简为两条（主出口 / AI 各一条）。',
        '只填订阅、不填节点也能跑；只填节点、不导订阅也一样。',
    ],
    ('lazy', 'v1.3'): [
        '新增 Wi-Fi 自动暂停（SSID Setting）：回到家里可信网络时自动停用代理，离开后自动恢复。（本版改动在 Surge 侧）',
    ],
    ('lazy', 'v1.4'): [
        '配置内文档引用路径修正，分流行为不变。',
    ],
    ('lazy', 'v1.5'): [
        '配置内文档引用路径迁移到仓库新目录结构，分流行为不变。',
    ],
    ('lazy', 'v1.6'): [
        '广告拦截组移除多余的 DIRECT 备选项，保持「默认拦截、可手动放行」的单一语义。',
        'Apple 系统服务规则集改用本仓自托管快照，两内核共用同一份来源。',
    ],
    ('lazy', 'v1.7'): [
        '国内域名规则集更名 CN-Domains，客户端日志中更易识别，分流行为不变。（本版改动在 Egern 侧，Surge 仅同步版本号）',
    ],
    ('lazy', 'v1.8'): [
        'AI 服务规则集换源：改用持续滚动维护的上游，覆盖 Gemini 新形态、Sora、Grok 等更多 AI 服务（原源已停更）。',
    ],
    ('lazy', 'v1.9'): [
        '新增本仓自托管 AI 域名整合集（10 个来源合并）：googleapis.com 等伴生域名整域收编，ChatGPT 认证 / 遥测基础设施域名不再漏出 AI 分流。',
        'AI 组由自动测速改为手动选择：AI 服务的账号风控对出口 IP 频繁跳变敏感，手动钉死一条稳定节点更稳妥。',
    ],
    ('routing', 'v1'): [
        '分流版初始发布：按应用分组（ChatGPT / Gemini / Claude / YouTube / Telegram …）+ 地区智能选组。',
        '本版本仅提供 Egern 侧文件。',
    ],
    ('routing', 'v2'): [
        'DNS 段重构：删掉冗余的域名映射与重复兜底规则，上游端点精简为「两机构 × DoH/DoT」矩阵 —— 明文解析通路压到只剩一条且被结构堵死。',
        '防泄露能力经仓库审计脚本逐项实测等价，配置更短更易读。',
    ],
    ('routing', 'v2.1'): [
        '清理仅取默认值的配置键（IPv6 开关、路由兼容选项等），文件更干净，行为不变。',
    ],
    ('routing', 'v2.2'): [
        '机场订阅槽位从 4 个精简到 2 个，订阅占位链接数量减半。',
        'MAX 组改为「低倍率节点智能筛选」：先按倍率过滤、再自动选优。',
    ],
    ('routing', 'v2.3'): [
        'MAX 低倍率筛选修正：原先的正则既误收（10.1 倍率这类名字会命中）又漏收（0.2 / 0.5 等被放过）；改为收录所有 <1 倍率，18 个真实节点样例复验零误判。',
        '修复 ChatGPT / Gemini 组为空导致「导入即断流」的问题：补上默认出口。',
        'Smart 组补节点展开，自动选优从「在几个组之间猜」修正为「节点级测速」。',
    ],
    ('routing', 'v2.4'): [
        '全部 21 条规则集补上每日自动刷新：原先缺省只下载一次、之后不再更新，规则集永远停在旧版本（实测有新收录域名命不中）。',
    ],
    ('routing', 'v3'): [
        '规则段与 Surge 分流版逐行对齐：新增内网直连规则、删除与主规则集重复的 .cn 兜底。',
        'DNS 转发扩为四层：白名单 → 两条广告清单解析期直接拒答 → 兜底，广告在 DNS 层即被拦截。',
        '机场订阅入口合并为单一隐藏槽位；各应用组补齐默认取向（Claude → 台湾、Spotify / YouTube Music → 美区、Microsoft → 直连等）。',
    ],
    ('routing', 'v3.1'): [
        '规则集刷新周期从每天统一放宽为每周（与 Surge 侧对齐），减少无谓的重复拉取。',
    ],
    ('routing', 'v3.2'): [
        '精细化的 no-resolve 取舍：逐个实测各规则集条目构成 —— 零 IP 条目的纯域名集不再写解析开关（写了是空转），真含 IP 条目的必须写（不写会导致额外本地解析）。',
        '新增本仓自托管 Apple 系统服务快照集，补齐 Egern 缺失的内置系统规则。',
        '文件启用首行版本号头注。',
    ],
    ('routing', 'v3.3'): [
        '新增两条占位节点：只填节点不导订阅时，主出口与 AI 两组照样有出口；只导订阅也能跑。',
        'Spotify / YouTube Music 默认出口设为美区（解锁区域以美区为准）。',
        'AI 组默认走独立占位节点，不与主出口混用。',
    ],
    ('routing', 'v3.4'): [
        '订阅占位符数量的说明口径修正（文档性修正，配置行为不变）。',
    ],
    ('routing', 'v3.5'): [
        '新增 Wi-Fi 自动暂停（SSID Setting）：回到可信网络自动停用代理，离开后恢复。（本版改动在 Surge 侧，Egern 仅同步版本号）',
    ],
    ('routing', 'v3.6'): [
        '配置内文档引用路径迁移到仓库新目录结构，分流行为不变。',
    ],
    ('routing', 'v3.7'): [
        '国内域名规则集更名 CN-Domains，客户端日志中更易识别，分流行为不变。（本版改动在 Egern 侧，Surge 仅同步版本号）',
    ],
    ('routing', 'v3.8'): [
        'AI 服务规则集换源：改用持续滚动维护的上游（原 ACL4SSR 源已停更、缺 Gemini 新形态）。',
    ],
    ('routing', 'v3.9'): [
        '新增本仓自托管 AI 域名整合集（266 条 · 10 源合并 · 零 IP 条目）：googleapis.com / googleusercontent.com 整域收编 —— GMS 网关与 ChatGPT 认证 / 遥测基础设施域名不再漏出 AI 分流。',
        '上行换源集继续滚动维护新 AI 域名，本集专管结构稳定的伴生域与宽后缀，分工互补。',
    ],
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

def _blob_birth(root, kern, fam, path):
    """path（仓库内相对路径）所指 blob 首次进入该 profile 历史的提交日期。

    历史重写查不到诞生提交时，兜底取该文件被加入 repo 的日期；再查不到返回 None。"""
    rel = path.replace(os.sep, '/')
    prof = f'{kern}/profiles/{fam}{".conf" if kern == "surge" else ".yaml"}'
    try:
        sha = git('rev-parse', f'HEAD:{rel}')
        log = git('log', '--reverse', '--format=%as', '--find-object=' + sha, '--', prof)
        lines = [l for l in log.splitlines() if l.strip()]
        if lines:
            return lines[0]
    except subprocess.CalledProcessError:
        pass
    try:
        log = git('log', '--diff-filter=A', '--format=%as', '--', rel)
        lines = [l for l in log.splitlines() if l.strip()]
        return lines[-1] if lines else None
    except subprocess.CalledProcessError:
        return None

def version_date(root, kern, fam, ver):
    """该版本内容的诞生日期：归档快照的 blob 在现役 profile 历史中首次出现的提交。

    （旧实现取"归档文件被加入 repo 的提交"= 退役提交，永远晚一个版本 —— 已废弃。）"""
    ext = '.conf' if kern == 'surge' else '.yaml'
    arch = os.path.join(kern, 'profiles', 'config_old', f'{fam}_{ver}{ext}')
    return _blob_birth(root, kern, fam, arch)

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
                date = _blob_birth(root, kern, fam, os.path.relpath(full, root)) if entry['is_current'] \
                    else version_date(root, kern, fam, ver)
                entry['kerns'][kern] = {'full': os.path.relpath(full, root), 'min': os.path.relpath(mn, root),
                                        'date': date}
            dates = sorted({i['date'] for i in entry['kerns'].values() if i and i['date']})
            entry['date'] = dates[0] if dates else None
            plan.append(entry)
    return plan

def asset_name(path):
    """固定名四件脸：归档原名（lazy_v1.8.conf）剥掉版本段（→ lazy.conf）。"""
    return re.sub(r'_(v\d+(?:\.\d+)?)', '', os.path.basename(path))

def release_title(e):
    """Release 标题：emoji + 分工 + 诞生日期 + 主题句（版本号由 tag 芯片承载）。"""
    emoji, headline = HEADLINES.get((e['family'], e['version']),
                                    ('📦', f"{FAM_CN[e['family']]} {e['version']}"))
    date = e.get('date') or '早期版本'
    return f'{emoji} {FAM_CN[e["family"]]} · {date} · {headline}'

def build_notes(e):
    """Release 说明（面向公众的产品更新日志）。

    顺序：更新内容 → 下载按钮 → 元信息小字。分工与日期在标题里（release_title），
    分工在按钮上也有；本函数只写内容与元信息，不再重复标题/按钮已有的信息。
    版本号只由 tag 芯片承载。"""
    fam, ver, tag = e['family'], e['version'], e['tag']
    kerns = [k for k in ('surge', 'egern') if e['kerns'][k]]
    notes = PUBLIC_NOTES.get((fam, ver), [])
    if isinstance(notes, str):
        notes = [notes]
    lines = list(notes)
    if lines:
        if len(lines) > 1:
            lines = [f'- {n}' for n in lines]
        lines.append('')
    buttons = []
    for kern in ('surge', 'egern'):
        if kern not in kerns:
            continue
        name = asset_name(e['kerns'][kern]['full'])
        buttons.append(f'[![Download {KERN_LABEL[kern]} {fam}]({badge_url(kern, fam)})]({DL}/{tag}/{name})')
    if buttons:
        lines += [' '.join(buttons), '']
    meta = '当前版本 · 内容与 raw/main 订阅地址一致' if e['is_current'] \
        else '历史版本 · 仅供回滚对照，日常使用请选最新版'
    meta += ' · .min 与完整文件见本页底部 Assets'
    missing = [k for k in ('surge', 'egern') if k not in kerns]
    if missing:
        meta += f'。本版本仅提供 {KERN_LABEL[missing[0]]} 侧文件（历史缺口，如实保留）'
    lines.append(f'<sub>{meta}</sub>')
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
                             {'tag_name': tag, 'target_commitish': 'main', 'name': release_title(e),
                              'body': build_notes(e),
                              'make_latest': 'true' if e['is_current'] else 'false'}) as r:
                    rel = json.load(r)
                created.append(tag)
            # 幂等 reconcile：已存在的 Release 标题/说明与当前模板不一致就回写
            # （模板改版 / 摘要修订都靠这一步落到既有 Release 上）
            new_body = build_notes(e)
            new_name = release_title(e)
            patch = {}
            if (rel.get('body') or '') != new_body:
                patch['body'] = new_body
            if (rel.get('name') or '') != new_name:
                patch['name'] = new_name
            if patch:
                api_req(f"{API}/releases/{rel['id']}", token, 'PATCH', patch)
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
