"""Core components initialization."""

from edify.core.database import db, migrate, init_db
from edify.core.extensions import bcrypt, jwt, mail, init_extensions

__all__ = [
    "db",
    "migrate",
    "init_db",
    "bcrypt",
    "jwt",
    "mail",
    "init_extensions",
]
