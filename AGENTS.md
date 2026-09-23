# 🤖 AGENTS.md · 给 AI agent 的开工说明

> 你在一个**公开的配置模板仓**里干活。这份文件是给你写的，不是给人写的，所以只列约束和动作。
> 人读的详解在 [`docs/`](docs/)，配置领域知识在 [`skill/SKILL.md`](skill/SKILL.md)。

## 0 · 先分清你在做哪类任务

| 任务 | 入口 | 有没有闸 |
|:-----|:-----|:---------|
| **A. 改这个仓**（profile / 脚本 / 文档 / 规则集指向） | 本文件 + [`docs/注意事项.md`](docs/注意事项.md) | **有**，见 §1，改完必须跑 |
| **B. 帮用户排查真实设备的 DNS / 分流问题** | [`skill/SKILL.md`](skill/SKILL.md)（按内核分支，别凭记忆答语法） | 无，但**先定内核**：Surge 与 Egern 模型不通用 |

## 1 · 改完的固定动作（这是本仓唯一的验收）

```bash
bash skill/tests/all.sh            # 四项检查；离线用 --offline
```

末行的三个数就是「线上线下是否一致」，**必须全 0**：

```
未提交 0 个文件 · HEAD=<sha> · 上游 origin/main：落后 0 · 未推送 0
```

然后 `git add -A && git commit && git push`。跑不绿就别推。
退出码口径：`0` 全绿 / `1` 判据失败 / `2` 环境或前置不达标（**没跑成不等于跑绿**）。

四项分别守：Surge 六阶段回归 · Egern 两阶段回归 · `.min` 与完整版去注释对拍 ·
换设备可移植性（行尾 / BOM / 命名 / 单机残留，**固定 18 条规则**）。

## 2 · 四条硬约束（agent 最常在这里犯错）

1. **不要加 CI / GitHub Actions / workflow。** 这是维护者的决定，记录在
   [`docs/跨内核差异对照.md`](docs/跨内核差异对照.md) 与 [`docs/注意事项.md`](docs/注意事项.md)：
   检查只以「本地一条命令」的形态存在仓里。
2. **不要去引用、依赖或克隆 `RiverFlowsInUUU/Surge`、`RiverFlowsInUUU/Egern` 这两个前身仓。**
   本仓完全独立，把它们当已弃用。内容需要就自己写在本仓里。
   （**规则集引用第三方社区仓库是允许的**，那是公共资源，不在此列。）
3. **不要为了「行尾对不上」去改任何人的 git 配置。** 字节层由仓根
   [`.gitattributes`](.gitattributes) 的 `* text=auto eol=lf` 钉死，优先级高于 `core.autocrlf`。
   若在 Windows 上 `git status` 干净但磁盘仍是 CRLF ⇒ 那是**老克隆**的一次性问题，解法见 §4。
4. **看到某个配置「好像不对」，先在文件里 grep `audit-waive`。** 明知故犯的地方都在 profile 头部
   留了豁免条目和理由，审计脚本的注释里也写了取舍。例：Surge 的 `encrypted-dns-server` 保留
   `dns.google` / `dns.alidns.com` 两条主机名端点是有意的（CDN 就近与 ECS 合规），不是泄露。

## 3 · 目录速查

| 路径 | 是什么 | 改了它要顺手改什么 |
|:-----|:-------|:-------------------|
| `surge/profiles/` · `egern/profiles/` | 订阅文件（`.conf` / `.yaml`，各有 `.min` 形态） | `.min` 与完整版由第 3 项对拍；升版走 §5 |
| `skill/` | 配置领域技能包：`skill/SKILL.md` + `skill/reference/` + `skill/scripts/` | 触发词表与 `agent_created` 头**别乱动**，是靠它被检索的 |
| `skill/scripts/` · `skill/tests/` | 审计脚本与回归判据 | 新增判据要把读数写进 `surge/docs/08-审计读数.md` 与 `egern/docs/08-审计读数.md` |
| `docs/` | 人读的六篇详解（跨设备一致性、差异对照、体检报告…） | 相对链接由 Surge 侧阶段 6 全仓校验 |
| `icons/` | 26 个策略组图标（两内核共用） | 路径**必须纯 ASCII**（`skill/tests/check_portability.py` 的 `N6`），别新加中文名 |

## 4 · 换到一台新机器只做三件事

```bash
git clone https://github.com/RiverFlowsInUUU/Self-Configuration.git
git config --global user.name  "你的名字"
git config --global user.email "你的邮箱"
```

推送凭据用 `gh auth login` 或 Git 凭据管理器。**token 不进仓内任何文件，也不写进 remote URL。**

`.gitattributes` 不回头改写已在磁盘上的文件 ⇒ **今天之前 clone 的旧目录** pull 之后磁盘可能仍是 CRLF
（而 `git status` 干净，属隐形差异）。一次修好：`git rm -r --cached . && git reset --hard`，
或直接删掉重 clone。详见 [`docs/注意事项.md`](docs/注意事项.md) 的「换设备 / 双端一致」。

## 5 · 升版只改一行 + 一个脚本

「当前推荐版」在三处 runner 里是**承诺值** `CURRENT="${CURRENT:-routing_v3.1}"`，不靠推导最大版本号。
机械部分交给 `python skill/tests/bump_version.py <旧> <新>`（默认只出计划，`--apply` 才写盘，`--gate` 跑 §1）。
散文（CHANGELOG、版本沿革、写死的断言数）由它列成清单交给人，**脚本不猜**。

## 6 · 想知道「为什么是这样」

- [`docs/跨内核差异对照.md`](docs/跨内核差异对照.md) §8 —— 本仓相对两个前身仓的全部刻意差异与理由
- [`docs/体检报告.md`](docs/体检报告.md) —— P1–P11 的问题记录，含**被实测推翻的原结论**
- [`docs/技能包合并与自包含.md`](docs/技能包合并与自包含.md) —— `skill/SKILL.md` 为什么长这样
- [`docs/注意事项.md`](docs/注意事项.md) —— 动手前读，含改配置 / 改判据 / 换设备的边界
