"""Database initialization and configuration."""

# Third-Party Framework imports
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize database
db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """Initialize database and migrations."""
    db.init_app(app)
    migrate.init_app(app, db)
