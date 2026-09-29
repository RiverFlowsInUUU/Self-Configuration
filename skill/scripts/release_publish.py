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
# 文风 = 面向用户的正式产品语言（参考 Apple 更新说明）：专业、克制、通俗，不用文言腔。
HEADLINES = {
    ('lazy', 'v1.0'): ('🚀', '首次公开发布'),
    ('lazy', 'v1.1'): ('📝', '规则注释说明更新'),
    ('lazy', 'v1.2'): ('🛫', '新增订阅槽位'),
    ('lazy', 'v1.3'): ('📶', 'Wi-Fi 自动暂停'),
    ('lazy', 'v1.4'): ('📚', '文档路径修正'),
    ('lazy', 'v1.5'): ('📚', '文档结构迁移'),
    ('lazy', 'v1.6'): ('🧹', '广告组与 Apple 规则优化'),
    ('lazy', 'v1.7'): ('🏷️', '规则集更名为 CN-Domains'),
    ('lazy', 'v1.8'): ('🔄', 'AI 规则集更换新源'),
    ('lazy', 'v1.9'): ('🧩', '自托管 AI 域名整合'),
    ('routing', 'v1'): ('🚀', '分流版首次发布'),
    ('routing', 'v2'): ('🛡️', 'DNS 配置重构与防泄露强化'),
    ('routing', 'v2.1'): ('🧹', '配置精简'),
    ('routing', 'v2.2'): ('🛫', '订阅槽位精简与 MAX 智能筛选'),
    ('routing', 'v2.3'): ('🛠️', '修复分组断流与筛选误判'),
    ('routing', 'v2.4'): ('⏱️', '规则集支持每日自动更新'),
    ('routing', 'v3'): ('🧭', '规则体系与 Surge 全面对齐'),
    ('routing', 'v3.1'): ('⏱️', '规则集更新周期调整为每周'),
    ('routing', 'v3.2'): ('🔬', '解析策略优化与新增系统快照集'),
    ('routing', 'v3.3'): ('👥', '新增占位节点与默认出口'),
    ('routing', 'v3.4'): ('📝', '订阅说明修正'),
    ('routing', 'v3.5'): ('📶', 'Wi-Fi 自动暂停'),
    ('routing', 'v3.6'): ('📚', '文档结构迁移'),
    ('routing', 'v3.7'): ('🏷️', '规则集更名为 CN-Domains'),
    ('routing', 'v3.8'): ('🔄', 'AI 规则集更换新源'),
    ('routing', 'v3.9'): ('🧩', '自托管 AI 域名整合'),
}

