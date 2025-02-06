"""
Mail utils
"""

# Standard Library imports
from http import HTTPStatus
from typing import List

# Third-Party Framework imports
from flask import current_app, jsonify
from flask_mail import Message

# Local Application imports
from edify.core import mail
from edify.utils.constants import ErrorType
from edify.utils.utils import error_response


def send(subject: str, html: str, recipients: List[str]) -> tuple:
    """Sends an email with the specified subject and HTML content.

    Args:
        subject (str): The subject of the email.
        html (str): The HTML content of the email.
        recipients (List[str]): A list of email addresses to send the email to.

    Returns:
        tuple: A tuple containing a JSON response message and an HTTP status code.
    """
    msg = Message(
        subject=subject,
        sender=current_app.config["MAIL_SENDER"],
        recipients=recipients,
        cc=[current_app.config["MAIL_SENDER"]],
    )

    msg.body = html
    msg.html = html

    # pylint: disable=broad-exception-caught
    try:
        mail.send(msg)
    except Exception as _:
        return error_response(
            f"Failed to send email to {str(recipients)}.", ErrorType.INTERNAL_ERROR
        )

    return jsonify("Success."), HTTPStatus.OK
