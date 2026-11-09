# netcfg-vault

> Search keywords: h3c配置备份工具 · 华为交换机配置备份 · 思科 running-config 批量导出 · 网络设备配置自动备份 · network device config backup CLI · H3C Huawei Cisco Ruijie config management

> 产品主页: <https://bg8cfb.github.io/netcfg-vault/> · PyPI: <https://pypi.org/project/netcfg-vault/> · 中文教程: <https://bg8cfb.github.io/netcfg-vault/tutorial.html>

**批量备份和对比网络设备配置的命令行工具** — 面向网络工程师 / 运维。

## 定时备份（Pro）

```bash
netcfg-vault watch devices.yml --out backups --interval 3600
```

每天/每小时自动备份，失败设备即时上报，支持钉钉/企业微信/飞书/Server酱 webhook（设 NETCFG_WEBHOOK 环境变量即可）。免费版限 5 台，Pro 解锁全部 + 告警。

## 为什么
交换机/路由器配置散落各处，改完没备份、出事没证据。现有方案要么要装平台（Oxidized 需 Ruby 环境），要么是厂商专属。

## 特性
- 多设备并发备份（SSH/Telnet），华为/H3C/锐捷/思科开箱即用
- 配置变更 diff（谁在什么时候改了什么）
- 输出: 本地目录 / git 仓库
- 单二进制 / 单 Python 文件，无依赖

## 快速开始
```bash
# 免费版: 最多 5 台设备
pip install netcfg-vault
netcfg-vault backup devices.yml
```

配置变更对比（自动忽略时间戳噪声，只看真实变更）：
```bash
netcfg-vault diff backups/old.cfg backups/new.cfg
# -sysname CoreSW01
# +sysname CoreSW02
# [summary] +1 / -1
```

📖 完整教程: [网络设备配置还在手动导出？](https://gist.github.com/BG8CFB/6aab6eb7b32ef1e06ab9fe632da6346a)

## Pro 版（¥99 一次性）
- 无设备数限制
- 定时任务 + 失败告警（邮件/企业微信/钉钉）
- 配置变更周报
- 1 年更新

购买链接: （见 releases 说明 / 联系作者）

## 状态
🚧 开发中 — 首个可用版本开发中。Star 关注进展。

## License
MIT（代码），品牌与文档保留权利。

## v0.4.0 新增

### 加密保管库（AES-256-GCM）
备份文件包含 ACL、SNMP community、账号等敏感信息，明文落盘有风险。保管库把整个备份目录加密成单个 .nvault 文件：

```bash
netcfg-vault vault save backups/ --out vault.nvault   # 加密（口令 PBKDF2 600k 迭代）
netcfg-vault vault list vault.nvault                  # 只看清单，不落盘
netcfg-vault vault extract vault.nvault --out restored
```

### Pro 授权体系（离线验证）
- Pro key 解锁无限设备 + watch 全量轮询，`netcfg-vault license` 查看状态
- license 通过 `NETCFG_LICENSE` 环境变量或 `~/.netcfg-vault/license` 文件配置
- 验证完全离线（HMAC-SHA256 签名，无遥测无外呼）

## Changelog

- 0.5.0: Ed25519 非对称 license（NCVE- 前缀），公钥内嵌验证、私钥离线签发；兼容 v1 HMAC key；GitHub Discussions 开张。
- 0.4.0: AES-256-GCM 加密 vault + 离线 Pro license。
- 0.3.x: 定时备份 + webhook 告警 + 配置 diff。


## v0.6.0 — 配置合规审计

```bash
netcfg-vault audit backups/2026-11-10/ --csv report.csv
```

离线扫描备份目录, 6 条规则 (telnet/SNMP默认团体名/Web管理/SSHv1/明文密码/VTY无ACL), 输出按严重度排序的 CSV 报告。不连设备, 不需要任何凭据。


## v0.7.0 — HTML 巡检报告

```bash
netcfg-vault backup -f devices.yml -o backups/$(date +%F)/
netcfg-vault report backups/2026-11-10/ --prev backups/2026-11-09/ --out report.html
```

一份可打印的 HTML 巡检报告: 设备数/高危项/中危项/变更设备数四张卡片 + 合规审计明细表 + 逐设备配置变更量表。给领导看的巡检, 一条命令。

## v0.8.0 — init 脚手架

一条命令生成 `devices.yml` + systemd timer + cron 样例：`netcfg-vault init`。

## v0.9.0 — 基线快照（baseline）

```bash
netcfg-vault baseline set backups/2026-11-10 --name golden   # 锁定当前配置为基线
netcfg-vault baseline diff backups/2026-11-14 --name golden  # 对比漂移（有变化 rc=1，可接告警）
netcfg-vault baseline list
netcfg-vault baseline remove golden
```

巡检场景：把上周备份设为基线，本周 diff 一眼看出谁改了配置（NEW/MISSING/CHANGED + 行级 diff）。
