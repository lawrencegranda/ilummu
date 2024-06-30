import os
from edify.utils.constants import EdifyEnvironments


class Config:
    MAINTENANCE_MODE = os.environ["MAINTENANCE_MODE"] == 1

    SECRET_KEY = os.environ["SECRET_KEY"]
    JWT_SECRET_KEY = SECRET_KEY

    if not any(member.name == os.environ["ENV"] for member in EdifyEnvironments):
        raise Exception(f"Invalid Environment {os.environ['ENV']}")

    ENV = os.environ["ENV"]

    if ENV == EdifyEnvironments.PRODUCTION.value:
        raise Exception("Production environment not in service.")
    elif ENV == EdifyEnvironments.LOCAL.value:
        SQLALCHEMY_DATABASE_URI = os.environ["DB_URL"]
    elif ENV == EdifyEnvironments.TEST.value:
        SQLALCHEMY_DATABASE_URI = "sqlite:///site.db"