# 公众向更新摘要（Release 页是产品对外的更新日志，不搬运内部 commit subject）。
# 键：(family, version)，值 = 要点列表（1~4 条，逐版本如实总结，禁止模板句复用）。
# 内容依据 = config_old 相邻版本快照的逐行 diff（行为改动 + 有意义的注释修正）。
# 文风 = 面向用户的正式产品语言（参考 Apple 更新说明）：完整句子、专业、克制、通俗；
# 不用文言腔（口径修正/收编/压到最小/上线），不搬内部过程语言。
# 发新版本前必须先在此补一组 —— 动线⑦的一部分。
PUBLIC_NOTES = {
    ('lazy', 'v1.0'): [
        '首次发布。内置订阅槽位与占位节点，导入后填入订阅即可使用。',
        '内置完整分流规则：广告拦截、AI 服务分流、系统与国内域名直连。',
        'DNS 全链路加密解析。',
    ],
    ('lazy', 'v1.1'): [
        '更新了配置内的注释说明：国内直连规则集的条数不再标注固定数字，因为上游每周更新，固定数字很快会过期。分流行为无变化。',
    ],
    ('lazy', 'v1.2'): [
        '新增订阅槽位：填入机场订阅链接后，节点会自动加入主出口与 AI 分组。',
        '精简了示例节点，保留两条占位节点（主出口与 AI 各一条）。',
        '仅填订阅或仅填节点均可正常使用。',
    ],
    ('lazy', 'v1.3'): [
        '新增 Wi-Fi 自动暂停（SSID Setting）：连接到可信网络时自动停用代理，离开后自动恢复。此改动仅涉及 Surge。',
    ],
    ('lazy', 'v1.4'): [
        '修正了配置内的文档引用路径。分流行为无变化。',
    ],
    ('lazy', 'v1.5'): [
        '文档引用路径已迁移至仓库的新目录结构。分流行为无变化。',
    ],
    ('lazy', 'v1.6'): [
        '广告拦截组移除了多余的 DIRECT 备选项，保持默认拦截、可手动放行。',
        'Apple 系统服务规则集改为使用本仓库自托管的快照，两个内核使用同一来源。',
    ],
    ('lazy', 'v1.7'): [
        '国内域名规则集更名为 CN-Domains，在客户端日志中更易识别。分流行为无变化。此改动仅涉及 Egern，Surge 仅同步版本号。',
    ],
    ('lazy', 'v1.8'): [
        'AI 服务规则集更换为持续维护的上游，新增覆盖 Gemini、Sora、Grok 等服务。原上游已停止更新。',
    ],
    ('lazy', 'v1.9'): [
        '新增自托管 AI 域名整合集（合并 10 个来源）：googleapis.com 等伴生域名整体纳入 AI 分流，ChatGPT 认证与遥测相关域名不再遗漏。',
        'AI 分组由自动测速改为手动选择：AI 服务对出口 IP 频繁变化较为敏感，固定节点使用更稳定。',
    ],
    ('routing', 'v1'): [
        '分流版首次发布：按应用分组（ChatGPT、Gemini、Claude、YouTube、Telegram 等），并支持地区智能选组。',
        '此版本仅提供 Egern 侧文件。',
    ],
    ('routing', 'v2'): [
        '重构 DNS 配置：移除冗余的域名映射与重复的兜底规则，上游端点精简为两个机构的 DoH / DoT 组合，明文解析通路仅保留一条。',
        '防泄露能力经审计脚本逐项验证，配置更简短、更易读。',
    ],
    ('routing', 'v2.1'): [
        '移除仅使用默认值的配置项（IPv6 开关、路由兼容选项等）。行为无变化，文件更简洁。',
    ],
    ('routing', 'v2.2'): [
        '机场订阅槽位由 4 个精简至 2 个。',
        'MAX 分组改为低倍率节点智能筛选：先按倍率过滤，再自动选择最优节点。',
    ],
    ('routing', 'v2.3'): [
        '修正 MAX 低倍率筛选：此前的规则会误收部分高倍率节点、同时遗漏低倍率节点，现改为收录所有低于 1 倍率的节点，并经 18 个真实节点样例验证。',
        '修复 ChatGPT、Gemini 分组为空时导入后断流的问题，已补充默认出口。',
        'Smart 分组补齐节点展开，自动选择改为节点级测速。',
    ],
    ('routing', 'v2.4'): [
        '为全部 21 条规则集补充每日自动更新：此前仅在首次下载后不再更新，导致新收录的域名无法命中。',
    ],
    ('routing', 'v3'): [
        '规则段与 Surge 分流版逐行对齐：新增内网直连规则，移除与主规则集重复的 .cn 兜底。',
        'DNS 转发扩展为四层：白名单、两条广告清单在解析阶段直接拒答，再到兜底，广告在 DNS 层即被拦截。',
        '机场订阅入口合并为单一隐藏槽位，并为各应用分组补充默认取向（Claude 至台湾、Spotify 与 YouTube Music 至美区、Microsoft 直连等）。',
    ],
    ('routing', 'v3.1'): [
        '规则集更新周期由每天调整为每周，与 Surge 侧保持一致，减少不必要的重复下载。',
    ],
    ('routing', 'v3.2'): [
        '逐条实测并优化各规则集的 no-resolve 设置：纯域名规则集不再写入解析开关；包含 IP 条目的规则集则必须写入，以避免额外的本地解析。',
        '新增自托管 Apple 系统服务快照集，补齐 Egern 缺失的内置系统规则。',
        '文件启用首行版本号标注。',
    ],
    ('routing', 'v3.3'): [
        '新增两条占位节点：仅填节点时主出口与 AI 分组同样可用，仅填订阅也可正常运行。',
        'Spotify 与 YouTube Music 的默认出口设为美区。',
        'AI 分组默认使用独立占位节点，不与主出口共用。',
    ],
    ('routing', 'v3.4'): [
        '修正了订阅占位符数量的说明。此为文档性修正，配置行为无变化。',
    ],
    ('routing', 'v3.5'): [
        '新增 Wi-Fi 自动暂停（SSID Setting）：连接到可信网络时自动停用代理，离开后自动恢复。此改动仅涉及 Surge，Egern 仅同步版本号。',
    ],
    ('routing', 'v3.6'): [
        '配置内的文档引用路径已迁移至仓库的新目录结构。分流行为无变化。',
    ],
    ('routing', 'v3.7'): [
        '国内域名规则集更名为 CN-Domains，在客户端日志中更易识别。分流行为无变化。此改动仅涉及 Egern，Surge 仅同步版本号。',
    ],
    ('routing', 'v3.8'): [
        'AI 服务规则集更换为持续维护的上游。原 ACL4SSR 源已停止更新，且缺少 Gemini 相关域名。',
    ],
    ('routing', 'v3.9'): [
        '新增自托管 AI 域名整合集（266 条，合并 10 个来源）：googleapis.com、googleusercontent.com 等伴生域名整体纳入，GMS 网关与 ChatGPT 认证、遥测相关域名不再遗漏。',
        '上游换源集继续滚动维护新增的 AI 域名，本集合负责结构稳定的伴生域与宽后缀，两者分工互补。',
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
    版本号只由 tag 芯片承载。
    行距：GitHub 会剥掉正文里的 CSS，无法真正设 line-height；用列表项之间空一行
    （GFM 渲染为松散列表）让多条要点之间留白变宽，作为近似。"""
    fam, ver, tag = e['family'], e['version'], e['tag']
    kerns = [k for k in ('surge', 'egern') if e['kerns'][k]]
    notes = PUBLIC_NOTES.get((fam, ver), [])
    if isinstance(notes, str):
        notes = [notes]
    lines = []
    for n in notes:
        lines += [f'- {n}', '']
    buttons = []
    for kern in ('surge', 'egern'):
        if kern not in kerns:
            continue
        name = asset_name(e['kerns'][kern]['full'])
        buttons.append(f'[![Download {KERN_LABEL[kern]} {fam}]({badge_url(kern, fam)})]({DL}/{tag}/{name})')
    if buttons:
        lines += [' '.join(buttons), '']
    meta = '当前版本，与仓库订阅地址内容一致' if e['is_current'] \
        else '历史版本，仅供回滚使用；日常使用请选择最新版本'
    meta += '。.min 精简版与完整文件见页面底部的 Assets'
    missing = [k for k in ('surge', 'egern') if k not in kerns]
    if missing:
        meta += f'。此版本仅提供 {KERN_LABEL[missing[0]]} 侧文件（历史缺口，如实保留）'
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
