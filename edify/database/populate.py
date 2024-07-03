import json
from edify import db
from edify.models import *
from edify.utils.constants import (
    AuthLevelEnum,
    SupportedLanguagesEnum,
    OfferStatusEnum,
)


def populate_universities():
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
            # Check if the university already exists
            existing_university = School.query.filter_by(
                name=university_data["name"]
            ).first()
            if not existing_university:
                university = School(
                    name=university_data["name"],
                    country=university_data.get("country"),
                    state=university_data.get("state"),
                    email_postfix=university_data.get("email_postfix"),
                )
                db.session.add(university)

    print("Universities (Schools) populated.")


def populate_academic_fields():
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
            # Check if the academic_field already exists
            existing_academic_field = AcademicField.query.filter_by(
                value=academic_field_data["value"]
            ).first()
            if not existing_academic_field:
                school = School.query.filter_by(name="Cornell University").first()
                academic_field = AcademicField(
                    value=academic_field_data["value"],
                    name=academic_field_data["name"],
                    school_id=school.id if school else None,
                )
                db.session.add(academic_field)

    print("AcademicFields populated.")


def populate_methods():
    methods = [
        {"value": "text-message", "name": "Text Message"},
        {"value": "voice-call", "name": "Voice Call"},
        {"value": "video-call", "name": "Video Call"},
        {"value": "photo-explanation", "name": "Photo Explanation"},
    ]

    with db.session.begin():
        for method_data in methods:
            # Check if the method already exists
            existing_method = Method.query.filter_by(value=method_data["value"]).first()
            if not existing_method:
                method = Method(value=method_data["value"], name=method_data["name"])
                db.session.add(method)

    print("Methods populated.")


def populate_time_intervals():
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
            # Check if the time interval already exists
            existing_interval = TimeInterval.query.filter_by(
                value=interval_data["value"]
            ).first()
            if not existing_interval:
                time_interval = TimeInterval(
                    value=interval_data["value"],
                    name=interval_data["name"],
                    shortname=interval_data["shortname"],
                )
                db.session.add(time_interval)

    print("Time Intervals populated.")


def populate_notification_types():
    notification_types = [
        {"name": "General", "question_required": False},
        {"name": "Offer Accepted", "question_required": True},
        {"name": "Offer Declined", "question_required": True},
        {"name": "New Offer", "question_required": True},
        {"name": "Price Change", "question_required": True},
        {"name": "Question Solved", "question_required": True},
        {"name": "Account Verified", "question_required": False},
        {"name": "Password Reset", "question_required": False},
    ]

    with db.session.begin():
        for type_data in notification_types:
            # Check if the notification type already exists
            existing_type = NotificationType.query.filter_by(
                name=type_data["name"]
            ).first()
            if not existing_type:
                notification_type = NotificationType(
                    name=type_data["name"],
                    question_required=type_data["question_required"],
                )
                db.session.add(notification_type)

    print("Notification Types populated.")


def populate_majors():
    def load_majors_from_json(json_file):
        with open(json_file) as f:
            majors_data = json.load(f)["majors"]
        return majors_data

    majors_data = load_majors_from_json("edify/static/majors.json")

    with db.session.begin():
        school = School.query.filter_by(name="Cornell University").first()

        for major_data in majors_data:
            # Check if the major already exists
            existing_major = Major.query.filter_by(name=major_data["major"]).first()
            if not existing_major and school:
                academic_field = AcademicField.query.filter_by(
                    name=major_data["college"]
                ).first()

                if academic_field:
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
            # Check if the course already exists
            existing_course = Course.query.filter_by(code=course_data["code"]).first()
            if not existing_course:
                # Fetch academic_field based on its value
                academic_field = AcademicField.query.filter_by(
                    value=course_data["academic_field"]
                ).first()

                if academic_field:
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
    with db.session.begin():
        # Populate AuthLevel table
        for level in AuthLevelEnum.values():
            if not AuthLevel.query.filter_by(value=level).first():
                db.session.add(AuthLevel(value=level))

        # Populate SupportedLanguage table
        for lang in SupportedLanguagesEnum.values():
            if not SupportedLanguage.query.filter_by(value=lang).first():
                db.session.add(SupportedLanguage(value=lang))

        # Populate OfferStatus table
        for status in OfferStatusEnum.values():
            if not OfferStatus.query.filter_by(value=status).first():
                db.session.add(OfferStatus(value=status))

        # Commit the changes to the database
        db.session.commit()

    print("Enums populated.")


def populate_constants():
    populate_enums()
    populate_universities()
    populate_academic_fields()
    populate_methods()
    populate_time_intervals()
    populate_notification_types()
    populate_majors()
    populate_courses()
