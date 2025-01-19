"""Base model classes and metaclasses."""

# Standard Library imports
from abc import ABCMeta, ABC, abstractmethod
from typing import Dict, Any, List

# Third-Party Framework imports
from flask_login import UserMixin

# Local Application imports
from edify import db


class ModelABCMeta(type(db.Model), ABCMeta):
    """Metaclass combining SQLAlchemy's Model metaclass with ABC metaclass."""


class BaseModel(db.Model, ABC, metaclass=ModelABCMeta):
    """Abstract base class for all models."""

    __abstract__ = True

    @abstractmethod
    def __repr__(self) -> str:
        """Return string representation of the model instance."""

    @abstractmethod
    def to_dict(self, simplified=False) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Args:
            simplified (bool): Whether to return a simplified version of the dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the model.
        """

    @staticmethod
    def to_dict_all(elem_list: List["BaseModel"]) -> List[Dict[str, Any]]:
        """
        Convert a list of model instances to a list of dictionaries.

        Args:
            elem_list: List of BaseModel instances to convert.

        Returns:
            List of dictionary representations of the model instances.
        """
        return [elem.to_dict(simplified=False) for elem in elem_list]


class UserModelABCMeta(type(BaseModel), type(UserMixin)):
    """Metaclass combining BaseModel and UserMixin metaclasses for user authentication."""
