# Local Application imports
from edify.models import User


def get_jwt_header(user: User) -> dict:
    access_token = user.get_access_token()

    return {"Authorization": f"Bearer {access_token}"}
