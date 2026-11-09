"""定时备份调度器（Pro 功能骨架）。

输入: 设备清单路径、备份根目录、轮询间隔秒。
输出: 每轮按日期子目录落盘各设备配置；失败设备名与错误经 notify 回调上报。
失败条件: 设备清单无法解析时直接抛出对应异常；备份失败按设备记录，不中断整轮。
"""
from __future__ import annotations

import time
from datetime import date
from pathlib import Path

from .backup import backup_device, load_devices


def default_notify(messages):
    """默认上报: 打印到标准错误，方便重定向到日志。"""
    for m in messages:
        print(f"[notify] {m}")


class Scheduler:
    """周期执行批量备份；errors 回调接收失败列表。"""

    def __init__(self, inventory, out_root, interval=86400, notify=None, device_limit=None):
        self.inventory = Path(inventory)
        self.out_root = Path(out_root)
        self.interval = interval
        self.notify = notify or default_notify
        self.device_limit = device_limit
        self._running = False

    def run_once(self):
        """执行一轮备份，返回 (成功数, 失败列表)。"""
        devices = load_devices(self.inventory)
        if self.device_limit is not None:
            devices = devices[: self.device_limit]
        stamp = date.today().isoformat()
        out_dir = self.out_root / stamp
        out_dir.mkdir(parents=True, exist_ok=True)
        ok = 0
        failed = []
        for dev in devices:
            try:
                text = backup_device(dev)
                (out_dir / f"{dev['name']}.cfg").write_text(text, encoding="utf-8")
                ok += 1
            except Exception as exc:  # noqa: BLE001 - 单台失败不中断整轮
                failed.append(f"{dev['name']}: {exc}")
        if failed:
            self.notify(failed)
        return ok, failed

    def run_forever(self):
        """阻塞式循环，直到 stop() 被调用。"""
        self._running = True
        while self._running:
            try:
                self.run_once()
            except Exception as exc:  # noqa: BLE001 - 清单级错误也要通知后继续
                self.notify([f"inventory error: {exc}"])
            time.sleep(self.interval)

    def stop(self):
        self._running = False
