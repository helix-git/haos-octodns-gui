"""Main routes (dashboard)."""
from flask import Blueprint, render_template, request

from extensions import db
from models import EnvVar, Provider, Zone, SyncJob

bp = Blueprint('main', __name__)


def get_user_info():
    """Extract user info from HA Ingress headers."""
    return {
        'id': request.headers.get('X-Remote-User-Id'),
        'name': request.headers.get('X-Remote-User-Display-Name')
               or request.headers.get('X-Remote-User-Name')
               or 'Unknown',
        'username': request.headers.get('X-Remote-User-Name'),
    }


@bp.route('/')
def index():
    """Dashboard with overview."""
    user = get_user_info()

    # Get counts for dashboard
    stats = {
        'env_vars': EnvVar.query.count(),
        'providers': Provider.query.count(),
        'zones': Zone.query.count(),
        'recent_jobs': SyncJob.query.order_by(SyncJob.created_at.desc()).limit(5).all()
    }

    return render_template('index.html', user=user, stats=stats)
