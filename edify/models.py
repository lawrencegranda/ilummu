from edify import db, jwt
from flask_login import UserMixin
from flask_jwt_extended import current_user
from datetime import datetime, timedelta
from flask import current_app, jsonify
from collections import OrderedDict, defaultdict
from functools import wraps
from http import HTTPStatus


def manager_required(
    minimum_manager_level, admin_minimum_impersonnation_level=AuthLevel.SUPER_ADMIN
):
    """
    Decorator for managing access to endpoints based on manager level.
    1) Checks that the user is of the desired manager level.
    2) If it is an impersonating-admin, check that it is of the correct leve.
    """

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.is_manager < minimum_manager_level.value:
                return jsonify({"error": "Forbidden"}), HTTPStatus.FORBIDDEN

            # If the user is an admin impersonating a manager.
            if current_user.is_manager >= AuthLevel.OVERSEER_ADMIN.value:
                if current_user.is_manager < admin_minimum_impersonnation_level.value:
                    return jsonify({"error": "Forbidden"}), HTTPStatus.FORBIDDEN

            return function(*args, **kwargs)

        return wrapper

    return decorator


# Decorator to enable/disable routes based on Maintenance Mode.
def maintenance_mode(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_app.config["MAINTENANCE_MODE"]:
            return (
                jsonify(
                    {"error": "App in maintenance mode", "type": "MAINTENANCE_MODE"}
                ),
                HTTPStatus.FORBIDDEN,
            )

        return function(*args, **kwargs)

    return wrapper


# Register a callback function that loads a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data) -> "User":
    identity = jwt_data["sub"]
    return User.query.get(int(identity))


# The login_manager extension requires the User Model
# to have certain attributes and methods:
# - is_authenticated: returns True if user has provided valid credentials
# - is_active:
# - is_anonymus:
# - get_id():
# Instead of creating these directly in the User model,
# we inherit from the class UserMixin which adds them
class User(db.Model, UserMixin):
    """
    Table that contains user information

    Entries are created in the sign up route
    Entries are updated in the account editing route
    """

    # Primary key that identifies the user
    # (MUST be called `id` for login_manager)
    id = db.Column(db.Integer, primary_key=True)

    # User's first name
    firstname = db.Column(db.String(20), nullable=False)

    # User's last name
    lastname = db.Column(db.String(30), nullable=False)

    # User's school/university
    school = db.Column(db.String(30), unique=False, nullable=False)

    # User's major
    major = db.Column(db.String(30), unique=False, nullable=False)

    # User's graduation year
    graduation = db.Column(db.DateTime, unique=False, nullable=False)

    # User's email
    # Must be unique
    email = db.Column(db.String(120), unique=True, nullable=False)

    # User's phone number
    # Must be unique
    phone = db.Column(db.String(50), unique=True, nullable=False)

    # Account password
    # Must be hashed
    password = db.Column(db.String(90), nullable=False)

    # Entry creation date (to keep track)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # API authentication token, token is given to user upon login to authenticate future requests
    # This is part of the API token-based authentication schema
    token = db.Column(db.String(300), nullable=True)

    token_last_refresh = db.Column(db.DateTime, nullable=True)

    # Field that indicates the level of permissions form 0 to 4, 1 is for the normal user
    is_manager = db.Column(db.Integer, nullable=False)

    # Whether or not the user verified it's email. NOT IMPLEMENTED
    mail_is_verified = db.Column(db.Boolean, nullable=False, default=False)

    # Whether or not the user verified it's phone number. NOT IMPLEMENTED
    phone_is_verified = db.Column(db.Boolean, nullable=False, default=False)

    # Indicates whether the user is a mock user or not.
    is_mock = db.Column(db.Boolean, nullable=False, default=False)

    # Preferred language by the user for display.
    language = db.Column(
        db.String(10), nullable=False, default=SupportedLanguages.ENGLISH.value
    )

    # Profile picture
    image_file = db.Column(db.String(20), nullable=False, default="default.jpg")

    def get_reset_token(self, expires_sec=18000):
        s = Serializer(current_app.config["SECRET_KEY"], expires_sec)
        return s.dumps({"user_id": self.id}).decode("utf8")

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token)["id"]
        except Exception:
            return None
        return User.query.get(user_id)

    def generate_auth_token(self, expires_sec=1000):
        s = Serializer(current_app.config["SECRET_KEY"], expires_sec=expires_sec)
        return s.dumps({"id": self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except Exception:
            return None  # valid token, but expired or invalid token
        user = User.query.get(data["id"])
        return user

    def __repr__(self):
        return f"({self.id}, {self.firstname} {self.lastname}, {self.email}\n"

    def to_dict(
        self,
        simplified=False,
    ):
        return_dict = {
            "id": self.id,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email,
            "phone": self.phone,
            "school": self.school,
            "major": self.major,
            "language": self.language,
        }

        # Add all extra information
        if not simplified:
            return_dict["is_manager"] = self.is_manager
            return_dict["mail_is_verified"] = self.mail_is_verified
            return_dict["phone_is_verified"] = self.phone_is_verified
            return_dict["is_mock"] = self.is_mock

        return return_dict
