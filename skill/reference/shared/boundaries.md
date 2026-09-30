# 边界手册 · 例外与已论定

> **用途**：回答「**这处算不算例外 / 这个为什么不做**」——防止下一轮审查把**已论定的裁定**当成**新发现的缺陷**重报（实例：`probe` 系列被外审两轮误报为「不走四态协议」的例外，实为四态协议的规范用户）。
> **纪律**：本页**只放仓里没有家的内容**；有原件的只写一行指针，**不复述论证**（复述 = 制造第二份要同步的副本）。
> **每条必须带「重议条件」**：只写「不要再报」而无条件 = 禁止质疑，比没有清单更危险。
> **体量上限 40 行** —— 超了说明它在复制正文，那它自己就变成了新的漂移面。

## 1 · 例外清单（不适用，不是缺陷）

| 对象 | 为什么是例外 | 重议条件 |
|:-----|:-------------|:---------|
| `skill/scripts/release_publish.py` | 发布器，**刻意不套四态退出码** —— 读不到远端只影响「要不要多 PATCH 一次」，不是「未能验证」 | 引入需要 SKIP 语义的新发布流程 |
| 非 GitHub 的请求点：`egern/probe_dns_endpoints.py`、`egern/probe_doh.py`、`egern/_egern_common.py`、`surge/audit_ruleset_content.py` | 不走 `check_releases._api_json` 那套 **GitHub 请求异常分类**（各自处理自身网络失败）。⚠️ 这与**四态协议无关** —— `probe_dns_endpoints.py` 恰是四态协议的**规范用户**（缺参 → 2、有失效 → 1、`sys.exit(main())`） | 出现第二个消费 GitHub API 的脚本（须共用 `_api_json`） |
| Clash / mihomo / Shadowrocket / sing-box 等其它内核 | 本仓只覆盖 Surge + Egern 两内核；`no-resolve`、`dns-server`、`fake-ip-filter` 在三者语义各不相同 | 新增内核分支 |

## 2 · 已论定清单（裁定 ｜ 依据指针 ｜ 重议条件）

| 裁定 | 依据指针 | 重议条件 |
|:-----|:---------|:---------|
| 不做 `env_check.py` / `requirements.txt`（「错误信息即体检」） | 本页（仓内无其它原件） | 出现第一起「环境不达标但报错不足以定位」的事故 |
| 不做 GitHub API 合并拉取 / 结果缓存 | 本页 | releases 闸门耗时或限流成为真实瓶颈 |
| 不把各闸门「结论行」统一成机器可读一行式 | 本页 | 出现需要机器解析结论行的下游消费者 |
| SKIP 独立占码 3 ／ **2 的准入** = 本地前置检查（禁止把远端 HTTP 码翻译成 2）／ 404 语义分档 | [`troubleshoot-faq.md`](troubleshoot-faq.md) §8.2 | 改动退出码协议本身时（同步 §8.2） |
| `release_publish` 的 `/releases/latest` 不套四态 | `skill/scripts/release_publish.py` 就近注释 | 同「例外清单」第 1 行 |
| 不做 E（AST 闸门 `check_exit_codes`） | `skill/SKILL.md` §3 其他共享纪律 | 见该处「推翻挂账的触发条件」 |
| 不做闸门清单的机器对账（`ci.yml` ↔ `verify_all.py`） | `skill/tests/verify_all.py` 头注 | 见该处「推翻挂账的触发条件」 |
| P5 `MyHome` 是**误报关闭**（照官方示例留的占位网络名），非缺陷 | [`ops.md`](ops.md) ／ [`cross-kernel-diff.md`](cross-kernel-diff.md) | 官方示例改名、或该段被实际启用时 |
| Egern 审计**跨 profile 输出折叠**（约省 3 KB）不做 | `skill/reference/egern/checker.md`（记 22 离线 / 24 联网） | 该处不再引用这组条数时 |
| 历史 release notes（`release_publish.PUBLIC_NOTES`）保留**发布当时**的条数，不回改 | 该值记录发布时点的事实（v3.9 条目即此例）；自 v2.0.1／v4.0.1 起新条目已改为「当前版本信息统一只保留在文件头注」 | 需修订历史记录本身（发布勘误） |

## 3 · 不是缺陷的边界

- **审计通过 ≠ 配置可用**：脚本只覆盖**静态可判定**的部分；拦截效果、误杀、节点可用性必须实测（[`../../SKILL.md`](../../SKILL.md) §3）。
- 文档里的条数是**写作时点的约数**，随上游规则集漂移 —— 要精确值现跑脚本（同 §3「任何条数一律现抓」）。**本仓自托管集（`rules/AI.list`）的条数真源 = 该文件头部档案的自动合计行**（由生成器算出，勿手抄）。
