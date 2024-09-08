# Standard Library imports
import json

# Local Application imports
from edify import db
from edify.models import *
from edify.utils.constants import (
    AuthLevelEnum,
    NotificationTypeEnum,
    OfferStatusEnum,
    SupportedLanguagesEnum,
)


def populate_universities():
    """Populate the database with predefined universities."""
    universities = [
        {
            "name": "Cornell University",
            "country": "USA",
            "state": "New York",
            "email_postfix": "cornell.edu",
        },
        {
            "name": "Harvard University",
            "country": "USA",
            "state": "Massachusetts",
            "email_postfix": "harvard.edu",
        },
        {
            "name": "Stanford University",
            "country": "USA",
            "state": "California",
            "email_postfix": "stanford.edu",
        },
    ]

    with db.session.begin():
        for university_data in universities:
            # Check for existing university by name
            existing_university = School.query.filter_by(
                name=university_data["name"]
            ).first()
            if not existing_university:
                # Create and add new university to the session
                university = School(
                    name=university_data["name"],
                    country=university_data.get("country"),
                    state=university_data.get("state"),
                    email_postfix=university_data.get("email_postfix"),
                )
                db.session.add(university)

    print("Universities (Schools) populated.")


def populate_academic_fields():
    """Populate the database with predefined academic fields."""
    academic_fields = [
        {"value": "cals", "name": "Agriculture and Life Sciences"},
        {"value": "aap", "name": "Architecture, Art and Planning"},
        {"value": "as", "name": "Arts and Sciences"},
        {"value": "dyson", "name": "Dyson"},
        {"value": "engineering", "name": "Engineering"},
        {"value": "human-ecology", "name": "Human Ecology"},
        {"value": "ilr", "name": "Industrial and Labor Relations"},
        {"value": "public-policy", "name": "Public Policy"},
    ]

    with db.session.begin():
        for academic_field_data in academic_fields:
            # Check for existing academic field by value
            existing_academic_field = AcademicField.query.filter_by(
                value=academic_field_data["value"]
            ).first()
            if not existing_academic_field:
                # Associate academic field with Cornell University
                school = School.query.filter_by(name="Cornell University").first()
                academic_field = AcademicField(
                    value=academic_field_data["value"],
                    name=academic_field_data["name"],
                    school_id=school.id if school else None,
                )
                db.session.add(academic_field)

    print("AcademicFields populated.")


def populate_methods():
    """Populate the database with predefined communication methods."""
    methods = [
        {"value": "text-message", "name": "Text Message"},
        {"value": "voice-call", "name": "Voice Call"},
        {"value": "video-call", "name": "Video Call"},
        {"value": "photo-explanation", "name": "Photo Explanation"},
    ]

    with db.session.begin():
        for method_data in methods:
            # Check for existing method by value
            existing_method = Method.query.filter_by(value=method_data["value"]).first()
            if not existing_method:
                # Create and add new method to the session
                method = Method(value=method_data["value"], name=method_data["name"])
                db.session.add(method)

    print("Methods populated.")


def populate_time_intervals():
    """Populate the database with predefined time intervals."""
    time_intervals = [
        {"value": 5, "name": "less than 5 min", "shortname": "<5 min"},
        {"value": 10, "name": "about 10 min", "shortname": "~10 min"},
        {"value": 20, "name": "about 20 min", "shortname": "~20 min"},
        {"value": 30, "name": "about 30 min", "shortname": "~30 min"},
        {"value": 45, "name": "about 45 min", "shortname": "~45 min"},
        {"value": 60, "name": "about 1 hour", "shortname": "~1 hour"},
        {"value": 90, "name": "about 1.5 hours", "shortname": "~1.5 hours"},
        {"value": 120, "name": "about 2 hours", "shortname": "~2 hours"},
        {"value": 999, "name": "over 2 hours", "shortname": ">2 hours"},
    ]

    with db.session.begin():
        for interval_data in time_intervals:
            # Check for existing time interval by value
            existing_interval = TimeInterval.query.filter_by(
                value=interval_data["value"]
            ).first()
            if not existing_interval:
                # Create and add new time interval to the session
                time_interval = TimeInterval(
                    value=interval_data["value"],
                    name=interval_data["name"],
                    shortname=interval_data["shortname"],
                )
                db.session.add(time_interval)

    print("Time Intervals populated.")


