# skill · 双内核 DNS 加固技能包

这份目录是**给 agent 用的技能包**，也是人查判据的地方。它把原来两个仓库各自的 `skill/` 合成一个入口，
内部按内核分支，共享的判定纪律收在门面里。

## 结构

```
SKILL.md                  单一入口：门面（内核判定 · 五类泄露面 · 四条铁律 · 共享纪律）
                          + 分支 A · Surge 正文 + 分支 B · Egern 正文
reference/surge/*.md      深度主题 ×6（Surge 侧）
reference/egern/*.md      深度主题 ×6（Egern 侧）
scripts/surge/            4 个审计脚本 + _surge_common.py
scripts/egern/            9 个审计/探测脚本 + _egern_common.py
tests/surge/              run.sh · architecture.sh · check_links.py · 3 fixture + fixtures/
tests/egern/              run.sh · 5 fixture
```

六个主题在两侧同名，按需读取（每个文件开头都写了「何时读」）：

| 主题 | 何时读 |
|:-----|:-------|
| `hardening-template.md` | 要产出一份加固后的配置时 —— 逐段模板 + 逐行理由 |
| `pitfalls.md` | 排查实际泄露、或改动判据 / 规则集之前 —— 事故复盘 |
| `leak-localization.md` | 用户报「leak test 显示某运营商」时 —— 网络侧实测流程 |
| `checker.md` | 跑审计脚本前（命令与环境要求）、或要改判据时（判据演进史） |
| `ruleset-weight.md` | 用户问「规则集是不是太重」时 |
| `public-repo.md` | 要更新模板 / 了解仓库结构时 |

## 为什么不把两份正文压成一份

两侧的 `SKILL.md` 是**同构但独立写成**的平行文档（实测逐行比对：同名章节重合度 0–4%，
`reference/` 六篇同样几乎不重复）。压缩合并必然丢细节，而这里的细节大多是拿真实事故换来的判据。

所以本技能包的合并发生在**门面层**：五类泄露面的归并、四条通用铁律、语法映射、不可套用清单——
这些是真正共享的方法论；内核正文逐字保留。逐项依据见
[`../docs/跨内核差异对照.md`](../docs/跨内核差异对照.md)。

## 跑测试

脚本接收 profile 路径作为参数，不依赖当前目录，但测试入口按仓库结构定位，**在仓库根目录执行**：

```bash
bash skill/tests/surge/run.sh                  # Surge：6 阶段 · 15 断言
bash skill/tests/surge/architecture.sh         #        占位符 / 凭据 / .conf↔.min 一致性
bash skill/tests/egern/run.sh                  # Egern：阶段 1 · 5 fixture；阶段 2 · 全部 profile
SKIP_NET=1 bash skill/tests/surge/run.sh       # 跳过需要联网的阶段
```

环境要求：Python 3；Egern 侧脚本需要 `PyYAML`（缺失时部分脚本会退化，见 `reference/egern/checker.md`）。
Windows 的 Git Bash 下脚本会自动用 `cygpath -w` 转换路径，无需干预。

> 🔒 本仓库**刻意不挂 CI**。审计的意义在于改动后真跑一遍，而不是让它挂在网页上变绿——
> 何况「审计全绿 ≠ 配置可用」是这两个项目共同的第一教训。

---

相关：[`../README.md`](../README.md) · [`../docs/跨内核差异对照.md`](../docs/跨内核差异对照.md) · [`../docs/注意事项.md`](../docs/注意事项.md)
