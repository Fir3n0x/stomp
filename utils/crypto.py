"""
crypto.py - RSA key generation and CRX ID utilities for stomp.py
"""

import base64
import hashlib
import hmac
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_extension_keys() -> tuple[str, str, str]:
    """
    Generate RSA key pair and CRX ID for Chrome extension.

    Returns:
        tuple: (crx_id, public_key_b64, private_key_b64)
    """
    try:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
    except Exception as e:
        raise Exception(f"Failed to generate RSA key: {e}")

    public_key = private_key.public_key()

    try:
        pub_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    except Exception as e:
        raise Exception(f"Failed to marshal public key: {e}")

    sha256_hash = hashlib.sha256(pub_key_bytes).digest()
    crx_id = _translate_crx_id(sha256_hash[:16].hex())

    pub_key_b64 = base64.b64encode(pub_key_bytes).decode("utf-8")

    try:
        priv_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    except Exception as e:
        raise Exception(f"Failed to serialize private key: {e}")

    priv_key_b64 = base64.b64encode(priv_key_bytes).decode("utf-8")

    return crx_id, pub_key_b64, priv_key_b64


def crx_id_from_public_key(pub_key_bytes: bytes) -> str:
    """Derive a CRX extension ID from raw DER public key bytes."""
    digest = hashlib.sha256(pub_key_bytes).hexdigest()[:32]
    return "".join(chr(ord("a") + int(c, 16)) for c in digest)


def _translate_crx_id(hex_str: str) -> str:
    """Translate first 16 hex bytes to Chrome extension ID format (a-p alphabet)."""
    table = {
        "0": "a", "1": "b", "2": "c", "3": "d",
        "4": "e", "5": "f", "6": "g", "7": "h",
        "8": "i", "9": "j", "a": "k", "b": "l",
        "c": "m", "d": "n", "e": "o", "f": "p",
    }
    return "".join(table.get(c, c) for c in hex_str)

def _remove_empty(d):
    """Recursively strip falsy values (except False and 0) from dicts/lists."""
    if isinstance(d, dict):
        keys_to_del = [k for k, v in d.items()
                       if not v and v not in (False, 0)
                       and isinstance(v, (dict, list))]
        for k in keys_to_del:
            del d[k]
        for v in d.values():
            _remove_empty(v)
    elif isinstance(d, list):
        d[:] = [i for i in d if i or i in (False, 0)]
 
 
def calculate_hmac(value, path: str, sid_or_uuid: str, seed: bytes) -> str:
    if isinstance(value, dict):
        _remove_empty(value)

    json_value = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    json_value = json_value.replace("<", "\\u003C").replace("\\u2122", "™")

    # If SID Windows (start with S-1-...), remove RID
    if sid_or_uuid.startswith("S-1-"):
        device_id = "-".join(sid_or_uuid.split("-")[:-1])  # strip RID

    # If macOS (Hardware UUID) or Linux (Machine ID), keep all the value 
    else:
        device_id = sid_or_uuid.strip()

    # Build msg for HMAC-SHA256
    message = device_id + path + json_value
    h = hmac.new(seed, message.encode("utf-8"), hashlib.sha256)
    return h.hexdigest().upper()


def calc_supermac(data: dict, sid_or_uuid: str, seed: bytes) -> str:
    
    # If SID Windows (start with S-1-...), remove RID
    if sid_or_uuid.startswith("S-1-"):
        device_id = "-".join(sid_or_uuid.split("-")[:-1])  # strip RID

    # If macOS (Hardware UUID) or Linux (Machine ID), keep all the value 
    else:
        device_id = sid_or_uuid.strip()

    macs_json = json.dumps(data["protection"]["macs"], separators=(",", ":"))
    super_msg = device_id + macs_json
    h = hmac.new(seed, super_msg.encode("utf-8"), hashlib.sha256)
    return h.hexdigest().upper()