def populate_notification_types():
    """Populate the database with notification types based on the enumeration."""
    with db.session.begin():
        for type_name in NotificationTypeEnum.keys():
            # Check for existing notification type by value
            existing_type = NotificationType.query.filter_by(value=type_name).first()
            if not existing_type:
                # Create and add new notification type to the session
                notification_type = NotificationType(
                    value=type_name,
                    question_required=NotificationTypeEnum.requires_question(type_name),
                )
                db.session.add(notification_type)

    print("Notification Types populated.")


def populate_majors():
    """Populate the database with majors from a JSON file."""

    def load_majors_from_json(json_file):
        """Load majors data from a JSON file."""
        with open(json_file) as f:
            majors_data = json.load(f)["majors"]
        return majors_data

    majors_data = load_majors_from_json("edify/static/majors.json")

    with db.session.begin():
        school = School.query.filter_by(name="Cornell University").first()

        for major_data in majors_data:
            # Check for existing major by name
            existing_major = Major.query.filter_by(
                name=major_data["major"].strip().title()
            ).first()

            if not existing_major and school:
                # Associate major with the correct academic field
                academic_field = AcademicField.query.filter_by(
                    name=major_data["college"]
                ).first()

                if academic_field:
                    # Create and add new major to the session
                    major = Major(
                        name=major_data["major"],
                        academic_field_id=academic_field.id,
                        school_id=school.id,
                    )
                    db.session.add(major)
            elif not school:
                print(
                    f"School 'Cornell University' not found for major '{major_data['major']}'. Skipping."
                )

    print("Majors populated.")


def populate_courses():
    """Populate the database with predefined courses."""
    courses_data = [
        {
            "code": "ENG101",
            "name": "Introduction to Engineering",
            "academic_field": "engineering",  # Engineering academic_field
        },
        {
            "code": "ART203",
            "name": "Modern Art History",
            "academic_field": "as",  # Arts and Sciences academic_field
        },
        {
            "code": "AGRI202",
            "name": "Agricultural Economics",
            "academic_field": "cals",  # Agriculture and Life Sciences academic_field
        },
    ]

    with db.session.begin():
        for course_data in courses_data:
            # Check for existing course by code
            existing_course = Course.query.filter_by(code=course_data["code"]).first()
            if not existing_course:
                # Fetch associated academic field
                academic_field = AcademicField.query.filter_by(
                    value=course_data["academic_field"]
                ).first()

                if academic_field:
                    # Create and add new course to the session
                    course = Course(
                        code=course_data["code"],
                        name=course_data["name"],
                        academic_field_id=academic_field.id,
                        school_id=academic_field.school_id,
                    )
                    db.session.add(course)
                else:
                    print(
                        f"AcademicField '{course_data['academic_field']}' not found for course '{course_data['name']}'. Skipping."
                    )

    print("Courses populated.")


def populate_enums():
    """Populate the database with various enumerations."""
    with db.session.begin():
        # Populate AuthLevel table
        for level in AuthLevelEnum.keys():
            if not AuthLevel.query.filter_by(value=level).first():
                db.session.add(AuthLevel(value=level))

        # Populate SupportedLanguage table
        for lang in SupportedLanguagesEnum.keys():
            if not SupportedLanguage.query.filter_by(value=lang).first():
                db.session.add(SupportedLanguage(value=lang))

        # Populate OfferStatus table
        for status in OfferStatusEnum.keys():
            if not OfferStatus.query.filter_by(value=status).first():
                db.session.add(OfferStatus(value=status))

        # Commit the changes to the database
        db.session.commit()

    print("Enums populated.")


def populate_constants():
    """Function to populate all constants into the database."""
    populate_enums()
    populate_universities()
    populate_academic_fields()
    populate_methods()
    populate_time_intervals()
    populate_notification_types()
    populate_majors()
    populate_courses()


if __name__ == "__main__":
    populate_constants()
