from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from edify import create_app, db
from edify.config import Config

# Create the Flask app instance using the app factory pattern
app = create_app(Config)

# Initialize Flask-Migrate
migrate = Migrate(app, db)
manager = Manager(app)

# Add Flask-Migrate commands to the manager
manager.add_command("db", MigrateCommand)

if __name__ == "__main__":
    manager.run()
