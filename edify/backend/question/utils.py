# Standard Library imports
from http import HTTPStatus
from typing import Any, Dict, Optional

# Local Application imports
from edify.backend.user.utils import check_author
from edify.models import Offer
from edify.utils.constants import OfferStatusEnum


def question_dictionary(
    user_id: Optional[int], question_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Completes the given question dictionary with author status, offers,
    and offer statuses based on the user's ID.

    Args:
        user_id (Optional[int]): The ID of the user.
        question_dict (Dict[str, Any]): The dictionary containing question data.

    Returns:
        Dict[str, Any]: The updated question dictionary with additional information.
    """
    is_author = check_author(user_id, question_dict["id"])

    # Initialize offer-related variables
    offers = []
    offer_made = None
    offer_accepted = None

    if user_id:
        if is_author:
            # Fetch all active offers for the author's question
            offers = Offer.query.filter_by(
                question_id=question_dict["id"], active=True
            ).all()
            offers = Offer.to_dict_all(offers)

            # Attempt to get the accepted offer, if it exists
            offer_accepted = Offer.query.filter_by(
                question_id=question_dict["id"],
                active=True,
                status=OfferStatusEnum.ACCEPTED,
            ).one_or_none()
            offer_accepted = (
                offer_accepted.to_dict(simplified=False) if offer_accepted else None
            )
        else:
            # Fetch the made offer if the user is not the author
            offer_made = Offer.query.filter_by(
                question_id=question_dict["id"], user_id=user_id, active=True
            ).first()
            offer_made = offer_made.to_dict(simplified=False) if offer_made else None

    # Update the question dictionary with computed values
    question_dict["is_author"] = is_author
    question_dict["offers"] = offers
    question_dict["offer_made"] = offer_made
    question_dict["offer_accepted"] = offer_accepted

    return question_dict

def get_offers_from_question(id_question: str, id_user: int):
    """
    Fetch all offers received for a specific question.

    Args:
        id_question (int): The ID of the question to fetch offers for.
        id_user (int): The ID of the user to fetch offers for.

    Returns:
        JSON response with a list of offers or an error if the user is not the author.
    """
    # Query the Question model to find the question by its ID
    question = db.session.query(Question).get(id_question)

    # If question is not visible, return an error response
    if not question.visible:
        return error_response("Question is hidden", ErrorType.UNAUTHORIZED)
    
    # Query the Offer model for all active offers received for the specified question
    offers = (
        db.session.query(Offer).filter_by(question_id=question.id, active=True).all()
    )

    # Convert the list of offers to a dictionary format suitable for JSON response
    offers = Offer.to_dict_all(offers)

    # Return the list of offers in JSON format with HTTP 200 OK status
    return data_response(offers)
