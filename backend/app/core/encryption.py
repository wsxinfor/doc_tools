"""Fernet 对称加密工具，用于 SystemConfig 敏感值加密存储。

密钥派生自 JWT_SECRET_KEY（已在启动时校验非空），无需额外配置。
"""
import base64
import hashlib

from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    from app.core.config import settings  # noqa: PLC0415  # 避免循环导入

    # 从 JWT_SECRET_KEY 派生 32 字节密钥
    key_bytes = hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_value(plain: str) -> str:
    """加密明文字符串，返回 Base64 密文。"""
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_value(cipher: str) -> str:
    """解密密文字符串，返回明文。"""
    return _get_fernet().decrypt(cipher.encode()).decode()
