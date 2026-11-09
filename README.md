# netcfg-vault

**批量备份和对比网络设备配置的命令行工具** — 面向网络工程师 / 运维。

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
