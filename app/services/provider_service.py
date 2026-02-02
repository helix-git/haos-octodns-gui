"""Provider management service.

Handles provider schema loading, version detection, and activation status.
"""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from flask import current_app

from models import EnvVar, Provider
from services.crypto import decrypt_value


@dataclass
class ProviderInfo:
    """Complete information about a provider type."""
    class_name: str
    name: str
    is_source: bool
    documentation: str
    package_name: str
    package_git: Optional[str]
    installed_version: Optional[str]
    is_enabled: bool
    fields: list
    capabilities: dict = field(default_factory=dict)


def _get_schema_dir() -> Path:
    """Get path to provider schemas directory."""
    return Path(__file__).parent.parent / 'provider_schemas'


def _load_schema(class_name: str) -> Optional[dict]:
    """Load schema for a provider class.

    Args:
        class_name: Full class path (e.g. octodns_cloudflare.CloudflareProvider)

    Returns:
        Schema dict or None if not found.
    """
    # Convert class name to schema filename
    # octodns_cloudflare.CloudflareProvider -> octodns_cloudflare.yaml
    module_name = class_name.split('.')[0]
    schema_file = _get_schema_dir() / f'{module_name}.yaml'

    if not schema_file.exists():
        return None

    with open(schema_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _get_all_schemas() -> list[dict]:
    """Load all provider schemas."""
    schemas = []
    schema_dir = _get_schema_dir()

    if not schema_dir.exists():
        return schemas

    for schema_file in schema_dir.glob('*.yaml'):
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
            if schema:
                schemas.append(schema)

    return schemas


def _short_name_from_class(class_name: str) -> str:
    """Extract short provider name from class path.

    e.g. 'octodns_cloudflare.CloudflareProvider' -> 'cloudflare'
    """
    module = class_name.split('.')[0]
    if module.startswith('octodns_'):
        return module[8:]
    return module


def _get_installed_version(package_name: str) -> Optional[str]:
    """Get installed version of a package.

    Args:
        package_name: PyPI package name (e.g. 'octodns-cloudflare')

    Returns:
        Version string or None if not installed.
    """
    if not package_name:
        return None

    try:
        from importlib.metadata import version, PackageNotFoundError
        # Normalize package name
        normalized = package_name.lower().replace('_', '-')
        return version(normalized)
    except PackageNotFoundError:
        return None
    except Exception:
        return None


def get_enabled_providers_from_config() -> dict[str, bool]:
    """Load enabled providers from HA addon config.

    Reads from /data/options.json (HA addon options) or falls back
    to a local config file for development.

    Returns:
        Dict mapping provider short names to enabled status.
    """
    # Try HA addon options first
    ha_options_path = '/data/options.json'
    if os.path.exists(ha_options_path):
        try:
            with open(ha_options_path, 'r') as f:
                options = json.load(f)
            return options.get('providers', {})
        except Exception as e:
            current_app.logger.warning(f"Failed to load addon options: {e}")

    # Fallback: check for local development config
    dev_config = Path(current_app.config.get('ZONE_FILE_PATH', './zones')) / 'addon_options.yaml'
    if dev_config.exists():
        try:
            with open(dev_config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('providers', {})
        except Exception:
            pass

    # Default: all providers enabled
    return {}


def get_provider_info(class_name: str) -> Optional[ProviderInfo]:
    """Get complete information about a provider type.

    Args:
        class_name: Full provider class path.

    Returns:
        ProviderInfo or None if schema not found.
    """
    schema = _load_schema(class_name)
    if not schema:
        return None

    package = schema.get('package', {})
    package_name = package.get('name', '')
    package_git = package.get('git')
    short_name = _short_name_from_class(class_name)

    # Check if enabled in config
    enabled_providers = get_enabled_providers_from_config()
    # If no config exists (empty dict), default to enabled
    is_enabled = enabled_providers.get(short_name, True) if enabled_providers else True

    # Get installed version
    installed_version = _get_installed_version(package_name)

    # Build capabilities
    fields = schema.get('fields', [])
    capabilities = {
        'is_source': schema.get('is_source', False),
        'supports_env_ref': any(f.get('env_ref', False) for f in fields),
        'field_types': list(set(f.get('type', 'text') for f in fields)),
    }

    return ProviderInfo(
        class_name=class_name,
        name=schema.get('name', class_name),
        is_source=schema.get('is_source', False),
        documentation=schema.get('documentation', ''),
        package_name=package_name,
        package_git=package_git,
        installed_version=installed_version,
        is_enabled=is_enabled,
        fields=fields,
        capabilities=capabilities,
    )


def get_all_provider_info() -> list[ProviderInfo]:
    """Get info for all available provider types.

    Returns:
        List of ProviderInfo for all schema-defined providers.
    """
    providers = []
    for schema in _get_all_schemas():
        class_name = schema.get('class')
        if class_name:
            info = get_provider_info(class_name)
            if info:
                providers.append(info)
    return providers


def get_enabled_provider_info() -> list[ProviderInfo]:
    """Get info for only enabled provider types.

    Returns:
        List of ProviderInfo for enabled providers only.
    """
    return [p for p in get_all_provider_info() if p.is_enabled]


def get_available_env_vars() -> list[dict]:
    """Get list of available environment variables for dropdown.

    Returns:
        List of dicts with 'key' and 'reference' (env/KEY format).
    """
    env_vars = EnvVar.query.order_by(EnvVar.key).all()
    return [
        {'key': ev.key, 'reference': f'env/{ev.key}'}
        for ev in env_vars
    ]


def resolve_env_reference(value: str) -> tuple[Optional[str], bool, Optional[str]]:
    """Resolve an env/ reference to its actual value.

    Args:
        value: Config value, possibly 'env/VARIABLE_NAME'.

    Returns:
        Tuple of (resolved_value, is_env_ref, env_var_name).
    """
    if not value or not isinstance(value, str):
        return (value, False, None)

    if not value.startswith('env/'):
        return (value, False, None)

    env_var_name = value[4:]

    # Look up in database
    env_var = EnvVar.query.filter_by(key=env_var_name).first()
    if env_var:
        try:
            resolved = decrypt_value(env_var.value_encrypted)
            return (resolved, True, env_var_name)
        except Exception:
            return (None, True, env_var_name)

    return (None, True, env_var_name)


def validate_provider_config(provider_type: str, config: dict) -> list[str]:
    """Validate provider configuration against schema.

    Args:
        provider_type: Full class path.
        config: Configuration dict to validate.

    Returns:
        List of validation error messages (empty if valid).
    """
    errors = []
    schema = _load_schema(provider_type)

    if not schema:
        return [f"Unbekannter Provider-Typ: {provider_type}"]

    for field_def in schema.get('fields', []):
        field_name = field_def['name']
        value = config.get(field_name)

        # Check required fields
        if field_def.get('required', False):
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"Feld '{field_def.get('label', field_name)}' ist erforderlich")

        # Type-specific validation
        if value is not None and value != '':
            field_type = field_def.get('type', 'text')

            if field_type == 'number':
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append(f"Feld '{field_def.get('label', field_name)}' muss eine Zahl sein")

            if field_type == 'select':
                options = field_def.get('options', [])
                if value not in options:
                    errors.append(f"Ungültige Auswahl für '{field_def.get('label', field_name)}'")

    return errors
