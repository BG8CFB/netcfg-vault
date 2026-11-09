"""加密保管库：把备份配置打包为 AES-256-GCM 加密档案。

用途：备份文件含设备全部配置（ACL、SNMP community、账号），明文落盘有泄露风险。
保管库把整个备份目录加密为单个 .nvault 文件，密钥由口令派生（PBKDF2-HMAC-SHA256）。

输入：backup 目录路径 + 口令
输出：单个 .nvault 文件（可离线保存 / 上传私有云盘）
失败条件：口令错误（GCM 校验失败抛 InvalidTag）、目录不存在
"""
from __future__ import annotations

import io
import json
import os
import struct
import zipfile
from datetime import datetime
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VAULT_MAGIC = b"NVAULT1"
KDF_ITERATIONS = 600_000


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """口令派生 256 位密钥。PBKDF2-HMAC-SHA256，600k 迭代抗暴力破解。"""
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes

    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                     iterations=KDF_ITERATIONS)
    return kdf.derive(passphrase.encode("utf-8"))


def vault_save(src_dir: str, out_path: str, passphrase: str) -> int:
    """加密整个目录为 .nvault 档案，返回加密的文件数。

    布局: MAGIC | salt(16) | nonce(12) | ciphertext(zip)
    zip 内容再整体 AES-GCM 加密，防篡改 + 保密一步完成。
    """
    src = Path(src_dir)
    if not src.is_dir():
        raise FileNotFoundError(f"目录不存在: {src_dir}")
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = derive_key(passphrase, salt)

    buf = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                zf.writestr(p.relative_to(src).as_posix(), p.read_bytes())
                count += 1
    aes = AESGCM(key)
    ct = aes.encrypt(nonce, buf.getvalue(), None)

    Path(out_path).write_bytes(VAULT_MAGIC + salt + nonce + ct)
    return count


def vault_list(vault_path: str, passphrase: str) -> list[dict]:
    """列出档案内文件（不解密到磁盘），返回 [{name, size, mtime}]。口令错误抛 cryptography InvalidTag。"""
    meta = vault_extract(vault_path, passphrase, out_dir=None)
    return meta


def vault_extract(vault_path: str, passphrase: str, out_dir: str | None) -> list[dict]:
    """解密档案。out_dir 为 None 时只解析清单不落盘，否则解出全部文件，返回文件清单。"""
    data = Path(vault_path).read_bytes()
    if not data.startswith(VAULT_MAGIC):
        raise ValueError("不是有效的 .nvault 档案")
    salt = data[7:23]
    nonce = data[23:35]
    ct = data[35:]
    key = derive_key(passphrase, salt)
    plain = AESGCM(key).decrypt(nonce, ct, None)

    buf = io.BytesIO(plain)
    result: list[dict] = []
    with zipfile.ZipFile(buf) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            result.append({"name": info.filename, "size": info.file_size})
            if out_dir is not None:
                target = Path(out_dir) / info.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(info.filename))
    return result
