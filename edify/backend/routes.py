"""
This module is used to define the backend routes.
"""

# Third-Party Framework imports
from flask import Blueprint

# Local Application imports
from edify.backend.data.routes import data
from edify.backend.user.routes import user
from edify.backend.offer.routes import offer
from edify.backend.question.routes import question
from edify.backend.oauth.routes import oauth

# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /backend
backend = Blueprint("backend", __name__, url_prefix="/backend")

# -----------------------------------------------------------------------------
# Children Blueprints
# -----------------------------------------------------------------------------
backend.register_blueprint(user)
backend.register_blueprint(offer)
backend.register_blueprint(question)
backend.register_blueprint(data)
backend.register_blueprint(oauth)
