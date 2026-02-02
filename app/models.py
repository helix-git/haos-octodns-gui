"""SQLAlchemy database models."""
from datetime import datetime

from extensions import db


class EnvVar(db.Model):
    """Environment variables (secrets) storage."""
    __tablename__ = 'env_vars'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)  # e.g. "CLOUDFLARE_TOKEN"
    value_encrypted = db.Column(db.LargeBinary, nullable=False)  # Fernet-encrypted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<EnvVar {self.key}>'


class Provider(db.Model):
    """DNS provider configuration."""
    __tablename__ = 'providers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    provider_type = db.Column(db.String(100), nullable=False)  # e.g. "octodns_cloudflare.CloudflareProvider"
    config_json = db.Column(db.JSON, default=dict)  # Provider-specific config
    is_source = db.Column(db.Boolean, default=False)  # True = Source, False = Target
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    source_zones = db.relationship('Zone', backref='source', lazy='dynamic',
                                   foreign_keys='Zone.source_id')

    def __repr__(self):
        return f'<Provider {self.name}>'


class Zone(db.Model):
    """DNS zone configuration."""
    __tablename__ = 'zones'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # e.g. "example.com."
    source_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    options_json = db.Column(db.JSON, default=dict)  # lenient, processors, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    targets = db.relationship('ZoneTarget', backref='zone', lazy='dynamic',
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Zone {self.name}>'


class ZoneTarget(db.Model):
    """Many-to-many relationship between zones and target providers."""
    __tablename__ = 'zone_targets'

    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    target_options_json = db.Column(db.JSON, default=dict)  # Target-specific overrides

    # Relationships
    target = db.relationship('Provider', backref='zone_targets')


class SyncJob(db.Model):
    """Track sync job executions."""
    __tablename__ = 'sync_jobs'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default='pending')  # pending, running, success, failed
    trigger_type = db.Column(db.String(20))  # manual, webhook
    dry_run = db.Column(db.Boolean, default=False)
    output = db.Column(db.Text)
    diff_json = db.Column(db.JSON)  # Parsed diff for UI display
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SyncJob {self.id} {self.status}>'
