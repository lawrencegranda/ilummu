from flask import Flask, render_template, request, Blueprint, jsonify, current_app
from edify.backend.user.routes import user

# -----------------------------------------------------------------------------
# Route Declaration
# -----------------------------------------------------------------------------
# Endpoint: /
backend = Blueprint("backend", __name__, url_prefix="/")

# -----------------------------------------------------------------------------
# Children Blueprints
# -----------------------------------------------------------------------------
backend.register_blueprint(user)
