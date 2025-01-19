"""Academic-related models."""

# Standard Library imports
from typing import Dict, Any

# Third-Party Framework imports
from sqlalchemy import Index, UniqueConstraint, event

# Local Application imports
from edify import db
from edify.models.base import BaseModel
from edify.utils.utils import (
    format_lower_case,
    format_title_case,
    format_upper_case,
    validate_email_postfix,
)


class Major(BaseModel):
    """
    Table that contains major information

    Entries are created to list available majors.
    """

    __table_args__ = (
        Index("ix_major_academic_field_id", "academic_field_id"),
        UniqueConstraint("name", "academic_field_id", name="_major_field_uc"),
    )

    # Primary key that identifies the major
    id = db.Column(db.Integer, primary_key=True)

    # Major name, titlecase
    name = db.Column(db.String(100), nullable=False)

    # AcademicField associated with the major
    # Many-to-One relationship with AcademicField model
    academic_field_id = db.Column(
        db.Integer, db.ForeignKey("academic_field.id"), nullable=False
    )
    academic_field = db.relationship("AcademicField", backref="majors", lazy=True)

    # School associated with the major
    # Many-to-One relationship with School model
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), nullable=False)
    school = db.relationship("School", backref="majors", lazy=True)

    def __repr__(self):
        return f"Major({self.id}, {self.name})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "academic_field_id": self.academic_field_id,
            "school_id": self.school_id,
        }

    @staticmethod
    def validator(_mapper, connection, target):
        """Validate major data, ensuring school consistency with academic field."""
        academic_field = connection.execute(
            db.select(AcademicField).filter_by(id=target.academic_field_id)
        ).fetchone()

        if academic_field.school_id != target.school_id:
            raise ValueError(
                f'MAJOR MODEL: School ("{target.school_id}") is inconsistent with the '
                f'academic field\'s school ("{target.academic_field.school_id}").'
            )


# Attach event listeners
event.listen(Major, "before_insert", Major.validator)
event.listen(Major, "before_update", Major.validator)
event.listen(Major.name, "set", format_title_case, retval=True)


class AcademicField(BaseModel):
    """
    Table that contains academic_field information

    Entries are created to list available academic_fields.
    """

    __table_args__ = (
        Index("ix_academic_field_school_id", "school_id"),
        UniqueConstraint("name", "school_id", name="_field_school_uc"),
    )

    # Primary key that identifies the academic_field
    id = db.Column(db.Integer, primary_key=True)

    # AcademicField's value (e.g., academic_field code), lowercase
    value = db.Column(db.String(30), unique=True, nullable=False)

    # AcademicField's name, titlecase
    name = db.Column(db.String(100), nullable=False)

    # AcademicField's school
    # Many-to-One relationship with School model
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), nullable=False)
    school = db.relationship("School", backref="academic_fields", lazy=True)

    def __repr__(self):
        return f"AcademicField({self.id}, {self.name}, {self.school_id})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "id": self.id,
            "value": self.value,
            "name": self.name,
            "school_id": self.school_id,
        }


# Attach event listeners
event.listen(AcademicField.value, "set", format_lower_case, retval=True)


class Course(BaseModel):
    """
    Table that contains course information

    Entries are created to list available courses.
    """

    __table_args__ = (
        Index("ix_course_code", "code"),
        Index("ix_course_academic_field_id", "academic_field_id"),
        UniqueConstraint("code", "name", "academic_field_id", name="_course_field_uc"),
    )

    # Primary key that identifies the course
    id = db.Column(db.Integer, primary_key=True)

    # Course value (e.g., course code), uppercase
    code = db.Column(db.String(10), nullable=False)

    # Course name, titlecase
    name = db.Column(db.String(100), nullable=False)

    # AcademicField associated with the course
    # Many-to-One relationship with AcademicField model
    academic_field_id = db.Column(
        db.Integer, db.ForeignKey("academic_field.id"), nullable=False
    )
    academic_field = db.relationship("AcademicField", backref="courses", lazy=True)

    # University associated with the course
    # Many-to-One relationship with AcademicField model
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), nullable=False)
    school = db.relationship("School", backref="courses", lazy=True)

    def __repr__(self):
        return f"Course({self.id}, {self.code}, {self.name}, {self.academic_field_id})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "academic_field_id": self.academic_field_id,
            "school_id": self.school_id,
        }

    @staticmethod
    def validator(_mapper, connection, target):
        """Validate course data, ensuring school consistency with academic field."""
        academic_field = connection.execute(
            db.select(AcademicField).filter_by(id=target.academic_field_id)
        ).fetchone()

        if academic_field.school_id != target.school_id:
            raise ValueError(
                f'COURSE MODEL: School ("{target.school_id}") is inconsistent with the '
                f'academic field\'s school ("{target.academic_field.school_id}").'
            )


# Attach event listeners
event.listen(Course, "before_insert", Course.validator)
event.listen(Course, "before_update", Course.validator)
event.listen(Course.code, "set", format_upper_case, retval=True)
event.listen(Course.name, "set", format_title_case, retval=True)


class School(BaseModel):
    """
    Table that contains school information

    Entries are created to list available schools.
    """

    __table_args__ = (Index("ix_school_name", "name"),)

    # Primary key that identifies the school
    id = db.Column(db.Integer, primary_key=True)

    # School name, titlecase
    name = db.Column(db.String(100), nullable=False, unique=True)

    # School country, titlecase
    country = db.Column(db.String(100), nullable=True)

    # School state, titlecase
    state = db.Column(db.String(100), nullable=True)

    # Enterprise email, ex.: cornell.edu, lowercase
    email_postfix = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"School({self.id}, {self.name}, {self.email_postfix})"

    def to_dict(self, simplified=True) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "state": self.state,
            "email_postfix": self.email_postfix,
        }

    @staticmethod
    def validator(_mapper, _connection, target):
        """Validate school data, ensuring email postfix format is valid."""
        if target.email_postfix and not validate_email_postfix(target.email_postfix):
            raise ValueError(
                f'SCHOOL MODEL: Email postfix does not fit pattern ("{target.email_postfix}").'
            )


# Attach event listeners
event.listen(School, "before_insert", School.validator)
event.listen(School, "before_update", School.validator)
event.listen(School.name, "set", format_title_case, retval=True)
event.listen(School.country, "set", format_title_case, retval=True)
event.listen(School.state, "set", format_title_case, retval=True)
event.listen(School.email_postfix, "set", format_lower_case, retval=True)
