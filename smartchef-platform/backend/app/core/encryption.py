"""
T139 FR-036: AES-256-GCM 数据加密模块。

用于对话历史、知识库文档等敏感数据的存储加密。
密钥从环境变量 ENCRYPTION_KEY 加载（32 字节，base64 编码）。
"""
import base64
import hashlib
import os
import secrets
import logging
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

# 密钥长度（AES-256 需要 32 字节）
_KEY_SIZE = 32
# nonce 长度（GCM 推荐 12 字节）
_NONCE_SIZE = 12


def _get_key() -> bytes:
    """从环境变量 ENCRYPTION_KEY 加载密钥。支持 hex 或 base64 编码的 32 字节。"""
    raw = os.environ.get("ENCRYPTION_KEY", "").strip()
    if not raw or len(raw) < 32:
        raise ValueError(
            "ENCRYPTION_KEY 未设置或无效。需 32 字节密钥，可 hex 编码(64 字符)或 base64 编码。"
            "示例: openssl rand -base64 32"
        )
    # 尝试 base64 解码
    try:
        key = base64.b64decode(raw)
    except Exception:
        try:
            key = bytes.fromhex(raw)
        except Exception:
            raise ValueError("ENCRYPTION_KEY 必须是有效的 base64 或 hex 编码")
    if len(key) != _KEY_SIZE:
        key = hashlib.sha256(key).digest()
    return key


def encrypt_text(plaintext: str) -> str:
    """
    使用 AES-256-GCM 加密文本。

    Args:
        plaintext: 明文

    Returns:
        base64 编码的密文，格式: base64(nonce + ciphertext + tag)
    """
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(_NONCE_SIZE)
    plainbytes = plaintext.encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, plainbytes, None)
    combined = nonce + ciphertext
    return base64.b64encode(combined).decode("ascii")


def decrypt_text(encrypted_base64: str) -> str:
    """
    使用 AES-256-GCM 解密文本。

    Args:
        encrypted_base64: base64 编码的密文（encrypt_text 输出）

    Returns:
        解密后的明文
    """
    key = _get_key()
    aesgcm = AESGCM(key)
    combined = base64.b64decode(encrypted_base64)
    if len(combined) < _NONCE_SIZE + 16:
        raise ValueError("密文格式无效或已损坏")
    nonce = combined[:_NONCE_SIZE]
    ciphertext = combined[_NONCE_SIZE:]
    plainbytes = aesgcm.decrypt(nonce, ciphertext, None)
    return plainbytes.decode("utf-8")


def encrypt_text_optional(plaintext: Optional[str]) -> Optional[str]:
    """
    可选加密：若 plaintext 为 None 或空，则返回 None。
    """
    if plaintext is None or plaintext == "":
        return None
    return encrypt_text(plaintext)


def decrypt_text_optional(encrypted_base64: Optional[str]) -> Optional[str]:
    """
    可选解密：若 encrypted_base64 为 None 或空，则返回 None。
    """
    if encrypted_base64 is None or encrypted_base64 == "":
        return None
    return decrypt_text(encrypted_base64)
