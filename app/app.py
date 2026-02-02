"""OctoDNS GUI - Flask Application"""
import os
import sys

# Add parent directory to path for imports when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask

from extensions import db
from config import Config


def create_app(config_class=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(Config)

    # Ensure directories exist
    zone_path = app.config.get('ZONE_FILE_PATH', '/config/octodns')
    os.makedirs(zone_path, exist_ok=True)
    os.makedirs(app.config.get('CONFIG_OUTPUT_DIR', os.path.join(zone_path, 'configs')), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from routes.main import bp as main_bp
    from routes.environment import bp as environment_bp
    from routes.providers import bp as providers_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(environment_bp)
    app.register_blueprint(providers_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


# Create app instance for running directly
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8100, debug=False)
