# netcfg-vault

Batch backup, diff, audit and encrypt network device configurations — built for network engineers and NOC teams managing H3C (Comware), Huawei (VRP), Cisco (IOS) and Ruijie fleets.

[主页 Homepage](https://bg8cfb.github.io/netcfg-vault/) · [PyPI](https://pypi.org/project/netcfg-vault/) · [中文文档](./README.md) · [Tutorial](https://bg8cfb.github.io/netcfg-vault/tutorial.html)

## Why

Most config backup tools assume Cisco-only fleets. Real-world networks in APAC run mixed vendors: H3C access switches, Huawei cores, Cisco leftovers. netcfg-vault speaks all four natively — one inventory file, one command.

| Capability | Free (5 devices) | Pro (¥99, unlimited) |
|---|---|---|
| Batch SSH backup (H3C/Huawei/Cisco/Ruijie) | ✓ | ✓ |
| Noise-filtered config diff | ✓ | ✓ |
| Scheduled backup + webhook alerts (DingTalk/WeCom/Feishu/ServerChan) | ✓ | ✓ |
| Security audit (telnet/SNMP default community/weak passwords) | ✓ | ✓ |
| HTML inspection report | ✓ | ✓ |
| `init` scaffolding (systemd timer + cron) | ✓ | ✓ |
| AES-256-GCM encrypted vault | — | ✓ |
| Offline license, unlimited devices | — | ✓ |

## Quick start (30 seconds)

```bash
pip install netcfg-vault
netcfg-vault init          # generates devices.yml + systemd units
# edit devices.yml: name/host/vendor/username per device
export NETCFG_PASSWORD=...  # or pass --ask-pass
netcfg-vault backup -f devices.yml -o backups/
```

Inventory format:

```yaml
devices:
  - name: core-01
    host: 10.0.0.1
    vendor: huawei      # h3c | huawei | cisco | ruijie
    protocol: ssh
    username: admin
```

## All commands

```
backup   batch fetch running-config over SSH
watch    scheduled backup loop with failure alerts
diff     compare two configs, noise lines filtered
audit    6-rule security scan (telnet, SNMP defaults, weak passwords...)
report   HTML inspection report with severity summary
vault    AES-256-GCM encrypted archive (save/list/extract)
init     scaffold inventory + systemd/cron timers
license  activate Pro (offline HMAC key, no telemetry)
```

## Online tools (free, no install)

- [Config diff](https://bg8cfb.github.io/netcfg-vault/config-diff.html)
- [Config security audit](https://bg8cfb.github.io/netcfg-vault/config-audit.html)
- [Subnet calculator](https://bg8cfb.github.io/netops-cheatsheets/subnet-calculator.html)
- [VLAN planner](https://bg8cfb.github.io/netops-cheatsheets/vlan-planner.html)

## Pro license

Pro removes the 5-device limit and unlocks the encrypted vault. One-time ¥99, offline signed key, works air-gapped. Contact: 2945362558@qq.com

## Related projects

- [netops-toolkit](https://github.com/BG8CFB/netops-toolkit) — Python CLI: info/find/save/interfaces/locate/topology/audit
- [netops-utils](https://github.com/BG8CFB/netops-utils) — Node.js CLI: subnet/diff/audit, zero dependencies
- [netops-cheatsheets](https://github.com/BG8CFB/netops-cheatsheets) — H3C/Huawei/Cisco cheatsheets + online tools

## License

MIT