"""netcfg-vault CLI: backup network device configs concurrently."""
import argparse
import sys
import getpass
import os
import sys
from pathlib import Path

from .backup import backup_device, load_devices
from .diff import changed_lines, diff_configs
from .license import effective_device_limit, load_license

FREE_DEVICE_LIMIT = 5


def cmd_backup(args):
    devices = load_devices(args.inventory)
    limit = effective_device_limit() if not args.pro else None
    if limit is not None:
        if len(devices) > limit:
            print(f"[free] 仅备份前 {limit} 台设备（Pro 解锁全部）")
        devices = devices[:limit]
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


def cmd_watch(args):
    """Pro: 定时备份循环。"""
    from .scheduler import Scheduler

    sched = Scheduler(args.inventory, args.out, interval=args.interval, device_limit=None if args.pro else effective_device_limit())
    if not args.pro:
        print(f"[free] watch 模式仅备份前 {FREE_DEVICE_LIMIT} 台设备（Pro 解锁全部）")
    sched.run_forever()


def cmd_vault_save(args):
    """加密备份目录为 .nvault 档案。"""
    from .vault import vault_save

    n = vault_save(args.dir, args.out, getpass.getpass("保管库口令: "))
    print(f"[ok] 已加密 {n} 个文件 -> {args.out}")


def cmd_vault_list(args):
    from .vault import vault_list

    for f in vault_list(args.vault, getpass.getpass("保管库口令: ")):
        print(f"{f['size']:>10}  {f['name']}")


def cmd_vault_extract(args):
    from .vault import vault_extract

    files = vault_extract(args.vault, getpass.getpass("保管库口令: "), args.out)
    print(f"[ok] 解出 {len(files)} 个文件 -> {args.out}")


def cmd_license(args):
    """显示当前授权状态。"""
    info = load_license()
    if info:
        import datetime

        exp = datetime.datetime.fromtimestamp(info["expiry"]).strftime("%Y-%m-%d")
        print(f"[Pro] {info['customer']} · 设备上限 {info['device_limit']} · 有效期至 {exp}")
    else:
        print("[free] 免费版（5 台设备）。Pro 授权: 设置 NETCFG_LICENSE 或 ~/.netcfg-vault/license")


def main() -> int:
    ap = argparse.ArgumentParser(prog="netcfg-vault", description="批量备份网络设备配置")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup", help="执行备份")
    b.add_argument("inventory", help="devices.yml 路径")
    b.add_argument("--out", default="backups", help="输出目录")
    b.add_argument("--ask-pass", action="store_true", help="交互式输入密码")
    b.add_argument("--pro", action="store_true", help="Pro 授权模式")
    b.set_defaults(func=cmd_backup)
    w = sub.add_parser("watch", help="定时备份（Pro 功能，免费限 5 台）")
    w.add_argument("inventory", help="devices.yml 路径")
    w.add_argument("--out", default="backups", help="输出目录")
    w.add_argument("--interval", type=int, default=86400, help="轮询间隔秒数，默认 86400（每天）")
    w.add_argument("--pro", action="store_true", help="Pro 模式（解锁全部设备）")
    w.set_defaults(func=cmd_watch)

    d = sub.add_parser("diff", help="对比两份配置文件")
    d.add_argument("old", help="旧配置路径")
    d.add_argument("new", help="新配置路径")
    d.set_defaults(func=cmd_diff)

    v = sub.add_parser("vault", help="加密保管库（AES-256-GCM）")
    vsub = v.add_subparsers(dest="vault_cmd", required=True)
    vs = vsub.add_parser("save", help="加密备份目录")
    vs.add_argument("dir", help="备份目录")
    vs.add_argument("--out", default="backups.nvault", help="输出档案路径")
    vs.set_defaults(func=cmd_vault_save)
    vl = vsub.add_parser("list", help="列出档案内容")
    vl.add_argument("vault", help=".nvault 路径")
    vl.set_defaults(func=cmd_vault_list)
    ve = vsub.add_parser("extract", help="解密档案")
    ve.add_argument("vault", help=".nvault 路径")
    ve.add_argument("--out", default="restored", help="解出目录")
    ve.set_defaults(func=cmd_vault_extract)
    lc = sub.add_parser("license", help="显示授权状态")
    lc.set_defaults(func=cmd_license)

    au = sub.add_parser("audit", help="离线合规审计（检查备份配置中的风险项）")
    au.add_argument("dir", help="备份目录")
    au.add_argument("--csv-out", default=None, help="CSV 输出路径")
    au.set_defaults(func=cmd_audit)

    rp = sub.add_parser("report", help="生成 HTML 巡检报告")
    rp.add_argument("dir", help="备份目录")
    rp.add_argument("--out", default="report.html", help="输出文件")
    rp.add_argument("--prev", default=None, dest="prev_dir", help="前一日目录（对比变更）")
    rp.set_defaults(func=cmd_report)

    it = sub.add_parser("init", help="初始化工作目录（清单模板+systemd/cron）")
    it.add_argument("dir", nargs="?", default=".", help="目标目录（默认当前）")
    it.set_defaults(func=cmd_init)

    args = ap.parse_args()
    return args.func(args)


def cmd_init(args) -> int:
    from .init_cmd import main as init_main
    import sys
    sys.argv = ["netcfg-vault init", args.dir]
    return init_main()


def cmd_audit(args) -> int:
    from .audit import audit_dir, write_csv
    findings = audit_dir(args.dir)
    if not findings:
        print("所有配置检查通过, 未发现风险项")
        return 0
    print(f"发现 {len(findings)} 项风险:")
    for f in findings:
        print(f"  [{f.severity.upper():6s}] {f.device}: {f.desc}")
    if args.csv_out:
        write_csv(findings, args.csv_out)
        print(f"已写入 {args.csv_out}")
    return 1

def cmd_report(args) -> int:
    from .report import generate_report
    out = generate_report(args.dir, args.out, prev_dir=args.prev_dir)
    print(f"报告已生成: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
