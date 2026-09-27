# 更新日志

本文件**只记录配置文件的修改** —— `surge/profiles/` 与 `egern/profiles/` 两内核的 profile（含 `.min` 形态）
以及它们引用的规则集素材。一条一句，动词开头，按日期倒序，同一天不开第二段。
文档、检查脚本与判据的改动不进这里，看 `git log`。
逐版史实看 git log；2026-09-27 仓库精简前的完整历史在备份 tag `pre-cleanup-20260927`。

## 2026-09-27

- 恢复 `surge/profiles/config_old/`（14 份）与 `egern/profiles/config_old/`（26 份）历史版本快照
  —— 精简时误删，自备份 tag 原字节找回，归档判据（V3–V6）随之恢复生效。
- 归档升版：变动前的 surge 懒人版与 Egern 分流版（v1.3 / v3.4）连同 `.min` 快照入档 `config_old/`；
  四份当前版头注同号升 `lazy_v1.3 → v1.4`、`routing_v3.4 → v3.5`（两内核同步），正文与 `.min` 未动。

## 2026-09-26

- 新增隐藏订阅入口 `Airport`（`surge/profiles/lazy.conf` 用 `select` + `policy-path` + `hidden=true`，
  `egern/profiles/lazy.yaml` 用 `external` 槽位 + `type: smart` + `hidden: true`），`Proxy` 与 `AI` 两个组改从它取
  订阅节点（Surge 侧 `include-other-group="Airport"`），组数 3 → 4。
- 补两条 hysteria2 占位节点 `Node-A` / `Node-B` 进四份模板（`server` 取 RFC 5737 文档段、凭据写 `REPLACE_WITH_*`），
  `Node-A` 归 `Proxy`、`Node-B` 归 `AI`；分流版里这两条不进任何地区组。
- 改 Egern 懒人版 `Proxy` 组的默认去向为跟随订阅（`select` 首项即默认，`policies` 排 `[Airport, Node-A]`），
  `AI.policies` 排 `[Node-B, Airport]` 并 `flatten: true` 摊成具体节点。
- 改分流版 `Spotify` 与 `YouTubeMusic` 的首项，由 `Proxy` 改为 `USA`（两内核同步）。
- 新增 `[SSID Setting]` 段到 Surge 两份完整版配置：`SSID:MyHome suspend=true` —— 连上该名称的 Wi-Fi 自动暂停
  Surge、离开自动恢复，两份 `.min` 随同重建。Egern 侧没有对等配置项，未动。
- 更正 `egern/profiles/routing.yaml` 头注里的 URL 占位符读数 9 → 8，并补口径括注（仅 `urls:` 下条目；
  含 `urls_disabled:` 为 11 → 5）。

## 2026-09-25

- 改四份当前版 profile 头注里 `direct.txt` 的写死条数为约数（「约 11.1 万条纯域名」），各处并带上本内核的现抓入口。
- 升懒人版两内核同号 `lazy_v1.0 → lazy_v1.1`：落盘的只有两行头注，归档零新增文件、订阅地址不变。
- 规范化 `surge/profiles/lazy.min.conf` 到生成器输出（仅空行位置，正文逐字未动）—— 订阅下载到的字节有变化。
- 改 `surge/profiles/routing.conf` 与 `egern/profiles/routing.yaml` 头注里的校验命令指向现役固定名 ——
  此前照抄必失败，带版本号的 profile 路径在订阅地址固定化后已不存在。

## 2026-09-24

- 升分流版 `routing_v3.2`（Surge）：按「实测零 IP 就不写」重排规则级 `no-resolve` —— 9 条零 IP 的规则集
  （`private.txt` · `Gemini` · `Anthropic` · `Claude` · `AI.list` · `YouTubeMusic` · `GitHub` · `Microsoft` · `direct.txt`）
  去掉开关，9 条真含 IP 的保留（内置 `LAN` · `OpenAI` · `Spotify` · `YouTube` · `Google` · `Telegram` · `Twitter` ·
  `WeChat` · `GEOIP`）；分组、规则条数与顺序、DNS 段逐字未动。
- 升分流版 `routing_v3.2`（Egern）：补一条 `apple_system.list → DIRECT`，与 Surge 内置 `SYSTEM` 同位同策略；
  `Proxy.list` 由 `disabled: true` 改成纯注释块 —— Surge 侧没有禁用开关、只有注释，注释化才是两侧同写法。
- 精简 `surge/profiles/lazy.conf`：删掉远程 Apple 全量集（只留内置 `SYSTEM`，规则 11 → 10 条），去掉 3 条零 IP
  规则的 `no-resolve`，段序统一为 白名单 → 广告 ×2 → 内网 ×2 → `SYSTEM` → `AI.list` → `direct.txt` → `GEOIP,CN`
  → `FINAL`，与 Egern 懒人版同位。
- 新增本仓第一份自托管规则集 `egern/apple_system.list` —— Surge 官方内置 `SYSTEM` 的 2026-09-24 快照，18 条域名
  （快照原件里的 2 条 `PROCESS-NAME` 删掉，Egern 不支持该类型）。
- 精简 `egern/profiles/lazy.yaml`：删掉内联 `domain_suffix: cn`（`direct.txt` 里本来就是 `DOMAIN-SUFFIX,cn`，属重复），
  补上 `apple_system.list → DIRECT`，规则一增一减仍 10 条。
- 固定订阅地址：两内核 `profiles/` 顶层从此恒为 `routing` · `routing.min` · `lazy` · `lazy.min` 四件，被替代的版本
  逐字节进各侧 `profiles/config_old/`，「哪一版」只由第一行 `#! version=` 头注标识 —— 此后每升一版都不再改订阅地址。
  带版本号的旧地址自这次起 404，维护者已确认接受这一次断链。
- 规范化 `surge/profiles/routing.min.conf` 到生成器输出（144 → 145 行，非空行序列逐字未变，动的全是空行位置）——
  订阅下载到的字节有变化，内容语义不变。

## 2026-09-23

- 补全 `egern/profiles/lazy.yaml` 与分流版的三项差异：`dns.forward` 扩为四层（白名单 → 两条广告清单 `reject` →
  兜底），`rules` 补 `Private`（`private.txt` → `DIRECT`），`AI` 组 `flatten: true` —— 广告域名改在解析阶段拒答，
  与 Surge 懒人版的 `pre-matching` 一致。
- 移除 `egern/profiles/lazy.yaml` 的 `Final` 组，兜底 `default.policy` 直写 `Proxy`（分组 4 → 3，规则仍 10 条，
  `name: Final` 保留为日志与调试用的标签）；分流版仍保留 `Final` 组，面板要能换兜底去向。
- 新建两内核 `routing_v3.1{,.min}`：远程规则集全部显式钉一周刷新（Surge 20 条 `"update-interval=604800"` ·
  Egern 22 条 `update_interval: 604800`），懒人版原地覆盖（7 条钉住）；分组、规则、DNS 段逐字未动。
- 修正 `surge/profiles/lazy.conf` 里 `proxy-test-url` 的注释与取值不符（注释写「用国内 204」，值是
  `www.gstatic.com`）—— 配置本体未动，注释不进 `.min`。
- 重装配两仓合并后的 profile：raw URL 换本仓名、图标引用改指共享 `icons/` 那一份。
