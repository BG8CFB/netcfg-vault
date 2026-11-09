"""netcfg-vault CLI: backup network device configs concurrently."""
import argparse
import os
import sys
from pathlib import Path

from .backup import backup_device, load_devices
from .diff import changed_lines, diff_configs

FREE_DEVICE_LIMIT = 5


def cmd_backup(args):
    devices = load_devices(args.inventory)
    if not args.pro:
        devices = devices[:FREE_DEVICE_LIMIT]
        if len(devices) == FREE_DEVICE_LIMIT:
            print(f"[free] 仅备份前 {FREE_DEVICE_LIMIT} 台设备（Pro 解锁全部）")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    for dev in devices:
        try:
            text = backup_device(dev, args.ask_pass)
            (out_dir / f"{dev['name']}.cfg").write_text(text, encoding="utf-8")
            print(f"[ok] {dev['name']} ({len(text)} bytes)")
        except Exception as exc:  # noqa: BLE001 - report per-device failures
            failures.append((dev["name"], str(exc)))
            print(f"[fail] {dev['name']}: {exc}")
    if failures:
        sys.exit(1)


def cmd_diff(args):
    """Compare newest backup against previous one (or two named files)."""
    from pathlib import Path

    old = Path(args.old).read_text(encoding="utf-8")
    new = Path(args.new).read_text(encoding="utf-8")
    added, removed = changed_lines(old, new)
    if added == 0 and removed == 0:
        print("无有效变更（已忽略时间戳等噪声行）")
        return
    print(diff_configs(old, new))
    print(f"\n[summary] +{added} / -{removed}")


def main():
    ap = argparse.ArgumentParser(prog="netcfg-vault", description="批量备份网络设备配置")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup", help="执行备份")
    b.add_argument("inventory", help="devices.yml 路径")
    b.add_argument("--out", default="backups", help="输出目录")
    b.add_argument("--ask-pass", action="store_true", help="交互式输入密码")
    b.add_argument("--pro", action="store_true", help="Pro 授权模式")
    b.set_defaults(func=cmd_backup)
    d = sub.add_parser("diff", help="对比两份配置文件")
    d.add_argument("old", help="旧配置路径")
    d.add_argument("new", help="新配置路径")
    d.set_defaults(func=cmd_diff)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
