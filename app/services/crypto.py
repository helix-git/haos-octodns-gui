"""Cryptography utilities for encrypting secrets."""
import os

import yaml
from cryptography.fernet import Fernet
from flask import current_app

# Default paths and key names
HA_SECRETS_PATH = '/config/secrets.yaml'
DEFAULT_FERNET_KEY_NAME = 'octodns_fernet_key'


def _load_key_from_ha_secrets() -> bytes | None:
    """Load Fernet key from Home Assistant secrets.yaml.

    Returns:
        Fernet key as bytes, or None if not found.
    """
    secrets_path = current_app.config.get('HA_SECRETS_PATH', HA_SECRETS_PATH)
    key_name = current_app.config.get('FERNET_KEY_NAME', DEFAULT_FERNET_KEY_NAME)

    if not os.path.exists(secrets_path):
        return None

    try:
        with open(secrets_path, 'r', encoding='utf-8') as f:
            secrets = yaml.safe_load(f)

        if secrets and key_name in secrets:
            key = secrets[key_name]
            if isinstance(key, str):
                return key.encode()
            return key
    except Exception as e:
        current_app.logger.warning(f"Failed to load Fernet key from secrets.yaml: {e}")

    return None


def get_fernet_key() -> bytes:
    """Get or generate the Fernet encryption key.

    Priority:
    1. FERNET_KEY environment variable / config
    2. Home Assistant secrets.yaml (key: octodns_fernet_key)
    3. Local .fernet_key file (auto-generated)
    """
    # 1. Check environment/config
    key = current_app.config.get('FERNET_KEY')
    if key:
        if isinstance(key, str):
            key = key.encode()
        return key

    # 2. Try HA secrets.yaml
    key = _load_key_from_ha_secrets()
    if key:
        current_app.logger.info("Using Fernet key from Home Assistant secrets.yaml")
        return key

    # 3. Fallback to local .fernet_key file
    zone_path = current_app.config.get('ZONE_FILE_PATH', '/config/octodns')
    key_file = os.path.join(zone_path, '.fernet_key')

    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()

    # Generate new key
    key = Fernet.generate_key()
    os.makedirs(os.path.dirname(key_file), exist_ok=True)
    with open(key_file, 'wb') as f:
        f.write(key)
    os.chmod(key_file, 0o600)

    current_app.logger.info(f"Generated new Fernet key at {key_file}")
    return key


def generate_fernet_key() -> str:
    """Generate a new Fernet key for manual setup.

    Returns:
        Base64-encoded Fernet key as string (suitable for secrets.yaml).
    """
    return Fernet.generate_key().decode()


def encrypt_value(plaintext: str) -> bytes:
    """Encrypt a plaintext string."""
    fernet = Fernet(get_fernet_key())
    return fernet.encrypt(plaintext.encode())


def decrypt_value(ciphertext: bytes) -> str:
    """Decrypt a ciphertext to string."""
    fernet = Fernet(get_fernet_key())
    return fernet.decrypt(ciphertext).decode()
