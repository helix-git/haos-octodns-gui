"""Provider management routes."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Provider
from services.provider_service import (
    get_all_provider_info,
    get_available_env_vars,
    get_enabled_provider_info,
    get_provider_info,
    validate_provider_config,
)

bp = Blueprint('providers', __name__, url_prefix='/providers')


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
    """List all configured providers with extended info."""
    user = get_user_info()
    providers = Provider.query.order_by(Provider.name).all()

    # Get provider info with versions and capabilities
    provider_info_map = {
        info.class_name: info
        for info in get_all_provider_info()
    }

    # Enrich providers with additional info
    enriched_providers = []
    for provider in providers:
        info = provider_info_map.get(provider.provider_type)
        enriched_providers.append({
            'provider': provider,
            'info': info,
            'version': info.installed_version if info else None,
            'is_enabled': info.is_enabled if info else True,
        })

    # Get available (enabled) provider types for display
    available_types = get_enabled_provider_info()

    return render_template(
        'providers/index.html',
        providers=enriched_providers,
        available_types=available_types,
        user=user,
    )


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create a new provider."""
    user = get_user_info()
    provider_infos = get_enabled_provider_info()
    env_vars = get_available_env_vars()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        provider_type = request.form.get('provider_type', '')

        # Validate
        if not name:
            flash('Name ist erforderlich.', 'danger')
            return render_template('providers/create.html',
                                   provider_types=provider_infos,
                                   env_vars=env_vars, user=user)

        if Provider.query.filter_by(name=name).first():
            flash('Ein Provider mit diesem Namen existiert bereits.', 'danger')
            return render_template('providers/create.html',
                                   provider_types=provider_infos,
                                   env_vars=env_vars, user=user)

        info = get_provider_info(provider_type)
        if not info:
            flash('Ungültiger Provider-Typ.', 'danger')
            return render_template('providers/create.html',
                                   provider_types=provider_infos,
                                   env_vars=env_vars, user=user)

        if not info.is_enabled:
            flash('Dieser Provider-Typ ist nicht aktiviert.', 'danger')
            return render_template('providers/create.html',
                                   provider_types=provider_infos,
                                   env_vars=env_vars, user=user)

        # Build config from form fields
        config = _extract_config_from_form(info.fields)

        # Validate config
        errors = validate_provider_config(provider_type, config)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('providers/create.html',
                                   provider_types=provider_infos,
                                   env_vars=env_vars, user=user)

        # Create provider
        provider = Provider(
            name=name,
            provider_type=provider_type,
            config_json=config,
            is_source=info.is_source
        )
        db.session.add(provider)
        db.session.commit()

        flash(f'Provider "{name}" wurde erstellt.', 'success')
        return redirect(url_for('providers.index'))

    return render_template('providers/create.html',
                           provider_types=provider_infos,
                           env_vars=env_vars, user=user)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit an existing provider."""
    user = get_user_info()
    provider = Provider.query.get_or_404(id)
    info = get_provider_info(provider.provider_type)
    env_vars = get_available_env_vars()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()

        # Validate
        if not name:
            flash('Name ist erforderlich.', 'danger')
            return render_template('providers/edit.html', provider=provider,
                                   type_info=info, env_vars=env_vars, user=user)

        existing = Provider.query.filter_by(name=name).first()
        if existing and existing.id != provider.id:
            flash('Ein Provider mit diesem Namen existiert bereits.', 'danger')
            return render_template('providers/edit.html', provider=provider,
                                   type_info=info, env_vars=env_vars, user=user)

        # Update config
        config = _extract_config_from_form(info.fields if info else [])

        # Validate config
        if info:
            errors = validate_provider_config(provider.provider_type, config)
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('providers/edit.html', provider=provider,
                                       type_info=info, env_vars=env_vars, user=user)

        provider.name = name
        provider.config_json = config
        db.session.commit()

        flash(f'Provider "{name}" wurde aktualisiert.', 'success')
        return redirect(url_for('providers.index'))

    return render_template('providers/edit.html', provider=provider,
                           type_info=info, env_vars=env_vars, user=user)


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete a provider."""
    provider = Provider.query.get_or_404(id)
    name = provider.name

    # Check if provider is in use
    if provider.source_zones.count() > 0:
        flash(f'Provider "{name}" wird als Source verwendet und kann nicht gelöscht werden.', 'danger')
        return redirect(url_for('providers.index'))

    if provider.zone_targets:
        flash(f'Provider "{name}" wird als Target verwendet und kann nicht gelöscht werden.', 'danger')
        return redirect(url_for('providers.index'))

    db.session.delete(provider)
    db.session.commit()

    flash(f'Provider "{name}" wurde gelöscht.', 'success')
    return redirect(url_for('providers.index'))


@bp.route('/type-fields')
def type_fields():
    """Get form fields for a provider type (HTMX partial)."""
    # HTMX sends select value as 'provider_type', also support 'type' for direct calls
    provider_type = request.args.get('provider_type', '') or request.args.get('type', '')
    config = {}

    # For edit mode, get existing config
    provider_id = request.args.get('provider_id')
    if provider_id:
        provider = Provider.query.get(provider_id)
        if provider:
            config = provider.config_json or {}

    info = get_provider_info(provider_type)
    env_vars = get_available_env_vars()

    if not info:
        return '<p style="color: var(--secondary-text-color);">Bitte wähle einen Provider-Typ aus.</p>'

    return render_template('providers/_type_fields.html',
                           type_info=info,
                           config=config,
                           env_vars=env_vars)


def _extract_config_from_form(fields: list) -> dict:
    """Extract provider config from form submission.

    Args:
        fields: List of field definitions from schema.

    Returns:
        Config dict.
    """
    config = {}
    for field in fields:
        field_name = field['name']
        field_type = field.get('type', 'text')

        value = request.form.get(f"config_{field_name}", '').strip()

        if value:
            if field_type == 'checkbox':
                config[field_name] = value == 'on'
            elif field_type == 'number':
                try:
                    config[field_name] = int(value)
                except ValueError:
                    try:
                        config[field_name] = float(value)
                    except ValueError:
                        config[field_name] = value
            else:
                config[field_name] = value
        elif field_type == 'checkbox':
            config[field_name] = False

    return config
