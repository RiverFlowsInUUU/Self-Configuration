# 公开模板仓库（本项目的对外交付物）

> 本文是 [`SKILL.md`](../../SKILL.md) 的引用文件。 **何时读**：要更新模板 / 了解公开仓库结构时。

---

自用配置已脱敏发布为公开模板 + 文档 + 本 skill：

**https://github.com/RiverFlowsInUUU/Self-Configuration**（Egern 分支在 `egern/`，与 Surge 版同仓）

```
README.md                                   # 门面：四份订阅地址 + 分组表 + DNS 防泄露对照 + 文档导航
CHANGELOG.md                                # **唯一一份**改动记录：只记两内核配置文件的修改（文档与脚本改动看 git log）
LICENSE · .gitattributes · .gitignore
icons/                                      # 26 个 PNG —— 两内核共用
docs/                                       # ★ 共享文档（九篇，2026-09-27 精简后）：quick-start · dns-basics · hardening-checklist ·
                                            #   no-resolve-pairing · cross-kernel-diff · rulesets · icon-license · ops · troubleshoot-faq
skill/                                      # 本 skill：SKILL.md（§0 判内核 → 分支 A/B）
  reference/{surge,egern}/ · scripts/{surge,egern}/ · tests/（check_secrets · check_portability · check_min_pair · check_links · make_min）
egern/profiles/lazy.yaml / lazy.min.yaml          # 懒人版 · 可选（4 组 / 10 条规则；隐藏订阅槽位 Airport）
egern/profiles/routing.yaml / .min.yaml           # 分流版 · 推荐（脱敏模板：2 条占位节点 + 1 个机场槽位，凭据与订阅均为占位符）
egern/apple_system.list                           # 本仓自托管的 Apple 系统域名规则集
egern/DetailsReadme/DetailsReadme.md              # 完整技术文档（逐键语义）
.github/workflows/ci.yml                          # 最小 CI：五项检查（push / PR 自动）
```

> ⚠️ **合并带来的四处职责变化**：① 首页只有根目录那**一份**；② 「注意事项 / 图标与许可 /
> 规则集与来源」三篇升到共享 `docs/`，要改这三件事去那一份，**不要**在内核目录里另起一篇；
> ③ 新增 [`docs/cross-kernel-diff.md`](../../../docs/cross-kernel-diff.md) ——
> 凡「Egern 的结论搬到 Surge」之类的问题，答案写在那一篇里；
> ④ **改动记录只有根 `CHANGELOG.md` 一份** —— 更早的历史看 git（备份 tag：`pre-cleanup-20260927`）。


> **可选版本只有两个** —— `routing`（分流版 · 推荐）与 `lazy`（懒人版），文件名不带版本号；
> 当前是第哪一版写在头注 `#! version=` 里；历史版本看 git（备份 tag：`pre-cleanup-20260927`）。

**要更新模板时**：**直接在仓库里改 `profiles/*.yaml` 即可。** 这份模板早已完成脱敏
（2 条占位节点 + 1 个占位订阅，全都连不出去，无真实证书），改它不需要"从自用配置重新生成"。改完跑
检查命令清单见 [`skill/README.md`](../../README.md)（CI 与本地同组命令），再提交推送。

> 📦 **历史做法（已不再使用）**：早期由维护者本地的 `outputs/` 脚本链生成 ——
> `_build_public_template.py`（从自用版做**带断言的行级替换** + 38 个敏感串零残留自检）、
> `_transform_template.py`、`_make_min.py`（由带注释版生成纯配置版）、`_fetch_icons.py`、
> `_publish_to_github.py`（Git Data API 单次提交；空仓库需先落初始化提交，
> 否则 `POST /git/blobs` 报 `409 Git Repository is empty`）。
> ⚠️ 这些脚本**不在本仓库**（避免暴露构建侧私人路径）—— 2026-09-21 核查时**本机也已找不到**。
> 换句话说"不要手改仓库里的 yaml"这条老规矩**已作废**：现在的 `routing_v2.1` / `routing_v2.2` / `routing_v2.3` / `routing_v2.4` / `routing_v3` / `routing_v3.2`
> 就是在仓库里直接改出来的。若将来要恢复"从自用配置生成"的流程，方法论见 skill
> `github-publish-sanitized-repo`，需按它重建脚本。

