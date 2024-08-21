# Standard Library imports
from http import HTTPStatus
from typing import List

# Third-Party Framework imports
from flask import jsonify
from flask_mail import Message

# Local Application imports
from edify import mail


def send(subject: str, body: str, recipients: List[str]):
    msg = Message(
        subject=subject,
        sender=mail.username,
        recipients=recipients,
    )

    msg.body = body

    mail.send(msg)

    return jsonify("Success."), HTTPStatus.OK
