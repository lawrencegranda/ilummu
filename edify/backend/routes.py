# Third-Party Framework imports
from flask import Blueprint, Flask, jsonify, render_template, request

# Local Application imports
from edify.backend.data.routes import data
from edify.backend.user.routes import user
from edify.backend.offer.routes import offer


# -----------------------------------------------------------------------------
# Route Blueprint
# -----------------------------------------------------------------------------
# Endpoint: /
backend = Blueprint("backend", __name__, url_prefix="/")


# -----------------------------------------------------------------------------
# Children Blueprints
# -----------------------------------------------------------------------------
backend.register_blueprint(user)
backend.register_blueprint(offer)
backend.register_blueprint(data)
