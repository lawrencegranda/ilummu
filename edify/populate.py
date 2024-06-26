import json
from edify import db
from edify.models import (
    Subject,
    Method,
    TimeInterval,
    School,
    NotificationType,
    Major,
    Course,
)


def populate_universities():
    universities = [
        {"name": "Cornell University", "country": "USA", "state": "New York"},
        {"name": "Harvard University", "country": "USA", "state": "Massachusetts"},
        {"name": "Stanford University", "country": "USA", "state": "California"},
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
                )
                db.session.add(university)

    print("Universities (Schools) populated.")


def populate_subjects():
    subjects = [
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
        for subject_data in subjects:
            # Check if the subject already exists
            existing_subject = Subject.query.filter_by(
                value=subject_data["value"]
            ).first()
            if not existing_subject:
                school = School.query.filter_by(name="Cornell University").first()
                subject = Subject(
                    value=subject_data["value"],
                    name=subject_data["name"],
                    school_id=school.id if school else None,
                )
                db.session.add(subject)

    print("Subjects populated.")


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
        {"name": "General"},
        {"name": "Offer Accepted"},
        {"name": "Offer Declined"},
        {"name": "New Offer"},
        {"name": "Price Change"},
        {"name": "Question Solved"},
        {"name": "Account Verified"},
        {"name": "Password Reset"},
    ]

    with db.session.begin():
        for type_data in notification_types:
            # Check if the notification type already exists
            existing_type = NotificationType.query.filter_by(
                name=type_data["name"]
            ).first()
            if not existing_type:
                notification_type = NotificationType(name=type_data["name"])
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
                subject = Subject.query.filter_by(name=major_data["college"]).first()

                if subject:
                    major = Major(
                        name=major_data["major"],
                        subject_id=subject.id,
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
            "subject": "engineering",  # Engineering subject
        },
        {
            "code": "ART203",
            "name": "Modern Art History",
            "subject": "as",  # Arts and Sciences subject
        },
        {
            "code": "AGRI202",
            "name": "Agricultural Economics",
            "subject": "cals",  # Agriculture and Life Sciences subject
        },
    ]

    with db.session.begin():
        for course_data in courses_data:
            # Check if the course already exists
            existing_course = Course.query.filter_by(code=course_data["code"]).first()
            if not existing_course:
                # Fetch subject based on its value
                subject = Subject.query.filter_by(value=course_data["subject"]).first()

                if subject:
                    course = Course(
                        code=course_data["code"],
                        name=course_data["name"],
                        subject_id=subject.id,
                        school_id=subject.school_id,
                    )
                    db.session.add(course)
                else:
                    print(
                        f"Subject '{course_data['subject']}' not found for course '{course_data['name']}'. Skipping."
                    )

    print("Courses populated.")


if __name__ == "__main__":
    populate_universities()
    populate_subjects()
    populate_methods()
    populate_time_intervals()
    populate_notification_types()
    populate_majors()
    populate_courses()
