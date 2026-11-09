"""Pro 授权验证：离线 HMAC 签名 license 文件。

设计：授权 key 形如 NCV-XXXX-XXXX-XXXX，内容 = HMAC-SHA256(vendor_secret, payload) 的 hex。
用户拿到 key 后保存到 ~/.netcfg-vault/license 或设置 NETCFG_LICENSE 环境变量。
验证完全离线（无遥测、无外呼），payload 含设备数上限与签发日。

生成端（vendor，即本项目作者）不随包分发 secret。
失败条件：格式错误 / 签名不匹配 / 过期 → 全部回退免费版（5 台限制），不抛异常。
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import time
from pathlib import Path

LICENSE_PATH = Path.home() / ".netcfg-vault" / "license"
KEY_RE = re.compile(r"^NCV-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")


def _payload_signature(payload: str) -> str:
    # vendor secret 占位：实际值由作者侧 keygen 持有，包内只内嵌验证公钥材料（此处对称简化实现）
    from netcfg_vault._pro_secret import PRO_SECRET  # noqa: PLC0415

    return hmac.new(PRO_SECRET, payload.encode(), hashlib.sha256).hexdigest()


def generate_license(customer: str, device_limit: int, days: int = 3650) -> str:
    """（作者侧工具）生成 license key。payload = customer|limit|expiry 时间戳。"""
    expiry = int(time.time()) + days * 86400
    payload = f"{customer}|{device_limit}|{expiry}"
    sig = _payload_signature(payload)
    raw = (payload + "|" + sig).encode()
    import base64

    body = base64.b32encode(raw).decode().rstrip("=")
    groups = [body[i:i + 4] for i in range(0, len(body), 4)]
    key = "-".join(groups[:3])
    # 完整 key 需含全部信息：改用完整 body 压缩表示
    full = "NCV-" + "-".join(body[i:i + 4] for i in range(0, len(body), 4))
    return full


def _decode_key(key: str) -> dict | None:
    import base64

    body = key[4:].replace("-", "")
    pad = "=" * ((8 - len(body) % 8) % 8)
    try:
        raw = base64.b32decode(body + pad)
        parts = raw.decode().split("|")
        if len(parts) != 4:
            return None
        customer, limit, expiry, sig = parts
        expect = _payload_signature(f"{customer}|{limit}|{expiry}")
        if not hmac.compare_digest(sig, expect):
            return None
        return {"customer": customer, "device_limit": int(limit), "expiry": int(expiry)}
    except Exception:
        return None


def load_license() -> dict | None:
    """读 license（环境变量优先，其次 ~/.netcfg-vault/license）。无效或过期返回 None（回退免费版）。"""
    key = os.environ.get("NETCFG_LICENSE", "").strip()
    if not key and LICENSE_PATH.is_file():
        key = LICENSE_PATH.read_text(encoding="utf-8").strip()
    if not key:
        return None
    info = _decode_key(key)
    if info and info["expiry"] > time.time():
        return info
    return None


def effective_device_limit() -> int:
    """当前生效的设备上限：Pro license 存在且有效 → license 限额，否则免费 5 台。"""
    lic = load_license()
    if lic:
        return lic["device_limit"]
    return 5
