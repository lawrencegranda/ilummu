# Third-Party Framework imports
from flask_jwt_extended import create_access_token

# Local Application imports
from edify.models import User


def get_jwt_header(user: User) -> dict:
    access_token = create_access_token(identity=user.id)

    return {"Authorization": f"Bearer {access_token}"}
