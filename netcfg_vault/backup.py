"""Device inventory loading and per-vendor config backup."""
import getpass
import os

import yaml

# 各厂商取配置的命令
SHOW_COMMANDS = {
    "h3c": "display current-configuration",
    "huawei": "display current-configuration",
    "cisco": "show running-config",
    "ruijie": "show running-config",
}


def load_devices(path):
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    devices = data.get("devices", [])
    for dev in devices:
        for key in ("name", "host", "vendor", "protocol", "username"):
            if key not in dev:
                raise ValueError(f"设备缺少字段 {key}: {dev}")
        if dev["vendor"] not in SHOW_COMMANDS:
            raise ValueError(f"不支持的 vendor: {dev['vendor']}")
    return devices


def backup_device(dev, ask_pass=False):
    """Connect and return the running-config text. Raises on failure."""
    import paramiko  # deferred import so --help works without it

    password = os.environ.get("NETCFG_PASSWORD") or (
        getpass.getpass(f"{dev['name']} 密码: ") if ask_pass else None
    )
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            dev["host"],
            username=dev["username"],
            password=password,
            look_for_keys=True,
            timeout=15,
        )
        _stdin, stdout, _stderr = client.exec_command(
            SHOW_COMMANDS[dev["vendor"]], timeout=30
        )
        return stdout.read().decode("utf-8", errors="replace")
    finally:
        client.close()
