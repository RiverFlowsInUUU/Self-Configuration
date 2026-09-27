# skill/ · 审计脚本与 agent 技能包

本目录是仓库的**工具层**：给 AI agent 的内核知识包（`SKILL.md` + `reference/`），
和一套对两内核 profile 做静态审计的脚本（`scripts/`）。人读的操作文档在 [`docs/`](../docs/)。

```
skill/
├── SKILL.md                  # agent 技能包门面：§0 判内核 → 分支 A(Surge) / 分支 B(Egern)
├── README.md                 # 本文件
├── reference/{surge,egern}/  # 深度主题各一侧：checker · pitfalls · hardening-template · public-repo · leak-localization · ruleset-weight
├── scripts/{surge,egern}/    # 审计脚本（Surge 6 / Egern 11，各含一个共享模块）
└── tests/                    # 四项共享检查：check_secrets · check_portability · check_min_pair · check_links；make_min 为 `.min` 生成器
```

## 检查怎么跑

CI（根 `.github/workflows/ci.yml`）在每次 push / PR 自动跑；本地复现同组命令：

```bash
python skill/tests/check_secrets.py                    # 占位符 / 凭据扫描（全仓 .conf + .yaml）
python skill/tests/check_portability.py                # 行尾 / BOM / 命名 / 单机残留
python skill/tests/check_min_pair.py                   # 固定名四件 + 两侧版本一致
python skill/tests/check_links.py .                    # 全仓 markdown 链接与锚点
python skill/scripts/surge/check_surge_dns.py surge/profiles/lazy.conf surge/profiles/routing.conf
python skill/scripts/egern/check_egern_dns.py egern/profiles/lazy.yaml egern/profiles/routing.yaml
python skill/tests/make_min.py                         # 计划模式：四份 .min 应全部「已同步」
```

环境：Python 3（Egern 侧脚本需 PyYAML）。退出码 `0` 全过 · `1` 有判负 · `2` 前置不达标。

## 改动动线

改 profile → `make_min.py` 重建 `.min` → 跑上面一组 → 提交推送（CI 再跑一遍）。
流程细节见 [`docs/ops.md`](../docs/ops.md)「日常维护」。

相关：[`SKILL.md`](SKILL.md) · [`../docs/troubleshoot-faq.md`](../docs/troubleshoot-faq.md)
