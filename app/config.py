"""Flask application configuration."""
import os
from pathlib import Path

# Get absolute path to project root (parent of app/)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Zone file path - use env var or fallback based on context
    # For local dev, resolve relative to project root
    _zone_path_env = os.environ.get('ZONE_FILE_PATH', '')
    if _zone_path_env:
        ZONE_FILE_PATH = str(Path(_zone_path_env).resolve())
    else:
        ZONE_FILE_PATH = str(PROJECT_ROOT / 'zones')

    # Database - SQLite default, MariaDB optional
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite')


def get_database_uri():
    """Get database URI based on configuration."""
    db_type = os.environ.get('DATABASE_TYPE', 'sqlite')

    if db_type == 'mariadb':
        host = os.environ.get('MARIADB_HOST', 'core-mariadb')
        port = os.environ.get('MARIADB_PORT', '3306')
        database = os.environ.get('MARIADB_DATABASE', 'octodns')
        username = os.environ.get('MARIADB_USERNAME', 'octodns')
        password = os.environ.get('MARIADB_PASSWORD', '')
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    else:
        # Use Config.ZONE_FILE_PATH which is already resolved to absolute path
        zone_path = Config.ZONE_FILE_PATH
        db_path = os.environ.get('DATABASE_PATH') or str(Path(zone_path) / 'octodns.db')
        return f'sqlite:///{db_path}'


# Set database URI
Config.SQLALCHEMY_DATABASE_URI = get_database_uri()
Config.SQLALCHEMY_TRACK_MODIFICATIONS = False

# Fernet key for encrypting secrets
Config.FERNET_KEY = os.environ.get('FERNET_KEY') or None

# OctoDNS config output directory
Config.CONFIG_OUTPUT_DIR = os.environ.get('CONFIG_OUTPUT_DIR') or \
    str(Path(Config.ZONE_FILE_PATH) / 'configs')