📌 **验证 = CI（`.github/workflows/ci.yml`，push / PR 自动）+ 本地同组命令复现。**
命令清单见 [`skill/README.md`](../../README.md)；探针 / 量测类脚本（`probe_*` / `weigh_*` / `profile_ruleset`）不在验证链上，是手工工具。

**脱敏清单（这五类必须洗）**：节点 server/凭据/sni/reality 公钥 → 占位；
机场订阅 URL（含 token）→ 占位；`mitm.ca_p12` + `ca_passphrase`（个人 CA 私钥）→ **注释掉**；
机场组名/节点名 → `Airport-A` / `Node-1`；`dns.forward` 里的**节点域名** → `example-node.com`。

---

## README 的边界：只讲产品，不讲改动过程

README 是**产品介绍** —— 读者要知道「这东西是什么、怎么用」。以下三类**不属于**它：

- 🚫 **归类 / 设计自述** —— 「某组为什么不算开关」「**上面是分类顺序**」这类解释我们怎么想的话。
- 🚫 **与评审 / 工单的对话** —— 「原写 X 属误标，已按功能拆开」。
- 🚫 **内部判据与断言名** —— 「由某脚本某断言守着」。

该放哪：**改动记录 → 根 [`CHANGELOG.md`](../../../CHANGELOG.md)（唯一一份）；判据与原理 → [`DetailsReadme/`](../../../egern/DetailsReadme/DetailsReadme.md) 或 [`docs/`](../../../docs/)。**

**日志体例（2026-09-24 定 · 2026-09-27 收窄为只记配置）**：① 只记两内核 `profiles/`（含 `.min`）与它们引用的
规则集素材，文档、脚本与判据的改动看 `git log`；② **一天一段**，当天后续改动往那段里增补，不开第二个同名日期段，
没动配置文件就不开段；③ 一条一句、动词开头，写清改到哪个文件、改了哪个行为，不写「哪里没动」与「验收」，
推理与自我辩护都不进日志 —— 自查：**删掉这句，事实会少吗？不会就删。**

**自查**：README 里出现「为什么…」「不算」「误标」「判据」「原写」「上面是…顺序」，
八成就是改动记录漏出来了。**挪走，别只删** —— 判据必须仍能在 `DetailsReadme` 里查到。

同一事实要用**使用者视角的性质**表述：`不被规则引用`（内部判据）→ `独立于规则链路`（读者能懂）。

实测反例（2026-09-22）：在 README 里补「我们为什么这样归类 / 上面是分类顺序」这类说明，
用户一句打回 —— 「readme 是产品介绍，不是自说自话的地方」。

---

## 首页不列规则集

规则集属**实现侧**：用了哪些 `.list`、从哪个仓库拉、顺序怎么排。使用者关心的是**分流结果**。

| | 首页（`README.md`） | 组件页（`docs/`） |
|:--|:--|:--|
| 顺序表 | 「匹配什么 → 去向」（白名单 / 广告 / 按应用 / 国内…） | 逐条列出规则集名与参数 |
| 规则集清单 | ❌ 一个都不出现 | ✅ 文件名 · 去向 · 来源 URL |
| 来源仓库 | ❌ | ✅ 含图标、数据库、许可 |

**判据**：首页上这句话，对读者**用**这份配置有没有帮助？
「`OpenAI.list` → `ChatGPT`」没有意义 —— 使用者不能按规则集文件名分流；
「ChatGPT 走 `ChatGPT` 组，面板上可改道」才有意义。

实测（2026-09-22）：首页原挂着「📚 规则来源」段 + 「分流版的应用规则」表 + 「排序约束」，
用户连判两次 —— 先要求来源段下沉，随即补充：「不仅是规则集的来源，而且是有哪些规则集……
我认为都没必要放在首页的 README 里面。」处理后新开
[`docs/rulesets.md`](../../../docs/rulesets.md) 承接全部规则集信息，
首页只在「📖 按需查阅」表里留一个链接（原「文件结构 / 更多文档」两节已于 2026-09-25 合并为一）。

闸门：`verify_readme_tone.py`（维护者本地的装配闸门，按仓库惯例不进公开仓）的「首页无规则集文件与来源仓库」一项
（匹配 `*.list` / `*.txt` / `*.mmdb` / `*.mrs`、`GEOIP` / `GEOSITE`、来源仓库 owner）。
⚠️ 只对**配置模板仓**生效 —— `jinx` 本身是规则集仓，README 讲规则集是它的产品，不适用这条。
