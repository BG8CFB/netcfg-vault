"""Scaffold a working directory: inventory template + systemd timer + cron examples."""
from __future__ import annotations

import argparse
from pathlib import Path

INVENTORY = """devices:
  - name: core-sw1
    host: 192.168.1.1
    vendor: h3c          # h3c | huawei | cisco | ruijie
    protocol: ssh
    username: netadmin
  - name: acc-sw-2f
    host: 192.168.1.2
    vendor: huawei
    protocol: ssh
    username: netadmin
"""

SYSTEMD = """[Unit]
Description=netcfg-vault scheduled backup
After=network-online.target

[Service]
Type=oneshot
Environment=NETCFG_PASSWORD=changeme
ExecStart=netcfg-vault backup -f devices.yml -o backups/%H

[Install]
WantedBy=multi-user.target
"""

TIMER = """[Unit]
Description=Run netcfg-vault backup daily at 02:30

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true

[Install]
WantedBy=timers.target
"""

CRON = """30 2 * * * NETCFG_PASSWORD=xxx netcfg-vault backup -f /opt/netcfg/devices.yml -o /opt/netcfg/backups/$(date +\%F)
"""


def main() -> int:
    ap = argparse.ArgumentParser(prog="netcfg-vault init", description="初始化工作目录")
    ap.add_argument("dir", nargs="?", default=".", help="目标目录 (默认当前)")
    a = ap.parse_args()

    root = Path(a.dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "devices.yml").write_text(INVENTORY, encoding="utf-8")
    sysdir = root / "systemd"
    sysdir.mkdir(exist_ok=True)
    (sysdir / "netcfg-backup.service").write_text(SYSTEMD, encoding="utf-8")
    (sysdir / "netcfg-backup.timer").write_text(TIMER, encoding="utf-8")
    (root / "cron.example").write_text(CRON, encoding="utf-8")
    print("已生成:")
    print(f"  {root / 'devices.yml'}          <- 编辑设备清单")
    print(f"  {sysdir / 'netcfg-backup.service'}  <- systemd 服务")
    print(f"  {sysdir / 'netcfg-backup.timer'}    <- systemd 定时")
    print(f"  {root / 'cron.example'}      <- cron 备选")
    print("\n下一步: netcfg-vault backup -f devices.yml -o backups/")
    return 0


if __name__ == "__main__":
    main()
