# Standard Library imports
from http import HTTPStatus
import datetime

# Third-Party Framework imports
from faker import Faker
from flask import Flask, url_for
import pytest

# Local Application imports
from edify import db
from edify.models import User, Offer, Question, Method, Course
from edify.utils.constants import OfferStatusEnum

# Initialize Faker for generating fake data
fake = Faker()


class TestCreateOffer:

    def test_create_offer_success(self, client_with_question, user_jwt):
        """
        Test creating an offer successfully.
        """
        pass
