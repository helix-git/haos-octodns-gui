"""Environment variables (secrets) management routes."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import EnvVar
from services.crypto import decrypt_value, encrypt_value

bp = Blueprint('environment', __name__, url_prefix='/environment')


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
    """List all environment variables."""
    user = get_user_info()
    env_vars = EnvVar.query.order_by(EnvVar.key).all()
    return render_template('environment/index.html', env_vars=env_vars, user=user)


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create a new environment variable."""
    user = get_user_info()

    if request.method == 'POST':
        key = request.form.get('key', '').strip().upper()
        value = request.form.get('value', '')

        # Validate
        if not key:
            flash('Key ist erforderlich.', 'danger')
            return render_template('environment/create.html', user=user)

        if not value:
            flash('Wert ist erforderlich.', 'danger')
            return render_template('environment/create.html', user=user)

        # Check for valid key format
        if not key.replace('_', '').isalnum():
            flash('Key darf nur Buchstaben, Zahlen und Unterstriche enthalten.', 'danger')
            return render_template('environment/create.html', user=user)

        if EnvVar.query.filter_by(key=key).first():
            flash('Eine Variable mit diesem Key existiert bereits.', 'danger')
            return render_template('environment/create.html', user=user)

        # Encrypt and store
        env_var = EnvVar(
            key=key,
            value_encrypted=encrypt_value(value)
        )
        db.session.add(env_var)
        db.session.commit()

        flash(f'Variable "{key}" wurde erstellt.', 'success')
        return redirect(url_for('environment.index'))

    return render_template('environment/create.html', user=user)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit an environment variable."""
    user = get_user_info()
    env_var = EnvVar.query.get_or_404(id)

    if request.method == 'POST':
        value = request.form.get('value', '')

        if not value:
            flash('Wert ist erforderlich.', 'danger')
            return render_template('environment/edit.html', env_var=env_var, user=user)

        env_var.value_encrypted = encrypt_value(value)
        db.session.commit()

        flash(f'Variable "{env_var.key}" wurde aktualisiert.', 'success')
        return redirect(url_for('environment.index'))

    return render_template('environment/edit.html', env_var=env_var, user=user)


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete an environment variable."""
    env_var = EnvVar.query.get_or_404(id)
    key = env_var.key

    db.session.delete(env_var)
    db.session.commit()

    flash(f'Variable "{key}" wurde gelöscht.', 'success')
    return redirect(url_for('environment.index'))
