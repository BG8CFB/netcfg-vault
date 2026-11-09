"""Pro 授权验证：离线签名 license，支持 Ed25519（v2）与 HMAC-SHA256（v1，兼容旧 key）。

Key 格式：
- v2: NCVE-<base32(payload|sig)>，sig = Ed25519 私钥对 payload 的签名（64 字节）。
  公钥内嵌于 _pro_secret.PUBLIC_KEY_PEM，私钥仅作者侧持有（earn/.secrets/ed25519-private.pem）。
- v1: NCV-XXXX-XXXX-XXXX，HMAC-SHA256 对称签名（_pro_secret.PRO_SECRET）。

验证完全离线（无遥测、无外呼）。失败条件：格式错误 / 签名不匹配 / 过期
→ 全部回退免费版（5 台限制），不抛异常。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import time
from pathlib import Path

LICENSE_PATH = Path.home() / ".netcfg-vault" / "license"
KEY_RE = re.compile(r"^NCV-([A-Z2-7]{4})(-[A-Z2-7]{4})+$")
KEYV2_RE = re.compile(r"^NCVE-[A-Z2-7]+$")
FREE_DEVICE_LIMIT = 5


def _payload_signature(payload: str) -> str:
    from netcfg_vault._pro_secret import PRO_SECRET  # noqa: PLC0415

    return hmac.new(PRO_SECRET, payload.encode(), hashlib.sha256).hexdigest()


def _verify_ed25519(payload: bytes, sig: bytes) -> bool:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        from netcfg_vault._pro_secret import PUBLIC_KEY_PEM  # noqa: PLC0415

        pub = serialization.load_pem_public_key(PUBLIC_KEY_PEM)
        if not isinstance(pub, Ed25519PublicKey):
            return False
        pub.verify(sig, payload)
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False


def generate_license(customer: str, device_limit: int, days: int = 3650) -> str:
    """（作者侧工具，v1）生成 HMAC license key。完整 payload+sig 的 base32，4 字符一组。"""
    expiry = int(time.time()) + days * 86400
    payload = f"{customer}|{device_limit}|{expiry}"
    sig = _payload_signature(payload)
    raw = (payload + "|" + sig).encode()
    body = base64.b32encode(raw).decode().rstrip("=")
    return "NCV-" + "-".join(body[i : i + 4] for i in range(0, len(body), 4))


def generate_license_v2(customer: str, device_limit: int, days: int = 3650, private_key_pem: str | None = None) -> str:
    """（作者侧工具，v2）生成 Ed25519 license key。

    private_key_pem：签发私钥 PEM；不传则读 NETCFG_SIGNING_KEY 环境变量。
    payload = customer|limit|expiry，sig = Ed25519 签名（64B）。
    """
    pem = private_key_pem or os.environ.get("NETCFG_SIGNING_KEY", "")
    if not pem:
        raise ValueError("need private_key_pem or NETCFG_SIGNING_KEY")
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    key = serialization.load_pem_private_key(pem.encode(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("not an Ed25519 private key")
    expiry = int(time.time()) + days * 86400
    payload = f"{customer}|{device_limit}|{expiry}".encode()
    sig = key.sign(payload)
    body = base64.b32encode(payload + b"|" + sig).decode().rstrip("=")
    return "NCVE-" + body


def _parse_v2(key: str) -> tuple[str, int, int] | None:
    body = key[len("NCVE-"):]
    raw = base64.b32decode(body + "=" * (-len(body) % 8))
    # payload 以 | 分隔 customer|limit|expiry，最后 64B 是签名；customer 可含中文不含 |
    sep = raw.rfind(b"|", 0, len(raw) - 64)
    if sep < 0:
        return None
    payload, sig = raw[:sep], raw[sep + 1:]
    if not _verify_ed25519(payload, sig):
        return None
    try:
        customer, limit_s, expiry_s = payload.decode().split("|")
        return customer, int(limit_s), int(expiry_s)
    except Exception:
        return None


def _parse_v1(key: str) -> tuple[str, int, int] | None:
    body = key[4:].replace("-", "")
    raw = base64.b32decode(body + "=" * (-len(body) % 8))
    parts = raw.decode(errors="ignore").split("|")
    if len(parts) != 4:
        return None
    customer, limit_s, expiry_s, sig = parts
    if not hmac.compare_digest(sig, _payload_signature(f"{customer}|{limit_s}|{expiry_s}")):
        return None
    try:
        return customer, int(limit_s), int(expiry_s)
    except Exception:
        return None


def load_license_from(key: str) -> dict | None:
    """直接校验给定 key 字符串（load_license 的无副作用入口，供测试/工具用）。"""
    parsed: tuple[str, int, int] | None = None
    version = 0
    if KEYV2_RE.match(key):
        parsed = _parse_v2(key)
        version = 2
    elif KEY_RE.match(key):
        parsed = _parse_v1(key)
        version = 1
    if parsed is None:
        return None
    customer, device_limit, expiry = parsed
    if expiry < time.time():
        return None
    return {"customer": customer, "device_limit": device_limit, "expiry": expiry, "version": version}



def load_license() -> dict | None:
    """读取并校验 license。返回 {customer, device_limit, expiry, version} 或 None（回退免费版）。"""
    key = os.environ.get("NETCFG_LICENSE", "").strip()
    if not key and LICENSE_PATH.exists():
        key = LICENSE_PATH.read_text(encoding="utf-8").strip()
    if not key:
        return None
    parsed: tuple[str, int, int] | None = None
    version = 0
    if KEYV2_RE.match(key):
        parsed = _parse_v2(key)
        version = 2
    elif KEY_RE.match(key):
        parsed = _parse_v1(key)
        version = 1
    if parsed is None:
        return None
    customer, device_limit, expiry = parsed
    if expiry < time.time():
        return None
    return {"customer": customer, "device_limit": device_limit, "expiry": expiry, "version": version}


def effective_device_limit() -> int:
    lic = load_license()
    if lic and lic["device_limit"] > 0:
        return lic["device_limit"]
    return FREE_DEVICE_LIMIT
